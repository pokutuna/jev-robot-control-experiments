<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験の置き場所と、init state ごとに回して集計するランナーを用意する

ID: 01-experiment-runner
Bunch: ../20261027-image-only-jev.md

## Goal

`experiments/NNN-slug/` に dataflow を置けば、1 つのコマンドで init state ごとにエピソードを回し、記録をその実験のディレクトリに集め、成功率などの表を作れるようにする。

## Done When

- `experiments/README.md` に、実験のディレクトリの構成、README に書くこと、git に入れるものと入れないものが書かれている
- ランナーで既存の staged policy の dataflow を init state 1 つ分回し、`experiments/<実験>/runs/` に記録ができ、集計の表が書かれる
- `docs/setup.md` に実行のしかたが書かれている

## Context

- dataflow の yml の `path` は yml の場所からの相対パスで解決される (`dataflows/*.yml` は `../nodes/...`)。実験のディレクトリに置く yml は `../../nodes/...` になる
- init state は sim ノードの環境変数 `INIT`、記録の保存先は evaluator ノードの環境変数 `OUT_DIR` で変えられる。evaluator は `summary.json` (成功、成功した step、判断の回数、平均レイテンシなど) を書く
- 実行は `uv run --env-file .env dora run <yml> --log-level info`。macOS では MUJOCO_GL を設定しない
- 1 エピソードの記録は 3〜4 MB (動画 2 本と jsonl)。全部を git に入れると数百 MB になる
- 費用の比較のため、判断の記録に Jev の呼び出しごとのトークン数を残す (`s1cap.jev.call_record`)

## Result

`experiments/NNN-slug/dataflow.yml` を置けば、`uv run --env-file .env scripts/run_experiment.py run <実験> --inits 0-9` で init state ごとに回せる。記録は `runs/init<N>-<日時>/`、表は `results.md` に書かれる。置き方と git に入れるものは [experiments/README.md](../../../experiments/README.md)、回し方は `docs/setup.md` の「実験を回す」。

- summary.json に `jev_calls`、`input_tokens`、`output_tokens` が入る。方策は判断の記録の `calls` に `s1cap.jev.call_record` の値を名前付きで入れる
- 向きの答えの正答率は方策ごとに問いが違うので、ランナーには入れなかった。必要な実験で、2026-10-26 の staged の分析 (真値の手先と目標から向きを作り、1.5 cm 以内を「動かさない」とする) を基に作る

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 06:13 判断の記録に Jev の呼び出しごとのレイテンシとトークン数 (calls) を足し、summary.json に jev_calls、input_tokens、output_tokens を出すようにした
  - 実験ごとに呼び出しの回数と費用を比べるため。staged は wrist / fixed / intent、direction は move の名前で入れる
- 2026-10-27 06:15 scripts/run_experiment.py (run / summary) と experiments/README.md を作り、staged の dataflow を判断 10 回に縮めて init 0 で回した。runs/init0-<日時>/ に記録、results.md に表ができた
  - 一時的な yml は実験のディレクトリに置く (ノードの path が yml の場所から解決されるため)。dora のログは dora.log に書く。dora.log は手元の絶対パスを含むので git に入れない
  - 確認に使った experiments/_check は scratchpad に移した
