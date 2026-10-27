x0, y0, z_start = gripper_position()

# Locate the tray
zero_count = 0
for _ in range(15):
    if in_wrist_view("the center of the tray") > 0.4:
        break
    d = fixed_direction("the center of the tray")
    if d == (0, 0):
        zero_count += 1
        if zero_count >= 2:
            break
    else:
        zero_count = 0
        move_by(d[0] * 0.02, d[1] * 0.02, 0)

for _ in range(8):
    d = wrist_direction("the center of the tray")
    if d == (0, 0):
        d2 = wrist_direction("the center of the tray")
        if d2 == (0, 0):
            break
        else:
            d = d2
    move_by(d[0] * 0.02, d[1] * 0.02, 0)

tray_x, tray_y, _ = gripper_position()
move_to(x0, y0, z_start)

# Guess bowl position based on tray and known left side
y_guess = y0 + 0.20
if tray_y < y0:
    y_guess = y0 + (y0 - tray_y)
x_guess = tray_x

move_to(x_guess, y_guess, z_start)

found = False
if in_wrist_view("the black bowl on the left") > 0.4:
    found = True
else:
    offsets = []
    for i in range(-2, 3):
        for j in range(-2, 3):
            offsets.append((i * 0.05, j * 0.05))
    offsets.sort(key=lambda p: p[0] * p[0] + p[1] * p[1])
    for dx, dy in offsets:
        if dx == 0 and dy == 0:
            continue
        move_to(x_guess + dx, y_guess + dy, z_start)
        if in_wrist_view("the black bowl on the left") > 0.4:
            found = True
            break

if not found:
    for _ in range(15):
        if in_wrist_view("the black bowl on the left") > 0.4:
            found = True
            break
        d = fixed_direction("the black bowl on the left")
        if d == (0, 0):
            move_by(0, 0.02, 0)
        else:
            move_by(d[0] * 0.02, d[1] * 0.02, 0)

# Align over bowl center
for _ in range(10):
    d = wrist_direction("the black bowl on the left")
    if d == (0, 0):
        d2 = wrist_direction("the black bowl on the left")
        if d2 == (0, 0):
            break
        else:
            d = d2
    move_by(d[0] * 0.02, d[1] * 0.02, 0)

# Move to the rim (6 cm in +y)
move_by(0, 0.06, 0)

# Go down to grasp
for _ in range(10):
    if not move_by(0, 0, -0.03):
        break
move_by(0, 0, 0.015)
close_gripper()

# Recovery if grasp missed
if gripper_opening() <= 0.003:
    open_gripper()
    cur_x, cur_y, cur_z = gripper_position()
    move_by(0, 0, z_start - cur_z)
    move_by(0, -0.06, 0)
    for _ in range(8):
        d = wrist_direction("the black bowl on the left")
        if d == (0, 0):
            break
        move_by(d[0] * 0.02, d[1] * 0.02, 0)
    move_by(0, 0.06, 0)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()

# Lift to start height
cur_x, cur_y, cur_z = gripper_position()
move_by(0, 0, z_start - cur_z)

# Move to tray placement position
move_to(tray_x, tray_y + 0.06, z_start)

# Lower into tray
for _ in range(10):
    if not move_by(0, 0, -0.03):
        break

# Release
open_gripper()

# Move up to start height
cur_x, cur_y, cur_z = gripper_position()
move_by(0, 0, z_start - cur_z)
