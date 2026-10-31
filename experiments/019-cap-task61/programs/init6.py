motion_count = 0

def m_move_by(dx, dy, dz):
    global motion_count
    if motion_count >= 120:
        return False
    motion_count += 1
    return move_by(dx, dy, dz)

def m_move_to(x, y, z):
    global motion_count
    if motion_count >= 120:
        return False
    motion_count += 1
    return move_to(x, y, z)

def m_open():
    global motion_count
    if motion_count < 120:
        motion_count += 1
        open_gripper()

def m_close():
    global motion_count
    if motion_count < 120:
        motion_count += 1
        close_gripper()

start_x, start_y, start_z = gripper_position()
m_open()

def lift_to_start():
    x, y, z = gripper_position()
    if abs(z - start_z) > 1e-6:
        m_move_to(x, y, start_z)

def align_pudding():
    target = "the chocolate pudding box"

    for i in range(12):
        p = in_wrist_view(target)
        if p > 0.3:
            break
        d = fixed_direction(target)
        if d == (0, 0):
            wd = wrist_direction(target)
            if wd == (0, 0):
                break
            d = wd
        if not m_move_by(d[0] * 0.025, d[1] * 0.025, 0):
            m_move_by(d[0] * 0.01, d[1] * 0.01, 0)

    zeros = 0
    for i in range(12):
        d = wrist_direction(target)
        if d == (0, 0):
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            step = 0.015 if i < 6 else 0.008
            m_move_by(d[0] * step, d[1] * step, 0)

    for i in range(6):
        d = wrist_direction("the box")
        if d[1] == 0:
            break
        m_move_by(0, d[1] * 0.01, 0)

    for i in range(4):
        d = wrist_direction("the center of the chocolate pudding box")
        if d[0] == 0:
            break
        m_move_by(d[0] * 0.01, 0, 0)

    for i in range(4):
        d = wrist_direction(target)
        if d == (0, 0):
            break
        m_move_by(d[0] * 0.008, d[1] * 0.008, 0)

def grasp_attempt():
    for i in range(10):
        if not m_move_by(0, 0, -0.03):
            break
    m_move_by(0, 0, 0.015)
    m_close()
    return gripper_opening() > 0.003

def pick_pudding():
    align_pudding()
    held = grasp_attempt()
    if held:
        lift_to_start()
        return True

    m_open()
    lift_to_start()

    for i in range(8):
        d = wrist_direction("the chocolate pudding box")
        if d == (0, 0):
            break
        m_move_by(d[0] * 0.012, d[1] * 0.012, 0)

    held = grasp_attempt()
    if held:
        lift_to_start()
        return True

    m_open()
    lift_to_start()
    return False

def go_to_tray():
    target = "the center of the tray"

    for i in range(15):
        d = fixed_direction(target)
        if d == (0, 0):
            break
        if not m_move_by(d[0] * 0.03, d[1] * 0.03, 0):
            m_move_by(d[0] * 0.015, d[1] * 0.015, 0)

    for i in range(6):
        d = wrist_direction(target)
        if d == (0, 0):
            break
        m_move_by(d[0] * 0.01, d[1] * 0.01, 0)

    for i in range(5):
        p = check("Is the gripper above the tray?")
        if p >= 0.5:
            break
        d = fixed_direction("the tray")
        if d == (0, 0):
            d = wrist_direction(target)
            if d == (0, 0):
                break
        m_move_by(d[0] * 0.02, d[1] * 0.02, 0)

def place_in_tray():
    for i in range(10):
        if not m_move_by(0, 0, -0.03):
            break
    m_open()
    lift_to_start()
    return check("Is the chocolate pudding box in the tray?") >= 0.4

if pick_pudding():
    go_to_tray()
    place_in_tray()
