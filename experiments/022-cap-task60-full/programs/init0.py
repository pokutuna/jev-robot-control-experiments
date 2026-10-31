STEP = 0.02
DESC_STEP = 0.03
START_Z = gripper_position()[2]

def align_to_target(wrist_target, fixed_target, max_iters=20):
    last_dx, last_dy = 0, 0
    zero_count = 0
    for _ in range(max_iters):
        vis = in_wrist_view(wrist_target)
        sx, sy = 0, 0
        if vis > 0.3:
            sx, sy = wrist_direction(wrist_target)
        if sx == 0 and sy == 0:
            sx, sy = fixed_direction(fixed_target)
        if sx == 0 and sy == 0:
            if vis > 0.5:
                zero_count += 1
                if zero_count >= 3:
                    break
            else:
                if last_dx != 0 or last_dy != 0:
                    sx, sy = last_dx, last_dy
                else:
                    sx, sy = 1, 0
        else:
            zero_count = 0
        if sx != 0 or sy != 0:
            move_by(sx * STEP, sy * STEP, 0)
            last_dx, last_dy = sx, sy

# Find tray center and record its coordinates
align_to_target("the center of the tray", "the center of the tray", 20)
tray_x, tray_y, _ = gripper_position()

# Find the black bowl and align to its center
align_to_target("the center of the bowl to pick up", "the black bowl on the left", 20)
cx, cy, _ = gripper_position()

# Move to the rim grasp point (6 cm in -y from the bowl center)
move_by(0, -0.06, 0)
rim_x, rim_y, _ = gripper_position()

# Attempt to grasp the bowl rim
attempts = [(0,0), (0.02,0), (-0.02,0), (0,0.02), (0,-0.02)]
grasped = False
current_x, current_y = rim_x, rim_y

for dx, dy in attempts:
    target_x = rim_x + dx
    target_y = rim_y + dy
    move_to(target_x, target_y, START_Z)
    # Descend until blocked
    while True:
        if not move_by(0, 0, -DESC_STEP):
            break
    move_by(0, 0, 0.015)  # move up 1.5 cm
    close_gripper()
    if gripper_opening() > 0.003:
        grasped = True
        current_x, current_y = target_x, target_y
        break
    else:
        open_gripper()
        move_to(target_x, target_y, START_Z)

if grasped:
    # Lift to start height
    move_to(current_x, current_y, START_Z)
    # Move over the tray at start height
    move_to(tray_x, tray_y, START_Z)
    # Descend into the tray until blocked
    while True:
        if not move_by(0, 0, -DESC_STEP):
            break
    # Release the bowl
    open_gripper()
    # Lift back to start height
    move_to(tray_x, tray_y, START_Z)
