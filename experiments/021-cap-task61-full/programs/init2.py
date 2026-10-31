start_x, start_y, start_z = gripper_position()

def align_pudding():
    for _ in range(10):
        d = fixed_direction("the chocolate pudding box")
        if d == (0, 0):
            break
        move_by(d[0] * 0.02, d[1] * 0.02, 0)
    for _ in range(10):
        d = wrist_direction("the box")
        if d == (0, 0):
            break
        move_by(d[0] * 0.02, d[1] * 0.02, 0)

for attempt in range(2):
    align_pudding()
    for _ in range(12):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        break
    else:
        open_gripper()
        cx, cy, cz = gripper_position()
        move_to(cx, cy, start_z)

if gripper_opening() > 0.003:
    cx, cy, cz = gripper_position()
    move_to(cx, cy, start_z)

for _ in range(15):
    d = fixed_direction("the center of the tray")
    if d == (0, 0):
        break
    move_by(d[0] * 0.02, d[1] * 0.02, 0)

for _ in range(12):
    if not move_by(0, 0, -0.03):
        break

move_by(0, 0, 0.03)
open_gripper()
cx, cy, cz = gripper_position()
move_to(cx, cy, start_z)
