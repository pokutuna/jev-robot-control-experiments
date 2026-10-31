start_pos = gripper_position()
start_z = start_pos[2]

def to_start_height():
    x, y, z = gripper_position()
    if abs(z - start_z) > 0.002:
        move_to(x, y, start_z)

def align_pudding():
    for i in range(15):
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            sx, sy = fixed_direction("the box")
            if sx == 0 and sy == 0:
                break
        move_by(sx * 0.03, sy * 0.03, 0)

    for i in range(8):
        sx, sy = wrist_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

    for i in range(2):
        sx, sy = wrist_direction("the box")
        if sy == 0:
            break
        move_by(0, sy * 0.015, 0)

def attempt_grasp():
    open_gripper()
    steps = 0
    while steps < 9:
        ok = move_by(0, 0, -0.03)
        if not ok:
            break
        steps += 1

    if steps >= 9:
        open_gripper()
        to_start_height()
        return False

    move_by(0, 0, 0.015)
    close_gripper()
    held = gripper_opening() > 0.003

    if held:
        move_by(0, 0, 0.06)
        to_start_height()
    else:
        open_gripper()
        to_start_height()

    return held

def go_to_tray():
    zero_count = 0
    for i in range(18):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            sx2, sy2 = fixed_direction("the tray")
            if not (sx2 == 0 and sy2 == 0):
                sx, sy = sx2, sy2
            else:
                zero_count += 1
                if zero_count >= 3:
                    break
                continue
        else:
            zero_count = 0
        move_by(sx * 0.035, sy * 0.035, 0)

    for i in range(4):
        sx, sy = wrist_direction("the center of the tray")
        if sy == 0:
            break
        move_by(0, sy * 0.02, 0)

def place_in_tray():
    steps = 0
    while steps < 9:
        ok = move_by(0, 0, -0.03)
        if not ok:
            break
        steps += 1

    move_by(0, 0, 0.03)
    open_gripper()
    to_start_height()

open_gripper()
align_pudding()

base_x, base_y, base_z = gripper_position()
held = False

for dx in [0.0, 0.03, -0.03, 0.06, -0.06]:
    move_to(base_x + dx, base_y, start_z)
    if attempt_grasp():
        held = True
        break

if held:
    go_to_tray()
    place_in_tray()
