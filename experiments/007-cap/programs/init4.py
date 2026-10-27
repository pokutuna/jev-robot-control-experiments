def align_wrist(target, max_steps=12, step=0.03):
    prev_dx = prev_dy = 0
    flips = 0
    for i in range(max_steps):
        dx, dy = wrist_direction(target)
        if dx == 0 and dy == 0:
            return True
        if (dx, dy) == (-prev_dx, -prev_dy) and (prev_dx != 0 or prev_dy != 0):
            flips += 1
            if flips >= 2:
                step = max(0.005, step * 0.5)
                flips = 0
        else:
            flips = 0
        move_by(dx * step, dy * step, 0)
        prev_dx, prev_dy = dx, dy
    return False


def align_fixed(target, max_steps=12, step=0.04):
    zero_count = 0
    for i in range(max_steps):
        dx, dy = fixed_direction(target)
        if dx == 0 and dy == 0:
            zero_count += 1
            if zero_count >= 3:
                return True
        else:
            zero_count = 0
            move_by(dx * step, dy * step, 0)
    return False


start_x, start_y, start_z = gripper_position()
open_gripper()

bowl = "the black bowl on the left"
found = False

if in_wrist_view(bowl) > 0.25:
    align_wrist(bowl, max_steps=15)
    found = True
else:
    for i in range(10):
        if in_wrist_view(bowl) > 0.25:
            align_wrist(bowl, max_steps=15)
            found = True
            break
        dx, dy = fixed_direction(bowl)
        if dx == 0 and dy == 0:
            dx, dy = 0, 1
        move_by(dx * 0.03, dy * 0.03, 0)
    if not found and in_wrist_view(bowl) > 0.25:
        align_wrist(bowl, max_steps=15)
        found = True

if not found:
    move_to(start_x, start_y, start_z)
    for i in range(1, 9):
        move_by(0, 0.03, 0)
        if in_wrist_view(bowl) > 0.25:
            align_wrist(bowl, max_steps=15)
            found = True
            break

if not found:
    align_wrist(bowl, max_steps=20)

max_attempts = 2
grasped = False
for attempt in range(max_attempts):
    open_gripper()
    p = gripper_position()
    move_to(p[0], p[1], start_z)
    if in_wrist_view(bowl) > 0.2:
        align_wrist(bowl, max_steps=15)
    move_by(0, 0.06, 0)
    for i in range(8):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        grasped = True
        break
    else:
        open_gripper()
        move_by(0, 0, 0.05)

p = gripper_position()
move_to(p[0], p[1], start_z)

tray = "the center of the tray"
align_fixed(tray, max_steps=12, step=0.04)
move_by(0, 0.06, 0)
for i in range(8):
    if not move_by(0, 0, -0.03):
        break
open_gripper()
p = gripper_position()
move_to(p[0], p[1], start_z)
