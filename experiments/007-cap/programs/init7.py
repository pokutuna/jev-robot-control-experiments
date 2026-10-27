start_x, start_y, start_z = gripper_position()
open_gripper()

def align_wrist(target, max_steps=15, step=0.02):
    zeros = 0
    for i in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
            continue
        else:
            zeros = 0
        if not move_by(sx * step, sy * step, 0):
            if not move_by(sx * step * 0.5, sy * step * 0.5, 0):
                break

def align_fixed(target, max_steps=30, step=0.02):
    zeros = 0
    for i in range(max_steps):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
            continue
        else:
            zeros = 0
        if not move_by(sx * step, sy * step, 0):
            if not move_by(sx * step * 0.5, sy * step * 0.5, 0):
                break

align_wrist("the black bowl on the left", max_steps=15)
move_by(0, 0.06, 0)

held = False
for attempt in range(2):
    if attempt > 0:
        open_gripper()
        cur_x, cur_y, cur_z = gripper_position()
        move_to(cur_x, cur_y, start_z)
        align_wrist("the black bowl on the left", max_steps=12)
        move_by(0, 0.06, 0)
    for i in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        break
    else:
        open_gripper()
        cur_x, cur_y, cur_z = gripper_position()
        move_to(cur_x, cur_y, start_z)

cur_x, cur_y, cur_z = gripper_position()
move_to(cur_x, cur_y, start_z)

align_fixed("the center of the tray", max_steps=30)
move_by(0, 0.06, 0)

for i in range(10):
    if not move_by(0, 0, -0.03):
        break

open_gripper()

cur_x, cur_y, cur_z = gripper_position()
move_to(cur_x, cur_y, start_z)
