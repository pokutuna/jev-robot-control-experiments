start_x, start_y, start_z = gripper_position()
motion_count = 0
MAX_MOTION = 115

def safe_move_by(dx, dy, dz):
    global motion_count
    if motion_count >= MAX_MOTION:
        return False
    motion_count += 1
    return move_by(dx, dy, dz)

def safe_move_to(x, y, z):
    global motion_count
    if motion_count >= MAX_MOTION:
        return False
    motion_count += 1
    return move_to(x, y, z)

def align_wrist(target, max_steps, step, use_x, use_y, patience=2):
    zero_count = 0
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if not use_x:
            sx = 0
        if not use_y:
            sy = 0
        if sx == 0 and sy == 0:
            zero_count += 1
            if zero_count >= patience:
                break
        else:
            zero_count = 0
            safe_move_by(sx * step, sy * step, 0)

def go_down(max_steps, step=0.03):
    for _ in range(max_steps):
        if not safe_move_by(0, 0, -step):
            return True
    return False

for i in range(30):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    safe_move_by(sx * 0.02, sy * 0.02, 0)

if in_wrist_view("the center of the tray") > 0.5:
    align_wrist("the center of the tray", max_steps=10, step=0.02, use_x=True, use_y=True, patience=2)

tray_x, tray_y, _ = gripper_position()

grasped = False
for attempt in range(3):
    if attempt == 0:
        for i in range(25):
            if in_wrist_view("the center of the bowl to pick up") > 0.6:
                break
            sx, sy = fixed_direction("the black bowl on the left")
            if sy == 0:
                sy = 1
            if sx == 0 and sy == 0:
                sy = 1
            safe_move_by(sx * 0.02, sy * 0.02, 0)
    else:
        safe_move_by(0, 0, 0.05)
        if attempt == 2:
            safe_move_by(0.02, 0, 0)

    align_wrist("the center of the bowl to pick up", max_steps=20, step=0.02, use_x=True, use_y=True, patience=2)
    align_wrist("the left edge of the bowl to pick up", max_steps=12, step=0.02, use_x=False, use_y=True, patience=2)

    go_down(max_steps=20, step=0.03)
    safe_move_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        grasped = True
        break
    else:
        open_gripper()

if not grasped:
    open_gripper()
    safe_move_by(0, 0, 0.08)
    align_wrist("the center of the bowl to pick up", max_steps=15, step=0.02, use_x=True, use_y=True, patience=2)
    safe_move_by(0.02, 0, 0)
    align_wrist("the left edge of the bowl to pick up", max_steps=10, step=0.02, use_x=False, use_y=True, patience=2)
    go_down(max_steps=20, step=0.03)
    safe_move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        grasped = True
    else:
        open_gripper()

x, y, z = gripper_position()
safe_move_to(x, y, start_z)

safe_move_to(tray_x, tray_y - 0.06, start_z)

go_down(max_steps=25, step=0.03)
open_gripper()
safe_move_by(0, 0, 0.08)

x, y, z = gripper_position()
if z < start_z:
    safe_move_to(x, y, start_z)
