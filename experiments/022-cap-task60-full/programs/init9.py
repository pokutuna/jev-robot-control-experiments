def align_bowl(max_steps=12):
    for _ in range(max_steps):
        wx, wy = wrist_direction("the center of the bowl to pick up")
        if wx == 0 or wy == 0:
            fx, fy = fixed_direction("the center of the bowl to pick up")
        else:
            fx, fy = 0, 0
        sx = wx if wx != 0 else fx
        sy = wy if wy != 0 else fy
        if sx == 0 and sy == 0:
            break
        move_by(0.02 * sx, 0.02 * sy, 0)
    for _ in range(2):
        wx, wy = wrist_direction("the center of the bowl to pick up")
        fx, fy = fixed_direction("the center of the bowl to pick up")
        if wx == 0 and fx != 0:
            move_by(0.02 * fx, 0, 0)
        else:
            break
    x, y, _ = gripper_position()
    return x, y


def align_tray(max_steps=15):
    for _ in range(max_steps):
        sx, sy = fixed_direction("the center of the tray")
        if sx != 0 or sy != 0:
            move_by(0.03 * sx, 0.03 * sy, 0)
            continue
        wx, wy = wrist_direction("the center of the tray")
        if wx != 0 or wy != 0:
            move_by(0.02 * wx, 0.02 * wy, 0)
        else:
            break
    x, y, _ = gripper_position()
    return x, y


start_x, start_y, start_z = gripper_position()

bowl_x, bowl_y = align_bowl()

tray_x, tray_y = align_tray()

move_to(bowl_x, bowl_y, start_z)

offsets = [0.0, 0.03, -0.03]
held = False

for dx in offsets:
    move_to(bowl_x + dx, bowl_y - 0.06, start_z)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        move_to(gripper_position()[0], gripper_position()[1], start_z)
        break
    else:
        open_gripper()
        move_to(gripper_position()[0], gripper_position()[1], start_z)

if not held:
    bx, by = align_bowl(max_steps=8)
    move_to(bx, by - 0.06, start_z)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        move_to(gripper_position()[0], gripper_position()[1], start_z)
    else:
        open_gripper()
        move_to(gripper_position()[0], gripper_position()[1], start_z)

if held:
    target_x = tray_x
    target_y = tray_y - 0.06
    move_to(target_x, target_y, start_z)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.03)
    open_gripper()
    move_to(gripper_position()[0], gripper_position()[1], start_z)
