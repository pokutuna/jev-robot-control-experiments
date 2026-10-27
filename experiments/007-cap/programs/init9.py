z_start = gripper_position()[2]

def align_wrist(target, max_iters=10, step=0.02, need_zero=2):
    prev_sx = 0
    prev_sy = 0
    zero_count = 0
    for _ in range(max_iters):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            zero_count += 1
            if zero_count >= need_zero:
                return True
        else:
            zero_count = 0
            dx = sx * step
            dy = sy * step
            if prev_sx != 0 and sx != 0 and sx == -prev_sx:
                dx *= 0.5
            if prev_sy != 0 and sy != 0 and sy == -prev_sy:
                dy *= 0.5
            if abs(dx) > 1e-4 or abs(dy) > 1e-4:
                move_by(dx, dy, 0)
            prev_sx, prev_sy = sx, sy
    return False

def align_fixed(target, max_iters=20, step=0.02):
    prev_sx = 0
    prev_sy = 0
    zero_count = 0
    for _ in range(max_iters):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            zero_count += 1
            if zero_count >= 1:
                return True
        else:
            zero_count = 0
            dx = sx * step
            dy = sy * step
            if prev_sx != 0 and sx != 0 and sx == -prev_sx:
                dx *= 0.5
            if prev_sy != 0 and sy != 0 and sy == -prev_sy:
                dy *= 0.5
            if abs(dx) > 1e-4 or abs(dy) > 1e-4:
                move_by(dx, dy, 0)
            prev_sx, prev_sy = sx, sy
    return False

def attempt_grasp():
    align_wrist("the black bowl on the left", max_iters=10, step=0.02, need_zero=2)
    align_wrist("the black bowl on the left", max_iters=6, step=0.01, need_zero=1)
    move_by(0, 0.06, 0)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    return gripper_opening() > 0.003

held = False
for attempt in range(2):
    if attempt > 0:
        open_gripper()
        cur_z = gripper_position()[2]
        move_by(0, 0, z_start - cur_z)
    if attempt_grasp():
        held = True
        break

cur_z = gripper_position()[2]
move_by(0, 0, z_start - cur_z)

align_fixed("the center of the tray", max_iters=20, step=0.02)

for _ in range(6):
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.01, sy * 0.01, 0)

move_by(0, 0.06, 0)

for _ in range(10):
    if not move_by(0, 0, -0.03):
        break

open_gripper()
move_by(0, 0, 0.10)
