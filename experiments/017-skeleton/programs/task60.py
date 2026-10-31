# libero_90 60「pick up the black bowl on the left and put it in the tray」に固有の値 (人が埋めた)。骨組みは skeleton.py。
# ボウル (直径 10.7 cm) は指の開き (8 cm) より大きいので、中心に合わせてから -y の縁へずらして縁を挟む。
# 左右の言い方では手首の画像の向きの答えがボウルへ向かわないので (実験 016)、掴む物を指示文から指す言い方にする。
OBJECT = "the center of the bowl to pick up"
PLACE = "the center of the tray"
GRASP_SHIFT = (0.0, -0.06)
GRASP_RISE = 0.015
DONE_QUESTION = "Is the black bowl in the tray?"
