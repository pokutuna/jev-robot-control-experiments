START_Z = gripper_position()[2]
open_gripper()

def find_tray_center():
    target = "the center of the tray"
    for i in range(6):
        fx, fy = fixed_direction(target)
        if fx == 0 and fy == 0:
            break
        move_by(fx*0.04, fy*0.04, 0)
    zeros = 0
    for i in range(12):
        wx, wy = wrist_direction(target)
        if wx == 0 and wy == 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            move_by(wx*0.02, wy*0.02, 0)
    if in_wrist_view(target) < 0.15:
        sx, sy, sz = gripper_position()
        best_p = in_wrist_view(target)
        best_pos = (sx, sy)
        for dx, dy in [(0.04,0),(-0.04,0),(0,0.04),(0,-0.04)]:
            move_to(sx+dx, sy+dy, sz)
            p = in_wrist_view(target)
            if p > best_p:
                best_p = p
                best_pos = (sx+dx, sy+dy)
        move_to(best_pos[0], best_pos[1], sz)
        for i in range(6):
            wx, wy = wrist_direction(target)
            if wx == 0 and wy == 0:
                break
            move_by(wx*0.02, wy*0.02, 0)
    return gripper_position()[:2]

def find_bowl_center():
    target = "the center of the bowl to pick up"
    for i in range(6):
        fx, fy = fixed_direction(target)
        if fx == 0 and fy == 0:
            break
        move_by(fx*0.03, fy*0.03, 0)
    zeros = 0
    for i in range(12):
        fx, fy = fixed_direction(target)
        wx, wy = wrist_direction(target)
        sx = fx if fx != 0 else wx
        sy = wy if wy != 0 else fy
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            move_by(sx*0.02, sy*0.02, 0)
    return gripper_position()[:2]

def grasp_at(x, y):
    move_to(x, y, START_Z)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    cur = gripper_position()
    move_to(cur[0], cur[1], START_Z)
    return gripper_opening() > 0.003

tray_x, tray_y = find_tray_center()
bowl_x, bowl_y = find_bowl_center()
pickup_y = bowl_y - 0.06

used_dx = 0.0
used_dy = 0.0
held = False
attempts = [(0.0, 0.0), (0.02, 0.0), (-0.02, 0.0), (0.0, 0.02)]
for dx, dy in attempts:
    open_gripper()
    if grasp_at(bowl_x + dx, pickup_y + dy):
        held = True
        used_dx = dx
        used_dy = dy
        break

place_x = tray_x + used_dx
place_y = tray_y - 0.06 + used_dy
move_to(place_x, place_y, START_Z)

for _ in range(10):
    if not move_by(0, 0, -0.03):
        break
move_by(0, 0, 0.03)
open_gripper()
cur = gripper_position()
move_to(cur[0], cur[1], START_Z)
