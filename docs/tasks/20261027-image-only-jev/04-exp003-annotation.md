<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 003: 画像に手先の印を描き、画像の中の向きを 1 回の呼び出しで問う

ID: 04-exp003-annotation
Bunch: ../20261027-image-only-jev.md

## Goal

真値を渡さず、画像に手先の印 (手首の画像の ×、固定カメラの画像の手先と真下の点) を描き、印を行き先へ寄せる画像の中の向きを問えば、Jev が行き先の向きを決められるかを init state 0〜9 で確かめる。

## Done When

- `experiments/003-marked-image/` に dataflow、init state 0〜9 の記録、`results.md` がある
- README に条件、結果、Jev とコードの分担、失敗の仕方が書かれている

## Context

- 方策は `s1cap.jev_marked.JevMarkedPolicy` (POLICY: marked)。印の位置は手先の位置 (ロボット自身の状態) を、sim が task で送る射影行列 (カメラの校正値) で画像に移して求める
- 画像の向きから世界座標の向きへの変換はコード。固定カメラは黄色い点の位置での射影のヤコビアンの逆で直す
- 掴む位置 (ボウルの縁) のずらしはコードに無いので、ボウルの中心に合わせて掴めないことが予想される。失敗の仕方を記録する

## Result

003 は 0/10。手首の画像の向きではボウルへ近づく向きをほぼ外さなかった (遠ざかる 12/292) が、9 エピソードでボウルの上に着く前 (テーブルから 7〜25 cm) に指を閉じ、下りてボウルを押し倒した。固定カメラの画像の向きは 002 と同じ程度に外れた。結果は [experiments/003-marked-image/README.md](../../../experiments/003-marked-image/README.md)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 07:21 init 0 の途中経過を見た。手首の画像の向きでボウルの上まで寄れたが、テーブルから 16 cm の高さで指を閉じ、閉じたまま下りてボウルを押した
  - その後は行き先が手首の画像から外れ、固定カメラの向きに切り替わった。正解は「右」(黄色い点からボウルへ duv = (47, -9) px) だが、Jev は「右、上」を多く答え、上の成分 (0.43) が AXIS_MIN 0.4 を超えて y が遠ざかる向きになった
- 2026-10-27 08:04 init 0〜9 を回し、README に結果、失敗の仕方、向きを決めた画像ごとの横の向きを書いた
  - ボウルは 3〜4 cm 浮いたが、押されて 34〜81° 傾いただけだった。direction_accuracy.py の運ぶ段の判定が誤るので、全判断をボウルの中心に対して数え直した
