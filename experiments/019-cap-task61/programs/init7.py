start = gripper_position()
start_x, start_y, start_z = start
open_gripper()

def grasp_pudding(use_fixed):
    if use_fixed:
        for _ in range(12):
            sx, sy = fixed_direction("the chocolate pudding box")
            if sx == 0 and sy == 0:
                break
            if not move_by(0.02 * sx, 0.02 * sy, 0):
                break
    for _ in range(6):
        sx, sy = wrist_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        move_by(0.02 * sx, 0.02 * sy, 0)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        cur = gripper_position()
        move_to(cur[0], cur[1], start_z)
        return True
    else:
        open_gripper()
        cur = gripper_position()
        move_to(cur[0], cur[1], start_z)
        return False

held = False
for attempt in range(3):
    if grasp_pudding(attempt == 0):
        held = True
        break

for _ in range(12):
    if in_wrist_view("the center of the tray") > 0.5:
        break
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(0.02 * sx, 0.02 * sy, 0)

for _ in range(6):
    p = in_wrist_view("the center of the tray")
    if p < 0.2:
        break
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(0.02 * sx, 0.02 * sy, 0)

for _ in range(12):
    if not move_by(0, 0, -0.03):
        break
open_gripper()
cur = gripper_position()
move_to(cur[0], cur[1], start_z)
