# libero_90 60「pick up the black bowl on the left and put it in the tray」に固有の値 (人が埋めた)。骨組みは skeleton.py。
# ボウル (直径 10.7 cm) は指の開き (8 cm) より大きいので、中心に合わせてから -y の縁 (手首の画像の左の縁) へずらして縁を挟む。
# 左右の言い方では手首の画像の向きの答えがボウルへ向かわないので (実験 016)、掴む物を指示文から指す言い方にする。
OBJECT = "the center of the bowl to pick up"
GRASP_SHIFT = (0.0, -0.06)
GRASP_TARGET = "the left edge of the bowl to pick up"
HELD = "black bowl in the gripper"
PLACE = "the center of the tray"
DONE_QUESTION = "Is the black bowl in the tray?"
