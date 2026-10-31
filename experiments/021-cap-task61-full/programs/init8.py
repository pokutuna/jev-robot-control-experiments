def main():
    z0 = gripper_position()[2]

    def pudding_visible():
        if in_wrist_view("the chocolate pudding box") > 0.5:
            return True
        if in_wrist_view("the box") > 0.5:
            return True
        return False

    # Coarse approach to the pudding box using the fixed camera.
    for _ in range(20):
        if pudding_visible():
            break
        sx, sy = fixed_direction("the chocolate pudding box")
        if sx == 0 and sy == 0:
            sx, sy = fixed_direction("the box")
        if sx == 0 and sy == 0:
            move_by(0.02, 0, 0)
        else:
            move_by(sx * 0.02, sy * 0.02, 0)

    def align_pudding(max_steps=12):
        for _ in range(max_steps):
            if not pudding_visible():
                sx, sy = fixed_direction("the chocolate pudding box")
                if sx == 0 and sy == 0:
                    move_by(0.02, 0, 0)
                else:
                    move_by(sx * 0.02, sy * 0.02, 0)
                continue

            sx, sy = wrist_direction("the chocolate pudding box")
            if sx == 0 and sy == 0:
                sx2, sy2 = wrist_direction("the box")
                if sx2 != 0 or sy2 != 0:
                    sx, sy = sx2, sy2

            if sx == 0 and sy == 0:
                return True
            move_by(sx * 0.02, sy * 0.02, 0)
        return False

    held = False

    # Align, go down until blocked, back off slightly, close, and check grasp.
    for attempt in range(3):
        x, y, z = gripper_position()
        if z < z0 - 0.001:
            move_by(0, 0, z0 - z)

        align_pudding()

        for _ in range(20):
            if not move_by(0, 0, -0.03):
                break

        move_by(0, 0, 0.015)
        close_gripper()
        held = gripper_opening() > 0.003

        if held:
            break

        open_gripper()
        x, y, z = gripper_position()
        if z < z0 - 0.001:
            move_by(0, 0, z0 - z)

        if attempt == 0:
            move_by(0.02, 0, 0)
        elif attempt == 1:
            move_by(-0.04, 0, 0)

    # Lift to carrying height.
    x, y, z = gripper_position()
    if z < z0 - 0.001:
        move_by(0, 0, z0 - z)

    # Coarse approach to the tray while carrying the pudding.
    zero_count = 0
    for _ in range(20):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            zero_count += 1
            if zero_count >= 2:
                break
        else:
            zero_count = 0
            move_by(sx * 0.02, sy * 0.02, 0)

    # Fine y adjustment over the tray using the wrist camera.
    for _ in range(8):
        sx, sy = wrist_direction("the center of the tray")
        if sy == 0:
            sx2, sy2 = wrist_direction("the center of the tray")
            if sy2 == 0:
                break
            sy = sy2
        move_by(0, sy * 0.01, 0)

    # Final fixed-camera correction.
    for _ in range(5):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(sx * 0.02, sy * 0.02, 0)

    # Lower into the tray until blocked, back off 3 cm, open, and lift.
    for _ in range(20):
        if not move_by(0, 0, -0.03):
            break

    move_by(0, 0, 0.03)
    open_gripper()

    x, y, z = gripper_position()
    if z < z0 - 0.001:
        move_by(0, 0, z0 - z)


main()
