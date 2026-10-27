start_z = gripper_position()[2]
target_bowl = "the black bowl on the left"
target_bowl_center = "the center of the black bowl on the left"
target_tray = "the center of the tray"


def lift_to_start():
    x, y, z = gripper_position()
    dz = start_z - z
    if abs(dz) > 0.001:
        move_by(0, 0, dz)


def align_wrist(target, max_steps=25, step=0.02):
    last = (0, 0)
    flips = 0
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            return True
        if (sx == -last[0] and sy == -last[1]) and (sx != 0 or sy != 0):
            flips += 1
        else:
            flips = 0
        last = (sx, sy)
        s = step
        if flips >= 2:
            s = 0.01
        move_by(sx * s, sy * s, 0)
    return False


def align_fixed(target, max_steps=25, step=0.02):
    last = (0, 0)
    flips = 0
    for _ in range(max_steps):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            return True
        if (sx == -last[0] and sy == -last[1]) and (sx != 0 or sy != 0):
            flips += 1
        else:
            flips = 0
        last = (sx, sy)
        s = step
        if flips >= 2:
            s = 0.01
        move_by(sx * s, sy * s, 0)
    return False


def ensure_bowl_visible():
    for _ in range(6):
        if in_wrist_view(target_bowl) > 0.35:
            return True
        sx, sy = fixed_direction(target_bowl)
        if sx == 0 and sy == 0:
            sx, sy = 0, 1
        move_by(sx * 0.02, sy * 0.02, 0)

    x0, y0, z0 = gripper_position()
    best_x, best_y = x0, y0
    best_p = in_wrist_view(target_bowl)
    offsets = [
        (0, 0.08),
        (0, 0.16),
        (0.08, 0.08),
        (-0.08, 0.08),
        (0.08, 0),
        (-0.08, 0),
        (0, -0.08),
    ]
    for dx, dy in offsets:
        move_to(x0 + dx, y0 + dy, z0)
        p = in_wrist_view(target_bowl)
        if p > best_p:
            best_p = p
            best_x, best_y = x0 + dx, y0 + dy
        if p > 0.45:
            return True
    move_to(best_x, best_y, z0)
    return best_p > 0.3


ensure_bowl_visible()
align_wrist(target_bowl_center, max_steps=25)

held = False
current_offset = 0.0
for attempt, target_offset in enumerate([0.06, 0.045, 0.075]):
    if attempt > 0:
        open_gripper()
        lift_to_start()

    dy = target_offset - current_offset
    if abs(dy) > 0.001:
        move_by(0, dy, 0)
    current_offset = target_offset

    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        held = True
        break

if held:
    lift_to_start()
else:
    open_gripper()
    lift_to_start()

align_fixed(target_tray, max_steps=25)

for _ in range(8):
    if in_wrist_view("the tray") < 0.3:
        break
    sx, sy = wrist_direction(target_tray)
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

move_by(0, 0.06, 0)

for _ in range(10):
    if not move_by(0, 0, -0.03):
        break

open_gripper()
lift_to_start()
