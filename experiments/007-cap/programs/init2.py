def search_bowl(start_x, start_y, start_z):
    if in_wrist_view("the black bowl on the left") > 0.4:
        return True
    for i in range(10):
        move_by(0, 0.03, 0)
        if in_wrist_view("the black bowl on the left") > 0.4:
            return True
    move_to(start_x, start_y, start_z)
    for dy in [0.06, 0.12, 0.18, 0.24, 0.30]:
        for dx in [0.06, -0.06, 0.12, -0.12]:
            move_to(start_x + dx, start_y + dy, start_z)
            if in_wrist_view("the black bowl on the left") > 0.4:
                return True
    move_to(start_x, start_y, start_z)
    for i in range(4):
        move_by(0, -0.03, 0)
        if in_wrist_view("the black bowl on the left") > 0.4:
            return True
    for i in range(10):
        sx, sy = fixed_direction("the black bowl on the left")
        if sx == 0 and sy == 0:
            break
        move_by(0.03 * sx, 0.03 * sy, 0)
        if in_wrist_view("the black bowl on the left") > 0.4:
            return True
    return False

def main():
    start_x, start_y, start_z = gripper_position()
    found = search_bowl(start_x, start_y, start_z)
    
    success = False
    for attempt in range(2):
        for i in range(15):
            sx, sy = wrist_direction("the center of the black bowl on the left")
            if sx == 0 and sy == 0:
                break
            move_by(0.02 * sx, 0.02 * sy, 0)
        move_by(0, 0.06, 0)
        for i in range(12):
            if not move_by(0, 0, -0.03):
                break
        move_by(0, 0, 0.015)
        close_gripper()
        opening = gripper_opening()
        if opening > 0.003:
            success = True
            gx, gy, gz = gripper_position()
            move_to(gx, gy, start_z)
            break
        else:
            open_gripper()
            gx, gy, gz = gripper_position()
            move_to(gx, gy, start_z)
            move_by(0, -0.06, 0)
    
    for i in range(30):
        sx, sy = fixed_direction("the center of the tray")
        if sx == 0 and sy == 0:
            break
        move_by(0.02 * sx, 0.02 * sy, 0)
    
    move_by(0, 0.06, 0)
    
    for i in range(15):
        if not move_by(0, 0, -0.03):
            break
    
    open_gripper()
    gx, gy, gz = gripper_position()
    move_to(gx, gy, start_z)

main()
