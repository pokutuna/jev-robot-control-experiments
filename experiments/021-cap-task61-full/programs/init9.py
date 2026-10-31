gx, gy, gz = gripper_position()
start_z = gz

def align_fixed(target, max_steps=12):
    for _ in range(max_steps):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            return True
        move_by(sx * 0.02, sy * 0.02, 0)
    return False

def align_wrist(target, max_steps=8):
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            return True
        move_by(sx * 0.02, sy * 0.02, 0)
    return False

def descend_until_blocked(max_steps=15):
    for _ in range(max_steps):
        if not move_by(0, 0, -0.03):
            return
    return

# Locate the tray
align_fixed("the center of the tray", 12)
align_wrist("the center of the tray", 8)

if check("Is the gripper above the tray?") < 0.5:
    for _ in range(6):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            sx, sy = wrist_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

tray_x, tray_y, _ = gripper_position()

# Go to the pudding box
align_fixed("the chocolate pudding box", 15)
align_wrist("the chocolate pudding box", 8)

aligned_x, aligned_y, _ = gripper_position()

# Try to grasp the pudding box
held = False
offsets = [(0, 0), (0.03, 0), (-0.03, 0)]
for dx, dy in offsets:
    move_to(aligned_x + dx, aligned_y + dy, start_z)
    descend_until_blocked()
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        break
    else:
        open_gripper()
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)

# Place the pudding box in the tray
if held:
    gx, gy, gz = gripper_position()
    move_to(gx, gy, start_z)
    move_to(tray_x, tray_y, start_z)
    for _ in range(4):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    descend_until_blocked()
    move_by(0, 0, 0.03)
    open_gripper()
    move_by(0, 0, 0.10)
