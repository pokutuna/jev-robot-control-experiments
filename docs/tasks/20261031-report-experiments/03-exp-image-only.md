<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 014: 画像だけを渡す方策を task 61 で回す

ID: 03-exp-image-only
Bunch: ../20261031-report-experiments.md

## Goal

アウトラインの実験 2。002 と同じ方策 (`JevDirectionPolicy`、1 回の判断で 1 回呼ぶ) を task 61 で回し、真値を文で渡す 013 (10/10) と、段ごとに問う骨組み (017) と比べる基準にする。

## Done When

- `experiments/014-image-direction/` に init 0〜9 の記録、results.md、README がある
- README に、成功数、掴む点への近さ、向きの答えの正しさ (`scripts/direction_accuracy.py`) を 013 と並べて書いている

## Context

- dataflow は `experiments/014-image-direction/dataflow.yml` (作成済み)。002 との違いは、タスク (task 61)、画像 448 px、固定カメラ quarterview、`MAX_STEPS` 7000
- 実行: `uv run --env-file .env scripts/run_experiment.py run experiments/014-image-direction --inits 0-9`。dora は同時に 1 つだけ
- 002 (task 60) は 0/10。ボウルは縁を挟まないと掴めないことを伝えていなかった。task 61 の箱は指の開きより小さいので、002 より掴みやすい
- README の節と書き方は 013 に合わせる

## Result

014 は 0/10 ([README](../../../experiments/014-image-direction/README.md))。失敗の形は 002 と同じで、箱に替えても向きの答えは物の位置によらず偏った。x は 76%、y は 71% が箱から遠ざかる向きで、x の偏りは 002 (近づく向き 70%) と逆だった (013 は遠ざかる向き 0 回)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-31 20:07 014 を init 0〜9 で回した。0/10。002 と同じく、最初に指を閉じ、下りてテーブルに押し付けたまま横へ引きずった。x、y とも 7 割以上が箱から遠ざかる向き。README を書いた
  - 出力トークンが毎回 154 で同じなのは、答えの形 (軸ごとの 3 択と指) が決まっているため。答えが壊れていないことを events で確かめた
