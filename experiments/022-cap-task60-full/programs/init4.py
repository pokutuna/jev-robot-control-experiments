def wrist_dir_robust(target, check_target):
    sx, sy = wrist_direction(target)
    if sx == 0:
        p_above = check("Is " + check_target + " above the red cross?")
        p_below = check("Is " + check_target + " below the red cross?")
        if p_above > 0.6 and p_above > p_below + 0.2:
            sx = -1
        elif p_below > 0.6 and p_below > p_above + 0.2:
            sx = 1
    if sy == 0:
        p_left = check("Is " + check_target + " to the left of the red cross?")
        p_right = check("Is " + check_target + " to the right of the red cross?")
        if p_left > 0.6 and p_left > p_right + 0.2:
            sy = -1
        elif p_right > 0.6 and p_right > p_left + 0.2:
            sy = 1
    return sx, sy

def align_to_target(target, check_target, max_coarse=15, max_fine=10):
    for _ in range(max_coarse):
        if in_wrist_view(target) > 0.6:
            break
        sx, sy = fixed_direction(target)
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)
    for _ in range(max_fine):
        sx, sy = wrist_dir_robust(target, check_target)
        if sx == 0 and sy == 0:
            sx2, sy2 = wrist_dir_robust(target, check_target)
            if sx2 == 0 and sy2 == 0:
                break
            else:
                sx, sy = sx2, sy2
        if not move_by(sx * 0.02, sy * 0.02, 0):
            break

start_x, start_y, start_z = gripper_position()

align_to_target("the center of the tray", "the tray")
tray_x, tray_y, _ = gripper_position()

align_to_target("the center of the bowl to pick up", "the bowl")
bowl_x, bowl_y, _ = gripper_position()

success = False
grasp_offset_y = -0.06

for offset_y in [-0.06, -0.05, -0.07, -0.04, -0.08]:
    move_to(bowl_x, bowl_y, start_z)
    move_by(0, offset_y, 0)
    for _ in range(12):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    if gripper_opening() > 0.003:
        success = True
        grasp_offset_y = offset_y
        break
    else:
        open_gripper()
        cur_x, cur_y, cur_z = gripper_position()
        move_to(cur_x, cur_y, start_z)

if not success:
    for dx in [0.02, -0.02, 0.04, -0.04]:
        move_to(bowl_x + dx, bowl_y, start_z)
        offset_y = -0.06
        move_by(0, offset_y, 0)
        for _ in range(12):
            if not move_by(0, 0, -0.03):
                break
        move_by(0, 0, 0.015)
        close_gripper()
        if gripper_opening() > 0.003:
            success = True
            grasp_offset_y = offset_y
            break
        else:
            open_gripper()
            cur_x, cur_y, cur_z = gripper_position()
            move_to(cur_x, cur_y, start_z)

cur_x, cur_y, cur_z = gripper_position()
move_to(cur_x, cur_y, start_z)

place_x = tray_x
place_y = tray_y + grasp_offset_y
move_to(place_x, place_y, start_z)

for _ in range(12):
    if not move_by(0, 0, -0.03):
        break

move_by(0, 0, 0.03)
open_gripper()

cur_x, cur_y, cur_z = gripper_position()
move_to(cur_x, cur_y, start_z)
