Write a Python program that controls a robot arm in a simulator to do this task:
"pick up the black bowl on the left and put it in the tray"

The program runs once, from top to bottom. It cannot see the scene directly. It can only read the
robot's own state, move the robot, and ask a vision model simple questions about the current camera
images. No function returns the positions of objects.

## Coordinates
World frame in meters: +x is forward (away from the robot base), +y is the robot's left, +z is up.
The table is horizontal.

## Start
The gripper points straight down, the fingers are open, and the gripper is about 24 cm above the
table. Call this height the start height.

## Functions (already defined; do not import anything)
Robot state:
- gripper_position() -> (x, y, z): the gripper position in meters.
- gripper_opening() -> float: the distance between the fingers in meters (about 0.08 when open).
Motion (each call waits until the motion ends):
- move_by(dx, dy, dz) -> bool: move the gripper by (dx, dy, dz) meters, keeping it pointing down.
  Returns True if the gripper reached the target, and False if it did not (for example, when the
  table or an object blocks it). A downward move gives up after 2 seconds.
- move_to(x, y, z) -> bool: the same, to an absolute position.
- close_gripper(), open_gripper(): close or open the fingers.
Vision (each call asks the vision model about the current images; answers can be wrong):
- wrist_direction(target) -> (sx, sy): uses the wrist camera, which looks straight down from the
  gripper. A red cross on the image marks the point below the gripper. Returns the signs (-1, 0 or
  1) of the world x and y moves that bring the cross onto target. (0, 0) means the cross is already
  on target. target is a short English phrase, such as "the center of the tray".
- fixed_direction(target) -> (sx, sy): the same, using a fixed camera that looks down diagonally at
  the table. A yellow dot on the image marks the point on the table directly below the gripper.
- in_wrist_view(target) -> float: the probability that target is visible in the wrist camera image.
- check(question) -> float: the probability that the answer to a yes/no question about the fixed
  and wrist camera images is yes. Example: check("Is there a bowl in the tray?").
Also available: print, math, np (numpy).

## Facts about this robot and scene
- The fingers close along the world y axis.
- Grip the bowl by its rim. The rim to grip is 6 cm from the bowl center in +y.
- The red cross of wrist_direction is placed for the start height. Do horizontal alignment at the
  start height, then go down.
- To go down onto something, move down 3 cm at a time until move_by returns False.
- Before closing the fingers, move up 1.5 cm from where the downward move stopped.
- After close_gripper(), gripper_opening() greater than 0.003 means something is held. A smaller
  value means the grasp missed.
- While the bowl is held by its rim, the bowl center is 6 cm in -y from the gripper.
- Carry objects at the start height.

## Reliability of the vision answers (measured on this task)
- Each answer is a direction only, not a distance. Move about 2 cm per step and ask again after
  each step.
- wrist_direction is mostly correct when the target is visible in the wrist camera image.
- fixed_direction toward the tray is mostly correct while the gripper is more than about 12 cm from
  the tray center. Near the tray it often answers (0, 0). Toward a bowl it is often wrong.
- in_wrist_view sometimes answers high for the tray when the tray is not in the image.

## Limits
- At most 360 vision calls and 120 motion calls in total. The program is stopped when
  it goes over either limit.
- Answers can be wrong or flip back and forth. Make sure the program does not get stuck.

Output only the Python code, with no explanation.
