z0 = gripper_position()[2]

def move_h(sx, sy, step=0.02):
    if sx == 0 and sy == 0:
        return True
    return move_by(sx * step, sy * step, 0)

def find_tray():
    tf = "the center of the tray"
    tw = "the center of the tray"
    for _ in range(10):
        sx, sy = fixed_direction(tf)
        if sx == 0 and sy == 0:
            break
        move_h(sx, sy, 0.03)
    for _ in range(6):
        sx, sy = wrist_direction(tw)
        if sx == 0 and sy == 0:
            break
        move_h(sx, sy, 0.02)
    pos = gripper_position()
    return pos[0], pos[1]

tray_x, tray_y = find_tray()

def align_pudding():
    tf = "the chocolate pudding box"
    tw = "the box"
    for _ in range(10):
        sx, sy = fixed_direction(tf)
        if sx == 0 and sy == 0:
            break
        move_h(sx, sy, 0.03)
    for _ in range(6):
        sx, sy = wrist_direction(tw)
        if sx == 0 and sy == 0:
            break
        move_h(sx, sy, 0.02)

def grasp_at(x0, y0, z0, dx, dy):
    move_to(x0 + dx, y0 + dy, z0)
    for _ in range(9):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        pos = gripper_position()
        move_to(pos[0], pos[1], z0)
        return True
    else:
        open_gripper()
        move_to(x0, y0, z0)
        return False

align_pudding()
pos = gripper_position()
x0 = pos[0]
y0 = pos[1]
move_to(x0, y0, z0)

held = False
offsets = [(0.0, 0.0), (0.03, 0.0), (-0.03, 0.0), (0.0, 0.015), (0.0, -0.015)]
for dx, dy in offsets:
    if grasp_at(x0, y0, z0, dx, dy):
        held = True
        break

if held:
    ok = move_to(tray_x, tray_y, z0)
    if not ok:
        move_by(0, 0, 0.06)
        pos = gripper_position()
        move_to(tray_x, tray_y, pos[2])
        move_to(tray_x, tray_y, z0)
    for _ in range(9):
        if not move_by(0, 0, -0.03):
            break
    open_gripper()
    move_by(0, 0, 0.06)
    pos = gripper_position()
    move_to(pos[0], pos[1], z0)
