start_z = gripper_position()[2]

# Attempt to pick the bowl
held = False
for attempt in range(3):
    open_gripper()
    x, y, z = gripper_position()
    if z < start_z - 0.005:
        move_to(x, y, start_z)
    
    # Align to the center of the bowl
    for i in range(25):
        sx, sy = wrist_direction("the center of the bowl to pick up")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    
    # Move towards the -y rim
    move_by(0, -0.05, 0)
    
    # Align to the rim (only y direction is reliable)
    for i in range(15):
        sx, sy = wrist_direction("the left edge of the bowl to pick up")
        if sy == 0:
            break
        move_by(0, sy * 0.02, 0)
    
    # Descend until blocked
    for i in range(15):
        if not move_by(0, 0, -0.03):
            break
    
    # Move up 1.5 cm before closing
    move_by(0, 0, 0.015)
    
    # Close gripper and check grasp
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        break
    
    # Missed: lift to start height for a retry
    x, y, z = gripper_position()
    if z < start_z:
        move_to(x, y, start_z)

# Lift to start height if held
if held:
    x, y, z = gripper_position()
    if z < start_z - 0.005:
        move_to(x, y, start_z)

# Move to the tray using fixed camera
last_sx, last_sy = 0, 0
for i in range(40):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    last_sx, last_sy = sx, sy
    move_by(sx * 0.02, sy * 0.02, 0)

# Move a bit closer in the last known direction
if last_sx != 0 or last_sy != 0:
    move_by(last_sx * 0.04, last_sy * 0.04, 0)

# Fine align to the tray center using wrist camera
for i in range(25):
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

# Shift -y by 6 cm so the bowl center is over the tray center
move_by(0, -0.06, 0)

# Lower into the tray until blocked
for i in range(15):
    if not move_by(0, 0, -0.03):
        break

# Release the bowl
open_gripper()

# Move up to start height
x, y, z = gripper_position()
if z < start_z:
    move_to(x, y, start_z)
