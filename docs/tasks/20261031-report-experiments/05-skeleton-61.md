<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 017: 人が書いた手順の骨組みを task 61 で回す

ID: 05-skeleton-61
Bunch: ../20261031-report-experiments.md

## Goal

アウトラインの実験 4。物を掴んで置き場所に置くタスクに共通の手順の骨組みを、CaP と同じ `s1cap.cap` の部品で人が 1 度だけ書き、タスクに固有の値だけを埋めて libero_90 61 で回す。

## Done When

- `experiments/017-skeleton/` に骨組み (`programs/skeleton.py`)、task 61 の値 (`programs/task61.py`)、dataflow、runs (init 0〜9)、results.md、README がある
- 骨組みに特定のタスクの解き方 (物の名前、座標、決まった移動量) が書かれていない
- README に成功率と失敗の仕方が書いてあり、動画か真値で確かめてある

## Context

- 値と骨組みは policy ノードの `PROGRAM` に `,` で並べ、その順につないで 1 つのプログラムにする (`nodes/jev_policy.py`)
- 位置合わせは 006 と同じ (固定カメラで寄せ、手首カメラで合わせる)
- 値は 04 (015、016) の結果から選ぶ

## Result

3 つ目の版の骨組みで task 61 を 10/10 で終えた ([experiments/017-skeleton/README.md](../../../experiments/017-skeleton/README.md))。平均 63.6 回の判断、Jev の呼び出し 38.9 回、入力 4.1 万トークン。

骨組みは task 61 の結果を見て 2 回直した (置く前に 3 cm 上げる、物を持っている間は手首の画像で y だけを合わせる)。この 2 つの知見は `KNOWLEDGE["017"]` として CaP にも渡す (021、022)。018 以降は 3 つ目の版で回す。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-31 17:00 骨組み (programs/skeleton.py) と task 61 の値 (programs/task61.py)、dataflow を書いた。部品を差し替えた空の実行で手順が最後まで通ることを確かめた (35 回の移動)
  - run_experiment.py は、PROGRAM_DIR が無ければ PROGRAM の各パスを実験のディレクトリから解決する
  - 言い方は 016 で y の向きが 93% 近づき、合っているときに 87% 動かさない "the chocolate pudding box" にした
- 2026-10-31 17:59 017 を 3 回回した。1 回目、2 回目の記録は excluded-runs/ (results-v1.md、results-v2.md)
  - v1 (骨組みの初版): 9/10。init 4、7 で、離した後に上げるとトレイが 21〜22 cm 持ち上がった。指が開ききらず (6.8 cm) トレイの仕切りを押していた
  - v2 (当たって止まった所から 3 cm 上げてから離す): 7/10。失敗 3 件とも、箱を持ったまま手首の画像でトレイに合わせると x の答えが +x を向き続け、箱をトレイの +x の縁に置いた
  - v1、v2 の 20 エピソードで、箱を持っているときの wrist_direction (トレイ) は、2 cm 以上離れた軸で x が近づく 8、動かさない 23、遠ざかる 71。y は近づく 23、動かさない 29、遠ざかる 0。固定カメラが (0, 0) と答えた所は、トレイの中心から x に 0.7〜4.7 cm、y に -2.0〜-5.9 cm
  - v3: 物を持っている間は、手首の画像では y だけを合わせる (x は固定カメラの答えまで)。物を持つと手首の画像で × の -x の側が隠れるため。物によらない規則として骨組みに入れた
  - 018 は v2 の骨組みで 2 エピソード回したところで止め、記録は使わない
- 2026-10-31 18:24 v4: 置き場所に何も持たないうちに合わせて位置を覚え、掴んだ後はそこへ move_to する。017 を回し直す (v3 は excluded-runs/results-v3.md、skeleton-v3.py)
- 2026-10-31 18:40 v4 で 017 は 10/10。覚えた置き場所はトレイの中心から x -5.2〜-8.3 cm、y -2.3〜-4.7 cm。README を v4 に書き直した
