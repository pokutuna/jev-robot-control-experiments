"""物体の位置の真値を文で渡し、Jev に意図と軸ごとの向きを選ばせる方策 (実験 001、先行事例の再現)。

OpenRoboto の incremental_policy (https://github.com/openroboto-ai/jev-robot-control, 7a4ed8b) の
問いの形を、libero_90 60 (黒いボウルをトレイに入れる) に置き換えた。1 回の判断で Jev を 2 回呼ぶ。

1. 意図: 状態 (JSON) を渡し、approach、grasp、lift、carry、lower、release、withdraw、finish から選ばせる。
   各意図の説明に、その意図を選ぶ条件を書く
2. 動き: 意図を足した状態を渡し、x、y、z を別々の問いにして negative / hold / positive を選ばせ、
   指の open / hold / close も選ばせる。各軸の問いの文に、その軸の今の座標、目標の座標、目標 − 今の差 [mm] を書く

状態の位置、目標、位置合わせの真偽は、どれも真値からコードで作る。Jev が決めるのは意図と、軸ごとの向きと、指である。
1 歩の大きさは、OpenRoboto と同じく目標までの距離からコードが決める (向きは変えない)。
指を開閉するときは移動を送らず、指の命令だけを送る。指が閉じきる前に次の判断をしないため。
"""

from __future__ import annotations

from typing import Any

import numpy as np
from typesafe_sdk import Choice, Question, TypeSafeClient

from s1cap import jev
from s1cap.jev_policy import Decision, Observation

BOWL = "akita_black_bowl_1"
TRAY = "wooden_tray_1"
# ボウルの +y 側の縁を掴む手先の位置 (ボウルの中心から)。s1cap.scripted と同じ
GRASP_OFFSET = np.array([0.0, 0.06, 0.03])
# 離す手先の位置 (トレイの中心から)。ボウルの中心がトレイの中心の上に来る
RELEASE_OFFSET = np.array([0.0, 0.06, 0.06])
TRAVEL_ABOVE_GRASP = 0.15  # 運ぶ高さ (掴む高さから)
TOP_DOWN = [1.0, 0.0, 0.0, 0.0]
HELD_WIDTH = (
    0.003  # 指を閉じた後の開きがこれより大きければ掴んでいる (s1cap.jev_staged と同じ)
)
# 位置合わせの許容幅 [m]。sim の制御器が届いたとみなす幅 (0.005 m) より広くする
ALIGN_TOL = 0.008
# 目標までの距離ごとの 1 歩の大きさ [m]。OpenRoboto の (0.012 未満 2 mm、0.025 未満 4 mm、それ以上 18 mm) を、
# この制御器が届いたとみなす幅に合わせて大きくした
NEAR, MID = 0.012, 0.025
STEP_NEAR, STEP_MID, STEP_FAR = 0.004, 0.008, 0.02
MOVE_TOL = 0.002  # 1 歩の命令が届いたとみなす幅

INTENTS = {
    "approach": (
        "Bowl not held and not already released in the tray. Open the gripper and align with the "
        "bowl grasp pose. Descend only after XY alignment."
    ),
    "grasp": (
        "Bowl not held, gripper open, AND alignment.grasp_pose_reached is TRUE. Hold all XYZ and "
        "close the fingers. Do not close early above the bowl."
    ),
    "lift": (
        "Bowl held, away from the tray, and at_travel_height is FALSE. Keep fingers closed and lift "
        "vertically to travel height before moving sideways."
    ),
    "carry": (
        "Bowl held, at_travel_height is TRUE, and over_tray is FALSE. Carry horizontally above the "
        "release pose with fingers closed."
    ),
    "lower": (
        "Bowl held AND alignment.over_tray is TRUE AND at_release_height is FALSE. Lower vertically "
        "with fingers closed. Never lower when away from the tray."
    ),
    "release": (
        "Bowl held AND alignment.over_tray is TRUE AND alignment.at_release_height is TRUE. Open the "
        "fingers; hold XYZ. Never release away from the tray."
    ),
    "withdraw": (
        "Bowl already released inside the tray, gripper open, at_travel_height is FALSE. Raise the "
        "open gripper vertically without regrasping."
    ),
    "finish": (
        "Bowl released in the tray, gripper open, and at_travel_height is TRUE. "
        "The task is physically complete."
    ),
}

INTENT_INSTRUCTIONS = """Choose the next immediate INTENT for this robot from the actual current geometry.
There is one bowl to pick up and one tray. A held bowl has a closed gripper command and a finger width above 3 mm; closed fingers alone do not imply held.
Use the option conditions. They define a feedback policy, not an obligation to stay in the previous intent.
The alignment fields are measured geometric checks, not previous commands. If grasp_pose_reached is false and the bowl is not held, APPROACH rather than GRASP. If the gripper is closed but the bowl is not held, APPROACH (it opens the gripper). If over_tray is false, do not LOWER or RELEASE.
When the bowl is already released in the tray, withdraw then finish; do not approach or regrasp it.
After a grasp, lift at the source, carry at travel height, then lower at the tray.
When held AND already aligned over the tray, lower/release takes priority over lifting back to travel height.
Relative errors are desired position MINUS current TCP, in millimetres. Conditions use absolute magnitudes.
No teleportation or complete pick/place skill exists. Each update only executes a small Cartesian increment."""

MOTOR_INSTRUCTIONS = """Choose the next small motor increment for the given intent and current geometry.
Axis labels refer to the robot base frame. positive increases that coordinate; negative decreases it; hold leaves it unchanged.
Read the signed target-minus-TCP errors. A positive error requires positive motion; a negative error requires negative motion. Within 5 mm of the target, hold that axis.
APPROACH: open fingers; correct X and Y using bowl_grasp_minus_tcp_mm. If either XY error exceeds 8 mm, HOLD Z; once aligned, correct Z toward grasp_tcp.
GRASP: HOLD all XYZ and CLOSE fingers.
LIFT: HOLD X/Y, keep fingers CLOSED, increase Z to travel_tcp_z_mm.
CARRY: keep fingers CLOSED, correct X/Y toward release_tcp_mm; maintain Z at travel_tcp_z_mm.
LOWER: keep fingers CLOSED, correct X/Y toward release_tcp_mm if necessary; decrease Z toward release_tcp_mm[2].
RELEASE: HOLD XYZ and OPEN fingers.
WITHDRAW: HOLD X/Y, keep fingers OPEN, raise Z to travel height.
FINISH: HOLD all XYZ and keep fingers OPEN.
The motion must follow the selected intent. Do not keep descending once the grasp or release height is reached."""

DIRECTION = {"negative": -1.0, "hold": 0.0, "positive": 1.0}


def intent_question() -> dict[str, Question]:
    return {"intent": Choice(instructions=INTENT_INSTRUCTIONS, criteria=INTENTS)}


def motor_questions(state: dict[str, Any], intent: str) -> dict[str, Question]:
    qs: dict[str, Question] = {}
    for i, axis in enumerate("xyz"):
        a = axis.upper()
        instructions = (
            f"{MOTOR_INSTRUCTIONS}\nCURRENT INTENT: {intent.upper()}. "
            f"This question controls ONLY {a}. "
            f"Current {a}={state['tcp_mm'][i]} mm. "
            f"Bowl grasp {a}={state['grasp_tcp_mm'][i]} mm. "
            f"Bowl grasp minus current on this axis={state['bowl_grasp_minus_tcp_mm'][i]} mm. "
            f"Tray release {a}={state['release_tcp_mm'][i]} mm. "
            f"Tray release minus current on this axis={state['tray_release_minus_tcp_mm'][i]} mm. "
            "Use ONLY this axis for this answer; do not answer for another axis."
        )
        qs[axis] = Choice(
            instructions=instructions,
            criteria={
                "negative": (
                    f"Move {a} toward a SMALLER coordinate. Correct when the relevant target {a} is "
                    f"below current {a} beyond tolerance, and intent permits motion on this axis."
                ),
                "hold": (
                    f"Do not move {a}. Correct if intent requires holding this axis or relevant "
                    "target error is within tolerance."
                ),
                "positive": (
                    f"Move {a} toward a LARGER coordinate. Correct when the relevant target {a} is "
                    f"above current {a} beyond tolerance, and intent permits motion on this axis."
                ),
            },
        )
    qs["gripper"] = Choice(
        instructions=f"{MOTOR_INSTRUCTIONS}\nCURRENT INTENT: {intent.upper()}. Decide only the gripper.",
        criteria={
            "open": "Open the fingers.",
            "hold": "Keep the current finger command.",
            "close": "Close the fingers.",
        },
    )
    return qs


def _mm(v: np.ndarray) -> list[float]:
    return (np.asarray(v) * 1000).round(1).tolist()


class JevTextPolicy:
    def __init__(self, client: TypeSafeClient, instruction: str) -> None:
        self.client = client
        self.instruction = instruction
        self.started = False
        self.fingers_closed = (
            False  # 最後に送った指の命令。sim は reset 直後に指を開いている
        )
        self.previous_intent = "none"
        self.feedback = "none"
        self.travel_z: float | None = None
        self._next_id = 1

    def state(self, obs: Observation) -> dict[str, Any]:
        """OpenRoboto の observe にならい、真値から状態を作る。"""
        assert obs.objects is not None
        tcp = np.asarray(obs.robot_state["eef"]["pos"])
        bowl = np.asarray(obs.objects[BOWL]["pos"])
        tray = np.asarray(obs.objects[TRAY]["pos"])
        grasp = bowl + GRASP_OFFSET
        release = tray + RELEASE_OFFSET
        if self.travel_z is None:
            self.travel_z = float(grasp[2] + TRAVEL_ABOVE_GRASP)
        width = float(obs.robot_state["gripper_width"])
        held = self.fingers_closed and width > HELD_WIDTH
        # ボウルの中心がトレイの中心から横に 7 cm 以内で、トレイより 5 cm 以上は上にない
        in_tray = bool(
            np.linalg.norm(bowl[:2] - tray[:2]) < 0.07 and bowl[2] < tray[2] + 0.05
        )
        return {
            "task": self.instruction,
            "source": "LIBERO simulator ground-truth object positions, not camera vision",
            "units": "millimetres; robot base coordinates; +Z is up",
            "tcp_mm": _mm(tcp),
            "bowl_mm": _mm(bowl),
            "grasp_tcp_mm": _mm(grasp),
            "tray_center_mm": _mm(tray),
            "release_tcp_mm": _mm(release),
            "bowl_grasp_minus_tcp_mm": _mm(grasp - tcp),
            "tray_release_minus_tcp_mm": _mm(release - tcp),
            "alignment": {
                "grasp_x_error_mm": round(float(grasp[0] - tcp[0]) * 1000, 1),
                "grasp_y_error_mm": round(float(grasp[1] - tcp[1]) * 1000, 1),
                "grasp_z_error_mm": round(float(grasp[2] - tcp[2]) * 1000, 1),
                "grasp_pose_reached": bool(np.all(np.abs(grasp - tcp) <= ALIGN_TOL)),
                "over_tray": bool(np.all(np.abs(release[:2] - tcp[:2]) <= ALIGN_TOL)),
                "at_travel_height": bool(tcp[2] >= self.travel_z - ALIGN_TOL),
                "at_release_height": bool(abs(release[2] - tcp[2]) <= ALIGN_TOL),
            },
            "travel_tcp_z_mm": round(self.travel_z * 1000, 1),
            "gripper_command": "closed" if self.fingers_closed else "open",
            "finger_width_mm": round(width * 1000, 1),
            "held": held,
            "bowl_in_tray": in_tray,
            "previous_intent": self.previous_intent,
            "feedback": self.feedback,
        }

    def decide(self, obs: Observation) -> Decision:
        if not self.started:
            # 手先を下向きにそろえる。Jev は呼ばない
            self.started = True
            eef = obs.robot_state["eef"]["pos"]
            return Decision(
                self._new({"type": "move_to", "pos": eef, "quat": TOP_DOWN}),
                {"obs_step": obs.step, "intent": "setup"},
            )
        state = self.state(obs)
        intent_answer, intent_ms = jev.ask(self.client, state, intent_question())
        intent = intent_answer.choices["intent"].choice
        motor_state = {**state, "selected_intent": intent}
        motor, motor_ms = jev.ask(
            self.client, motor_state, motor_questions(state, intent)
        )
        choices = {name: a.choice for name, a in motor.choices.items()}
        record = {
            "obs_step": obs.step,
            "latency_ms": {"intent": round(intent_ms), "motor": round(motor_ms)},
            "calls": {
                "intent": jev.call_record(intent_answer, intent_ms),
                "motor": jev.call_record(motor, motor_ms),
            },
            "state": state,
            "intent": intent,
            "intent_probabilities": {
                k: round(v, 3)
                for k, v in intent_answer.choices["intent"].probabilities.items()
            },
            "motor": choices,
        }
        self.previous_intent = intent
        if intent == "finish":
            return Decision(None, record)
        command = self._command(choices, intent, obs, state)
        record["command"] = command
        return Decision(command, record)

    def on_result(self, result: dict[str, Any], command: dict[str, Any]) -> None:
        self.feedback = f"{command['type']} {result['status']}"

    def _command(
        self,
        choices: dict[str, str],
        intent: str,
        obs: Observation,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        grip = choices["gripper"]
        if grip != "hold" and (grip == "close") != self.fingers_closed:
            self.fingers_closed = grip == "close"
            return self._new({"type": "gripper", "closed": self.fingers_closed})
        signs = np.array([DIRECTION[choices[a]] for a in "xyz"])
        if not signs.any():
            return self._new({"type": "hold"})
        # 1 歩の大きさは、意図の目標までの距離で決める (OpenRoboto の increment と同じ)
        tcp = np.asarray(obs.robot_state["eef"]["pos"])
        assert self.travel_z is not None
        if intent in ("carry", "lower", "release"):
            reference = np.asarray(state["release_tcp_mm"]) / 1000
            if intent == "carry":
                reference[2] = self.travel_z
        elif intent in ("lift", "withdraw"):
            reference = np.r_[tcp[:2], self.travel_z]
        else:
            reference = np.asarray(state["grasp_tcp_mm"]) / 1000
        distance = np.abs(reference - tcp)
        sizes = np.where(
            distance < NEAR, STEP_NEAR, np.where(distance < MID, STEP_MID, STEP_FAR)
        )
        return self._new(
            {"type": "move_delta", "dpos": (signs * sizes).tolist(), "tol": MOVE_TOL}
        )

    def _new(self, command: dict[str, Any]) -> dict[str, Any]:
        command = {"id": self._next_id, **command}
        self._next_id += 1
        return command
