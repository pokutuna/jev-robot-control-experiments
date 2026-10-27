<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 005: 手順のガイドを与え、段階ごとの動きをコードで決める

ID: 06-exp005-staged-guide
Bunch: ../20261027-image-only-jev.md

## Goal

段階を選ぶ条件 (真偽) をロボットの状態と画像への答えからコードが作り、段階ごとの動きもコードで決めたとき、真値を渡さずに libero_90 60 をどこまで解けるかを init state 0〜9 で確かめる。運ぶ段で、トレイが手首の画像に写っていなければ、003 の固定カメラの印で向きを決める。

## Done When

- `experiments/005-staged-guide/` に dataflow、init state 0〜9 の記録、`results.md` がある
- README に条件、結果、Jev とコードの分担、失敗の仕方 (あれば)、001〜004 との違いが書かれている

## Context

- 方策は `s1cap.jev_staged.JevStagedPolicy` (POLICY: staged、policy の env に FIXED_MARK=1)
- 2026-10-26 の staged policy の試行は [wiki/findings/jev-c2-staged-policy.md](../../../wiki/findings/jev-c2-staged-policy.md)
- 004 の結果は [experiments/004-marked-two-call/README.md](../../../experiments/004-marked-two-call/README.md)

## Result

005 は 8/10。成功したエピソードは段を順序どおりに進んだ。失敗した init 4、7 は運ぶ段で「トレイが手首の画像に写っているか」の答えが 0.5 の前後で揺れ、手首の画像 (遠ざかる向き) と固定カメラの画像 (近づく向き) が交互に使われて進めなかった。固定カメラの印でトレイへ寄せる向きは、左右 131/131 が近づく向きだった。結果は [experiments/005-staged-guide/README.md](../../../experiments/005-staged-guide/README.md)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 09:16 init 0〜9 を回し、README に結果、段の進み方、運ぶ段の失敗、横の向き、トレイの持ち上げ、001〜004 との比較を書いた
  - init 7 の step 1034 の手首の画像を動画から取り出し、トレイが写っていないのに tray_in_wrist が 0.67 だったことを確かめた
  - init 2、5 で、指を開いて上げるときにトレイがボウルごと約 19 cm 持ち上がった。原因は確かめていない
