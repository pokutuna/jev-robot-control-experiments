def main():
    start_pos = gripper_position()
    start_z = start_pos[2]

    grasped = False
    offsets = [-0.06, -0.04]
    for offset in offsets:
        # Approach the center of the bowl to pick up
        for _ in range(10):
            fx, fy = fixed_direction("the center of the bowl to pick up")
            if fx == 0 and fy == 0:
                break
            move_by(0.05 * fx, 0.05 * fy, 0)
        for _ in range(10):
            wx, wy = wrist_direction("the center of the bowl to pick up")
            if wx == 0 and wy == 0:
                break
            move_by(0.02 * wx, 0.02 * wy, 0)

        # Move to the rim grasp point (6 cm in -y from the bowl center)
        move_by(0, offset, 0)

        # Descend until blocked
        while move_by(0, 0, -0.03):
            pass

        # Move up 1.5 cm before closing
        move_by(0, 0, 0.015)
        close_gripper()

        if gripper_opening() > 0.003:
            grasped = True
            break
        else:
            open_gripper()
            cur = gripper_position()
            move_to(cur[0], cur[1], start_z)

    # Lift to start height
    cur = gripper_position()
    move_to(cur[0], cur[1], start_z)

    # Navigate toward the tray using fixed camera
    reached_zero = False
    for _ in range(25):
        fx, fy = fixed_direction("the center of the tray")
        if fx == 0 and fy == 0:
            reached_zero = True
            break
        move_by(0.04 * fx, 0.04 * fy, 0)

    if reached_zero:
        # Correct known x bias when holding the bowl by its rim
        move_by(0.10, 0, 0)
    else:
        # Fallback: use wrist camera to get closer
        for _ in range(10):
            wx, wy = wrist_direction("the center of the tray")
            if wx == 0 and wy == 0:
                break
            move_by(0.02 * wx, 0.02 * wy, 0)

    # Fine-tune y alignment with wrist camera
    for _ in range(8):
        wx, wy = wrist_direction("the center of the tray")
        if wy == 0:
            break
        move_by(0, 0.02 * wy, 0)

    # Lower into the tray until blocked
    while move_by(0, 0, -0.03):
        pass

    # Move up 3 cm before opening to avoid lifting the tray
    move_by(0, 0, 0.03)
    open_gripper()

    # Lift back to start height
    cur = gripper_position()
    move_to(cur[0], cur[1], start_z)


main()
