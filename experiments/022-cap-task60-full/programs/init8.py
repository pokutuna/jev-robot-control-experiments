gx, gy, gz = gripper_position()
start_z = gz

for i in range(30):
    wx, wy = wrist_direction("the center of the bowl to pick up")
    fx, fy = fixed_direction("the black bowl on the left")
    if fx == 0 and fy == 0:
        fx, fy = fixed_direction("the center of the bowl to pick up")
    sx = fx if fx != 0 else wx
    sy = wy if wy != 0 else fy
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

for i in range(5):
    fx, fy = fixed_direction("the center of the bowl to pick up")
    if fx == 0:
        break
    move_by(fx * 0.01, 0, 0)

move_by(0, -0.06, 0)

while move_by(0, 0, -0.03):
    pass

move_by(0, 0, 0.015)
close_gripper()

if gripper_opening() <= 0.003:
    open_gripper()
    move_by(0, 0, 0.03)
    move_by(0, 0.01, 0)
    while move_by(0, 0, -0.03):
        pass
    move_by(0, 0, 0.015)
    close_gripper()

cx, cy, cz = gripper_position()
move_to(cx, cy, start_z)

for i in range(30):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

move_by(0.11, 0.02, 0)

for i in range(5):
    if check("Is the bowl above the tray?") > 0.6:
        break
    move_by(0.02, 0, 0)

open_gripper()
move_by(0, 0, 0.05)
