motion_count = 0
vision_count = 0

def move_by_lim(dx, dy, dz):
    global motion_count
    if motion_count >= 118:
        return False
    motion_count += 1
    return move_by(dx, dy, dz)

def move_to_lim(x, y, z):
    global motion_count
    if motion_count >= 118:
        return False
    motion_count += 1
    return move_to(x, y, z)

def wrist_dir(target):
    global vision_count
    if vision_count >= 358:
        return (0, 0)
    vision_count += 1
    return wrist_direction(target)

def fixed_dir(target):
    global vision_count
    if vision_count >= 358:
        return (0, 0)
    vision_count += 1
    return fixed_direction(target)

open_gripper()
start_z = gripper_position()[2]

target_pudding = "the chocolate pudding box"

for _ in range(22):
    sx, sy = fixed_dir(target_pudding)
    if sx == 0 and sy == 0:
        break
    move_by_lim(0.03 * sx, 0.03 * sy, 0)

for _ in range(14):
    sx, sy = wrist_dir(target_pudding)
    if sx == 0 and sy == 0:
        break
    move_by_lim(0.02 * sx, 0.02 * sy, 0)

held = False
for attempt in range(2):
    pos = gripper_position()
    if abs(pos[2] - start_z) > 0.001:
        move_to_lim(pos[0], pos[1], start_z)
    open_gripper()

    for _ in range(12):
        if not move_by_lim(0, 0, -0.03):
            break

    move_by_lim(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        held = True
        break

    open_gripper()
    pos = gripper_position()
    move_to_lim(pos[0], pos[1], start_z)

    if attempt == 0:
        sx, sy = fixed_dir(target_pudding)
        if sx != 0 or sy != 0:
            move_by_lim(0.02 * sx, 0.02 * sy, 0)
        sx, sy = wrist_dir(target_pudding)
        if sx != 0 or sy != 0:
            move_by_lim(0.02 * sx, 0.02 * sy, 0)

if held:
    pos = gripper_position()
    move_to_lim(pos[0], pos[1], start_z)

target_tray = "the center of the tray"

for _ in range(24):
    sx, sy = fixed_dir(target_tray)
    if sx == 0 and sy == 0:
        break
    move_by_lim(0.03 * sx, 0.03 * sy, 0)

for _ in range(8):
    sx, sy = wrist_dir(target_tray)
    if sy == 0:
        break
    move_by_lim(0, 0.02 * sy, 0)

pos = gripper_position()
if abs(pos[2] - start_z) > 0.002:
    move_to_lim(pos[0], pos[1], start_z)

for _ in range(12):
    if not move_by_lim(0, 0, -0.03):
        break

move_by_lim(0, 0, 0.03)
open_gripper()

pos = gripper_position()
move_to_lim(pos[0], pos[1], start_z)
open_gripper()
