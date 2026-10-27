<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 006: 運ぶ段の向きを固定カメラの画像の答えで決める

ID: 09-exp006-fixed-carry
Bunch: ../20261027-image-only-jev.md

## Goal

005 の失敗 (運ぶ段で、向きを決める画像が手首と固定カメラで交互に切り替わった) が、運ぶ段の向きを固定カメラの画像の答えだけで決めると無くなるかを、init state 0〜9 で確かめる。

## Done When

- `experiments/006-fixed-carry/` に dataflow、init state 0〜9 の記録、`results.md` がある
- README に 005 との違い、結果、運ぶ段の進み方、横の向きが書かれている

## Context

- 方策は `s1cap.jev_staged.JevStagedPolicy` (POLICY: staged、FIXED_MARK=1、CARRY_VIEW=fixed)
- 005 の結果は [experiments/005-staged-guide/README.md](../../../experiments/005-staged-guide/README.md)。固定カメラの画像でトレイへ寄せる向きは、トレイの中心から 12 cm 以上離れていれば左右 131/131 が近づく向きだった

## Result

006 は 9/10。運ぶ段の行き来は無くなり、運ぶ段の判断はどのエピソードでも 15〜18 回になった (005 は 14〜100 回)。失敗した init 9 は、ボウルの中心に 2.3 cm ずれて合わせた後、縁へ 6 cm ずらして 2 つのボウルの間に下り、もう 1 つのボウルを掴んでトレイに入れた。結果は [experiments/006-fixed-carry/README.md](../../../experiments/006-fixed-carry/README.md)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 10:21 init 0〜9 を回し、README に 005 との違い、運ぶ段の回数、横の向き、init 9 の失敗を書いた
  - init 9 は真値 (akita_black_bowl_2 が 24.5 cm 持ち上がった) と動画の step 350、500 で、別のボウルを掴んだことを確かめた
  - init 5 は指を閉じたまま finish を選んだが、ボウルは下ろす途中で指から外れてトレイに入っており、成功と判定された
