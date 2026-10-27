<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 観測を知覚と真値に分け、相対移動の命令を用意する

ID: 02-percept-api
Bunch: ../20261026-dora-nodes.md

## Goal

`LiberoEnv` の観測を、ロボットが知覚できるもの (`Percept`) とシミュレータの真値 (`GroundTruth`) の別々の型に分ける。物体の座標を使わずに手先を動かす命令 (今の位置からの相対移動、指の開閉) と、目標を保ち続ける制御器を `src/s1cap/` に用意する。

## Done When

- `env.perceive()` が `Percept` (画像、手先の姿勢、指、腕の関節角) を、`env.ground_truth()` が `GroundTruth` (物体と固定物の姿勢、固定物の関節値、成功判定) を返し、`step` と `reset` は `Percept` を返す
- 制御器 (目標の手先姿勢と指の指令を持ち、知覚から毎 step の action を計算する) があり、`move_to`、相対移動、`set_gripper` がその上で動く。物を掴んだまま動かしても、指が勝手に開かない
- `scripts/probe_scene.py`、`scripts/viewer.py`、wiki のページ (`wiki/guides/robot-control.md`、`wiki/guides/mujoco-viewer.md`) が新しい API に合わせて動く・書かれている。ruff が通る

## Context

- 今の `Observation` (`src/s1cap/sim.py`) は、画像、手先、指と一緒に、物体と固定物の姿勢、固定物の関節値をまとめて持つ。方策に渡すとき、真値が混ざらない型にしたい
- 知覚に入れるもの: カメラ画像 (agentview、robot0_eye_in_hand)、手先の位置と向き (xyzw)、指の関節値と開き、腕の 7 関節の角度。実機でもロボット自身のセンサで分かる情報に限る
- 真値に入れるもの: 物体と固定物の姿勢、引き出しやつまみの関節値、BDDL の成功判定
- `src/s1cap/control.py` の `move_to` は既定で `gripper=-1.0` (開く) なので、掴んだ後に `move_to` を呼ぶと指が開く。最後に送った指の指令を保つようにする
- 03 以降の sim ノードは、命令 (目標) を受け取り、命令の間も目標を保つ制御器で毎 tick の action を出す。この制御器を dora に依存しない形でここに作る
- OSC_POSE の action と測定値は `wiki/guides/robot-control.md` にある (1 step の移動は目標の一部で、`dx = 1` で約 0.7 cm)
- 確認には `LIBERO_ROOT` が要る。`.env` に書いてあるので `uv run --env-file .env ...` で動かす

## Result

`LiberoEnv` は `perceive()` で `Percept` (画像、手先、指、腕の関節角) を、`ground_truth()` で `GroundTruth` (物体、固定物、関節値、成功判定) を返す。`step` と `reset` は `Percept` を返す。`src/s1cap/control.py` の `PoseController` が目標の手先姿勢と指の指令を保ち、`Percept` から action を計算する。`move_to`、`move_delta`、`set_gripper` はその上で動き、ボウルを皿に置く手書きの流れが init state 0〜2 で成功した。

後続タスク向けの注意:

- sim ノード (03) は `PoseController` を持ち、命令で `pos` / `quat` / `gripper` を書き換え、毎 tick `ctrl.action(percept)` を `env.step` に渡せばよい
- `env.gripper_command` が最後に送った指の指令を持つ。reset で -1 (開く) に戻る
- ボウルの掴み方と使い方は [wiki/guides/robot-control.md](../../../wiki/guides/robot-control.md) にある

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-26 11:18 sim.py の Observation を Percept (画像、手先、指、腕の関節角) と GroundTruth (物体、固定物、関節値、成功判定) に分け、perceive() / ground_truth() を用意した
  - env.gripper_command に最後の指の指令を持たせ、move_to は gripper 省略時にそれを保つ
- 2026-10-26 11:18 control.py に PoseController (目標の姿勢と指の指令を保ち、Percept から action を計算) を作り、move_to / move_delta / set_gripper をその上に載せた
- 2026-10-26 11:18 ボウルを掴んで皿に置く流れを init 0〜2 で試し、すべて success (約 2.5 秒)。掴んだ後の move_delta で指は閉じたまま (幅 0.0067 m)、ボウルは 14.2 cm 持ち上がった
  - 掴めたのは +y 側の縁 (中心から y +6 cm、z +3 cm)。中心、+x、-x の縁では空振り
- 2026-10-26 11:18 probe_scene.py (scene.json を percept / ground_truth に分割)、viewer.py (move_delta を追加、pos は ground_truth から)、wiki と docs/setup.md を更新。mjpython のシェルで動作を確認し、ruff が通った
