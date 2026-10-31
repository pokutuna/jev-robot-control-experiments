# 言い方ごとの向きの答え (pudding)

`scripts/probe_targets.py` が書く表。手先から採点する物の位置 (真値) への差と、答えを世界座標に直した向きを、軸ごとに比べる。
差が 2 cm 以上の軸は近づく、動かさない、遠ざかるに分け、1 cm 未満の軸は動かさない答えを正しいとする。

- libero_90 61、カメラ wrist、init [0, 1, 2, 3, 4]
- 問いの数: 525 (失敗して記録の無いもの 0)、届かなかった位置: 0 問

| 言い方 | 採点する物 | 軸 | 数 | 近づく | 動かさない | 遠ざかる | 合っている軸で動かさない |
| --- | --- | --- | --- | --- | --- | --- | --- |
| the chocolate pudding box | chocolate_pudding_1 | x | 70 | 47 (67%) | 23 (33%) | 0 (0%) | 35 (100%) |
| the chocolate pudding box | chocolate_pudding_1 | y | 75 | 70 (93%) | 5 (7%) | 0 (0%) | 13 (87%) |
| the chocolate pudding | chocolate_pudding_1 | x | 70 | 48 (69%) | 22 (31%) | 0 (0%) | 35 (100%) |
| the chocolate pudding | chocolate_pudding_1 | y | 75 | 70 (93%) | 5 (7%) | 0 (0%) | 14 (93%) |
| the brown box | chocolate_pudding_1 | x | 70 | 37 (53%) | 33 (47%) | 0 (0%) | 35 (100%) |
| the brown box | chocolate_pudding_1 | y | 75 | 69 (92%) | 6 (8%) | 0 (0%) | 15 (100%) |
| the box | chocolate_pudding_1 | x | 70 | 40 (57%) | 30 (43%) | 0 (0%) | 35 (100%) |
| the box | chocolate_pudding_1 | y | 75 | 70 (93%) | 5 (7%) | 0 (0%) | 15 (100%) |
| the center of the chocolate pudding box | chocolate_pudding_1 | x | 70 | 51 (73%) | 19 (27%) | 0 (0%) | 35 (100%) |
| the center of the chocolate pudding box | chocolate_pudding_1 | y | 75 | 75 (100%) | 0 (0%) | 0 (0%) | 8 (53%) |

| 言い方 | レイテンシの中央値 [ms] | 入力トークンの平均 |
| --- | --- | --- |
| the chocolate pudding box | 414 | 1028 |
| the chocolate pudding | 419 | 1024 |
| the brown box | 418 | 1024 |
| the box | 411 | 1020 |
| the center of the chocolate pudding box | 420 | 1040 |
