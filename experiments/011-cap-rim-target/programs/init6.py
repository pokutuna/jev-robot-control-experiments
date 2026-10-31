start_x, start_y, start_z = gripper_position()
start_height = start_z

def move_to_start_height():
    cx, cy, cz = gripper_position()
    if abs(cz - start_height) > 0.001:
        move_to(cx, cy, start_height)

def find_bowl():
    if in_wrist_view("the black bowl") > 0.5:
        return True
    for _ in range(4):
        sx, sy = fixed_direction("the black bowl on the left")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.05, sy * 0.05, 0)
        if in_wrist_view("the black bowl") > 0.5:
            return True
    step = 0.06
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    d_idx = 0
    leg_len = 1
    leg_count = 0
    for _ in range(15):
        if in_wrist_view("the black bowl") > 0.5:
            return True
        dx, dy = dirs[d_idx]
        move_by(dx * step, dy * step, 0)
        leg_count += 1
        if leg_count == leg_len:
            leg_count = 0
            d_idx = (d_idx + 1) % 4
            if d_idx % 2 == 0:
                leg_len += 1
    return in_wrist_view("the black bowl") > 0.5

def pick_bowl():
    for attempt in range(2):
        move_to_start_height()
        for _ in range(5):
            sx, sy = wrist_direction("the center of the bowl to pick up")
            if sx == 0 and sy == 0:
                break
            move_by(sx * 0.02, sy * 0.02, 0)
        for _ in range(5):
            sx, sy = wrist_direction("the left edge of the bowl to pick up")
            if sy == 0:
                break
            move_by(0, sy * 0.02, 0)
        for _ in range(3):
            sx, sy = wrist_direction("the center of the bowl to pick up")
            if sx == 0:
                break
            move_by(sx * 0.02, 0, 0)
        for _ in range(10):
            if not move_by(0, 0, -0.03):
                break
        move_by(0, 0, 0.015)
        close_gripper()
        if gripper_opening() > 0.003:
            return True
        open_gripper()
        cx, cy, cz = gripper_position()
        move_by(0, 0, start_height - cz)
    return False

def go_to_tray():
    last_fixed = (0, 0)
    for _ in range(20):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        last_fixed = (sx, sy)
        move_by(sx * 0.05, sy * 0.05, 0)
    if last_fixed != (0, 0):
        move_by(last_fixed[0] * 0.06, last_fixed[1] * 0.06, 0)
    for _ in range(8):
        sx, sy = wrist_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    move_by(0, -0.06, 0)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    open_gripper()
    move_by(0, 0, 0.05)

picked = False
for _ in range(2):
    find_bowl()
    if pick_bowl():
        picked = True
        break
    open_gripper()
    cx, cy, cz = gripper_position()
    move_by(0, 0, start_height - cz)

if picked:
    cx, cy, cz = gripper_position()
    move_by(0, 0, start_height - cz)
    go_to_tray()
