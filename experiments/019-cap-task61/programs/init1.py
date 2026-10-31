_orig_move_by = move_by
_orig_move_to = move_to
_orig_close = close_gripper
_orig_open = open_gripper

motion_calls = 0

def move_by(dx, dy, dz):
    global motion_calls
    if motion_calls >= 120:
        return False
    motion_calls += 1
    return _orig_move_by(dx, dy, dz)

def move_to(x, y, z):
    global motion_calls
    if motion_calls >= 120:
        return False
    motion_calls += 1
    return _orig_move_to(x, y, z)

def close_gripper():
    global motion_calls
    if motion_calls >= 120:
        return
    motion_calls += 1
    _orig_close()

def open_gripper():
    global motion_calls
    if motion_calls >= 120:
        return
    motion_calls += 1
    _orig_open()

start_x, start_y, start_z = gripper_position()

def up_to_start():
    x, y, z = gripper_position()
    if abs(z - start_z) > 0.001:
        move_to(x, y, start_z)

def align_pudding():
    for i in range(12):
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    for i in range(6):
        sx, sy = wrist_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    up_to_start()

def grasp_pudding():
    for i in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    opening = gripper_opening()
    if opening > 0.003:
        x, y, z = gripper_position()
        move_to(x, y, start_z)
        return True
    else:
        open_gripper()
        x, y, z = gripper_position()
        move_to(x, y, start_z)
        return False

held = False
for attempt in range(2):
    up_to_start()
    align_pudding()
    if grasp_pudding():
        held = True
        break

if not held and motion_calls < 100:
    up_to_start()
    align_pudding()
    if grasp_pudding():
        held = True

if not held and motion_calls < 110:
    up_to_start()
    align_pudding()
    move_by(0, 0.01, 0)
    if grasp_pudding():
        held = True

up_to_start()

last_dir = None
for i in range(20):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        if last_dir is not None:
            for _ in range(4):
                move_by(last_dir[0] * 0.02, last_dir[1] * 0.02, 0)
        break
    last_dir = (sx, sy)
    move_by(sx * 0.02, sy * 0.02, 0)

if in_wrist_view("the center of the tray") > 0.3:
    for i in range(5):
        sx, sy = wrist_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

move_by(0, 0, -0.10)
open_gripper()
move_to(gripper_position()[0], gripper_position()[1], start_z)
