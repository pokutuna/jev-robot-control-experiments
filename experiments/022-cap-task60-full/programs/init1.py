start_x, start_y, start_z = gripper_position()

def align_fixed(target, max_iter, step=0.02):
    for _ in range(max_iter):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            break
        move_by(step * sx, step * sy, 0)

def align_wrist(target, max_iter, step=0.02):
    for _ in range(max_iter):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            break
        move_by(step * sx, step * sy, 0)

# Approach the bowl
align_fixed("the center of the bowl to pick up", 10)
align_wrist("the center of the bowl to pick up", 5)

cx, cy, _ = gripper_position()

held = False
dx_list = [0.0, -0.02, 0.02, -0.04, 0.04]

for dx in dx_list:
    open_gripper()
    move_to(cx + dx, cy - 0.06, start_z)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        break
    else:
        open_gripper()
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)

if held:
    gx, gy, gz = gripper_position()
    move_to(gx, gy, start_z)
    
    # Move above the tray
    align_fixed("the center of the tray", 10)
    # Compensate for the rim grasp offset and vision bias
    move_by(0.11, 0.02, 0)
    
    # Lower into the tray
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    # Move up before opening to avoid pressing on the tray
    move_by(0, 0, 0.03)
    open_gripper()
    gx, gy, gz = gripper_position()
    move_to(gx, gy, start_z)
