start_pos = gripper_position()
start_z = start_pos[2]


def raise_to_start():
    x, y, z = gripper_position()
    dz = start_z - z
    tries = 0
    while dz > 0.005 and tries < 12:
        step = min(0.10, dz)
        if not move_by(0, 0, step):
            if not move_by(0, 0, 0.03):
                break
        x, y, z = gripper_position()
        dz = start_z - z
        tries += 1


def descend_until_block(max_steps=12):
    for _ in range(max_steps):
        if not move_by(0, 0, -0.03):
            return True
    return False


def align_pudding():
    # Coarse approach with the fixed camera.
    for i in range(20):
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx != 0 or sy != 0:
            step = 0.04 if i < 8 else 0.02
            move_by(sx * step, sy * step, 0)
            continue

        if in_wrist_view("the chocolate pudding box") > 0.5:
            break

        wx, wy = wrist_direction("the box")
        if wx == 0 and wy == 0:
            break
        move_by(wx * 0.02, wy * 0.02, 0)

    # Fine alignment at start height using the wrist camera.
    stable = 0
    for _ in range(15):
        sx, sy = wrist_direction("the box")
        if sx == 0 and sy == 0:
            stable += 1
            if stable >= 2:
                break
        else:
            stable = 0
            dx = sx * 0.015
            dy = sy * 0.015
            if dx != 0 or dy != 0:
                move_by(dx, dy, 0)


# Pick up the chocolate pudding.
held = False

for attempt in range(4):
    raise_to_start()
    align_pudding()
    descend_until_block()
    move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        held = True
        break

    open_gripper()

if not held:
    # One final attempt without the small upward move before closing.
    raise_to_start()
    align_pudding()
    descend_until_block()
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
    else:
        open_gripper()

if held:
    raise_to_start()


def align_tray():
    zero_count = 0

    # Coarse approach with the fixed camera.
    for i in range(20):
        fx, fy = fixed_direction("the center of the tray")

        if fx != 0 or fy != 0:
            step = 0.03 if i < 10 else 0.015
            move_by(fx * step, fy * step, 0)
            zero_count = 0
        else:
            wx, wy = wrist_direction("the center of the tray")
            if wy != 0:
                move_by(0, wy * 0.015, 0)
                zero_count = 0
            else:
                zero_count += 1
                if zero_count >= 2:
                    break

    # Fine y alignment with the wrist camera. Ignore wrist x answers while holding.
    stable = 0
    for _ in range(12):
        wx, wy = wrist_direction("the center of the tray")
        if wy == 0:
            stable += 1
            if stable >= 2:
                break
        else:
            stable = 0
            move_by(0, wy * 0.015, 0)

    # Final small correction from the fixed camera.
    for _ in range(5):
        fx, fy = fixed_direction("the center of the tray")
        if fx != 0 or fy != 0:
            move_by(fx * 0.015, fy * 0.015, 0)
        else:
            break


if held:
    raise_to_start()
    align_tray()

    # Lower until blocked, back up 3 cm, then release.
    descend_until_block()
    move_by(0, 0, 0.03)
    open_gripper()
    raise_to_start()
