start_x, start_y, start_z = gripper_position()

def lift_to_start():
    x, y, z = gripper_position()
    if z < start_z - 0.001:
        move_by(0, 0, start_z - z)

# Search for the bowl if not initially visible
if in_wrist_view("the black bowl on the left") < 0.5:
    for i in range(20):
        move_by(0, 0.02, 0)
        if in_wrist_view("the black bowl on the left") > 0.5:
            break

held = False
offsets = [0.0, 0.015]
for oy in offsets:
    open_gripper()
    lift_to_start()
    # Align to bowl center
    for i in range(10):
        sx, sy = wrist_direction("the black bowl on the left")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    # Move to the rim (+y from center)
    move_by(0, 0.06 + oy, 0)
    # Go down until blocked
    while move_by(0, 0, -0.03):
        pass
    # Move up 1.5 cm
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        break
    else:
        open_gripper()
        lift_to_start()

if held:
    lift_to_start()

# Move to the tray
for i in range(15):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

# Fine align to tray center using wrist camera
stable = 0
for i in range(12):
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        stable += 1
        if stable >= 2:
            break
    else:
        stable = 0
        move_by(sx * 0.02, sy * 0.02, 0)

# Offset so the bowl center aligns with the tray center
move_by(0, 0.06, 0)

# Lower the bowl into the tray
while move_by(0, 0, -0.03):
    pass

# Release
open_gripper()

# Lift up
move_by(0, 0, 0.15)
