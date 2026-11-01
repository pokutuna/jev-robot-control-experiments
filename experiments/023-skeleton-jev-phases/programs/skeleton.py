# 物を掴んで置き場所に置くタスクに共通の手順の骨組み (実験 023)。人が書き、タスクを替えても変えない。
#
# s1cap.cap の部品だけを使い、物の位置は使わない。タスクに固有の値は、この前につなぐファイル (task61.py など) で決める。
#   OBJECT         運ぶ物の言い方。始めの高さで × を寄せる行き先
#   GRASP_SHIFT    OBJECT に合わせた後、掴む場所までずらす量 (dx, dy) [m]。置き場所に寄せた後も同じだけずらす
#   GRASP_TARGET   掴む段で × を寄せる行き先の言い方
#   HELD           持っている物の言い方。置く段で、持っている物を置き場所へ寄せる向きを問う
#   PLACE          置き場所の言い方
#   DONE_QUESTION  置き終えたかを両方の画像に問う文
#
# 手順: 運ぶ物に寄せる → 掴む段 → 持ち上げる → 置き場所へ寄せる → 置く段 → 上げる → 置けたかを問う
# 掴む段と置く段では、手首の画像 1 枚で、向き (h、v) と次の動作 (ACTIONS) を 1 回ごとに Jev に選ばせる。
# 横に寄せる、下ろす、閉じる、開くのどれを行うかは Jev が決め、コードは選ばれた動作を行う。下ろす命令が
# 届かずに止まった直後だけは、選択肢を閉じる、開くに絞る。向きの答えは
# 横に寄せるときだけ使い、下ろすときは真下へ下ろす。閉じた後は指の開きで掴めたかを確かめ、
# 掴めていなければ開いて上げ、運ぶ物に寄せるところからやり直す。

STEP = 0.02  # 1 回の向きの答えで動く量 [m]
DOWN = 0.03  # "lower" で真下へ下ろす量 [m]
HELD_WIDTH = 0.003  # 指を閉じた後の開きがこれより大きければ物を持っている [m]
MAX_FIXED_STEPS = 30  # 固定カメラの答えで寄せる歩数の上限 (2 cm × 30 = 60 cm)
MAX_WRIST_STEPS = 15  # 手首カメラの答えで合わせる歩数の上限
MAX_GRASP_STEPS = 25  # 掴む段で Jev に問う回数の上限
MAX_RELEASE_STEPS = 30  # 置く段で Jev に問う回数の上限
MAX_GRASP_TRIES = 3

# 掴む段と置く段で同じ選択肢を渡す。動作の名前と、それを選ぶ条件
ACTIONS = {
    "move": "the {mark} is not over {target} yet",
    "lower": "the {mark} is over {target}, and the gripper can still go down",
    "close": "the fingers are open, around {target}, and low enough to grip it",
    "open": "the fingers are closed, and the held object is on {target}",
}

START_Z = gripper_position()[2]  # 始めの高さ。運ぶ高さにも使う


def follow(direction, target, max_steps):
    """direction (wrist_direction か fixed_direction) の答えの向きへ STEP ずつ動き、(0, 0) と答えたら止まる。"""
    for _ in range(max_steps):
        sx, sy = direction(target)
        if sx == 0 and sy == 0:
            return True
        move_by(sx * STEP, sy * STEP, 0.0)
    return False


def go_up():
    x, y, _ = gripper_position()
    move_to(x, y, START_Z)


def step(target, mark, max_steps, done):
    """向きと動作を問い、選ばれた動作を行う。done(action) が真を返したら、その動作を返す。
    下ろす命令が届かずに止まった直後は、指か持っている物が何かに当たっている。それ以上は下りられず、
    横に動くと当たっている物を引きずるので、選択肢を指の開閉 (close、open) だけにする。"""
    actions = {k: c.format(mark=mark, target=target) for k, c in ACTIONS.items()}
    blocked = False
    for _ in range(max_steps):
        offered = {
            k: c for k, c in actions.items() if not blocked or k in ("close", "open")
        }
        sx, sy, action = wrist_step(target, offered, mark)
        blocked = False
        if action == "close":
            close_gripper()
        elif action == "open":
            open_gripper()
        elif action == "lower":
            blocked = not move_by(0.0, 0.0, -DOWN)
        else:
            move_by(sx * STEP, sy * STEP, 0.0)
        if done(action):
            return action
    return None


def pick():
    for attempt in range(MAX_GRASP_TRIES):
        follow(fixed_direction, OBJECT, MAX_FIXED_STEPS)
        follow(wrist_direction, OBJECT, MAX_WRIST_STEPS)
        move_by(GRASP_SHIFT[0], GRASP_SHIFT[1], 0.0)
        if step(GRASP_TARGET, "red cross", MAX_GRASP_STEPS, lambda a: a == "close"):
            if gripper_opening() > HELD_WIDTH:
                go_up()
                if gripper_opening() > HELD_WIDTH:
                    return True
                print(f"try {attempt}: dropped while lifting")
            else:
                print(f"try {attempt}: missed")
        else:
            print(f"try {attempt}: did not close")
        open_gripper()
        go_up()
    return False


def place():
    follow(fixed_direction, PLACE, MAX_FIXED_STEPS)
    move_by(GRASP_SHIFT[0], GRASP_SHIFT[1], 0.0)
    if not step(PLACE, HELD, MAX_RELEASE_STEPS, lambda a: a == "open"):
        print("did not open")
        return
    go_up()


if pick():
    place()
    print(f"done: {DONE_QUESTION} {check(DONE_QUESTION)}")
else:
    print("gave up picking")
