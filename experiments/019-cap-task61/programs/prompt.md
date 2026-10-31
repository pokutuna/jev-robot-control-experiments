Write a Python program that controls a robot arm in a simulator to do this task:
"pick up the chocolate pudding and put it in the tray"

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
- The fingers close along the world y axis and open to about 8 cm.
- The wrist camera image is turned so that its right is +y and its bottom is +x.
- The red cross of wrist_direction is placed for the start height. Do horizontal alignment at the
  start height, then go down.
- To go down onto something, move down 3 cm at a time until move_by returns False.
- After close_gripper(), gripper_opening() greater than 0.003 means something is held. A smaller
  value means the grasp missed.
- Carry objects at the start height.
- Objects in this scene (x size, y size, height): chocolate pudding box 8.0 x 4.6 x 2.7 cm, salad
  dressing bottle 3.6 x 5.3 x 14.6 cm, black bowls 10.7 cm across and 5.1 cm high, wooden tray
  29.7 x 16.7 cm.

## Reliability of the vision answers (measured on this task)
Measured with the gripper at the start height, 0 to 6 cm from the object (wrist_direction) or 4 to
6 cm (fixed_direction), with still images:
- Each answer is a direction only, not a distance. Move about 2 cm per step and ask again after
  each step.
- wrist_direction never answered away from the target on y with the phrases below. On x it often
  answered 0 even when the cross was 4 cm away.
- Pudding box, wrist_direction, y toward the box when 2 cm or more away / 0 when within 1 cm:
  "the chocolate pudding box" 93% / 87%, "the box" 93% / 100%,
  "the center of the chocolate pudding box" 100% / 53%.
- Dressing bottle: "the bottle" 91% / 100%, "the salad dressing" 88% / 73% and 21% away on x.
- Left black bowl (task 60): "the center of the bowl to pick up" 83% / 100%. "the black bowl on the
  left" and "the left black bowl" answered 0 in most cases even when the cross was 4 cm away.
- fixed_direction answered (0, 0) in about 90% of cases when the gripper was 4 to 6 cm from the
  pudding box. Use it only to come near; finish with wrist_direction.
- fixed_direction toward the tray is mostly correct while the gripper is more than about 12 cm from
  the tray center. Near the tray it often answers (0, 0).
Grasp trials (go down from the start height until blocked, move up 1.5 cm, close, lift):
- Pudding box: held in 73 of 75 trials when the gripper was 1 cm in -y to 1 cm in +y from the box
  center, and in 20 of 25 trials at 2 cm in -y. Failed at 3 cm in either direction, where a finger likely
  lands on the box. Offsets of up to 4 cm in x did not matter.
- Dressing bottle: the gripper cannot go below about 0.60 m (the table is at 0.437 m) at the
  bottle's x position, even where there is no object, so a top-down grasp lifted it in only 11 of
  175 trials.
- Black bowl: it is wider than the open fingers, so grip its rim. With the gripper 6 cm in -y
  from the bowl center, it held in 156 of 175 trials. Within 2 cm in x and 3 cm in y of that point
  it held in 102 of 105 trials. It failed at 4 cm in x combined with 2 to 3 cm further in -y,
  likely because the fingers miss the curved rim there.

## Limits
- At most 360 vision calls and 120 motion calls in total. The program is stopped when
  it goes over either limit.
- Answers can be wrong or flip back and forth. Make sure the program does not get stuck.

Output only the Python code, with no explanation.
