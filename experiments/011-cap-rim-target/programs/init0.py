start_z = gripper_position()[2]
open_gripper()

# Pick the bowl
for attempt in range(2):
    cx, cy, cz = gripper_position()
    if abs(cz - start_z) > 0.01:
        move_to(cx, cy, start_z)
    open_gripper()
    
    # Make sure the bowl is in view
    for _ in range(8):
        if in_wrist_view("the black bowl on the left") > 0.3:
            break
        move_by(0, 0.03, 0)
    
    # Align to bowl center
    for _ in range(12):
        sx, sy = wrist_direction("the center of the bowl to pick up")
        if sx == 0 and sy == 0:
            break
        move_by(0.02 * sx, 0.02 * sy, 0)
    
    # Align to the -y rim (left edge in wrist image)
    for _ in range(10):
        sx, sy = wrist_direction("the left edge of the bowl to pick up")
        if sy == 0:
            break
        move_by(0, 0.02 * sy, 0)
    
    # Descend until blocked
    for _ in range(12):
        if not move_by(0, 0, -0.03):
            break
    
    # Move up 1.5 cm before closing
    move_by(0, 0, 0.015)
    
    # Close and check
    close_gripper()
    if gripper_opening() > 0.003:
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)
        break
    else:
        open_gripper()
        gx, gy, gz = gripper_position()
        move_to(gx, gy, start_z)

# Move to the tray and place
last_sx = 0
last_sy = 0
above_count = 0

for _ in range(30):
    p = check("Is the black bowl above the tray?")
    if p > 0.5:
        above_count += 1
        if above_count >= 2:
            break
    else:
        above_count = 0
        
    sx, sy = fixed_direction("the center of the tray")
    if sx != 0 or sy != 0:
        last_sx, last_sy = sx, sy
        move_by(0.02 * sx, 0.02 * sy, 0)
    else:
        if last_sx == 0 and last_sy == 0:
            wx, wy = wrist_direction("the center of the tray")
            if wx != 0 or wy != 0:
                last_sx, last_sy = wx, wy
                move_by(0.02 * wx, 0.02 * wy, 0)
            else:
                move_by(0.02, 0, 0)
        else:
            move_by(0.02 * last_sx, 0.02 * last_sy, 0)

# Center on the tray using the wrist camera
for _ in range(10):
    wx, wy = wrist_direction("the center of the tray")
    if wx == 0 and wy == 0:
        break
    move_by(0.02 * wx, 0.02 * wy, 0)

# Adjust for the bowl center offset (+6 cm in y from the gripper)
p_center = check("Is the black bowl above the tray?")
move_by(0, -0.06, 0)
p_offset = check("Is the black bowl above the tray?")
if p_offset < p_center and p_center > 0.5:
    move_by(0, 0.06, 0)

# Lower the bowl into the tray
for _ in range(12):
    if not move_by(0, 0, -0.03):
        break

# Release the bowl
open_gripper()

# Lift to start height
gx, gy, gz = gripper_position()
move_to(gx, gy, start_z)
