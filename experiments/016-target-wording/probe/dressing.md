# 言い方ごとの向きの答え (dressing)

`scripts/probe_targets.py` が書く表。手先から採点する物の位置 (真値) への差と、答えを世界座標に直した向きを、軸ごとに比べる。
差が 2 cm 以上の軸は近づく、動かさない、遠ざかるに分け、1 cm 未満の軸は動かさない答えを正しいとする。

- libero_90 62、カメラ wrist、init [0, 1, 2, 3, 4]
- 問いの数: 315 (失敗して記録の無いもの 0)、届かなかった位置: 42 問

| 言い方 | 採点する物 | 軸 | 数 | 近づく | 動かさない | 遠ざかる | 合っている軸で動かさない |
| --- | --- | --- | --- | --- | --- | --- | --- |
| the salad dressing bottle | new_salad_dressing_1 | x | 70 | 34 (49%) | 29 (41%) | 7 (10%) | 19 (54%) |
| the salad dressing bottle | new_salad_dressing_1 | y | 75 | 67 (89%) | 6 (8%) | 2 (3%) | 15 (100%) |
| the salad dressing | new_salad_dressing_1 | x | 70 | 31 (44%) | 24 (34%) | 15 (21%) | 12 (34%) |
| the salad dressing | new_salad_dressing_1 | y | 75 | 66 (88%) | 6 (8%) | 3 (4%) | 11 (73%) |
| the bottle | new_salad_dressing_1 | x | 70 | 41 (59%) | 27 (39%) | 2 (3%) | 27 (77%) |
| the bottle | new_salad_dressing_1 | y | 75 | 68 (91%) | 6 (8%) | 1 (1%) | 15 (100%) |

| 言い方 | レイテンシの中央値 [ms] | 入力トークンの平均 |
| --- | --- | --- |
| the salad dressing bottle | 417 | 1028 |
| the salad dressing | 422 | 1024 |
| the bottle | 425 | 1020 |
