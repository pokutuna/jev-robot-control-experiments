def step_move(sx, sy, d=0.02):
    if sx == 0 and sy == 0:
        return False
    return move_by(sx * d, sy * d, 0)

def align_target(target, max_steps=20, step=0.02, refine=5):
    for _ in range(max_steps):
        p = in_wrist_view(target)
        if p > 0.55:
            sx, sy = wrist_direction(target)
        else:
            sx, sy = fixed_direction(target)
            if sx == 0 and sy == 0:
                p2 = in_wrist_view(target)
                if p2 > 0.55:
                    sx, sy = wrist_direction(target)
                if sx == 0 and sy == 0:
                    break
        if sx == 0 and sy == 0:
            break
        if not step_move(sx, sy, step):
            break
    for _ in range(refine):
        p = in_wrist_view(target)
        if p <= 0.55:
            break
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            break
        step_move(sx, sy, 0.01)

start_z = gripper_position()[2]

align_target("the center of the tray", max_steps=25, step=0.02, refine=5)
tray_x, tray_y, _ = gripper_position()

held = False
for attempt in range(2):
    open_gripper()
    cx, cy, cz = gripper_position()
    move_to(cx, cy, start_z)
    align_target("the chocolate pudding box", max_steps=20, step=0.02, refine=8)
    for _ in range(6):
        p = in_wrist_view("the chocolate pudding box")
        if p > 0.5:
            sx, sy = wrist_direction("the chocolate pudding box")
        else:
            sx, sy = fixed_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            break
        step_move(sx, sy, 0.015)
    cx, cy, cz = gripper_position()
    move_to(cx, cy, start_z)
    for _ in range(15):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        move_to(gripper_position()[0], gripper_position()[1], start_z)
        break
    else:
        open_gripper()
        move_to(gripper_position()[0], gripper_position()[1], start_z)

if held:
    for _ in range(5):
        if move_to(tray_x, tray_y, start_z):
            break
        else:
            move_by(0, 0, 0.02)
    for _ in range(15):
        if not move_by(0, 0, -0.03):
            break
    open_gripper()
    move_to(gripper_position()[0], gripper_position()[1], start_z)
