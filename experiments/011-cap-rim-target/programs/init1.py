start_z = gripper_position()[2]
motion_count = 0

def M(dx, dy, dz):
    global motion_count
    motion_count += 1
    if motion_count > 115:
        return False
    return move_by(dx, dy, dz)

def go_to_start_height():
    x, y, z = gripper_position()
    dz = start_z - z
    if abs(dz) > 0.001:
        M(0, 0, dz)

held = False
attempts = 0
while attempts < 2 and not held:
    attempts += 1
    open_gripper()
    go_to_start_height()
    
    # Get bowl in wrist view
    for i in range(15):
        if in_wrist_view("the black bowl") > 0.3:
            break
        sx, sy = fixed_direction("the black bowl on the left")
        if sx == 0 and sy == 0:
            sx, sy = 0, 1
        M(sx * 0.03, sy * 0.03, 0)
    
    # Align to center of bowl
    zeros = 0
    for i in range(15):
        sx, sy = wrist_direction("the center of the bowl to pick up")
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            M(sx * 0.02, sy * 0.02, 0)
    
    # Move to -y rim (6 cm right)
    M(0, -0.06, 0)
    
    # Fine tune y using rim target
    for i in range(3):
        sx, sy = wrist_direction("the left edge of the bowl to pick up")
        if sy == 0:
            break
        M(0, sy * 0.01, 0)
    
    # Go down until blocked
    while True:
        if not M(0, 0, -0.03):
            break
    
    # Move up 1.5 cm
    M(0, 0, 0.015)
    
    # Close gripper
    close_gripper()
    
    if gripper_opening() > 0.003:
        held = True
    else:
        open_gripper()
        M(0, 0, 0.05)

# Move up to start height before carrying
go_to_start_height()

# Navigate toward tray using fixed camera
zeros = 0
for i in range(15):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        zeros += 1
        if zeros >= 2:
            break
    else:
        zeros = 0
        M(sx * 0.03, sy * 0.03, 0)

# Try precise alignment with wrist camera if tray visible
if in_wrist_view("the center of the tray") > 0.3:
    zeros = 0
    for i in range(10):
        sx, sy = wrist_direction("the center of the tray")
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            M(sx * 0.02, sy * 0.02, 0)

# Shift to account for bowl center offset (+y 6 cm from gripper)
M(0, -0.06, 0)

# Lower to place
while True:
    if not M(0, 0, -0.03):
        break

# Open gripper to release bowl
open_gripper()

# Move up to clear
M(0, 0, 0.1)
