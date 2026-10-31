motion_count = 0

def mby(dx, dy, dz):
    global motion_count
    if motion_count >= 115:
        return False
    motion_count += 1
    return move_by(dx, dy, dz)

def mto(x, y, z):
    global motion_count
    if motion_count >= 115:
        return False
    motion_count += 1
    return move_to(x, y, z)

def close_g():
    global motion_count
    if motion_count >= 115:
        return
    motion_count += 1
    close_gripper()

def open_g():
    global motion_count
    if motion_count >= 115:
        return
    motion_count += 1
    open_gripper()

x0, y0, z0 = gripper_position()
start_z = z0

# Find the bowl if not already visible in the wrist camera
if in_wrist_view("the black bowl on the left") <= 0.4:
    for _ in range(15):
        mby(0, 0.02, 0)
        if in_wrist_view("the black bowl on the left") > 0.4:
            break

# Align above the center of the bowl
for _ in range(10):
    sx, sy = wrist_direction("the center of the bowl to pick up")
    if sx == 0 and sy == 0:
        sx2, sy2 = wrist_direction("the center of the bowl to pick up")
        if sx2 == 0 and sy2 == 0:
            break
        sx, sy = sx2, sy2
    mby(sx * 0.02, sy * 0.02, 0)

# Move to the -y rim (left edge in the wrist image)
for _ in range(8):
    sx, sy = wrist_direction("the left edge of the bowl to pick up")
    if sy == 0:
        break
    mby(0, sy * 0.02, 0)

# Refine x alignment at the rim
for _ in range(5):
    sx, sy = wrist_direction("the center of the bowl to pick up")
    if sx == 0:
        break
    mby(sx * 0.02, 0, 0)

def descend_and_close():
    for _ in range(10):
        if not mby(0, 0, -0.03):
            break
    mby(0, 0, 0.015)
    close_g()
    return gripper_opening() > 0.003

held = descend_and_close()

# Quick retries with small y adjustments if the grasp missed
if not held:
    open_g()
    mby(0, 0, 0.08)
    mby(0, -0.01, 0)
    held = descend_and_close()

if not held:
    open_g()
    mby(0, 0, 0.08)
    mby(0, 0.02, 0)
    held = descend_and_close()

# Lift to start height
cx, cy, cz = gripper_position()
mto(cx, cy, start_z)

# Move above the tray
for _ in range(15):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        sx2, sy2 = fixed_direction("the center of the tray")
        if sx2 == 0 and sy2 == 0:
            break
        sx, sy = sx2, sy2
    mby(sx * 0.02, sy * 0.02, 0)

# Offset for the bowl center being +6 cm in y from the gripper
mby(0, -0.06, 0)

# Lower until the bowl reaches the tray/table
for _ in range(10):
    if not mby(0, 0, -0.03):
        break

# Release and lift
open_g()
mby(0, 0, 0.10)
