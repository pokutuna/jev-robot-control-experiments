# 言い方ごとの向きの答え (pudding_fixed)

`scripts/probe_targets.py` が書く表。手先から採点する物の位置 (真値) への差と、答えを世界座標に直した向きを、軸ごとに比べる。
差が 2 cm 以上の軸は近づく、動かさない、遠ざかるに分け、1 cm 未満の軸は動かさない答えを正しいとする。

- libero_90 61、カメラ fixed、init [0, 1, 2, 3, 4]
- 問いの数: 210 (失敗して記録の無いもの 0)、届かなかった位置: 0 問

| 言い方 | 採点する物 | 軸 | 数 | 近づく | 動かさない | 遠ざかる | 合っている軸で動かさない |
| --- | --- | --- | --- | --- | --- | --- | --- |
| the chocolate pudding box | chocolate_pudding_1 | x | 70 | 6 (9%) | 64 (91%) | 0 (0%) | 34 (97%) |
| the chocolate pudding box | chocolate_pudding_1 | y | 75 | 8 (11%) | 67 (89%) | 0 (0%) | 15 (100%) |
| the brown box | chocolate_pudding_1 | x | 70 | 9 (13%) | 61 (87%) | 0 (0%) | 35 (100%) |
| the brown box | chocolate_pudding_1 | y | 75 | 9 (12%) | 66 (88%) | 0 (0%) | 13 (87%) |

| 言い方 | レイテンシの中央値 [ms] | 入力トークンの平均 |
| --- | --- | --- |
| the chocolate pudding box | 454 | 1045 |
| the brown box | 493 | 1041 |
