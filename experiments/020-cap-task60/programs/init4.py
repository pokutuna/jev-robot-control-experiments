def center_on(target, max_iter=8):
    probes = 0
    for _ in range(max_iter):
        sx, sy = wrist_direction(target)
        if sx != 0 or sy != 0:
            dx = sx * 0.02 if sx != 0 else 0.0
            dy = sy * 0.02 if sy != 0 else 0.0
            move_by(dx, dy, 0.0)
            probes = 0
        else:
            if probes >= 2:
                break
            probes += 1
            move_by(0.02, 0.0, 0.0)
            px, _ = wrist_direction(target)
            if px != 0:
                move_by(px * 0.03, 0.0, 0.0)
                continue
            move_by(-0.04, 0.0, 0.0)
            nx, _ = wrist_direction(target)
            if nx != 0:
                move_by(nx * 0.03, 0.0, 0.0)
                continue
            move_by(0.02, 0.0, 0.0)


start_x, start_y, start_z = gripper_position()
tray_target = "the center of the tray"
bowl_target = "the center of the bowl to pick up"

# Locate the tray center and remember its coordinates.
zero = 0
for i in range(10):
    if in_wrist_view(tray_target) > 0.2:
        break
    sx, sy = fixed_direction(tray_target)
    if sx == 0 and sy == 0:
        zero += 1
        if zero >= 2:
            break
        sx2, sy2 = fixed_direction("the tray")
        if sx2 != 0 or sy2 != 0:
            sx, sy = sx2, sy2
            zero = 0
    else:
        zero = 0
    if sx != 0 or sy != 0:
        move_by(sx * 0.04, sy * 0.04, 0.0)

center_on(tray_target, max_iter=8)
tray_x, tray_y, _ = gripper_position()

# Move toward the black bowl on the left.
zero = 0
for i in range(12):
    if in_wrist_view(bowl_target) > 0.2:
        break
    sx, sy = fixed_direction(bowl_target)
    if sx == 0 and sy == 0:
        sx2, sy2 = fixed_direction("the black bowl on the left")
        if sx2 != 0 or sy2 != 0:
            sx, sy = sx2, sy2
    if sx == 0 and sy == 0:
        wx, wy = wrist_direction(bowl_target)
        if wx == 0 and wy == 0:
            zero += 1
            if zero >= 2:
                break
        else:
            zero = 0
            sx, sy = wx, wy
    else:
        zero = 0
    if sx != 0 or sy != 0:
        move_by(sx * 0.04, sy * 0.04, 0.0)

if in_wrist_view(bowl_target) < 0.1:
    for i in range(5):
        move_by(0.0, 0.03, 0.0)
        if in_wrist_view(bowl_target) > 0.15:
            break

center_on(bowl_target, max_iter=8)

# Try to grasp the bowl rim.
held = False
held_offset = 0.06
held_xadj = 0.0
attempts = [(0.06, 0.0), (0.05, 0.02), (0.07, -0.02)]

for idx, (offset, xadj) in enumerate(attempts):
    if idx > 0:
        cur = gripper_position()
        if cur[2] < start_z - 0.001:
            move_to(cur[0], cur[1], start_z)
        center_on(bowl_target, max_iter=5)
    cur = gripper_position()
    if cur[2] < start_z - 0.001:
        move_to(cur[0], cur[1], start_z)

    open_gripper()
    move_by(xadj, -offset, 0.0)

    for j in range(10):
        if not move_by(0.0, 0.0, -0.03):
            break
    move_by(0.0, 0.0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        held = True
        held_offset = offset
        held_xadj = xadj
        break
    else:
        open_gripper()
        cur = gripper_position()
        move_to(cur[0], cur[1], start_z)

# Carry the bowl to the remembered tray center and place it.
if held:
    cur = gripper_position()
    move_to(cur[0], cur[1], start_z)

    target_x = tray_x + held_xadj
    target_y = tray_y - held_offset
    move_to(target_x, target_y, start_z)

    for i in range(12):
        if not move_by(0.0, 0.0, -0.03):
            break

    open_gripper()
    cur = gripper_position()
    move_to(cur[0], cur[1], start_z)
