pos = gripper_position()
start_x, start_y, start_z = pos

# Find the black bowl
bowl_visible = in_wrist_view("the black bowl") > 0.5

if not bowl_visible:
    for _ in range(3):
        if in_wrist_view("the black bowl") > 0.5:
            bowl_visible = True
            break
        sx, sy = fixed_direction("the black bowl")
        if sx == 0 and sy == 0:
            sy = 1
        move_by(sx * 0.02, sy * 0.02, 0)
    if not bowl_visible:
        move_to(start_x, start_y, start_z)
        for _ in range(15):
            if in_wrist_view("the black bowl") > 0.5:
                bowl_visible = True
                break
            if not move_by(0, 0.03, 0):
                break

# Align to bowl center
for _ in range(15):
    sx, sy = wrist_direction("the black bowl")
    if sx == 0 and sy == 0:
        sx2, sy2 = wrist_direction("the black bowl")
        if sx2 == 0 and sy2 == 0:
            break
    move_by(sx * 0.02, sy * 0.02, 0)

# Move to rim
move_by(0, 0.06, 0)

# Descend and grasp
for _ in range(10):
    if not move_by(0, 0, -0.03):
        break
move_by(0, 0, 0.015)
close_gripper()
grasped = gripper_opening() > 0.003

# Retry once if grasp failed
if not grasped:
    open_gripper()
    pos = gripper_position()
    move_to(pos[0], pos[1], start_z)
    for _ in range(10):
        sx, sy = wrist_direction("the black bowl")
        if sx == 0 and sy == 0:
            sx2, sy2 = wrist_direction("the black bowl")
            if sx2 == 0 and sy2 == 0:
                break
        move_by(sx * 0.02, sy * 0.02, 0)
    move_by(0, 0.06, 0)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    grasped = gripper_opening() > 0.003

# Lift to start height
pos = gripper_position()
move_to(pos[0], pos[1], start_z)

# Move to tray
for _ in range(15):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.03, sy * 0.03, 0)

# Fine align with tray if visible
if in_wrist_view("the tray") > 0.5:
    for _ in range(10):
        sx, sy = wrist_direction("the center of the tray")
        if sx == 0 and sy == 0:
            sx2, sy2 = wrist_direction("the center of the tray")
            if sx2 == 0 and sy2 == 0:
                break
        move_by(sx * 0.02, sy * 0.02, 0)

# Offset for bowl center (held 6 cm in -y from gripper)
move_by(0, 0.06, 0)

# Lower to place
for _ in range(10):
    if not move_by(0, 0, -0.03):
        break

# Open gripper and clear
open_gripper()
pos = gripper_position()
move_to(pos[0], pos[1], start_z)
