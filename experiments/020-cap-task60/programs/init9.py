z_start = gripper_position()[2]
bowl_target = "the center of the bowl to pick up"
tray_target = "the center of the tray"

# Approach the bowl using the fixed camera
for i in range(20):
    if in_wrist_view(bowl_target) > 0.4:
        break
    sx, sy = fixed_direction(bowl_target)
    if sx == 0 and sy == 0:
        sx, sy = fixed_direction("the black bowl on the left")
        if sx == 0 and sy == 0:
            if check("Is there a black bowl on the left?") > 0.5:
                break
            move_by(0.03, 0, 0)
            continue
    move_by(sx * 0.03, sy * 0.03, 0)

# Align the gripper to the bowl center using the wrist camera
for i in range(12):
    sx, sy = wrist_direction(bowl_target)
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

# Grasp the bowl, trying a few x-offsets to compensate for possible x error
offsets = [0.0, 0.04, -0.04]
held = False
current_offset = 0.0
for offset in offsets:
    if abs(offset - current_offset) > 1e-4:
        move_by(offset - current_offset, 0, 0)
        current_offset = offset
    move_by(0, -0.06, 0)
    for d in range(15):
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
        move_to(cur_x, cur_y, z_start)
        move_by(0, 0.06, 0)

if held:
    cur_x, cur_y, cur_z = gripper_position()
    move_to(cur_x, cur_y, z_start)

# Move toward the tray
last_sx, last_sy = 0, 0
for i in range(20):
    sx, sy = fixed_direction(tray_target)
    if sx == 0 and sy == 0:
        break
    last_sx, last_sy = sx, sy
    move_by(sx * 0.03, sy * 0.03, 0)

if last_sx != 0 or last_sy != 0:
    move_by(last_sx * 0.04, last_sy * 0.04, 0)

# Refine alignment over the tray
for i in range(10):
    sx, sy = wrist_direction(tray_target)
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

# Lower the bowl into the tray
for i in range(15):
    if not move_by(0, 0, -0.03):
        break

open_gripper()

cur_x, cur_y, cur_z = gripper_position()
move_to(cur_x, cur_y, z_start)
