def align_bowl():
    target = "the center of the bowl to pick up"
    zero = 0
    for i in range(8):
        fx, fy = fixed_direction(target)
        if fx == 0 and fy == 0:
            zero += 1
            if zero >= 2:
                break
        else:
            zero = 0
            move_by(fx * 0.03, fy * 0.03, 0)
    zero = 0
    for i in range(6):
        fx, fy = fixed_direction(target)
        wx, wy = wrist_direction(target)
        dx = fx if fx != 0 else wx
        dy = wy if wy != 0 else fy
        if dx == 0 and dy == 0:
            zero += 1
            if zero >= 2:
                break
        else:
            zero = 0
            move_by(dx * 0.01, dy * 0.01, 0)

def align_tray():
    target = "the center of the tray"
    zero = 0
    for i in range(12):
        fx, fy = fixed_direction(target)
        if fx == 0 and fy == 0:
            zero += 1
            if zero >= 2:
                break
        else:
            zero = 0
            move_by(fx * 0.03, fy * 0.03, 0)
    zero = 0
    for i in range(10):
        wx, wy = wrist_direction(target)
        fx, fy = fixed_direction(target)
        dx = wx if wx != 0 else fx
        dy = wy if wy != 0 else fy
        if dx == 0 and dy == 0:
            zero += 1
            if zero >= 2:
                break
        else:
            zero = 0
            move_by(dx * 0.015, dy * 0.015, 0)

start_x, start_y, start_z = gripper_position()

held = False
for attempt in range(3):
    align_bowl()
    if attempt == 1:
        move_by(0.02, 0, 0)
    elif attempt == 2:
        move_by(-0.02, 0, 0)
    move_by(0, -0.06, 0)
    for i in range(9):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)
        break
    else:
        open_gripper()
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)

align_tray()
move_by(0, -0.06, 0)
for i in range(9):
    if not move_by(0, 0, -0.03):
        break
open_gripper()
gx, gy, gz = gripper_position()
move_to(gx, gy, start_z)
