motion_count = 0
vision_count = 0

def mb(dx, dy, dz):
    global motion_count
    if motion_count >= 119:
        return False
    motion_count += 1
    return move_by(dx, dy, dz)

def mt(x, y, z):
    global motion_count
    if motion_count >= 119:
        return False
    motion_count += 1
    return move_to(x, y, z)

def fd(target):
    global vision_count
    if vision_count >= 359:
        return (0, 0)
    vision_count += 1
    return fixed_direction(target)

def wd(target):
    global vision_count
    if vision_count >= 359:
        return (0, 0)
    vision_count += 1
    return wrist_direction(target)

def chk(q):
    global vision_count
    if vision_count >= 359:
        return 0.0
    vision_count += 1
    return check(q)

start_x, start_y, start_z = gripper_position()

def align_fixed(target, max_iters=20, step=0.02):
    for i in range(max_iters):
        sx, sy = fd(target)
        if sx == 0 and sy == 0:
            break
        if not mb(sx * step, sy * step, 0):
            break

def align_wrist(target, max_iters=10, step=0.02):
    for i in range(max_iters):
        sx, sy = wd(target)
        if sx == 0 and sy == 0:
            break
        if not mb(sx * step, sy * step, 0):
            break

def grasp_bowl():
    align_fixed("the center of the bowl to pick up", max_iters=25, step=0.02)
    align_wrist("the center of the bowl to pick up", max_iters=8, step=0.02)
    align_fixed("the center of the bowl to pick up", max_iters=5, step=0.02)
    align_wrist("the center of the bowl to pick up", max_iters=5, step=0.02)
    
    base_x, base_y, base_z = gripper_position()
    if abs(base_z - start_z) > 0.001:
        mt(base_x, base_y, start_z)
    
    offsets = [
        (0.000, -0.060),
        (-0.020, -0.060),
        (0.020, -0.060),
        (0.000, -0.045),
        (0.000, -0.075),
        (-0.020, -0.045),
        (0.020, -0.045),
    ]
    
    for dx, dy in offsets:
        if motion_count > 105:
            break
        mt(base_x + dx, base_y + dy, start_z)
        for _ in range(15):
            if not mb(0, 0, -0.03):
                break
        mb(0, 0, 0.015)
        close_gripper()
        held = gripper_opening() > 0.003
        cur_x, cur_y, cur_z = gripper_position()
        mt(cur_x, cur_y, start_z)
        held = held and (gripper_opening() > 0.003)
        if held:
            return True
        else:
            open_gripper()
    return False

def place_in_tray():
    align_fixed("the center of the tray", max_iters=30, step=0.02)
    mb(0, -0.06, 0)
    for _ in range(15):
        if not mb(0, 0, -0.03):
            break
    open_gripper()
    cur_x, cur_y, cur_z = gripper_position()
    mt(cur_x, cur_y, start_z)
    p1 = chk("Is the black bowl in the tray?")
    p2 = chk("Is there a bowl in the tray?")
    return p1 > 0.5 or p2 > 0.5

success = grasp_bowl()
if success:
    placed = place_in_tray()
    if not placed and motion_count < 70:
        open_gripper()
        cur_x, cur_y, cur_z = gripper_position()
        mt(cur_x, cur_y, start_z)
        success2 = grasp_bowl()
        if success2:
            place_in_tray()
