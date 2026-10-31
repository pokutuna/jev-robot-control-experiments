start_z = gripper_position()[2]
open_gripper()

grasped = False
for attempt in range(2):
    cz = gripper_position()[2]
    if abs(cz - start_z) > 0.01:
        move_by(0, 0, start_z - cz)

    if attempt == 0:
        for _ in range(8):
            if in_wrist_view("the black bowl") > 0.5:
                break
            move_by(0, 0.03, 0)

    for _ in range(15):
        sx, sy = wrist_direction("the center of the bowl to pick up")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

    move_by(0, -0.06, 0)

    for _ in range(5):
        sx, sy = wrist_direction("the left edge of the bowl to pick up")
        if sy == 0:
            break
        move_by(0, sy * 0.02, 0)

    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break

    move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        grasped = True
        break
    else:
        open_gripper()
        cz = gripper_position()[2]
        move_by(0, 0, start_z - cz)

cz = gripper_position()[2]
if cz < start_z - 0.01:
    move_by(0, 0, start_z - cz)

for _ in range(20):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

for _ in range(8):
    if in_wrist_view("the center of the tray") < 0.3:
        break
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

move_by(0, -0.06, 0)

for _ in range(10):
    if not move_by(0, 0, -0.03):
        break

open_gripper()
move_by(0, 0, 0.10)
