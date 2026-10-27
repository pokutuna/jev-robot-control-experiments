---
type: Guide
title: dora のノード構成と命令の形式
description: LIBERO を dora-rs の sim / policy / evaluator ノードに分けた構成。各ノードの入出力、policy が sim に送る命令と結果の形式、方策の推論が遅いときの振る舞い
tags: [robotics, libero, dora]
---

# dora のノード構成と命令の形式

LIBERO のシミュレーションを、dora-rs のノードに分けて動かす構成。ロボットを非同期の分散システムとして扱い、センサとロボット (sim)、方策 (policy)、評価 (evaluator) を別のノードにする。dora 自体の挙動と注意点は [dora-rs で LIBERO のノードを動かすときの挙動と注意点](../findings/dora-dataflow.md) にある。

## ノードと入出力

```
          tick (50 ms)
              │
              ▼
          ┌───────┐ task, image_agentview, image_wrist,       ┌────────┐
          │  sim  │ robot_state, command_result               │ policy │
          │       │ ────────────────────────────────────────▶ │        │
          │       │ ◀──────────────────────────────────────── │        │
          └───────┘                                command    └────────┘
              │ image_agentview, image_wrist, ground_truth,       │
              │ task, command_result, episode_end                 │ command
              ▼                                                   │
         ┌───────────┐ ◀──────────────────────────────────────────┘
         │ evaluator │ → outputs/runs/<日時>/
         └───────────┘
```

| ノード | ファイル | 役割 |
| --- | --- | --- |
| sim | `nodes/sim.py` | tick ごとに LIBERO を 1 step 進め、画像、ロボットの状態、真値を流す。命令を受けて制御器の目標を書き換え、命令が終わったら結果を出す。実機のロボットドライバとセンサに当たる |
| policy | `nodes/scripted_policy.py` など | 画像とロボットの状態から命令を決める |
| evaluator | `nodes/evaluator.py` | 真値で成功を判定し、動画 (`episode.mp4`)、step ごとの真値 (`ground_truth.jsonl`)、命令と結果などの出来事 (`events.jsonl`)、まとめ (`summary.json`) を保存する |

sim の出力:

| 出力 | 中身 |
| --- | --- |
| `task` | タスクの名前、指示文、固定カメラの置き方と射影行列の JSON (`{"suite", "task_name", "instruction", "fixed_view", "camera_matrix"}`)。`fixed_view` は `agentview` か `quarterview`。`camera_matrix` は世界座標 [m] を `image_agentview` の画素 (u は右、v は下へ増える) に移す 3x4 の行列 (`LiberoEnv.camera_matrix`)。カメラの校正値にあたり、方策が手先の位置を画像に描くのに使う。最初に 1 回だけ送る |
| `image_agentview` | 斜め上の固定カメラの画像。uint8 の 1 次元配列で、shape はメタデータの `shape` |
| `image_wrist` | 手首カメラの画像 |
| `robot_state` | `Percept` の画像以外 (手先の姿勢、指の開き、腕の関節角) の JSON |
| `ground_truth` | `GroundTruth` (物体と固定物の姿勢、固定物の関節値、成功判定) の JSON |
| `command_result` | 命令の結果の JSON |
| `episode_end` | エピソードを終えた理由の JSON (`{"reason", "step"}`)。終わる直前に 1 回だけ送る |

どの出力もメタデータの `step` に step 番号が入る。

sim がエピソードを終える条件と、`episode_end` の `reason` は次のとおり。

| reason | 条件 |
| --- | --- |
| `policy_end` | policy が `{"type": "end"}` を送った |
| `policy_closed` | policy が `end` を送らずに止まり、`command` の入力が閉じた (policy の例外など)。sim はすぐに止まり、`dora run` は終了コード 1 で policy の traceback を出す |
| `max_steps` | step 数が `MAX_STEPS` に達した |

evaluator の `summary.json` には、成功判定のほかに、タスクの情報、`end_reason`、命令の数 (`commands`)、結果の status ごとの数 (`command_status`) が入る。`events.jsonl` の各行は `{"step", "kind", ...}` で、`kind` は evaluator の入力の名前 (`task`、`command`、`command_result`、`episode_end`) である。`command` には step 番号が無いので、evaluator がその前に受けた sim の出力の step 番号を付ける。

policy は `ground_truth` を購読しない。物体の姿勢を方策に渡す「JSON 入力」条件のときだけ、dataflow で `sim/ground_truth` を policy の入力につなぐ (`dataflows/scripted_json.yml` の `scene`)。

ノードの中身は `src/s1cap/` にあり、dora に依存しない。sim は `RobotDriver` (`src/s1cap/driver.py`)、evaluator は `EpisodeRecorder` (`src/s1cap/recorder.py`)、手書きの方策は `ScriptedPolicy` (`src/s1cap/scripted.py`) を使う。`nodes/` には dora との受け渡しだけを書く。

## 命令の形式

policy は `command` に JSON の命令を送る。ROS 2 の action と同じく、sim は命令を受け付けた後、終わったときに `command_result` で結果を返す。

```json
{"id": 1, "type": "move_to", "pos": [-0.1, 0.0, 1.05], "quat": [1, 0, 0, 0], "gripper": 1.0}
{"id": 2, "type": "move_delta", "dpos": [0, 0, 0.1]}
{"id": 3, "type": "gripper", "closed": true}
{"id": 4, "type": "hold"}
{"type": "end"}
```

| type | 動き | 終わる条件 |
| --- | --- | --- |
| `move_to` | 手先を `pos` (世界座標 [m]) へ動かす。`quat` (xyzw) と `gripper` (-1 で開き +1 で閉じる) は省略でき、省略すると今の目標の向きと最後の指の指令を保つ | 位置が目標から `tol` (既定 0.005 m) 以内で reached。`timeout_steps` (既定 200) step で届かなければ timeout |
| `move_delta` | 手先を今の位置から `dpos` [m] 動かす。向きと指の指令は保つ | `move_to` と同じ |
| `gripper` | 手先の目標を保ったまま、指を閉じる (`closed: true`) か開く | 15 step で reached |
| `hold` | 今の手先の姿勢で止まる | すぐに reached |
| `end` | エピソードを終える。sim が止まり、evaluator が記録を閉じる | 結果は返さない |

`move_to` と `move_delta` には、`tol` [m] と `timeout_steps` を付けて既定値を変えられる。

結果は `{"id": 1, "status": "reached", "started_step": 40, "steps": 23, "message": ""}` の形で、`started_step` は命令を受け付けた step、`steps` は終わるまでの step 数である。`status` は次のどれかになる。

| status | 意味 |
| --- | --- |
| `reached` | 終わる条件を満たした |
| `timeout` | 時間内に届かなかった。手先はその場の姿勢で止まる |
| `preempted` | 実行中に次の命令が来て、打ち切られた |
| `rejected` | 命令の形式が正しくない。`message` に理由が入る。実行中の命令はそのまま続く |

命令が来ない間、sim は最後の目標を保つ。命令を出し終えた後や、次の命令を考えている間も、手先はその場に留まり、掴んだ物を離さない。座標系と、目標に届かないときの振る舞いは [LIBERO のロボットの動かし方](robot-control.md) にある。

### 小さな相対移動と tol

`reached` は手先が目標から `tol` 以内に入った時点で返る。その後も制御器は目標へ寄り続け、20 step 後には目標との差が 0.1〜0.3 mm になる。ところが `move_delta` は「今の手先の位置」から `dpos` だけ動かすので、`reached` を受けてすぐに次の `move_delta` を送ると、届いていなかった分 (最大 `tol`) が目標から抜け落ちる。既定の `tol` (5 mm) で 2 cm ずつ動かすと、1 回あたり 2〜4 mm 足りなくなる。

`move_delta` を 1 回だけ送って、`reached` の時点で目標からどれだけ離れているかを測った (task 8、init state 0、2026-10-26)。

| tol | reached までの step 数 | reached の時点での目標との差 |
| --- | --- | --- |
| 5 mm (既定) | 1〜7 | 3.3〜5.0 mm |
| 2 mm | 4〜8 | 1.4〜2.0 mm |
| 1 mm | 6〜9 | 0.6〜0.9 mm |
| 0.5 mm | 8〜23 | 0.4〜0.5 mm |

dpos は x +2 cm、z +2 cm、y +1 cm、z -5 mm の 4 通りである。小さな相対移動を続けて送る方策 (画像を見ながら少しずつ寄せる方策) では `tol` を 1 mm にするとよい。step 数は既定より 2〜5 増えるだけで済む。0.5 mm にすると、23 step かかることがあった。

## 方策の推論が遅いとき

sim は方策を待たずに 50 ms ごとに進む (非同期)。手書きの方策に、結果を受けてから次の命令を出すまでの待ち時間 (`POLICY_DELAY_MS`) を入れ、「put the bowl on the plate」(task 8、init state 0) を動かした (2026-10-26)。

| 待ち時間 | 結果から次の命令まで | 成功 | 成功した step | 全体の step |
| --- | --- | --- | --- | --- |
| 0 ms | 0 step (0.4 ms) | する | 106 | 129 |
| 500 ms | 10 step (504 ms) | する | 161 | 222 |
| 2000 ms | 40 step (2005 ms) | する | 341 | 486 |

命令の往復そのものは 1 ms 未満で、tick の間に収まる。方策が遅くても、待つ間はロボットが目標を保って止まっているだけで、結果は変わらなかった。待ち時間の分だけエピソードが長くなり、動画に止まっている場面が増える。

この結果は、命令を出した後は sim の制御器に任せる命令の形式でのものである。方策が画像を見て細かく動きを直す使い方では、画像が届いてから命令が届くまでにロボットが動くので、推論の遅さが結果に効く可能性がある (未確認)。

非同期なので、方策の推論時間が 1 step (50 ms) の幅で揺れると、命令が届く step も揺れる。同じ init state、同じ方策でも、実行ごとに step 数や軌道が少し変わる。

## policy を差し替えるとき

policy ノードは `command` を出し、`command_result` を受けるという約束さえ守れば差し替えられる。画像から命令を決める方策と、LLM が書いたコードを実行する方策の 2 種類を、仮の policy ノード (判断の中身は真値を使った仮のもの) で dora に載せ、どちらも「put the bowl on the plate」を成功させた (2026-10-26)。

画像を見て少しずつ動かす方策 (Jev のような System 1 の方策):

- `image_agentview` と `robot_state` を `queue_size: 1` で購読すると、判断を始めるときに最新の画像を受けられる。古い画像が溜まって、それを順に読むことにはならない
- 判断に時間がかかると、その間に sim が進む。判断に 300 ms かかると、命令が届くときには、判断に使った画像は 6 step 前のものになっていた
- 小さな `move_delta` を続けて送るので、`tol` を 1 mm 程度にする (前節)

コードを生成して実行する方策 (Code as Policies):

- 生成したコードは `move_to(...)` のように、命令が終わるまで返らない関数を順に呼ぶ。dora のイベントのループとは別のスレッドで実行し、両者をキューでつなぐ。dora の呼び出し (`node.next`、`node.send_output`) はメインスレッドに限り、`node.next(timeout=0.01)` で待ちながら、コードのスレッドが積んだ命令を送り、届いた結果を返す。このとき結果から次の命令までに 12 ms かかった
- コードが状況を確かめる関数 (`check()` など) は、その時点の最新の観測を返す必要がある。最初の 1 つだけを読む入力 (`scripted_json.yml` の `scene`) とは違い、`queue_size: 1` で購読し続け、最後に受けたものを返す
- 指示文は sim の `task` 出力から受け取り、コードを生成するプロンプトに入れる
