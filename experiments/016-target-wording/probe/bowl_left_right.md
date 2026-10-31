# 言い方ごとの向きの答え (bowl_left_right)

`scripts/probe_targets.py` が書く表。手先から採点する物の位置 (真値) への差と、答えを世界座標に直した向きを、軸ごとに比べる。
差が 2 cm 以上の軸は近づく、動かさない、遠ざかるに分け、1 cm 未満の軸は動かさない答えを正しいとする。

- libero_90 60、カメラ wrist、init [0, 1, 2, 3, 4]
- 問いの数: 420 (失敗して記録の無いもの 0)、届かなかった位置: 0 問

| 言い方 | 採点する物 | 軸 | 数 | 近づく | 動かさない | 遠ざかる | 合っている軸で動かさない |
| --- | --- | --- | --- | --- | --- | --- | --- |
| the black bowl on the left | akita_black_bowl_1 | x | 70 | 16 (23%) | 27 (39%) | 27 (39%) | 29 (83%) |
| the black bowl on the left | akita_black_bowl_1 | y | 75 | 26 (35%) | 45 (60%) | 4 (5%) | 12 (80%) |
| the left black bowl | akita_black_bowl_1 | x | 70 | 4 (6%) | 49 (70%) | 17 (24%) | 32 (91%) |
| the left black bowl | akita_black_bowl_1 | y | 75 | 16 (21%) | 49 (65%) | 10 (13%) | 14 (93%) |
| the black bowl on the right | akita_black_bowl_2 | x | 71 | 3 (4%) | 57 (80%) | 11 (15%) | 9 (100%) |
| the black bowl on the right | akita_black_bowl_2 | y | 105 | 105 (100%) | 0 (0%) | 0 (0%) | - |
| the center of the bowl to pick up | akita_black_bowl_1 | x | 70 | 46 (66%) | 24 (34%) | 0 (0%) | 35 (100%) |
| the center of the bowl to pick up | akita_black_bowl_1 | y | 75 | 62 (83%) | 13 (17%) | 0 (0%) | 15 (100%) |

| 言い方 | レイテンシの中央値 [ms] | 入力トークンの平均 |
| --- | --- | --- |
| the black bowl on the left | 415 | 1045 |
| the left black bowl | 425 | 1037 |
| the black bowl on the right | 434 | 1045 |
| the center of the bowl to pick up | 429 | 1053 |
