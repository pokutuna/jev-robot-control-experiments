mc = 0
vc = 0

def mv(dx, dy, dz):
    global mc
    if mc >= 118:
        return False
    mc += 1
    return move_by(dx, dy, dz)

def close_g():
    global mc
    if mc >= 120:
        return
    mc += 1
    close_gripper()

def open_g():
    global mc
    if mc >= 120:
        return
    mc += 1
    open_gripper()

def wd(t):
    global vc
    if vc >= 360:
        return (0, 0)
    vc += 1
    return wrist_direction(t)

def fd(t):
    global vc
    if vc >= 360:
        return (0, 0)
    vc += 1
    return fixed_direction(t)

def inv(t):
    global vc
    if vc >= 360:
        return 0.0
    vc += 1
    return in_wrist_view(t)

def chk(q):
    global vc
    if vc >= 360:
        return 0.0
    vc += 1
    return check(q)

sx0, sy0, sz0 = gripper_position()

pud_fixed = "the chocolate pudding box"
pud_wrist = "the box"
tray = "the center of the tray"

grabbed = False
for attempt in range(2):
    last_dx = 0
    last_dy = 0
    zero = 0
    for i in range(12):
        vis = inv(pud_fixed)
        if vis > 0.45:
            break
        dx, dy = fd(pud_fixed)
        if dx != 0 or dy != 0:
            last_dx, last_dy = dx, dy
            zero = 0
            mv(0.02 * dx, 0.02 * dy, 0)
        else:
            if zero < 2 and (last_dx != 0 or last_dy != 0):
                mv(0.02 * last_dx, 0.02 * last_dy, 0)
                zero += 1
            else:
                break

    for i in range(6):
        dx, dy = wd(pud_wrist)
        if dx == 0 and dy == 0:
            break
        if dx != 0:
            mv(0.02 * dx, 0, 0)
        if dy != 0:
            mv(0, 0.02 * dy, 0)

    for i in range(10):
        if not mv(0, 0, -0.03):
            break
    mv(0, 0, 0.015)
    close_g()

    if gripper_opening() > 0.003:
        grabbed = True
        z = gripper_position()[2]
        mv(0, 0, sz0 - z)
        break
    else:
        open_g()
        z = gripper_position()[2]
        mv(0, 0, sz0 - z)

if grabbed:
    last_dx = 0
    last_dy = 0
    zero = 0
    for i in range(18):
        dx, dy = fd(tray)
        if dx != 0 or dy != 0:
            last_dx, last_dy = dx, dy
            zero = 0
            mv(0.02 * dx, 0.02 * dy, 0)
        else:
            if inv(tray) > 0.30:
                break
            if zero < 3 and (last_dx != 0 or last_dy != 0):
                mv(0.02 * last_dx, 0.02 * last_dy, 0)
                zero += 1
            else:
                break

    for i in range(6):
        dx, dy = wd(tray)
        if dx == 0 and dy == 0:
            break
        if dx != 0:
            mv(0.02 * dx, 0, 0)
        if dy != 0:
            mv(0, 0.02 * dy, 0)

    for i in range(8):
        if not mv(0, 0, -0.03):
            break
    open_g()
else:
    open_g()
