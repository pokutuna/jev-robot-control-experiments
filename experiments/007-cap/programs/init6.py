start_pos = gripper_position()
start_x, start_y, start_z = start_pos[0], start_pos[1], start_pos[2]

bowl_target = "the black bowl on the left"
tray_target = "the center of the tray"

def align_to_target_wrist(target, max_steps=12, step=0.02):
    stable = 0
    for _ in range(max_steps):
        if in_wrist_view(target) < 0.25:
            return False
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            stable += 1
            if stable >= 2:
                return True
        else:
            stable = 0
            move_by(sx * step, sy * step, 0)
    return False

def acquire_bowl():
    target = "the black bowl on the left"
    x0, y0, z0 = gripper_position()
    for _ in range(2):
        if in_wrist_view(target) > 0.3:
            if align_to_target_wrist(target):
                return True
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            sx, sy = 0, 1
        move_by(sx * 0.03, sy * 0.03, 0)
    for i in range(1, 5):
        move_to(x0, y0 + 0.05 * i, z0)
        if in_wrist_view(target) > 0.3:
            if align_to_target_wrist(target):
                return True
    cx, cy = x0, y0 + 0.1
    for dx in [-0.14, -0.07, 0, 0.07, 0.14]:
        for dy in [-0.07, 0, 0.07, 0.14, 0.21]:
            move_to(cx + dx, cy + dy, z0)
            if in_wrist_view(target) > 0.3:
                if align_to_target_wrist(target):
                    return True
    for i in range(1, 4):
        move_to(x0, y0 - 0.05 * i, z0)
        if in_wrist_view(target) > 0.3:
            if align_to_target_wrist(target):
                return True
    return False

acquire_bowl()
move_by(0, 0.06, 0)

grasped = False
for attempt in range(2):
    open_gripper()
    for i in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        grasped = True
        break
    else:
        open_gripper()
        cur = gripper_position()
        move_by(0, 0, start_z - cur[2])
        if in_wrist_view(bowl_target) > 0.25:
            align_to_target_wrist(bowl_target)
        else:
            acquire_bowl()
        move_by(0, 0.06, 0)

cur = gripper_position()
if cur[2] < start_z - 1e-4:
    move_by(0, 0, start_z - cur[2])

for i in range(20):
    sx, sy = fixed_direction(tray_target)
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.04, sy * 0.04, 0)

move_by(0, 0.06, 0)

for i in range(8):
    if not move_by(0, 0, -0.03):
        break

open_gripper()
cur = gripper_position()
move_by(0, 0, start_z - cur[2])
