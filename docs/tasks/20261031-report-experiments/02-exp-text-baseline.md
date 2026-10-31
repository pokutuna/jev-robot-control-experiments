<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 013: 真値を文で渡す方策を task 61 で回す

ID: 02-exp-text-baseline
Bunch: ../20261031-report-experiments.md

## Goal

アウトラインの実験 1。001 と同じ方策 (`s1cap.jev_text`) を libero_90 61 で回し、物体の位置の真値を文で渡せば Jev がタスクを解けることを本筋のタスクで確かめる。

## Done When

- `experiments/013-text-baseline/` に dataflow、runs (init 0〜9)、results.md、README がある
- README に成功率と失敗の仕方が書いてあり、動画か真値で確かめてある

## Context

- 方策と問いの形は [001 の README](../../../experiments/001-text-baseline/README.md)。運ぶ物と掴む点は `s1cap.tasks` の TaskSpec (箱の中心の高さで挟む、離す点はトレイの位置の 5 cm 上)
- 画像は 448 px、sim_state を記録する (Bunch の Approach & Rules)
- 実行: `uv run --env-file .env scripts/run_experiment.py run experiments/013-text-baseline --inits 0-9`

## Result

成功 10/10 (init 3 は通信の不調で止まった 1 回目を外し、回し直した)。平均 83.1 回の判断、1 回の判断 727 ms、入力 30.2 万トークン。001 (task 60) と同じく、真値を文で渡せば運ぶ物を替えても解けた。[README](../../../experiments/013-text-baseline/README.md)

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-31 17:03 init 0〜2 は成功。init 3 は、step 163 の move_delta (id 8) の結果が policy と evaluator のどちらにも届かず、方策が待ったまま max_steps まで進んで失敗した
  - 手先は step 179 に目標へ届いて止まっている。sim の dora.log に、同じ頃 zenoh_shm の watchdog の timer overrun が出ている (同時に 015、016 の probe を回していた)
  - 方策の失敗ではないので、0〜9 を回し終えた後に init 3 を回し直し、表には回し直したものを使う
- 2026-10-31 17:13 init 3 を回し直して成功 10/10。1 回目は excluded-runs/ に移し、README に理由を書いた。init 0 の最後のフレームで箱がトレイの中にあることを見た
  - sim が MAX_STEPS の手前で LIBERO の horizon に当たって落ちていたので、nodes/sim.py の horizon を max_steps + 100 にした
