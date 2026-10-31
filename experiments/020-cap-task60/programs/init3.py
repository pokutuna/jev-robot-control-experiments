z_start = gripper_position()[2]

def get_dir(target):
    wx, wy = wrist_direction(target)
    fx, fy = fixed_direction(target)
    sx = wx if wx != 0 else fx
    sy = wy if wy != 0 else fy
    return sx, sy

def align(target, max_iter=20, step=0.02):
    zeros = 0
    for _ in range(max_iter):
        sx, sy = get_dir(target)
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            move_by(sx * step, sy * step, 0)
    return gripper_position()

align("the center of the tray", 20, 0.02)
align("the center of the tray", 8, 0.01)
tray_x, tray_y, _ = gripper_position()

held = False
for attempt in range(2):
    if attempt == 0:
        align("the center of the bowl to pick up", 22, 0.02)
        align("the center of the bowl to pick up", 8, 0.01)
    else:
        align("the center of the bowl to pick up", 12, 0.02)
        align("the center of the bowl to pick up", 4, 0.01)

    move_by(0, -0.06, 0)

    for _ in range(12):
        if not move_by(0, 0, -0.03):
            break

    move_by(0, 0, 0.015)
    close_gripper()
    held = gripper_opening() > 0.003

    if held:
        z = gripper_position()[2]
        move_by(0, 0, z_start - z)
        break
    else:
        open_gripper()
        z = gripper_position()[2]
        if z < z_start:
            move_by(0, 0, z_start - z)

if held:
    place_x = tray_x
    place_y = tray_y - 0.06
    move_to(place_x, place_y, z_start)

    for _ in range(12):
        if not move_by(0, 0, -0.03):
            break

    open_gripper()
    z = gripper_position()[2]
    move_by(0, 0, z_start - z)
