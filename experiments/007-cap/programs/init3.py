start_x, start_y, start_z = gripper_position()

bowl_target = "the black bowl on the left"

found = False
if in_wrist_view(bowl_target) > 0.5:
    found = True

if not found:
    for _ in range(12):
        if in_wrist_view(bowl_target) > 0.5:
            found = True
            break
        sx, sy = fixed_direction(bowl_target)
        if sx == 0 and sy == 0:
            sx, sy = 0, 1
        move_by(sx * 0.02, sy * 0.02, 0)

if not found:
    for _ in range(12):
        if in_wrist_view(bowl_target) > 0.5:
            found = True
            break
        move_by(0, 0.02, 0)

if not found:
    for _ in range(5):
        sx, sy = fixed_direction(bowl_target)
        if sx == 0 and sy == 0:
            sx, sy = 0, 1
        move_by(sx * 0.02, sy * 0.02, 0)
        if in_wrist_view(bowl_target) > 0.5:
            found = True
            break

for _ in range(8):
    if in_wrist_view(bowl_target) < 0.3:
        sx, sy = fixed_direction(bowl_target)
        if sx == 0 and sy == 0:
            sx, sy = 0, 1
        move_by(sx * 0.02, sy * 0.02, 0)
        continue
    sx, sy = wrist_direction("the center of the black bowl on the left")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

move_by(0, 0.06, 0)

grasped = False
for attempt in range(2):
    if attempt > 0:
        open_gripper()
        x, y, z = gripper_position()
        if z < start_z - 0.005:
            move_by(0, 0, start_z - z)
        for _ in range(6):
            if in_wrist_view(bowl_target) < 0.3:
                sx, sy = fixed_direction(bowl_target)
                if sx == 0 and sy == 0:
                    sx, sy = 0, 1
                move_by(sx * 0.02, sy * 0.02, 0)
                continue
            sx, sy = wrist_direction("the center of the black bowl on the left")
            if sx == 0 and sy == 0:
                break
            move_by(sx * 0.02, sy * 0.02, 0)
        move_by(0, 0.06, 0)

    while move_by(0, 0, -0.03):
        pass
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        grasped = True
        break
    else:
        open_gripper()
        move_by(0, 0, 0.03)

if grasped:
    x, y, z = gripper_position()
    if z < start_z - 0.005:
        move_by(0, 0, start_z - z)

tray_target = "the tray"

for _ in range(20):
    sx, sy = fixed_direction(tray_target)
    if sx == 0 and sy == 0:
        break
    if not move_by(sx * 0.02, sy * 0.02, 0):
        break

for _ in range(8):
    inv = in_wrist_view(tray_target)
    if inv < 0.3:
        sx, sy = fixed_direction(tray_target)
        if sx != 0 or sy != 0:
            move_by(sx * 0.02, sy * 0.02, 0)
            continue
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        if in_wrist_view(tray_target) > 0.3:
            break
        else:
            move_by(0.02, 0, 0)
    else:
        move_by(sx * 0.02, sy * 0.02, 0)

move_by(0, 0.06, 0)

while move_by(0, 0, -0.03):
    pass

open_gripper()

x, y, z = gripper_position()
if z < start_z - 0.005:
    move_by(0, 0, start_z - z)
