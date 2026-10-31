def majority_sign(vals):
    s = sum(vals)
    if s > 0:
        return 1
    elif s < 0:
        return -1
    else:
        return 0

def coarse_align_fixed(target, max_steps=12, step=0.03):
    last_sx, last_sy = 0, 0
    zero_count = 0
    for _ in range(max_steps):
        sx_sum = 0
        sy_sum = 0
        for _ in range(3):
            sx, sy = fixed_direction(target)
            sx_sum += sx
            sy_sum += sy
        sx = 1 if sx_sum > 0 else (-1 if sx_sum < 0 else 0)
        sy = 1 if sy_sum > 0 else (-1 if sy_sum < 0 else 0)
        if sx == 0 and sy == 0:
            zero_count += 1
            if zero_count >= 2:
                break
        else:
            zero_count = 0
            last_sx, last_sy = sx, sy
            move_by(step * sx, step * sy, 0)
    return last_sx, last_sy

def align_y_wrist(target, max_steps=8, step=0.015):
    for _ in range(max_steps):
        sx_sum = 0
        sy_sum = 0
        for _ in range(2):
            sx, sy = wrist_direction(target)
            sx_sum += sx
            sy_sum += sy
        sx = 1 if sx_sum > 0 else (-1 if sx_sum < 0 else 0)
        sy = 1 if sy_sum > 0 else (-1 if sy_sum < 0 else 0)
        if sy == 0:
            sx2, sy2 = wrist_direction(target)
            if sy2 == 0:
                break
            sy = sy2
        move_by(0, step * sy, 0)

def locate_tray(start_z):
    target = "the center of the tray"
    last_sx, last_sy = coarse_align_fixed(target, max_steps=12, step=0.03)
    if last_sx != 0 or last_sy != 0:
        move_by(0.06 * last_sx, 0.06 * last_sy, 0)
    for _ in range(10):
        sx_sum = 0
        sy_sum = 0
        for _ in range(2):
            sx, sy = wrist_direction(target)
            sx_sum += sx
            sy_sum += sy
        sx = 1 if sx_sum > 0 else (-1 if sx_sum < 0 else 0)
        sy = 1 if sy_sum > 0 else (-1 if sy_sum < 0 else 0)
        if sx == 0 and sy == 0:
            sx2, sy2 = wrist_direction(target)
            if sx2 == 0 and sy2 == 0:
                break
            sx, sy = sx2, sy2
        move_by(0.02 * sx, 0.02 * sy, 0)
    x, y, z = gripper_position()
    return x, y

# Main program
start_x, start_y, start_z = gripper_position()
open_gripper()

# Locate the tray and record its center coordinates
tray_x, tray_y = locate_tray(start_z)

# Move towards the bowl
target_bowl = "the center of the bowl to pick up"
last_sx, last_sy = coarse_align_fixed(target_bowl, max_steps=12, step=0.03)
if last_sx != 0 or last_sy != 0:
    move_by(0.06 * last_sx, 0.06 * last_sy, 0)

# Align in y with the wrist camera
align_y_wrist(target_bowl, max_steps=10, step=0.015)

# Scan in x using the vision check to find the bowl center
pos = gripper_position()
current_x = pos[0]
y_center = pos[1]

best_x = current_x
best_score = -1.0
for offset_cm in range(-6, 7):
    x = current_x + offset_cm * 0.01
    move_to(x, y_center, start_z)
    score = 0.0
    for _ in range(2):
        score += check("Is the red cross on the center of the black bowl?")
    score /= 2.0
    if score > best_score:
        best_score = score
        best_x = x

move_to(best_x, y_center, start_z)
align_y_wrist(target_bowl, max_steps=5, step=0.01)

pos = gripper_position()
bowl_x = pos[0]
bowl_y = pos[1]

# Try to grasp the bowl's rim with several y offsets
grasp_offsets = [-0.06, -0.05, -0.07, -0.04]
grasp_success = False
for offset in grasp_offsets:
    move_to(bowl_x, bowl_y + offset, start_z)
    open_gripper()
    for _ in range(8):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        grasp_success = True
        cur_z = gripper_position()[2]
        move_by(0, 0, start_z - cur_z)
        break
    else:
        open_gripper()
        cur_z = gripper_position()[2]
        move_by(0, 0, start_z - cur_z)

# If still not held, try a small x search around the estimated center
if not grasp_success:
    for dx in [-0.02, 0.02, -0.04, 0.04]:
        move_to(bowl_x + dx, bowl_y - 0.06, start_z)
        open_gripper()
        for _ in range(8):
            if not move_by(0, 0, -0.03):
                break
        move_by(0, 0, 0.015)
        close_gripper()
        if gripper_opening() > 0.003:
            grasp_success = True
            cur_z = gripper_position()[2]
            move_by(0, 0, start_z - cur_z)
            break
        else:
            open_gripper()
            cur_z = gripper_position()[2]
            move_by(0, 0, start_z - cur_z)

# Carry the bowl to the tray and place it
if grasp_success:
    move_to(tray_x, tray_y, start_z)
    for _ in range(8):
        if not move_by(0, 0, -0.03):
            break
    open_gripper()
    move_by(0, 0, 0.05)
