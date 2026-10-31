pos = gripper_position()
start_z = pos[2]

# Locate tray
for _ in range(10):
    sx, sy = fixed_direction("the center of the tray")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

for _ in range(8):
    sx, sy = wrist_direction("the center of the tray")
    if sx == 0 and sy == 0:
        prob = check("Is the red cross on the tray?")
        if prob > 0.5:
            break
    move_by(sx * 0.015, sy * 0.015, 0)

tray_check = check("Is the red cross on the tray?")
if tray_check < 0.3:
    base = gripper_position()
    best_x, best_y = base[0], base[1]
    best_p = tray_check
    for dx in [-0.03, 0, 0.03]:
        for dy in [-0.03, 0, 0.03]:
            if dx == 0 and dy == 0:
                continue
            move_to(base[0] + dx, base[1] + dy, start_z)
            p = check("Is the red cross on the tray?")
            if p > best_p:
                best_p = p
                best_x, best_y = base[0] + dx, base[1] + dy
    move_to(best_x, best_y, start_z)

tray_pos = gripper_position()
tray_x, tray_y = tray_pos[0], tray_pos[1]

# Locate bowl
for _ in range(12):
    sx, sy = fixed_direction("the center of the bowl to pick up")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.02, sy * 0.02, 0)

for _ in range(8):
    sx, sy = wrist_direction("the center of the bowl to pick up")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.015, sy * 0.015, 0)

base = gripper_position()
base_x, base_y = base[0], base[1]

best_x = base_x
best_p = -1.0
for i in range(7):
    x = base_x - 0.06 + i * 0.02
    move_to(x, base_y, start_z)
    p = check("Is the red cross at the center of the black bowl to pick up?")
    p += check("Is the red cross at the center of the black bowl to pick up?")
    p /= 2.0
    if p > best_p:
        best_p = p
        best_x = x

move_to(best_x, base_y, start_z)

for _ in range(4):
    sx, sy = wrist_direction("the center of the bowl to pick up")
    if sx == 0 and sy == 0:
        break
    move_by(sx * 0.01, sy * 0.01, 0)

pos = gripper_position()
bowl_center_x = pos[0]
bowl_center_y = pos[1]

open_gripper()
held = False

for dx in [0, 0.02, -0.02]:
    move_to(bowl_center_x + dx, bowl_center_y - 0.06, start_z)
    while move_by(0, 0, -0.03):
        pass
    move_by(0, 0, 0.015)
    close_gripper()
    move_by(0, 0, 0.20)
    if gripper_opening() > 0.003:
        held = True
        cur = gripper_position()
        move_to(cur[0], cur[1], start_z)
        break
    else:
        open_gripper()
        move_to(bowl_center_x + dx, bowl_center_y - 0.06, start_z)

if not held:
    move_to(bowl_center_x, bowl_center_y - 0.05, start_z)
    while move_by(0, 0, -0.03):
        pass
    move_by(0, 0, 0.015)
    close_gripper()
    move_by(0, 0, 0.20)
    if gripper_opening() > 0.003:
        held = True
        cur = gripper_position()
        move_to(cur[0], cur[1], start_z)
    else:
        open_gripper()
        move_to(bowl_center_x, bowl_center_y - 0.05, start_z)

if held:
    move_to(tray_x, tray_y, start_z)
    while move_by(0, 0, -0.03):
        pass
    move_by(0, 0, 0.03)
    open_gripper()
    move_to(tray_x, tray_y, start_z)
