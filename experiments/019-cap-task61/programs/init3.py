def align_fixed(target, max_steps, step):
    for _ in range(max_steps):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            return
        move_by(sx * step, sy * step, 0)

def align_wrist(target, max_steps, step_x, step_y):
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            return
        move_by(sx * step_x, sy * step_y, 0)

def lift_to(z_target):
    z = gripper_position()[2]
    dz = z_target - z
    if dz > 0:
        move_by(0, 0, dz)

def lower_until_block(max_steps, step=0.03):
    for _ in range(max_steps):
        if not move_by(0, 0, -step):
            return True
    return False

z0 = gripper_position()[2]

align_fixed("the chocolate pudding box", 10, 0.03)
align_wrist("the chocolate pudding box", 12, 0.015, 0.015)

held = False
for attempt in range(3):
    lower_until_block(9)
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        held = True
        break
    open_gripper()
    if attempt < 2:
        lift_to(z0)
        if attempt == 0:
            align_wrist("the box", 8, 0.015, 0.015)
        else:
            align_wrist("the chocolate pudding box", 8, 0.015, 0.015)

lift_to(z0)

align_fixed("the center of the tray", 22, 0.035)
align_wrist("the center of the tray", 10, 0.02, 0.02)

for _ in range(4):
    if in_wrist_view("the tray") > 0.25:
        break
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.025, sy * 0.025, 0)

lower_until_block(9)
open_gripper()
move_by(0, 0, 0.10)
