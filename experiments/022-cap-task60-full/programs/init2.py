start = gripper_position()
z0 = start[2]
open_gripper()

def move_signs(sx, sy, step):
    if sx == 0 and sy == 0:
        return False
    move_by(sx * step, sy * step, 0)
    return True

# Align to tray
for _ in range(8):
    sx, sy = fixed_direction("the center of the tray")
    if not move_signs(sx, sy, 0.02):
        break
for _ in range(8):
    sx, sy = wrist_direction("the center of the tray")
    if not move_signs(sx, sy, 0.02):
        break
for _ in range(4):
    fx, fy = fixed_direction("the center of the tray")
    wx, wy = wrist_direction("the center of the tray")
    sx = wx if wx != 0 else fx
    sy = wy if wy != 0 else fy
    if not move_signs(sx, sy, 0.01):
        break

tray_pos = gripper_position()
tx, ty = tray_pos[0], tray_pos[1]

# Align to bowl
for _ in range(12):
    sx, sy = fixed_direction("the center of the bowl to pick up")
    if not move_signs(sx, sy, 0.02):
        break
for _ in range(8):
    sx, sy = wrist_direction("the center of the bowl to pick up")
    if not move_signs(sx, sy, 0.02):
        break
for _ in range(4):
    fx, fy = fixed_direction("the center of the bowl to pick up")
    wx, wy = wrist_direction("the center of the bowl to pick up")
    sx = fx if fx != 0 else wx
    sy = wy if wy != 0 else fy
    if not move_signs(sx, sy, 0.01):
        break

bowl_pos = gripper_position()
bcx, bcy = bowl_pos[0], bowl_pos[1]

# Grasp attempts
offsets = [(0.0, 0.0), (0.02, 0.0), (-0.02, 0.0)]
for idx, (dx, dy) in enumerate(offsets):
    if idx == 0:
        target_x = bcx + dx
        target_y = bcy - 0.06 + dy
        move_by(target_x - bcx, target_y - bcy, 0)
    else:
        open_gripper()
        cur = gripper_position()
        move_to(cur[0], cur[1], z0)
        target_x = bcx + dx
        target_y = bcy - 0.06 + dy
        move_to(target_x, target_y, z0)
    
    for _ in range(15):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        break

# Lift to start height
cur = gripper_position()
move_to(cur[0], cur[1], z0)

# Move to tray placement position
target_x = tx
target_y = ty - 0.04
move_to(target_x, target_y, z0)

# Lower into tray
for _ in range(15):
    if not move_by(0, 0, -0.03):
        break
move_by(0, 0, 0.03)
open_gripper()

# Lift up
cur = gripper_position()
move_to(cur[0], cur[1], z0)
