_motion_count = 0

def mby(dx, dy, dz):
    global _motion_count
    if _motion_count >= 105:
        return False
    _motion_count += 1
    return move_by(dx, dy, dz)

def mto(x, y, z):
    global _motion_count
    if _motion_count >= 105:
        return False
    _motion_count += 1
    return move_to(x, y, z)

def attempt_grasp(tx, ty, start_z):
    if _motion_count >= 105:
        return False

    mto(tx, ty, start_z)

    for _ in range(9):
        if not mby(0, 0, -0.03):
            break

    mby(0, 0, 0.015)
    close_gripper()

    if gripper_opening() > 0.003:
        return True

    open_gripper()
    p = gripper_position()
    dz = start_z - p[2]
    if dz > 0.001:
        mby(0, 0, dz)

    return False


start_pos = gripper_position()
start_x, start_y, start_z = start_pos

# Move roughly toward the pudding using the fixed camera.
for _ in range(12):
    sx, sy = fixed_direction("the chocolate pudding box")
    if sx == 0 and sy == 0:
        break
    mby(sx * 0.04, sy * 0.04, 0)

# Finish horizontal alignment at start height with the wrist camera.
for _ in range(15):
    sx, sy = wrist_direction("the box")
    if sx == 0 and sy == 0:
        break
    mby(sx * 0.015, sy * 0.015, 0)

base_x, base_y, _ = gripper_position()

held = False
offsets = [
    (0.0, 0.0),
    (0.025, 0.0),
    (-0.025, 0.0),
    (0.0, 0.02),
    (0.0, -0.02),
]

for dx, dy in offsets:
    if attempt_grasp(base_x + dx, base_y + dy, start_z):
        held = True
        break

if not held:
    # Recovery attempt if the first approach missed.
    for _ in range(8):
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        mby(sx * 0.03, sy * 0.03, 0)

    for _ in range(10):
        sx, sy = wrist_direction("the box")
        if sx == 0 and sy == 0:
            break
        mby(sx * 0.015, sy * 0.015, 0)

    base_x, base_y, _ = gripper_position()

    for dx, dy in [
        (0.0, 0.0),
        (0.03, 0.0),
        (-0.03, 0.0),
        (0.0, 0.03),
        (0.0, -0.03),
    ]:
        if attempt_grasp(base_x + dx, base_y + dy, start_z):
            held = True
            break

if held:
    # Lift to carrying height.
    p = gripper_position()
    dz = start_z - p[2]
    if dz > 0.001:
        mby(0, 0, dz)

    # Move above the tray.
    for _ in range(12):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        mby(sx * 0.04, sy * 0.04, 0)

    # Refine only in y; x answers are unreliable while holding the pudding.
    for _ in range(5):
        sx, sy = wrist_direction("the center of the tray")
        if sy == 0:
            break
        mby(0, sy * 0.015, 0)

    # Lower into the tray until blocked.
    for _ in range(10):
        if not mby(0, 0, -0.03):
            break

    # Back off before opening so the tray is not lifted.
    mby(0, 0, 0.03)
    open_gripper()

    # Lift away.
    p = gripper_position()
    dz = start_z - p[2]
    if dz > 0.001:
        mby(0, 0, dz)
