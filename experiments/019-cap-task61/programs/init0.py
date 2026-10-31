_motion_count = 0

def mby(dx, dy, dz):
    global _motion_count
    if _motion_count >= 118:
        return False
    _motion_count += 1
    return move_by(dx, dy, dz)

def mto(x, y, z):
    global _motion_count
    if _motion_count >= 118:
        return False
    _motion_count += 1
    return move_to(x, y, z)

z0 = gripper_position()[2]

def lift_to_start():
    z = gripper_position()[2]
    if z < z0 - 1e-6:
        mby(0, 0, z0 - z)

def descend_until_block():
    for _ in range(12):
        if not mby(0, 0, -0.03):
            return

# Find and record the tray center at the start height.
for _ in range(35):
    p1 = in_wrist_view("the center of the tray")
    p2 = in_wrist_view("the tray")
    if p1 < 0.10 and p2 < 0.10:
        sx, sy = fixed_direction("the center of the tray")
        if sx != 0 or sy != 0:
            mby(sx * 0.025, sy * 0.025, 0)
            continue
    if p1 >= p2 and p1 >= 0.05:
        sx, sy = wrist_direction("the center of the tray")
    elif p2 >= 0.05:
        sx, sy = wrist_direction("the tray")
    else:
        sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    mby(sx * 0.015, sy * 0.015, 0)

tray_x, tray_y, _ = gripper_position()

# Move near and align with the chocolate pudding box.
for _ in range(40):
    p1 = in_wrist_view("the box")
    p2 = in_wrist_view("the chocolate pudding box")
    if p1 < 0.12 and p2 < 0.12:
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx != 0 or sy != 0:
            mby(sx * 0.025, sy * 0.025, 0)
            continue
    if p1 >= 0.10:
        sx, sy = wrist_direction("the box")
        if sx == 0:
            sx2, _ = wrist_direction("the chocolate pudding box")
            if sx2 != 0:
                sx = sx2
    else:
        sx, sy = wrist_direction("the chocolate pudding box")
    if sx == 0 and sy == 0:
        break
    mby(sx * 0.015, sy * 0.015, 0)

base_x, base_y, _ = gripper_position()

def try_grasp(off_x, off_y):
    cx, cy, cz = gripper_position()
    if abs(cz - z0) > 1e-6:
        mby(0, 0, z0 - cz)
    mto(base_x + off_x, base_y + off_y, z0)
    open_gripper()
    descend_until_block()
    mby(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        lift_to_start()
        return True
    else:
        open_gripper()
        lift_to_start()
        return False

held = False

for off_x in [0.0, 0.03, -0.03]:
    if try_grasp(off_x, 0.0):
        held = True
        break

if not held:
    for off_y in [0.01, -0.02, 0.02]:
        if try_grasp(0.0, off_y):
            held = True
            break

if held:
    cx, cy, cz = gripper_position()
    if abs(cz - z0) > 1e-6:
        mby(0, 0, z0 - cz)
    mto(tray_x, tray_y, z0)
    descend_until_block()
    open_gripper()
    lift_to_start()
