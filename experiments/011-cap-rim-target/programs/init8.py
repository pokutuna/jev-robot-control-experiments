start_x, start_y, start_z = gripper_position()

def align_wrist(target, max_steps=8, step=0.02, use_x=True, use_y=True):
    last_sx = 0
    last_sy = 0
    flip_x = False
    flip_y = False
    for i in range(max_steps):
        sx, sy = wrist_direction(target)
        if not use_x:
            sx = 0
        if not use_y:
            sy = 0
        if sx == 0 and sy == 0:
            break
        if sx != 0 and last_sx != 0 and sx != last_sx:
            flip_x = True
        if sy != 0 and last_sy != 0 and sy != last_sy:
            flip_y = True
        dx = 0 if flip_x or sx == 0 else sx * step
        dy = 0 if flip_y or sy == 0 else sy * step
        if dx == 0 and dy == 0:
            break
        move_by(dx, dy, 0)
        if sx != 0:
            last_sx = sx
        if sy != 0:
            last_sy = sy
    return last_sx, last_sy

# Bring the bowl into the wrist camera view
for i in range(15):
    if in_wrist_view("the black bowl on the left") > 0.5:
        break
    sx, sy = fixed_direction("the black bowl on the left")
    if sx == 0 and sy == 0:
        move_by(0, 0.03, 0)
    else:
        move_by(sx * 0.03, sy * 0.03, 0)

# Align to the bowl center to get x aligned and bowl centered
align_wrist("the center of the bowl to pick up", max_steps=8, step=0.02, use_x=True, use_y=True)

# Align to the left rim of the bowl (the -y side) in y
align_wrist("the left edge of the bowl to pick up", max_steps=8, step=0.02, use_x=False, use_y=True)

# Attempt to grasp the rim
success = False
for attempt in range(2):
    if attempt == 1:
        move_by(0, 0.02, 0)
    # Descend until blocked
    for i in range(10):
        if not move_by(0, 0, -0.03):
            break
    # Move up a small amount before closing
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        success = True
        break
    else:
        open_gripper()
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)

# Lift the bowl to start height
gx, gy, gz = gripper_position()
move_to(gx, gy, start_z)

# Move toward the tray using the fixed camera
for i in range(25):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

# Fine align to the tray center using the wrist camera
last_sx = 0
last_sy = 0
flip_x = False
flip_y = False
for i in range(10):
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    if sx != 0 and last_sx != 0 and sx != last_sx:
        flip_x = True
    if sy != 0 and last_sy != 0 and sy != last_sy:
        flip_y = True
    dx = 0 if flip_x or sx == 0 else sx * 0.02
    dy = 0 if flip_y or sy == 0 else sy * 0.02
    if dx == 0 and dy == 0:
        break
    move_by(dx, dy, 0)
    if sx != 0:
        last_sx = sx
    if sy != 0:
        last_sy = sy

# Offset for the bowl center: while held by the -y rim,
# the bowl center is about +6 cm in y from the gripper
move_by(0, -0.06, 0)

# Lower until the bowl reaches the tray/table
for i in range(15):
    if not move_by(0, 0, -0.03):
        break

# Release and lift
open_gripper()
gx, gy, gz = gripper_position()
move_to(gx, gy, start_z)
