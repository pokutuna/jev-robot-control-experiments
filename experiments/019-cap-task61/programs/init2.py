start_z = gripper_position()[2]

# Roughly approach the chocolate pudding using the fixed camera
for _ in range(8):
    vis = in_wrist_view("the chocolate pudding box")
    if vis > 0.5:
        break
    sx, sy = fixed_direction("the chocolate pudding box")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.035, sy * 0.035, 0)

# Fine alignment with the wrist camera
for _ in range(8):
    sx, sy = wrist_direction("the box")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

# Remember the aligned position for small search offsets
base_x, base_y, _ = gripper_position()
offsets = [(0, 0), (0.02, 0), (-0.02, 0), (0.04, 0)]

open_gripper()
success = False

for dx, dy in offsets:
    if dx != 0 or dy != 0:
        move_to(base_x + dx, base_y + dy, start_z)
        sx, sy = wrist_direction("the box")
        if sy != 0:
            move_by(0, sy * 0.02, 0)

    # Descend until blocked by the pudding or table
    for _ in range(20):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()

    # Lift back to the start height
    z = gripper_position()[2]
    dz = start_z - z
    if dz > 0:
        move_by(0, 0, dz)

    if gripper_opening() > 0.003:
        success = True
        break
    else:
        open_gripper()

# Move to the tray
for _ in range(12):
    vis = in_wrist_view("the tray")
    if vis > 0.6:
        sx, sy = wrist_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    else:
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.04, sy * 0.04, 0)

# Lower the pudding into the tray
for _ in range(20):
    if not move_by(0, 0, -0.03):
        break
open_gripper()

# Lift the arm back to the start height
z = gripper_position()[2]
dz = start_z - z
if dz > 0:
    move_by(0, 0, dz)
