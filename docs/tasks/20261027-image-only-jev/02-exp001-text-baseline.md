<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 001: 先行事例の 2 回呼び出しを、真値のテキスト入力で再現する

ID: 02-exp001-text-baseline
Bunch: ../20261027-image-only-jev.md

## Goal

公開デモ (OpenRoboto、Hrybov) と同じく、物体の位置の真値を文で渡し、意図 → 軸ごとの向きと指の 2 回呼び出しで、libero_90 60 をこなせるかを init state 0〜9 で確かめる。後の画像の実験と比べる基準にする。

## Done When

- `experiments/001-text-baseline/` に dataflow、init state 0〜9 の記録、`results.md` がある
- `experiments/001-text-baseline/README.md` に条件、結果、Jev が決めていることとコードが決めていること、失敗の仕方が書かれている

## Context

- 問いの形は OpenRoboto の `incremental_policy.py` (https://github.com/openroboto-ai/jev-robot-control, 7a4ed8b) をほぼそのまま移した。clone は scratchpad の `repos/jev-robot-control/` にある (リポジトリには入れない)
- 先行事例の入力の比較は [wiki/research/jev-robot-control-inputs.md](../../../wiki/research/jev-robot-control-inputs.md)
- 掴む位置はボウルの中心から (0, +6, +3) cm (`s1cap.scripted` と同じ)、離す位置はトレイの中心から (0, +6, +6) cm
- この実験だけが方策に真値 (`scene`) を配線する

## Result

init state 0〜9 で 10/10 成功 (LIBERO の判定)。1 エピソードで平均 65 回の判断、129 回の呼び出し、入力 23 万トークン。結果と、Jev とコードの分担は [experiments/001-text-baseline/README.md](../../../experiments/001-text-baseline/README.md)。

- 離した直後にトレイが一時的に浮く (最後は元の高さ)。原因は未確認
- policy ノードが end の直後に止まると sim が `policy_closed` と記録する競合を、policy ノードが sim の終了を待つように直した

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 06:20 src/s1cap/jev_text.py (JevTextPolicy) と nodes/jev_policy.py の POLICY: text を作り、init 0 で 1 回目から成功した (判断 59 回、Jev 呼び出し 116 回、成功 step 977)
  - 1 歩の大きさは OpenRoboto の距離ごとの段階 (2/4/18 mm) を、sim の制御器の届いたとみなす幅 (5 mm) に合わせて 4/8/20 mm にした。位置合わせの許容幅は 8 mm
  - 運ぶ段と下ろす段で x を ±4 mm 行き来した (許容幅の境目)。終わったときボウルはトレイの中心から 1.6 cm、トレイは 2 cm 動いた
  - init 1〜9 をバックグラウンドで回し始めた
- 2026-10-27 06:32 init 1〜9 も成功し 10/10。README と代表動画 (videos/init0.mp4) を置いた
  - トレイが離した直後に 24〜127 step 浮き、最後は元の高さに戻る (init 3 以外)
  - 終わり方の policy_closed は end と入力の閉じる順の競合。nodes/jev_policy.py を直し、init 9 から policy_end になった
