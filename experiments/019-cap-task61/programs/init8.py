start_x, start_y, start_z = gripper_position()
open_gripper()

def move_signs(d, step):
    if d[0] == 0 and d[1] == 0:
        return False
    return move_by(d[0] * step, d[1] * step, 0)

def lift_to_start():
    x, y, z = gripper_position()
    if z < start_z - 0.001:
        move_to(x, y, start_z)

def lower_until_block(max_steps=10):
    for _ in range(max_steps):
        if not move_by(0, 0, -0.03):
            return True
    return False

# Roughly approach the chocolate pudding.
for _ in range(12):
    vis = max(in_wrist_view("the chocolate pudding box"), in_wrist_view("the box"))
    if vis > 0.35:
        break
    d = fixed_direction("the chocolate pudding box")
    if d == (0, 0):
        d = fixed_direction("the box")
    if d != (0, 0):
        move_signs(d, 0.03)
    else:
        w = wrist_direction("the chocolate pudding box")
        if w == (0, 0):
            w = wrist_direction("the box")
        if w != (0, 0):
            move_signs(w, 0.02)
        else:
            break

# Fine alignment in the wrist view.
for _ in range(8):
    d = wrist_direction("the chocolate pudding box")
    if d == (0, 0):
        d = wrist_direction("the box")
    if d == (0, 0):
        break
    move_signs(d, 0.02)

base_x, base_y, _ = gripper_position()

# Try to grasp the pudding from a few small y offsets.
offsets = [(0.0, 0.0), (0.0, 0.02), (0.0, -0.02)]
success = False
for dx, dy in offsets:
    move_to(base_x + dx, base_y + dy, start_z)
    lower_until_block(10)
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        success = True
        lift_to_start()
        break
    else:
        open_gripper()
        lift_to_start()

# Move above the tray.
tray_phrase = "the center of the tray"
last_d = (0, 0)
for _ in range(12):
    d = fixed_direction(tray_phrase)
    if d == (0, 0):
        d = fixed_direction("the tray")
    if d != (0, 0):
        last_d = d
        move_signs(d, 0.04)
    else:
        if last_d != (0, 0):
            move_signs(last_d, 0.03)
            last_d = (0, 0)
        break

# Refine over the tray if it is visible in the wrist camera.
for _ in range(4):
    if in_wrist_view(tray_phrase) < 0.15:
        break
    d = wrist_direction(tray_phrase)
    if d == (0, 0):
        break
    move_signs(d, 0.02)

# Lower and release the pudding.
lower_until_block(10)
open_gripper()
move_by(0, 0, 0.10)
