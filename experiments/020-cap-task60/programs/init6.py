def align_fixed(target, max_steps=18, step=0.02):
    for _ in range(max_steps):
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            break
        move_by(step * sx, step * sy, 0)

def align_wrist(target, max_steps=10, step=0.02):
    zeros = 0
    for _ in range(max_steps):
        sx, sy = wrist_direction(target)
        if sx == 0 and sy == 0:
            zeros += 1
            if zeros >= 2:
                break
        else:
            zeros = 0
            move_by(step * sx, step * sy, 0)

def try_grasp(start_z):
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        x, y, z = gripper_position()
        move_to(x, y, start_z)
        return True
    else:
        open_gripper()
        x, y, z = gripper_position()
        move_to(x, y, start_z)
        return False

ix, iy, iz = gripper_position()
start_z = iz

align_fixed("the center of the tray", max_steps=18)
align_wrist("the center of the tray", max_steps=10)
tray_x, tray_y, _ = gripper_position()

move_to(ix, iy, start_z)

align_fixed("the center of the bowl to pick up", max_steps=18)
align_wrist("the center of the bowl to pick up", max_steps=10)

move_by(0, -0.06, 0)
base_x, base_y, _ = gripper_position()

held = False
x_offsets = [0, -0.03, 0.03, -0.06, 0.06]
for dx in x_offsets:
    move_to(base_x + dx, base_y, start_z)
    if try_grasp(start_z):
        held = True
        break

if not held:
    for dy in [-0.02, 0.02]:
        move_to(base_x, base_y + dy, start_z)
        if try_grasp(start_z):
            held = True
            break

if held:
    move_to(tray_x, tray_y, start_z)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.01)
    open_gripper()
    move_by(0, 0, 0.05)
