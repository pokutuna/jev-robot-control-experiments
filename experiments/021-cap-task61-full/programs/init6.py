START = gripper_position()
START_Z = START[2]
MOT = 0
VIS = 0

def wdir(target):
    global VIS
    if VIS >= 355:
        return (0, 0)
    VIS += 1
    return wrist_direction(target)

def fdir(target):
    global VIS
    if VIS >= 355:
        return (0, 0)
    VIS += 1
    return fixed_direction(target)

def mby(dx, dy, dz):
    global MOT
    if MOT >= 119:
        return False
    MOT += 1
    return move_by(dx, dy, dz)

def mto(x, y, z):
    global MOT
    if MOT >= 119:
        return False
    MOT += 1
    return move_to(x, y, z)

def op():
    global MOT
    if MOT >= 119:
        return
    MOT += 1
    open_gripper()

def cl():
    global MOT
    if MOT >= 119:
        return
    MOT += 1
    close_gripper()

def align_tray():
    for _ in range(12):
        if MOT >= 114:
            break
        sx, sy = fdir("the center of the tray")
        if sx == 0 and sy == 0:
            break
        mby(0.05 * sx, 0.05 * sy, 0)

    for _ in range(16):
        if MOT >= 114:
            break
        sx, sy = wdir("the center of the tray")
        if sx == 0 and sy == 0:
            sx, sy = wdir("the tray")
            if sx == 0 and sy == 0:
                break
        mby(0.015 * sx, 0.015 * sy, 0)

    return gripper_position()

def align_pudding():
    for _ in range(10):
        if MOT >= 114:
            break
        sx, sy = fdir("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        mby(0.04 * sx, 0.04 * sy, 0)

    for _ in range(18):
        if MOT >= 116:
            break
        sx, sy = wdir("the chocolate pudding box")
        if sx == 0 and sy == 0:
            sx, sy = wdir("the box")
        if sx == 0 and sy == 0:
            sx, sy = wdir("the center of the chocolate pudding box")
            if sx == 0 and sy == 0:
                break
        mby(0.012 * sx, 0.010 * sy, 0)

def quick_pudding():
    for _ in range(8):
        if MOT >= 116:
            break
        sx, sy = wdir("the chocolate pudding box")
        if sx == 0 and sy == 0:
            sx, sy = wdir("the box")
            if sx == 0 and sy == 0:
                break
        mby(0.010 * sx, 0.010 * sy, 0)

def pick_pudding():
    for attempt in range(2):
        if MOT >= 116:
            return False

        cur = gripper_position()
        if abs(cur[2] - START_Z) > 0.004:
            mto(cur[0], cur[1], START_Z)

        op()

        blocked = False
        for _ in range(12):
            if MOT >= 119:
                break
            if not mby(0, 0, -0.03):
                blocked = True
                break

        if not blocked:
            cur = gripper_position()
            mto(cur[0], cur[1], START_Z)
            if attempt == 0:
                quick_pudding()
            continue

        mby(0, 0, 0.015)
        cl()

        if gripper_opening() > 0.003:
            cur = gripper_position()
            mto(cur[0], cur[1], START_Z)
            return True

        op()
        cur = gripper_position()
        mto(cur[0], cur[1], START_Z)
        if attempt == 0:
            quick_pudding()

    return False

def place_in_tray(tx, ty):
    cur = gripper_position()
    mto(tx, ty, START_Z)

    blocked = False
    for _ in range(12):
        if MOT >= 119:
            break
        if not mby(0, 0, -0.03):
            blocked = True
            break

    mby(0, 0, 0.03)
    op()

    cur = gripper_position()
    mto(cur[0], cur[1], START_Z)

op()

tray_pos = align_tray()
tray_x, tray_y = tray_pos[0], tray_pos[1]

align_pudding()

if pick_pudding():
    place_in_tray(tray_x, tray_y)
