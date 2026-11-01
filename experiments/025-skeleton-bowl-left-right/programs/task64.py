# libero_90 64「stack the right bowl on the left bowl and place them in the tray」に固有の値 (人が埋めた)。骨組みは skeleton.py。
# 掴む物の言い方と掴み方は task 60 (../../023-skeleton-jev-phases/programs/task60.py) と同じにし、どちらのボウルを掴むかは指示文だけで決める。
# 骨組みは 1 回運んで置く手順なので、右のボウルを左のボウルに重ねるところまでを行う (トレイへは運ばない)。
OBJECT = "the center of the bowl to pick up"
GRASP_SHIFT = (0.0, -0.06)
GRASP_TARGET = "the left edge of the bowl to pick up"
HELD = "black bowl in the gripper"
PLACE = "the center of the other black bowl"
DONE_QUESTION = "Is one black bowl stacked on the other?"
