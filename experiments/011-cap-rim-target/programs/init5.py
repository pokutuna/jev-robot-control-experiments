start_x, start_y, z0 = gripper_position()

# Helper to align using the wrist camera.
def align_wrist(target, max_iter=8, step=0.02):
    for _ in range(max_iter):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            return True
        if not move_by(sx * step, sy * step, 0):
            if sx != 0:
                move_by(sx * step, 0, 0)
            if sy != 0:
                move_by(0, sy * step, 0)
    return False

# Locate the tray center and remember it.
if in_wrist_view("the center of the tray") > 0.20:
    align_wrist("the center of the tray", max_iter=8, step=0.02)
else:
    for _ in range(20):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        if not move_by(sx * 0.03, sy * 0.03, 0):
            if sx != 0:
                move_by(sx * 0.03, 0, 0)
            if sy != 0:
                move_by(0, sy * 0.03, 0)
    if in_wrist_view("the center of the tray") > 0.20:
        align_wrist("the center of the tray", max_iter=8, step=0.02)
    else:
        cur_x, cur_y, _ = gripper_position()
        for dx, dy in [(0,0),(-0.06,0),(0.06,0),(0,-0.06),(0,0.06),
                       (-0.06,-0.06),(-0.06,0.06),(0.06,-0.06),(0.06,0.06)]:
            move_to(cur_x + dx, cur_y + dy, z0)
            if in_wrist_view("the center of the tray") > 0.20:
                align_wrist("the center of the tray", max_iter=8, step=0.02)
                break

tray_x, tray_y, _ = gripper_position()
move_to(start_x, start_y, z0)

# Find the bowl and align to the gripping pose.
if in_wrist_view("the center of the bowl to pick up") <= 0.15:
    found = False
    for dx in [-0.2, -0.1, 0.0, 0.1, 0.2]:
        for dy in [-0.2, -0.1, 0.0, 0.1, 0.2]:
            move_to(start_x + dx, start_y + dy, z0)
            if in_wrist_view("the center of the bowl to pick up") > 0.15:
                found = True
                break
        if found:
            break
    if not found:
        for _ in range(8):
            sx, sy = fixed_direction("the black bowl on the left")
            if sx == 0 and sy == 0:
                break
            move_by(sx * 0.03, sy * 0.03, 0)
            if in_wrist_view("the center of the bowl to pick up") > 0.15:
                break

# Align over bowl center.
align_wrist("the center of the bowl to pick up", max_iter=8, step=0.02)

# Move from bowl center toward the -y rim.
for _ in range(6):
    sx, sy = wrist_direction("the left edge of the bowl to pick up")
    if sy == 0:
        break
    move_by(0, sy * 0.02, 0)
move_by(0, -0.01, 0)

# Refine x using the bowl center.
for _ in range(4):
    sx, sy = wrist_direction("the center of the bowl to pick up")
    if sx == 0:
        break
    move_by(sx * 0.02, 0, 0)

# Grasp the bowl.
grasped = False
open_gripper()
for attempt in range(2):
    cur_x, cur_y, cur_z = gripper_position()

    for _ in range(15):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        grasped = True
        break
    else:
        open_gripper()
        move_to(cur_x, cur_y, z0)
        align_wrist("the center of the bowl to pick up", max_iter=6, step=0.02)
        for _ in range(6):
            sx, sy = wrist_direction("the left edge of the bowl to pick up")
            if sy == 0:
                break
            move_by(0, sy * 0.02, 0)
        move_by(0, -0.01, 0)
        for _ in range(4):
            sx, sy = wrist_direction("the center of the bowl to pick up")
            if sx == 0:
                break
            move_by(sx * 0.02, 0, 0)

# Lift to carrying height.
cur_x, cur_y, cur_z = gripper_position()
move_to(cur_x, cur_y, z0)

# Move to the pre-placement pose above the tray.
place_x = tray_x
place_y = tray_y - 0.06
move_to(place_x, place_y, z0)

# Lower into the tray and release.
for _ in range(20):
    if not move_by(0, 0, -0.03):
        break
open_gripper()
move_by(0, 0, 0.05)
