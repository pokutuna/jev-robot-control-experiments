<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# dora-rs を入れて最小の dataflow を動かす

ID: 01-dora-install
Bunch: ../20261026-dora-nodes.md

## Goal

dora-rs をこのリポジトリの uv 環境に入れ、最小の dataflow がこのマシン (macOS、Python 3.14) で動くことを確かめる。

## Done When

- `pyproject.toml` に dora-rs が入り、`uv run dora --version` が通る
- タイマー → 送信 → 表示の 2 ノードの dataflow が `uv run dora run` で動き、終了する
- numpy 配列 (画像くらいの大きさ) をノード間で送れることを確かめる

## Context

- PyPI の `dora-rs` と `dora-rs-cli` は 1.1.0 (2026-10-26 時点)。macOS arm64 用の abi3 wheel (cp311 以降) がある
- dora の最小構成: `dataflow.yml` に `nodes:` を並べ、`inputs: { tick: dora/timer/millis/500 }` で組込みタイマーを受ける。ノードは `from dora import Node` の `Node()` のイベントループで `event["type"] == "INPUT"` を受け、`node.send_output(name, pa.array(...))` で送る。`dora run dataflow.yml` で coordinator、daemon、各ノードがまとめて起動する
- ノードの置き場所は `nodes/`、dataflow の yaml はリポジトリ直下か `dataflows/` を想定。このタスクの最小例は確認用なので、残すかどうかは結果を見て決める
- ノードを起動する Python が venv のものになるかを確かめる (`uv run dora run` で PATH に `.venv/bin` が入るはず)

## Result

dora-rs 1.1.0 は uv の Python 3.14 環境で動く。`uv run dora run <yaml>` で、ノードは venv の Python で起動する。512px の RGB 画像を毎 50 ms 送っても、配送の遅れは平均 1.4 ms だった。

後続タスク向けの注意:

- 画像は `pa.array(img.ravel())` で送り、shape をメタデータに入れて、受け側で `to_numpy().reshape(shape)` する
- 大きい出力のたびに WARN の診断ログが出る。`--log-level error` ではノードの stdout も消える
- 確認に使った最小例はスクラッチに置き、リポジトリには残していない

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-26 11:13 uv add dora-rs dora-rs-cli pyarrow で 1.1.0 / pyarrow 26.0.0 が入り、dora-cli 1.1.0 が動いた
  - dora-rs-cli は依存に uv (0.13.5) を持ち、venv に uv が入る。動作に支障はない
- 2026-10-26 11:13 タイマー (50 ms) → 512×512×3 の uint8 を 40 回送る → 受信の 2 ノードを uv run dora run で動かし、正常終了した
  - ノードは .venv/bin/python で起動された。shape はメタデータで渡して reshape する
  - 配送の遅れは平均 1.42 ms、最大 41.8 ms。885 KB のメッセージは共有メモリ経由
  - 大きい出力のたびに WARN の診断ログ (dora-rs/dora#2742 diagnostic) が 3 行出る。--log-level error にするとノードの stdout も消えるので、ログの絞り方は 03 で決める
