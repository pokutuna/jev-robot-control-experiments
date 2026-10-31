motion_calls = 0
vision_calls = 0

def m_by(dx, dy, dz):
    global motion_calls
    if motion_calls >= 115:
        return False
    motion_calls += 1
    return move_by(dx, dy, dz)

def m_to(x, y, z):
    global motion_calls
    if motion_calls >= 115:
        return False
    motion_calls += 1
    return move_to(x, y, z)

def w_dir(target):
    global vision_calls
    if vision_calls >= 350:
        return (0, 0)
    vision_calls += 1
    return wrist_direction(target)

def f_dir(target):
    global vision_calls
    if vision_calls >= 350:
        return (0, 0)
    vision_calls += 1
    return fixed_direction(target)

def in_w(target):
    global vision_calls
    if vision_calls >= 350:
        return 0.0
    vision_calls += 1
    return in_wrist_view(target)

start_x, start_y, start_z = gripper_position()

# Estimate tray center.
for _ in range(20):
    sx, sy = f_dir("the center of the tray")
    if sx == 0 and sy == 0:
        if in_w("the center of the tray") < 0.15:
            tx, ty = f_dir("the tray")
            if tx != 0 or ty != 0:
                m_by(tx * 0.025, ty * 0.025, 0)
                continue
        break
    m_by(sx * 0.025, sy * 0.025, 0)

for _ in range(10):
    sx, sy = w_dir("the center of the tray")
    if sx == 0 and sy == 0:
        sx2, sy2 = w_dir("the center of the tray")
        if sx2 == 0 and sy2 == 0:
            break
        sx, sy = sx2, sy2
    m_by(sx * 0.02, sy * 0.02, 0)

tray_x, tray_y, _ = gripper_position()

# Approach the black bowl on the left.
for _ in range(25):
    if in_w("the center of the bowl to pick up") > 0.15:
        break
    sx, sy = f_dir("the center of the bowl to pick up")
    if sx == 0 and sy == 0:
        tx, ty = f_dir("the black bowl on the left")
        if tx == 0 and ty == 0:
            break
        sx, sy = tx, ty
    m_by(sx * 0.025, sy * 0.025, 0)

for _ in range(12):
    sx, sy = w_dir("the center of the bowl to pick up")
    if sx == 0 and sy == 0:
        sx2, sy2 = w_dir("the center of the bowl to pick up")
        if sx2 == 0 and sy2 == 0:
            break
        sx, sy = sx2, sy2
    m_by(sx * 0.02, sy * 0.02, 0)

bowl_x, bowl_y, _ = gripper_position()

# Grasp the bowl by its rim.
held = False
for dx in [0.0, 0.04, -0.04]:
    gx = bowl_x + dx
    gy = bowl_y - 0.06

    open_gripper()
    m_to(gx, gy, start_z)

    for _ in range(10):
        if not m_by(0, 0, -0.03):
            break

    m_by(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        held = True
        px, py, pz = gripper_position()
        m_to(px, py, start_z)
        break
    else:
        open_gripper()
        px, py, pz = gripper_position()
        m_to(px, py, start_z)

# Place the bowl in the tray.
if held:
    target_x = tray_x
    target_y = tray_y - 0.06

    m_to(target_x, target_y, start_z)

    for _ in range(10):
        if not m_by(0, 0, -0.03):
            break

    m_by(0, 0, 0.03)
    open_gripper()

    px, py, pz = gripper_position()
    m_to(px, py, start_z)
