---
type: Finding
title: dora-rs で LIBERO のノードを動かすときの挙動と注意点
description: dora-rs 1.1.0 を uv の Python 3.14 で使い、LIBERO の sim ノードと evaluator ノードを動かして分かったこと。起動、作業ディレクトリ、入力の待ち行列、ログ、画像の受け渡し、step の速さ
tags: [robotics, libero, dora]
---

# dora-rs で LIBERO のノードを動かすときの挙動と注意点

2026-10-26 に、dora-rs 1.1.0 (PyPI の `dora-rs` と `dora-rs-cli`) と pyarrow 26.0.0 を、uv で作った Python 3.14 の venv に入れて試した結果。構成は `dataflows/sim_eval.yml` (sim と evaluator) で、ノードの入出力は [dora のノード構成と命令の形式](../guides/dora-nodes.md) にある。

## 起動

- `uv run dora run <yaml>` で、coordinator、daemon、各ノードがまとめて起動する。ノードは venv の Python (`.venv/bin/python -u <path>`) で起動された
- dora-rs-cli は依存に uv (0.13.5) を持つので、venv に uv が入る。動作に支障は無かった
- 全ノードが `Node()` を作り終えると「all nodes are ready」となり、dataflow が始まる。組込みのタイマー (`dora/timer/millis/50`) の tick もここから届く
- 上流のノードが終わると、下流のノードには入力ごとに `INPUT_CLOSED` イベントが届く。全部の入力が閉じたら自分でループを抜ける (`nodes/evaluator.py`)。全ノードが終わると `dora run` も終わる
- ノードが例外で止まっても、他のノードは止まらない。下流には、正常に終わったときと同じく `INPUT_CLOSED` が届く。全ノードが終わると、`dora run` は終了コード 1 で止まったノードの traceback を出す。sim ノードは、policy からの `command` の入力が閉じたらエピソードを終える (`episode_end` の `reason` は `policy_closed`)。こうしないと、policy が止まった後も sim は `MAX_STEPS` まで進み続ける
- ノードが出力を送った直後に終わると、下流のノードには、その出力より先にその入力の `INPUT_CLOSED` が届くことがある。policy ノードが `end` を送ってすぐにループを抜けると、実験 001 の 10 エピソード中 6 回で sim が `end` を受け取らず `policy_closed` と記録した。policy ノードは `end` を送った後も、sim の出力 (`robot_state`) が閉じるまで入力を読み捨てて待つ (`nodes/jev_policy.py`)

## ノードの作業ディレクトリ

ノードは dataflow の yaml があるディレクトリで起動される。`path:` も yaml からの相対パスで書く。ノードの中で相対パス (`outputs/...` など) を使うと、yaml の隣にできる。リポジトリの決まった場所に書くときは、ノードのファイルの位置 (`Path(__file__)`) から決める。

## 入力の待ち行列

- 入力ごとに待ち行列があり、溢れると古いイベントから捨てられ、`Discarding event for input ... due to queue size limit` の WARN が出る。既定の長さは 10 だった (このとき evaluator の起動中に届いたイベントが捨てられた)
- 長さは yaml の入力ごとに `queue_size` で変えられる

  ```yaml
  inputs:
    tick:
      source: dora/timer/millis/50
      queue_size: 1      # 遅れた tick は溜めず、最新の 1 つだけ受ける
    ground_truth:
      source: sim/ground_truth
      queue_size: 1000   # 記録用。1 つも落とさない
  ```

- sim ノードが `Node()` の後で LIBERO の reset (数秒かかる) をすると、その間の tick が溜まり、捨てられた。reset を `Node()` の前に済ませると捨てられなくなった

## ログ

- `dora run` の既定の `--log-level stdout` は、ノードの stdout と dora のログを全部出す
- `--log-level info` にすると、ノードの stdout (`print`) は出なくなる。ノードから `node.log("info", "...")` で送ったメッセージは INFO として出る。Python の `logging` の出力は info でも warn でも出なかった
- 大きな出力 (画像) の最初の数回に、`(dora-rs/dora#2742 diagnostic)` という WARN が 3 行ずつ出る。100 step の実行では 9 行で、それ以降は出なかった
- `--log-filter "node=level"` でノードごとの level を変えられる。メッセージの種類では絞れない

このリポジトリのノードは、知らせたいことを `node.log("info", ...)` で出し、`--log-level info` で動かす。

## 画像と構造化データの受け渡し

- 画像は `pa.array(img.ravel())` で 1 次元の Arrow 配列にし、shape をメタデータ (`{"shape": [H, W, 3]}`) で送る。受け側で `value.to_numpy().reshape(shape)` する (`nodes/arrow_io.py`)
- 512×512×3 の uint8 を 50 ms ごとに送ったとき、配送の遅れは平均 1.42 ms、最大 41.8 ms だった。大きいメッセージは共有メモリ経由で送られる
- dict は JSON の文字列 1 つの Arrow 配列 (`pa.array([json.dumps(d)])`) で送っている
- メタデータには int、float、int のリストを入れられた。sim の出力には step 番号を入れ、evaluator は step 番号で画像と真値を対応付ける

## sim の速さ

LIBERO の 1 step (OSC_POSE の action 1 つ、1/20 秒) にかかる時間を、カメラ 2 台 (agentview と手首) の画像の一辺ごとに測った。dora を通さずに `env.step` だけを測った値である。

| 画像の一辺 | 1 step の平均 | 95 パーセンタイル |
| --- | --- | --- |
| 128 px | 17.9 ms | 18.6 ms |
| 256 px | 18.1 ms | 18.6 ms |
| 512 px | 18.8 ms | 19.5 ms |

時間のほとんどは物理の計算で、画像の大きさにはほとんど左右されない。dora で 50 ms の tick ごとに 1 step 進めると、256 px でも 512 px でも 100 step を 5.0 秒 (20.1 step/s) で進め、evaluator は 101 フレーム (step 0〜100) を 1 つも落とさずに記録した。

## 命令の結果が届かなかった例

実験 013 の init 3 (2026-10-31) で、sim が出した `command_result` が policy にも evaluator にも届かず、policy が結果を待ったまま `MAX_STEPS` まで進んだ[^lost]。同じ命令を同じ step に送り直すと、dora を通さない `RobotDriver` では step 172 に reached になった。dora の実行では、その頃 (開始から約 40 秒) に sim のログに `zenoh_shm::watchdog::periodic_task Some("Watchdog Validator"): timer overrun` が出ていた。このとき、同じ Mac で LIBERO を使う probe のスクリプトを 2 つ並べて回していた。

timer overrun と結果が届かないことの因果は確かめていない。006 の init 9 では evaluator に timer overrun が出たが、届かなかった出力は無かった。policy は結果を待つ間に次の命令を送らないので、結果が 1 つ落ちるとエピソードが止まる。dora の実行中は、ほかの重い処理を同じ Mac で並べて回さない。

[^lost]: `experiments/013-text-baseline/excluded-runs/init3-20261031-165527/`と、その Task Document (`docs/tasks/20261031-report-experiments/02-exp-text-baseline.md`) の Work Log
