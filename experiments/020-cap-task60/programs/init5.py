def majority_direction(func, target, samples=3):
    xs = []
    ys = []
    for _ in range(samples):
        sx, sy = func(target)
        xs.append(sx)
        ys.append(sy)
    def mode(vals):
        counts = {-1:0, 0:0, 1:0}
        for v in vals:
            if v in counts:
                counts[v] += 1
            else:
                counts[v] = 1
        maxc = max(counts.values())
        for v in [0, 1, -1]:
            if counts.get(v, 0) == maxc:
                return v
        return 0
    return mode(xs), mode(ys)

def align_to_bowl_center():
    target = "the center of the bowl to pick up"
    for _ in range(10):
        sx, sy = majority_direction(fixed_direction, target, 3)
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    for _ in range(6):
        sx_f, sy_f = majority_direction(fixed_direction, target, 3)
        sx_w, sy_w = majority_direction(wrist_direction, target, 3)
        dx = sx_f if sx_f != 0 else sx_w
        dy = sy_w if sy_w != 0 else sy_f
        if dx == 0 and dy == 0:
            break
        move_by(dx * 0.02, dy * 0.02, 0)
    for _ in range(2):
        sx, sy = majority_direction(wrist_direction, target, 3)
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

def align_to_tray_center():
    target = "the center of the tray"
    for _ in range(12):
        sx, sy = majority_direction(fixed_direction, target, 3)
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    zero_count = 0
    for _ in range(8):
        sx_f, sy_f = majority_direction(fixed_direction, target, 3)
        sx_w, sy_w = majority_direction(wrist_direction, target, 3)
        dx = sx_f if sx_f != 0 else sx_w
        dy = sy_w if sy_w != 0 else sy_f
        if dx == 0 and dy == 0:
            zero_count += 1
            if zero_count >= 2:
                break
            else:
                move_by(0.01, 0, 0)
                continue
        else:
            zero_count = 0
        move_by(dx * 0.02, dy * 0.02, 0)
    for _ in range(2):
        sx, sy = majority_direction(wrist_direction, target, 3)
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

x0, y0, z_start = gripper_position()

align_to_bowl_center()

attempts = [(0.0, -0.06), (0.02, -0.05), (-0.02, -0.05)]
success = False
successful_x_off = 0.0
successful_y_off = -0.06

for idx, (x_off, y_off) in enumerate(attempts):
    if idx == 1:
        align_to_bowl_center()
    move_by(x_off, y_off, 0)
    while True:
        if move_by(0, 0, -0.03):
            continue
        else:
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        z_now = gripper_position()[2]
        move_by(0, 0, z_start - z_now)
        success = True
        successful_x_off = x_off
        successful_y_off = y_off
        break
    else:
        open_gripper()
        z_now = gripper_position()[2]
        move_by(0, 0, z_start - z_now)
        move_by(-x_off, -y_off, 0)

if not success:
    z_now = gripper_position()[2]
    if z_now < z_start - 0.01:
        move_by(0, 0, z_start - z_now)

align_to_tray_center()

move_by(successful_x_off, successful_y_off, 0)

while True:
    if move_by(0, 0, -0.03):
        continue
    else:
        break

open_gripper()
move_by(0, 0, 0.05)
