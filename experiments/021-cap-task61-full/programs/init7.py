start_z = gripper_position()[2]

# Approach the pudding if it is not clearly visible in the wrist camera.
if in_wrist_view("the chocolate pudding box") < 0.6:
    for _ in range(8):
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        move_by(0.02 * sx, 0.02 * sy, 0)

# Fine alignment with the wrist camera at start height.
for _ in range(12):
    sx, sy = wrist_direction("the chocolate pudding box")
    if sx == 0 and sy == 0:
        sx2, sy2 = wrist_direction("the box")
        if sx2 == 0 and sy2 == 0:
            break
        sx, sy = sx2, sy2
    move_by(0.02 * sx, 0.02 * sy, 0)

held = False
for attempt in range(3):
    open_gripper()

    if attempt > 0:
        p = gripper_position()
        move_to(p[0], p[1], start_z)

        for _ in range(5):
            sx, sy = wrist_direction("the chocolate pudding box")
            if sx == 0 and sy == 0:
                sx2, sy2 = wrist_direction("the box")
                if sx2 == 0 and sy2 == 0:
                    break
                sx, sy = sx2, sy2
            move_by(0.02 * sx, 0.02 * sy, 0)

    # Lower until blocked.
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break

    move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        held = True
        break

    open_gripper()
    p = gripper_position()
    move_to(p[0], p[1], start_z)

# Lift the held object to carry height.
p = gripper_position()
move_to(p[0], p[1], start_z)

# Move above the tray.
for _ in range(18):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(0.02 * sx, 0.02 * sy, 0)

# Fine y alignment toward the tray; ignore x because it is unreliable while holding.
for _ in range(10):
    sx, sy = wrist_direction("the center of the tray")
    if sy == 0:
        break
    move_by(0, 0.02 * sy, 0)

# Lower into the tray until blocked.
for _ in range(10):
    if not move_by(0, 0, -0.03):
        break

# Move up before opening so the fingers do not press on tray dividers.
move_by(0, 0, 0.03)
open_gripper()

# Retreat upward.
p = gripper_position()
move_to(p[0], p[1], start_z)
