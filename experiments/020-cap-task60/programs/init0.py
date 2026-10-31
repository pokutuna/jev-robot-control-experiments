mv_count = 0
vis_count = 0

def mv(dx, dy, dz):
    global mv_count
    if mv_count >= 115:
        return False
    mv_count += 1
    return move_by(dx, dy, dz)

def mv_to(x, y, z):
    global mv_count
    if mv_count >= 115:
        return False
    mv_count += 1
    return move_to(x, y, z)

def wdir(target):
    global vis_count
    if vis_count >= 355:
        return (0, 0)
    vis_count += 1
    return wrist_direction(target)

def fdir(target):
    global vis_count
    if vis_count >= 355:
        return (0, 0)
    vis_count += 1
    return fixed_direction(target)

def chk(q):
    global vis_count
    if vis_count >= 355:
        return 0.0
    vis_count += 1
    return check(q)

def approach_fixed(target, step=0.02, max_steps=25, need_zeros=2):
    zeros = 0
    for _ in range(max_steps):
        sx, sy = fdir(target)
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= need_zeros:
                break
        else:
            zeros = 0
            if sx != 0 and sy != 0:
                mv(step * sx, step * sy, 0)
            elif sx != 0:
                mv(step * sx, 0, 0)
            else:
                mv(0, step * sy, 0)

def check_x_relative(desc):
    p1 = chk("In the wrist camera image, is " + desc + " below the red cross?")
    p2 = chk("In the wrist camera image, is " + desc + " above the red cross?")
    if p1 > 0.65 and p1 > p2:
        return 1
    if p2 > 0.65 and p2 > p1:
        return -1
    return 0

def align_wrist(target, step=0.015, max_steps=10, need_zeros=2, x_check_desc=None):
    zeros = 0
    for i in range(max_steps):
        sx, sy = wdir(target)
        moved = False
        if sy != 0:
            mv(0, step * sy, 0)
            moved = True
        if sx != 0:
            mv(step * sx, 0, 0)
            moved = True
        elif x_check_desc is not None and (i % 3 == 2):
            dx = check_x_relative(x_check_desc)
            if dx != 0:
                mv(step * dx, 0, 0)
                moved = True
        if not moved:
            zeros += 1
            if zeros >= need_zeros:
                break
        else:
            zeros = 0

def grasp_bowl(max_attempts=3):
    phrase = "the center of the bowl to pick up"
    for attempt in range(max_attempts):
        if mv_count > 75:
            break
        approach_fixed(phrase, step=0.02, max_steps=25 if attempt == 0 else 12, need_zeros=2)
        align_wrist(phrase, step=0.015, max_steps=10, need_zeros=2, x_check_desc=phrase)
        mv(0, -0.06, 0)
        open_gripper()
        for _ in range(12):
            if not mv(0, 0, -0.03):
                break
        mv(0, 0, 0.015)
        close_gripper()
        if gripper_opening() > 0.003:
            cur = gripper_position()
            dz = start_z - cur[2]
            if dz > 0.001:
                mv(0, 0, dz)
            return True
        else:
            open_gripper()
            cur = gripper_position()
            dz = start_z - cur[2]
            if dz > 0.001:
                mv(0, 0, dz)
    return False

open_gripper()
sx0, sy0, start_z = gripper_position()

tray_phrase = "the center of the tray"
approach_fixed(tray_phrase, step=0.02, max_steps=35, need_zeros=2)
align_wrist(tray_phrase, step=0.015, max_steps=12, need_zeros=2, x_check_desc=None)
tx, ty, _ = gripper_position()

held = grasp_bowl(max_attempts=3)

if not held and mv_count < 90:
    phrase = "the center of the bowl to pick up"
    approach_fixed(phrase, step=0.02, max_steps=10, need_zeros=2)
    align_wrist(phrase, step=0.015, max_steps=8, need_zeros=2, x_check_desc=None)
    mv(0, -0.06, 0)
    open_gripper()
    for _ in range(12):
        if not mv(0, 0, -0.03):
            break
    mv(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
    cur = gripper_position()
    dz = start_z - cur[2]
    if dz > 0.001:
        mv(0, 0, dz)
    if not held:
        open_gripper()

cur = gripper_position()
if cur[2] < start_z - 0.001:
    mv(0, 0, start_z - cur[2])

place_x = tx
place_y = ty - 0.06
if not mv_to(place_x, place_y, start_z):
    cur = gripper_position()
    dx = place_x - cur[0]
    dy = place_y - cur[1]
    dz = start_z - cur[2]
    if abs(dx) > 0.001:
        mv(dx, 0, 0)
    if abs(dy) > 0.001:
        mv(0, dy, 0)
    if abs(dz) > 0.001:
        mv(0, 0, dz)

for _ in range(12):
    if not mv(0, 0, -0.03):
        break
open_gripper()
mv(0, 0, 0.12)
cur = gripper_position()
if cur[2] < start_z:
    mv(0, 0, start_z - cur[2])
