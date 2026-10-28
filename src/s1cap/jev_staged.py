"""Jev に画像の中の位置関係を問い、その答えから意図を選ばせる方策 (計画の C2 の 2 段の形)。

1 回の判断で Jev を 2 段で呼ぶ。

1. 知覚: 画像についての問い。次の 2 つのリクエストを並べて送る
   - 手首カメラ (180° 回し、手先の真下の点に赤い × を描く): × を掴むボウルの中心、トレイの中心に
     重ねるには、× を画像の左右と上下のどちらへ動かせばよいか (Choice)
   - 固定カメラ: トレイの中にボウルがあるか (Noul)
2. 意図: 知覚の答えとロボットの状態から決めた条件 (bool) を文にして渡し、意図を 1 つ選ばせる (Choice)。
   各意図の説明に、その意図を選ぶ条件を書く (OpenRoboto の incremental_policy と同じ形)

ボウルを掴んでいるかは、指を閉じた後の指の開きで決める。固定カメラの画像で Jev に問うと、
掴んで持ち上げている間も 0.02〜0.52 と揺れ、掴み損ねたとき (0.01〜0.04) と分けられなかった。

意図ごとの動きはコードで決める。画像の向きから世界座標の向きへの対応は固定で、180° 回した手首の
画像の右が世界座標の +y、下が +x にあたる。

手首カメラは手先の中心から前後にずれているので、手先の真下の点が画像に写る位置は高さで変わる。
横の位置合わせは開始の高さ (運ぶ高さ) で行い、× はその高さで掴む高さの点が写る位置に描く。
高さは問わず、3 cm ずつ下ろして、届かずに timeout で終わった所 (テーブルやトレイの底に当たった所) で止める。
ボウルの縁を寄せる先として問うと上下 (世界の x) の向きを答えないので、中心に揃えてから縁の方へ RIM_OFFSET だけずらす
(experiments/004-2-rim-probe)。掴んだボウルの中心は手先から -RIM_OFFSET の所にあるので、
トレイに下ろす前にも × をトレイの中心に揃えてから RIM_OFFSET だけずらし、ボウルの中心をトレイの中心に置く。

rim_target ("left" / "right") を与えると、中心に揃えた後に決まった距離ずらす代わりに、手首の画像で × を
その側の縁へ寄せる左右の向きだけを問い、none と答えるまで (最大 RIM_MAX_MOVES 歩) y に動かしてから下ろす。
掴む縁がボウルのどちら側かが変わるので、トレイに下ろす前のずらしもその側に合わせる。

camera_matrix (固定カメラの射影行列) を与えると、固定カメラの画像に手先の印 (s1cap.marks) を描き、
トレイが手首の画像に写っているかと、固定カメラの画像で黄色い点 (手先の真下のテーブルの点) をトレイの中心へ
寄せる向きも問う。運ぶ段の向きは carry_view で決める。

- "wrist": トレイが手首の画像に写っていれば手首の画像の答え、写っていなければ固定カメラの答えで決める
- "fixed": 固定カメラの答えで決め、黄色い点がトレイの上にある (左右も上下も none) と答えたら、手首の画像の答えで
  位置を合わせる。トレイから遠い所で Jev が「トレイが手首の画像に写っている」と誤って答えると、"wrist" では
  手首の画像と固定カメラの画像の答えが交互に使われ、手先が行き来した (experiments/005-staged-guide)
"""

from __future__ import annotations

from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
from typesafe_sdk import Choice, Noul, Question, TypeSafeClient

from s1cap import jev
from s1cap.jev_policy import WRIST_CAMERA, Decision, Observation, wrist_view
from s1cap.marks import FIXED_CAPTION as MARKED_FIXED_CAPTION
from s1cap.marks import fixed_direction, fixed_view

# 掴む縁はボウルの中心から +y (手首の画像の右) に 6 cm。ボウルの大きさから決めた値 (s1cap.scripted と同じ)
RIM_OFFSET = np.array([0.0, 0.06, 0.0])
# rim_target ごとの、縁の言い方と、ボウルの中心から見た縁の y の向き
RIM_TARGETS = {
    "left": ("the left edge of the bowl to pick up", -1.0),
    "right": ("the right edge of the bowl to pick up", 1.0),
}
# 縁へ寄せる歩数の上限。2 cm の歩幅で、中心から縁 (6 cm) を越えて 4 cm 先まで
RIM_MAX_MOVES = 5
# libero_90 60 の開始の高さで、掴む高さ (手先の 21.8 cm 下) の点が手首の画像に写る位置
CROSS_UV = (0.5, 0.40)
# 下向きの手先の姿勢 (xyzw)
TOP_DOWN = [1.0, 0.0, 0.0, 0.0]
# 掴む前に、当たって止まった所から上げる量。指先がテーブルに当たった高さで閉じるより持ち上がりやすい
GRASP_RISE = 0.015
# 指を閉じた後の開きがこれより大きければ、指の間に物がある。ボウルの縁を掴むと 0.004 m 以上、
# 掴み損ねると 0.001〜0.002 m
HELD_WIDTH = 0.003
CARRY_TOL = 0.01  # 開始の高さからこの範囲なら「運ぶ高さにある」とする
DEFAULT_FIXED_CAMERA = "quarterview"

WRIST_CAPTION = (
    "Wrist camera, looking straight down from the gripper. "
    "The red cross marks the point directly below the gripper:"
)
FIXED_CAPTION = "Fixed camera, looking down diagonally at the table:"

TARGETS = {
    "bowl": "the center of the bowl to pick up",
    "tray": "the center of the tray",
}
# 手首の画像での向き -> 世界座標の単位ベクトル
IMAGE_TO_WORLD = {
    "left": np.array([0.0, -1.0, 0.0]),
    "right": np.array([0.0, 1.0, 0.0]),
    "up": np.array([-1.0, 0.0, 0.0]),
    "down": np.array([1.0, 0.0, 0.0]),
    "none": np.zeros(3),
}

INTENTS = {
    "approach": (
        "move the gripper horizontally toward the bowl. Choose when fingers_closed is false, "
        "bowl_held is false, at_carry_height is true, and cross_on_bowl is false"
    ),
    "descend": (
        "move the open gripper down onto the rim of the bowl. Choose when fingers_closed is false "
        "and bowl_held is false, and either at_carry_height and cross_on_bowl are both true, "
        "or previous_intent is descend and last_move is 'down reached'"
    ),
    "grasp": (
        "close the fingers on the rim of the bowl. Choose when fingers_closed is false, "
        "previous_intent is descend, and last_move is 'down blocked'. Do not close early"
    ),
    "lift": (
        "raise the gripper to the carrying height. Choose when fingers_closed is true "
        "and previous_intent is grasp"
    ),
    "retry": (
        "open the fingers to try again. Choose when fingers_closed is true, at_carry_height is true, "
        "and bowl_held is false (the grasp missed)"
    ),
    "carry": (
        "move the held bowl horizontally toward the tray. Choose when fingers_closed is true, "
        "bowl_held is true, at_carry_height is true, and cross_on_tray is false"
    ),
    "lower": (
        "move the held bowl down into the tray. Choose when fingers_closed is true and "
        "bowl_held is true, and either at_carry_height and cross_on_tray are both true, "
        "or previous_intent is lower and last_move is 'down reached'"
    ),
    "release": (
        "open the fingers and move up. Choose when fingers_closed is true, previous_intent is lower, "
        "and last_move is 'down blocked'"
    ),
    "finish": (
        "the task is done. Choose when fingers_closed is false and bowl_in_tray is true"
    ),
}


def wrist_questions(instruction: str) -> dict[str, Question]:
    qs: dict[str, Question] = {}
    for name, what in TARGETS.items():
        for axis, (a, b) in {"h": ("left", "right"), "v": ("up", "down")}.items():
            word = "horizontally" if axis == "h" else "vertically"
            qs[f"{name}_{axis}"] = Choice(
                instructions=(
                    f"Task: {instruction}. In the wrist camera image, to move the red cross "
                    f"onto {what}, which way should it move {word}?"
                ),
                criteria={
                    a: None,
                    "none": f"the red cross is already {word} at {what}",
                    b: None,
                },
            )
    return qs


def rim_question(instruction: str, what: str) -> dict[str, Question]:
    return {
        "rim_h": Choice(
            instructions=(
                f"Task: {instruction}. In the wrist camera image, to move the red cross "
                f"onto {what}, which way should it move horizontally?"
            ),
            criteria={
                "left": None,
                "none": f"the red cross is already horizontally at {what}",
                "right": None,
            },
        )
    }


def fixed_questions(instruction: str) -> dict[str, Question]:
    return {
        # 「the bowl to pick up」と書くと、トレイに置いた後も 0.04〜0.12 と答えた
        "bowl_in_tray": Noul(
            instructions=(
                f"Task: {instruction}. In the fixed camera image, is there any bowl in the tray?"
            ),
        ),
    }


def marked_questions(
    instruction: str,
) -> tuple[dict[str, Question], dict[str, Question]]:
    """固定カメラの印を使うときに足す問い (手首の画像への問い、固定カメラの画像への問い)。"""
    wrist = {
        "tray_in_wrist": Noul(
            instructions=(
                f"Task: {instruction}. Is the tray visible in the wrist camera image?"
            ),
        ),
    }
    fixed: dict[str, Question] = {}
    for axis, (a, b) in {"h": ("left", "right"), "v": ("up", "down")}.items():
        word = "horizontally" if axis == "h" else "vertically"
        fixed[f"tray_fixed_{axis}"] = Choice(
            instructions=(
                f"Task: {instruction}. In the fixed camera image, to move the yellow dot "
                f"onto {TARGETS['tray']}, which way should it move {word}?"
            ),
            criteria={
                a: None,
                "none": f"the yellow dot is already {word} at {TARGETS['tray']}",
                b: None,
            },
        )
    return wrist, fixed


def intent_question(instruction: str) -> dict[str, Question]:
    return {
        "intent": Choice(
            instructions=(
                f"Task: {instruction}. The robot does the task in phases. "
                "Using the conditions in the state, which phase should the robot do next?"
            ),
            criteria=INTENTS,
        )
    }


class JevStagedPolicy:
    def __init__(
        self,
        client: TypeSafeClient,
        instruction: str,
        *,
        fixed_camera: str = DEFAULT_FIXED_CAMERA,
        step_m: float = 0.02,
        down_m: float = 0.03,
        down_timeout_steps: int = 40,
        noul_threshold: float = 0.5,
        camera_matrix: np.ndarray | None = None,
        carry_view: str = "wrist",
        rim_target: str | None = None,
    ) -> None:
        self.client = client
        self.instruction = instruction
        self.fixed_camera = fixed_camera
        self.step_m = step_m
        self.down_m = down_m
        self.down_timeout_steps = down_timeout_steps
        self.noul_threshold = noul_threshold
        self.wrist_questions = wrist_questions(instruction)
        self.fixed_questions = fixed_questions(instruction)
        self.intent_question = intent_question(instruction)
        self.camera_matrix = camera_matrix
        self.carry_view = carry_view
        if camera_matrix is not None:
            extra_wrist, extra_fixed = marked_questions(instruction)
            self.wrist_questions |= extra_wrist
            self.fixed_questions |= extra_fixed
        self.rim_target = rim_target
        self.rim_question: dict[str, Question] = {}
        self.rim_offset = RIM_OFFSET  # 掴む縁から見たボウルの中心は -rim_offset の所
        if rim_target is not None:
            what, side = RIM_TARGETS[rim_target]
            self.rim_question = rim_question(instruction, what)
            self.rim_offset = RIM_OFFSET * side
        self.rim_moves: int | None = (
            None  # 縁へ寄せている間の歩数。寄せていなければ None
        )
        self.carry_z: float | None = None  # 開始の高さ。最初の観測で決める
        self.fingers_closed = (
            False  # 最後に送った指の命令。sim は reset 直後に指を開いている
        )
        self.previous_intent = "none"
        self.last_move = "none"
        self.queue: deque[dict[str, Any]] = deque()  # 1 つの意図で続けて送る命令
        self._next_id = 1
        self._pool = ThreadPoolExecutor(max_workers=2)

    def decide(self, obs: Observation) -> Decision:
        eef = np.asarray(obs.robot_state["eef"]["pos"])
        if self.carry_z is None:
            # 手首の画像の × の位置は、手先が下を向いている前提で測った
            self.carry_z = float(eef[2])
            return Decision(
                self._new({"type": "move_to", "pos": eef.tolist(), "quat": TOP_DOWN}),
                {"obs_step": obs.step, "intent": "setup"},
            )
        if self.queue:
            return Decision(
                self._new(self.queue.popleft()),
                {"obs_step": obs.step, "intent": self.previous_intent, "queued": True},
            )
        if self.rim_moves is not None:
            command, rim = self._rim_step(obs)
            command = self._new(command)
            record = {"obs_step": obs.step, "intent": self.previous_intent, "rim": rim}
            return Decision(command, record | {"command": command})

        perception, latency_p, calls = self._perceive(obs, eef)
        conditions = self._conditions(eef, obs.robot_state["gripper_width"], perception)
        response, latency_i = jev.ask(
            self.client, self._intent_state(conditions), self.intent_question
        )
        intent = response.choices["intent"].choice
        record = {
            "obs_step": obs.step,
            "latency_ms": {"perception": round(latency_p), "intent": round(latency_i)},
            "calls": {**calls, "intent": jev.call_record(response, latency_i)},
            "perception": perception,
            "conditions": conditions,
            "intent": intent,
            "intent_probabilities": {
                k: round(v, 3)
                for k, v in response.choices["intent"].probabilities.items()
            },
        }
        commands = self._commands(intent, eef, perception)
        if intent == "descend" and self.rim_target and self.previous_intent != intent:
            # 決まった距離ずらす代わりに、縁へ寄せる。寄せ終えたら下ろす
            self.rim_moves = 0
            command, record["rim"] = self._rim_step(obs)
            commands = [command]
        self.previous_intent = intent
        if not commands:
            return Decision(None, record)
        self.queue.extend(commands[1:])
        command = self._new(commands[0])
        record["command"] = command
        return Decision(command, record)

    def on_result(self, result: dict[str, Any], command: dict[str, Any]) -> None:
        if command["type"] == "move_delta" and command["dpos"][2] < 0:
            reached = result["status"] == "reached"
            self.last_move = "down reached" if reached else "down blocked"
        elif command["type"] in ("move_delta", "move_to"):
            self.last_move = f"move {result['status']}"

    def _perceive(
        self, obs: Observation, eef: np.ndarray
    ) -> tuple[dict[str, Any], float, dict[str, dict[str, Any]]]:
        wrist = wrist_view(obs.images[WRIST_CAMERA], CROSS_UV)
        wrist_state = [
            f"Task: {self.instruction}",
            WRIST_CAPTION,
            jev.image_content(wrist),
        ]
        fixed = obs.images[self.fixed_camera]
        caption = FIXED_CAPTION
        if self.camera_matrix is not None:
            fixed = fixed_view(fixed, self.camera_matrix, eef)
            caption = MARKED_FIXED_CAPTION
        fixed_state = [f"Task: {self.instruction}", caption, jev.image_content(fixed)]
        wrist_job = self._pool.submit(
            jev.ask, self.client, wrist_state, self.wrist_questions
        )
        fixed_job = self._pool.submit(
            jev.ask, self.client, fixed_state, self.fixed_questions
        )
        (w, w_ms), (f, f_ms) = wrist_job.result(), fixed_job.result()
        perception: dict[str, Any] = {}
        for response in (w, f):
            perception.update({name: a.choice for name, a in response.choices.items()})
            perception.update(
                {name: round(a.noul, 3) for name, a in response.nouls.items()}
            )
        calls = {"wrist": jev.call_record(w, w_ms), "fixed": jev.call_record(f, f_ms)}
        return perception, max(w_ms, f_ms), calls

    def _rim_step(self, obs: Observation) -> tuple[dict[str, Any], dict[str, Any]]:
        """× を縁へ寄せる左右の向きを問い、y に 1 歩動く命令か、寄せ終えたら下ろす命令を返す。"""
        assert self.rim_moves is not None
        wrist = wrist_view(obs.images[WRIST_CAMERA], CROSS_UV)
        state = [f"Task: {self.instruction}", WRIST_CAPTION, jev.image_content(wrist)]
        response, latency = jev.ask(self.client, state, self.rim_question)
        choice = response.choices["rim_h"].choice
        rim = {
            "rim_h": choice,
            "moves": self.rim_moves,
            "call": jev.call_record(response, latency),
        }
        if choice == "none" or self.rim_moves >= RIM_MAX_MOVES:
            self.rim_moves = None
            return self._down(), rim
        self.rim_moves += 1
        return {
            "type": "move_delta",
            "dpos": (IMAGE_TO_WORLD[choice] * self.step_m).tolist(),
        }, rim

    def _conditions(
        self, eef: np.ndarray, gripper_width: float, perception: dict[str, Any]
    ) -> dict[str, Any]:
        assert self.carry_z is not None
        return {
            "fingers_closed": self.fingers_closed,
            "at_carry_height": abs(float(eef[2]) - self.carry_z) < CARRY_TOL,
            "cross_on_bowl": perception["bowl_h"] == perception["bowl_v"] == "none",
            "cross_on_tray": self._tray_in_wrist(perception)
            and perception["tray_h"] == perception["tray_v"] == "none",
            "bowl_held": self.fingers_closed and gripper_width > HELD_WIDTH,
            "bowl_in_tray": perception["bowl_in_tray"] >= self.noul_threshold,
            "previous_intent": self.previous_intent,
            "last_move": self.last_move,
        }

    def _intent_state(self, conditions: dict[str, Any]) -> list[Any]:
        lines = [f"Task: {self.instruction}", "Conditions:"]
        lines += [
            f"- {name}: {str(v).lower() if isinstance(v, bool) else repr(v)}"
            for name, v in conditions.items()
        ]
        return ["\n".join(lines)]

    def _commands(
        self, intent: str, eef: np.ndarray, perception: dict[str, Any]
    ) -> list[dict[str, Any]]:
        assert self.carry_z is not None
        up_to_carry = [0.0, 0.0, self.carry_z - float(eef[2])]
        if intent == "carry" and self._carry_by_fixed(perception):
            assert self.camera_matrix is not None
            xy = fixed_direction(
                self.camera_matrix,
                eef,
                perception["tray_fixed_h"],
                perception["tray_fixed_v"],
            )
            if not xy.any():
                return [{"type": "hold"}]
            return [{"type": "move_delta", "dpos": [*(xy * self.step_m).tolist(), 0.0]}]
        if intent in ("approach", "carry"):
            target = "bowl" if intent == "approach" else "tray"
            d = IMAGE_TO_WORLD[perception[f"{target}_h"]]
            d = d + IMAGE_TO_WORLD[perception[f"{target}_v"]]
            if not d.any():
                return [{"type": "hold"}]
            return [{"type": "move_delta", "dpos": (d * self.step_m).tolist()}]
        if intent in ("descend", "lower"):
            down = self._down()
            if self.previous_intent != intent:
                return [{"type": "move_delta", "dpos": self.rim_offset.tolist()}, down]
            return [down]
        if intent == "grasp":
            self.fingers_closed = True
            return [
                {"type": "move_delta", "dpos": [0.0, 0.0, GRASP_RISE]},
                {"type": "gripper", "closed": True},
            ]
        if intent == "lift":
            return [{"type": "move_delta", "dpos": up_to_carry}]
        if intent in ("retry", "release"):
            self.fingers_closed = False
            return [
                {"type": "gripper", "closed": False},
                {"type": "move_delta", "dpos": up_to_carry},
            ]
        return []  # finish

    def _carry_by_fixed(self, perception: dict[str, Any]) -> bool:
        """運ぶ段の向きを固定カメラの画像の答えで決めるか。"""
        if self.camera_matrix is None:
            return False
        if self.carry_view == "fixed":
            return (
                not perception["tray_fixed_h"] == perception["tray_fixed_v"] == "none"
            )
        return not self._tray_in_wrist(perception)

    def _tray_in_wrist(self, perception: dict[str, Any]) -> bool:
        """トレイが手首の画像に写っているか。固定カメラの印を使わないときは、写っているとみなす。"""
        if self.camera_matrix is None:
            return True
        return perception["tray_in_wrist"] >= self.noul_threshold

    def _down(self) -> dict[str, Any]:
        return {
            "type": "move_delta",
            "dpos": [0.0, 0.0, -self.down_m],
            "timeout_steps": self.down_timeout_steps,
        }

    def _new(self, command: dict[str, Any]) -> dict[str, Any]:
        command = {"id": self._next_id, **command}
        self._next_id += 1
        return command
