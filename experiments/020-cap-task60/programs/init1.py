def sign(v):
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0

start_x, start_y, start_z = gripper_position()
open_gripper()

phrase = "the center of the bowl to pick up"

for i in range(10):
    sx, sy = fixed_direction(phrase)
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.03, sy * 0.03, 0)

for i in range(12):
    sx_sum = 0
    sy_sum = 0
    for j in range(3):
        sx, sy = wrist_direction(phrase)
        sx_sum += sx
        sy_sum += sy
    sx = sign(sx_sum)
    sy = sign(sy_sum)
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

pos = gripper_position()
base_x, base_y, base_z = pos
left_x = base_x - 0.06
move_to(left_x, base_y, base_z)
best_x = left_x
best_p = -1.0
for i in range(7):
    p1 = check("Is the red cross on the center of the black bowl?")
    p2 = check("Is the red cross on the center of the bowl to pick up?")
    p = (p1 + p2) / 2.0
    cur_x = left_x + i * 0.02
    if p > best_p:
        best_p = p
        best_x = cur_x
    if i < 6:
        move_by(0.02, 0, 0)
move_to(best_x, base_y, base_z)

for i in range(5):
    sx, sy = wrist_direction(phrase)
    if sy == 0:
        break
    move_by(0, sy * 0.02, 0)

center = gripper_position()
cx, cy, cz = center

held = False
offsets_y = [0.0, 0.015, -0.015]
for attempt in range(3):
    move_to(cx, cy, cz)
    open_gripper()
    y_offset = -0.06 + offsets_y[attempt]
    move_to(cx, cy + y_offset, cz)
    blocked = False
    for i in range(20):
        if not move_by(0, 0, -0.03):
            blocked = True
            break
    move_by(0, 0, 0.015)
    close_gripper()
    opening = gripper_opening()
    if opening > 0.003:
        held = True
        break
    else:
        open_gripper()
        move_to(cx, cy + y_offset, cz)

move_to(gripper_position()[0], gripper_position()[1], start_z)

for i in range(15):
    sx, sy = fixed_direction("the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.04, sy * 0.04, 0)

question = "Is the bowl above the tray?"
for step in range(3):
    p0 = (check(question) + check(question)) / 2.0
    best_p = p0
    best_dx = 0
    best_dy = 0
    for dx, dy in [(0.04, 0), (-0.04, 0), (0, 0.04), (0, -0.04)]:
        move_by(dx, dy, 0)
        p = (check(question) + check(question)) / 2.0
        move_by(-dx, -dy, 0)
        if p > best_p:
            best_p = p
            best_dx = dx
            best_dy = dy
    if best_p > p0 + 0.05 and (best_dx != 0 or best_dy != 0):
        move_by(best_dx, best_dy, 0)
    else:
        break

for i in range(20):
    if not move_by(0, 0, -0.03):
        break
open_gripper()
move_to(gripper_position()[0], gripper_position()[1], start_z)
