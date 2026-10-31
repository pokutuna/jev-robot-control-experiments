# 物を掴んで置き場所に置くタスクに共通の手順の骨組み (実験 017)。人が書き、タスクを替えても変えない。
#
# s1cap.cap の部品 (move_by、wrist_direction など) だけを使い、物の位置は使わない。
# タスクに固有の値は、この前につなぐファイル (task61.py など) で決める。
#   OBJECT         運ぶ物の言い方。Jev に向きを問う行き先に使う
#   PLACE          置き場所の言い方
#   GRASP_SHIFT    運ぶ物に合わせた後、掴む場所までずらす量 (dx, dy) [m]。置くときも置き場所の位置から
#                  同じだけずらし、運ぶ物の中心を置き場所に合わせる
#   GRASP_RISE     下ろして当たって止まった所から、指を閉じる前に上げる量 [m]
#   DONE_QUESTION  置き終えたかを両方の画像に問う文
#
# 手順: 置き場所に合わせて位置を覚える → 運ぶ物に合わせる → ずらす → 下ろす → 掴む (掴めなければやり直す)
#       → 持ち上げる → 覚えた位置から同じだけずらした所へ動く → 下ろす → 少し上げて離す → 上げる → 置けたかを問う
# 位置合わせは、固定カメラの答えで寄せてから、手首カメラの答えで合わせる (実験 006 と同じ)。
# 物を持っている間は、持っている物が手首の画像の × の近くを隠し、固定カメラでも手先の印と物が重なるので、
# 向きの答えが置き場所の手前で止まったり逆を向いたりする。そこで置き場所には何も持たないうちに合わせ、
# その位置を覚えておく。

STEP = 0.02  # 1 回の向きの答えで動く量 [m]
DOWN = 0.03  # 1 回に下ろす量 [m]。当たって止まるまで繰り返す
# 置くとき、当たって止まった所からこれだけ上げてから指を開く [m]。止まった所で開くと、指が置き場所の縁や
# 仕切りを押し、上げるときに置き場所ごと持ち上げることがある
RELEASE_RISE = 0.03
HELD_WIDTH = 0.003  # 指を閉じた後の開きがこれより大きければ物を持っている [m]
MAX_FIXED_STEPS = 30  # 固定カメラの答えで寄せる歩数の上限 (2 cm × 30 = 60 cm)
MAX_WRIST_STEPS = 15  # 手首カメラの答えで合わせる歩数の上限
MAX_DOWNS = 10
MAX_GRASP_TRIES = 3

# 始めの高さ。手首の画像の赤い × はこの高さに合わせてある
START_Z = gripper_position()[2]


def follow(direction, target, max_steps):
    """direction (wrist_direction か fixed_direction) の答えの向きへ STEP ずつ動き、(0, 0) と答えたら止まる。"""
    for _ in range(max_steps):
        sx, sy = direction(target)
        if sx == 0 and sy == 0:
            return True
        move_by(sx * STEP, sy * STEP, 0.0)
    return False


def align(target):
    """始めの高さで、手首の画像の赤い × を target に合わせる。"""
    x, y, _ = gripper_position()
    move_to(x, y, START_Z)
    follow(fixed_direction, target, MAX_FIXED_STEPS)
    return follow(wrist_direction, target, MAX_WRIST_STEPS)


def go_down():
    """当たって止まるまで DOWN ずつ下ろす。"""
    for _ in range(MAX_DOWNS):
        if not move_by(0.0, 0.0, -DOWN):
            return


def go_up():
    x, y, _ = gripper_position()
    move_to(x, y, START_Z)


def pick():
    for attempt in range(MAX_GRASP_TRIES):
        align(OBJECT)
        move_by(GRASP_SHIFT[0], GRASP_SHIFT[1], 0.0)
        go_down()
        move_by(0.0, 0.0, GRASP_RISE)
        close_gripper()
        if gripper_opening() > HELD_WIDTH:
            go_up()
            if gripper_opening() > HELD_WIDTH:
                return True
            print(f"try {attempt}: dropped while lifting")
        else:
            print(f"try {attempt}: missed")
        open_gripper()
        go_up()
    return False


def place(place_x, place_y):
    move_to(place_x + GRASP_SHIFT[0], place_y + GRASP_SHIFT[1], START_Z)
    go_down()
    move_by(0.0, 0.0, RELEASE_RISE)
    open_gripper()
    go_up()


align(PLACE)
place_x, place_y, _ = gripper_position()
if pick():
    place(place_x, place_y)
    print(f"done: {DONE_QUESTION} {check(DONE_QUESTION)}")
else:
    print("gave up picking")
