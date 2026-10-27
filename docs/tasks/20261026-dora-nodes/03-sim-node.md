<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# sim ノードと evaluator ノードを dora で動かす

ID: 03-sim-node
Bunch: ../20261026-dora-nodes.md

## Goal

LIBERO を dora の sim ノードで進め、画像、ロボットの状態、真値を流す。evaluator ノードが真値で成功を判定し、動画と記録を保存する。policy ノードはまだ無く、sim は制御器の目標を保ったまま進む。

## Done When

- `uv run --env-file .env dora run <dataflow>.yml` で sim と evaluator が起動し、決めた step 数で終わる。evaluator が `outputs/` の下に agentview の動画 (mp4) と、step ごとの成功判定の記録を残す
- sim が 1 step にかかる時間を、画像サイズごとに測る。20 Hz (50 ms) の tick に追いつくかどうかと、追いつかないときの扱いを Result に書く
- ノードの中身は `src/s1cap/` に dora に依存しない形で置き、`nodes/` には dora との受け渡しだけを書く。ruff が通る

## Context

- Approach & Rules (Bunch Document) の構成: sim / policy / evaluator の 3 ノード。policy は真値を購読しない。sim は命令 (目標) を受け、内部の制御器で目標を保つ。命令の形式は 04 で決めるので、このタスクでは命令の入力を作らなくてよい
- 02 の成果: `LiberoEnv.perceive()` が `Percept`、`ground_truth()` が `GroundTruth` を返す。`src/s1cap/control.py` の `PoseController.hold(percept)` で今の姿勢を保つ制御器が作れ、`ctrl.action(percept)` を `env.step` に渡せばよい
- 01 の成果 (`01-dora-install.md` の Result): 画像は `pa.array(img.ravel())` で送り、shape をメタデータに入れて受け側で reshape する。大きい出力のたびに WARN の診断ログが出る。`--log-level error` ではノードの stdout も消える。ノードは `uv run dora run` で venv の Python で起動する
- 出力の候補: sim から `image_agentview`、`image_wrist`、`robot_state` (Percept の画像以外)、`ground_truth`。ノードの設定 (suite、task、init、seed、画像サイズ、step 数) は dataflow の `env:` で渡す
- 動画は imageio と imageio-ffmpeg (venv に入っている) で書ける。`outputs/` は gitignore 済み
- 確認には `LIBERO_ROOT` が要る。`.env` に書いてあるので `uv run --env-file .env ...` で動かす
- 講義 (応用編1 第 6 回) の「MuJoCo + dora」の例: `~/ghq/github.com/pokutuna/physicalai2026/lectures/advanced1/06/lecture06_SUMMARY.md` (リポジトリ外。参照だけで、内容はコピーしない)

## Result

`uv run --env-file .env dora run dataflows/sim_eval.yml --log-level info` で sim と evaluator が動き、100 step で終わる。evaluator は `outputs/runs/<日時>/` に `episode.mp4` (agentview と手首カメラを横に並べた 20 fps の動画)、`ground_truth.jsonl`、`summary.json` を残す。

- sim の 1 step は画像の一辺 128〜512 px で 18〜19 ms で、50 ms の tick に追いつく。256 px と 512 px で 20.1 steps/s を保ち、フレームを落とさなかった。追いつかないときは、tick の入力を `queue_size: 1` にしてあるので、遅れた tick は溜まらずに捨てられる (sim の時間が実時間より遅れる)
- ノードの中身は `src/s1cap/driver.py` (`RobotDriver`) と `src/s1cap/recorder.py` (`EpisodeRecorder`) で、dora に依存しない。`nodes/` は受け渡しだけ
- dora の挙動 (cwd、待ち行列、ログ) は [wiki/findings/dora-dataflow.md](../../../wiki/findings/dora-dataflow.md) にある

後続タスク向けの注意:

- policy ノードは `image_agentview`、`image_wrist`、`robot_state` を購読し、`ground_truth` は購読しない。sim の出力のメタデータの `step` で対応付けられる
- 命令は `RobotDriver.ctrl` (`PoseController`) の `pos` / `quat` / `gripper` を書き換える形にすると、命令の間も目標を保てる
- 初回の実行で `dataflows/outputs/` ができた (gitignore 済み)。消してよい

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-26 11:24 env.step の時間を画像サイズごとに測った。128〜512 px で 17.9〜18.8 ms とほぼ同じで、物理の計算が大半。20 Hz に追いつく
- 2026-10-26 11:24 src/s1cap/driver.py (RobotDriver: 制御器を持ち、step ごとに目標へ向かう action を送る) と src/s1cap/recorder.py (EpisodeRecorder: 2 カメラを横に並べた mp4、ground_truth.jsonl、summary.json) を dora に依存しない形で作った。nodes/sim.py、nodes/evaluator.py、nodes/arrow_io.py、dataflows/sim_eval.yml で dora につないだ
- 2026-10-26 11:24 初回は evaluator の入力の待ち行列 (既定 10) が溢れて真値 25 step 分などが捨てられ、出力が dataflows/outputs/ にできた (ノードの cwd は yaml の場所)
  - evaluator の入力を queue_size: 1000 に、保存先を nodes/ の位置から決めるように直した
  - sim の reset を Node() の前に移し、起動中の tick が捨てられる WARN を無くした
- 2026-10-26 11:24 ログは node.log("info", ...) で出し、--log-level info で動かすことにした。print は info では消える。#2742 の diagnostic WARN は最初の数回の出力だけ (100 step で 9 行) なので放置
- 2026-10-26 11:24 256 px と 512 px で 100 step を 5.0 s (20.1 steps/s) で進め、101 フレームを落とさず記録した。wiki/findings/dora-dataflow.md と docs/setup.md に書いた
