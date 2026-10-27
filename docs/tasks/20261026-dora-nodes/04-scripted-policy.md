<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 手書きの policy ノードで命令の閉ループを回す

ID: 04-scripted-policy
Bunch: ../20261026-dora-nodes.md

## Goal

policy → sim の命令の形式と、命令の実行中・完了後の sim の振る舞いを決めて実装する。手書きの policy ノードが命令を出し、sim から完了の知らせとロボットの状態を受けて次の命令を出す閉ループを回し、LIBERO-Goal の「put the bowl on the plate」を成功させる。

## Done When

- 命令の形式 (種類、引数、完了の知らせ方、タイムアウト) が決まり、`src/s1cap/` に dora に依存しない形で実装されている。sim ノードは命令を受けて制御器の目標を書き換え、完了したら結果を出す
- 手書きの policy ノードと dataflow があり、`dora run` で task 8 が成功し (evaluator の `summary.json` の `success` が true)、動画が残る
- 非同期 (実時間の tick) で動かしたときの命令の往復の遅れを測り、05 で同期モードが要るかの判断材料を Result に書く。ruff が通る

## Context

- Approach & Rules: policy は真値 (`ground_truth`) を購読しない。比較用の「JSON 入力」条件のときだけ、物体の姿勢を明示して渡す。手書きの policy は画像から物体の位置を推定しないので、物体の位置を JSON 入力条件で受け取る。dataflow の名前などで JSON 入力条件だと分かるようにする
- 03 の成果: `src/s1cap/driver.py` の `RobotDriver` が `PoseController` を持ち、`step()` で目標へ向かう action を 1 つ送る。sim ノード (`nodes/sim.py`) は 50 ms の tick ごとに `image_agentview`、`image_wrist`、`robot_state`、`ground_truth` を流し、メタデータに `step` を入れる。evaluator は `outputs/runs/<日時>/` に動画と記録を書く。dora の注意点は `wiki/findings/dora-dataflow.md`
- 02 の成果: `src/s1cap/control.py` の `move_to` / `move_delta` / `set_gripper` が同期的な命令の見本。`move_to` は位置が 5 mm 以内で完了、200 step で打ち切り。`set_gripper` は 15 step。gripper を省略したときは最後の指の指令を保つ
- ボウルを皿に置く手順は `wiki/guides/robot-control.md` の「物を掴んで運ぶ流れ」にある (+y 側の縁を y +6 cm、z +3 cm で掴む)
- 命令の形式は ROS 2 の action (目標を送り、途中経過と結果を受ける) に倣う案がある。06 (Jev) と 07 (CaP) の policy も同じ命令を使う
- 確認には `uv run --env-file .env dora run <yaml> --log-level info` を使う

## Result

命令の形式を決め、`src/s1cap/driver.py` の `RobotDriver` に実装した。形式と結果の意味は [wiki/guides/dora-nodes.md](../../../wiki/guides/dora-nodes.md) にある。手書きの policy (`dataflows/scripted_json.yml`、JSON 入力条件) で「put the bowl on the plate」が init state 0〜5 のすべてで成功し、動画が `outputs/runs/` に残った。

05 の判断材料:

- 命令の往復は 0.4 ms で、50 ms の tick の間に収まる
- 方策に 500 ms、2000 ms の推論時間を入れても成功した。待つ間、ロボットは最後の目標を保って止まる。待ち時間の分だけエピソードが長くなり、動画に止まった場面が増える (2000 ms で 129 → 486 step)
- この命令の形式 (目標を渡し、届くまで sim の制御器に任せる) では、非同期のままで結果は変わらない。同期モードが効くのは、止まった場面を動画から減らしたいときと、方策が画像を見て step ごとに直す使い方のとき

後続タスク向けの注意:

- `POLICY_DELAY_MS` で policy ノードの推論時間を真似られる
- Jev や CaP の policy も同じ `command` / `command_result` を使い、`ground_truth` は購読しない

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-26 11:30 命令の形式を ROS 2 の action に倣って決め、RobotDriver.submit / step に実装した (move_to、move_delta、gripper、hold。結果は reached / timeout / preempted / rejected)。end は sim ノードが扱う
  - move_to の quat を省略したときは、今の目標の向きを保つ (control.move_to の既定値 TOP_DOWN とは違う)。命令の列で向きを毎回書かずに済むように
  - timeout のときは、届かない目標を押し続けないよう、その場の姿勢を目標にする
- 2026-10-26 11:30 src/s1cap/scripted.py (ScriptedPolicy と bowl_on_plate_commands)、nodes/scripted_policy.py、dataflows/scripted_json.yml を作った。policy は sim/ground_truth を scene として最初の 1 つだけ読む (JSON 入力条件)
- 2026-10-26 11:30 dora で task 8 が init 0〜5 のすべてで成功した (成功は step 103〜110)。driver の rejected、preempted、timeout、hold も dora を通さずに確かめた
- 2026-10-26 11:30 結果から次の命令までの時間を sim で測った。遅れ無しで 0.4 ms (0 step)。POLICY_DELAY_MS で 500 ms、2000 ms の待ちを入れても成功し、待つ間はロボットが止まって待つだけだった (全体 129 → 222 → 486 step)
  - 命令の往復は tick に収まり、同期モードは結果のためには要らない。要るとしたら、動画の止まった場面を減らすためか、画像を見て細かく直す方策のため
- 2026-10-26 11:30 wiki/guides/dora-nodes.md (ノード構成、命令の形式、推論が遅いときの結果) を作り、docs/setup.md と wiki/index.md からリンクした
