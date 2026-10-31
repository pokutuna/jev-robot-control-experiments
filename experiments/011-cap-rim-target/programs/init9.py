def align_xy(target, max_steps, step=0.02):
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            break
        move_by(sx * step, sy * step, 0)

def align_y(target, max_steps, step=0.02):
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sy == 0:
            break
        move_by(0, sy * step, 0)

def align_x(target, max_steps, step=0.02):
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0:
            break
        move_by(sx * step, 0, 0)

start_z = gripper_position()[2]

# Search for the bowl on the left
target_bowl_view = "the bowl to pick up"
if in_wrist_view(target_bowl_view) < 0.5:
    for _ in range(8):
        if in_wrist_view(target_bowl_view) > 0.5:
            break
        move_by(0, 0.02, 0)

# Attempt to pick the bowl
for attempt in range(2):
    current_z = gripper_position()[2]
    if current_z < start_z - 0.02:
        move_by(0, 0, start_z - current_z)
    open_gripper()
    
    align_xy("the center of the bowl to pick up", 8)
    move_by(0, -0.06, 0)
    align_y("the left edge of the bowl to pick up", 5)
    align_x("the center of the bowl to pick up", 5)
    align_y("the left edge of the bowl to pick up", 3)
    
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    
    move_by(0, 0, 0.015)
    close_gripper()
    
    if gripper_opening() > 0.003:
        break
    else:
        move_by(0, 0, 0.10)
        current_z = gripper_position()[2]
        if current_z < start_z - 0.02:
            move_by(0, 0, start_z - current_z)

# Lift to start height
current_z = gripper_position()[2]
if current_z < start_z:
    move_by(0, 0, start_z - current_z)

# Move to tray
for _ in range(10):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.03, sy * 0.03, 0)

# Ensure tray is in wrist view
for _ in range(8):
    if in_wrist_view("the tray") > 0.5:
        break
    move_by(0, -0.02, 0)

# Refine alignment to tray center
align_xy("the center of the tray", 8)

# Offset to center the bowl over the tray
move_by(0, -0.06, 0)

# Lower to place
for _ in range(8):
    if not move_by(0, 0, -0.03):
        break

# Release the bowl
open_gripper()

# Move up to clear
move_by(0, 0, 0.15)
