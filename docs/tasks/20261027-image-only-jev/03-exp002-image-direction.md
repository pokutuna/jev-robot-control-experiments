<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 002: 画像だけで手先の向きを選ぶ方策を共通の条件で回す

ID: 03-exp002-image-direction
Bunch: ../20261027-image-only-jev.md

## Goal

真値を渡さず、指示文、手先の状態、2 台のカメラ画像だけで Jev に移動方向と指を選ばせたとき、libero_90 60 をどこまで進められるかを init state 0〜9 で確かめる。2026-10-26 の静止画での向きの正答率の結果と合わせ、画像だけでは向きを決められないことを示す。

## Done When

- `experiments/002-image-direction/` に dataflow、init state 0〜9 の記録、`results.md` がある
- `experiments/002-image-direction/README.md` に条件、結果、Jev とコードの分担、失敗の仕方、静止画の結果 (カメラの置き方や印を変えてもほぼ変わらない) が書かれている

## Context

- 方策は `s1cap.jev_policy.JevDirectionPolicy` (POLICY: direction、INPUT: image)
- 静止画の結果は [wiki/findings/jev-c2-direction-policy.md](../../../wiki/findings/jev-c2-direction-policy.md)

## Result

002 は 0/10。10 エピソードとも最初に指を閉じ、テーブルまで下りて横に引きずり、ボウルを通り過ぎて −y へ進み続けた。左右はボウルの位置によらず −y に偏った。結果は [experiments/002-image-direction/README.md](../../../experiments/002-image-direction/README.md)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 07:20 init 0〜9 を回し、README に結果、失敗の仕方、横の向き、静止画の結果を書いた
  - 横の向きはボウルのある側で分けて数え直した。前後の「近づく 70%」は手先がボウルの後ろ側に引きずられた後の +x の偏りによる
