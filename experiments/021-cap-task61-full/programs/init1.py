start_x, start_y, start_z = gripper_position()

def lift_to_start():
    x, y, z = gripper_position()
    dz = start_z - z
    if dz > 0.001:
        move_by(0, 0, dz)

def align_fixed(target, max_steps, step=0.03, need_zero=1):
    zeros = 0
    for _ in range(max_steps):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= need_zero:
                return True
        else:
            zeros = 0
            move_by(sx * step, sy * step, 0)
    return False

def align_wrist_pick():
    zeros = 0
    for _ in range(8):
        sx, sy = wrist_direction("the box")
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                return
        else:
            zeros = 0
            move_by(sx * 0.02, sy * 0.02, 0)

def align_wrist_tray_y():
    zeros = 0
    for _ in range(6):
        sx, sy = wrist_direction("the center of the tray")
        if sy == 0:
            zeros += 1
            if zeros >= 2:
                return
        else:
            zeros = 0
            move_by(0, sy * 0.02, 0)

def attempt_pick():
    align_fixed("the chocolate pudding box", 9, 0.03, 1)
    align_wrist_pick()

    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break

    move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        lift_to_start()
        return True
    else:
        open_gripper()
        lift_to_start()
        return False

def place_in_tray():
    align_fixed("the center of the tray", 9, 0.03, 2)
    align_wrist_tray_y()

    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break

    move_by(0, 0, 0.03)
    open_gripper()
    lift_to_start()

held = False
for _ in range(3):
    if attempt_pick():
        held = True
        break

if held:
    place_in_tray()
