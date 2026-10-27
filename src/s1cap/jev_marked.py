"""画像に手先の印を描き、Jev に画像の中の向きを問う方策 (実験 003、004)。

Jev に渡すのは、指示文、ロボット自身の状態 (指の開閉、テーブルからの手先の高さ)、印を描いた 2 枚の画像だけで、
物体の位置の真値は渡さない。

- 固定カメラ (quarterview) の画像: 手先の位置に赤い丸、手先の真下のテーブルの点に黄色い点を描き、線で結ぶ
  (s1cap.marks)
- 手首カメラの画像: 180° 回し、赤い × を描く (s1cap.jev_staged と同じ)

Jev には、手先の行き先へ印を寄せる向きを、画像の左右と上下で問う。手首の画像と固定カメラの画像の両方で問い、
行き先が手首の画像に写っているかも問う。写っていれば手首の画像の答えを、写っていなければ固定カメラの
画像の答えを使う。画像の向きから世界座標の向きへの変換はコードで行う。

- 手首の画像: 右が世界座標の +y、下が +x (s1cap.jev_staged.IMAGE_TO_WORLD)
- 固定カメラの画像: 射影行列から求める (s1cap.marks.fixed_direction)

高さ (下げる / そのまま / 上げる) と指 (開いた状態 / 閉じた状態) とタスクが終わったかも問う。

two_call が False なら 1 回の呼び出しで全部を問う (実験 003)。True なら先に意図を選ばせ、
その意図の行き先 (掴むボウルかトレイか) を問いの文に入れて、2 回目で動きを問う (実験 004)。
意図の選び方は Jev に任せ、コードで作った条件は渡さない。
"""

from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np
from typesafe_sdk import Choice, Noul, Question, TypeSafeClient

from s1cap import jev
from s1cap.jev_policy import WRIST_CAMERA, Decision, Observation, wrist_view
from s1cap.jev_staged import CROSS_UV, DEFAULT_FIXED_CAMERA, IMAGE_TO_WORLD, TOP_DOWN
from s1cap.marks import FIXED_CAPTION, TABLE_Z, fixed_direction, fixed_view

HISTORY = 5

WRIST_CAPTION = (
    "Wrist camera, looking straight down from the gripper. "
    "The red cross marks the point below the gripper, at the height of objects on the table:"
)
DEFAULT_TARGET = "the place where the gripper should go next to do the task"

INTENTS = {
    "approach": "move the open gripper horizontally until it is right above the bowl to pick up",
    "descend": "move the open gripper down to the rim of the bowl to pick up",
    "grasp": "close the fingers on the rim of the bowl",
    "lift": "raise the held bowl up from the table",
    "carry": "move the held bowl horizontally until it is right above the tray",
    "lower": "move the held bowl down into the tray",
    "release": "open the fingers to put the bowl in the tray",
    "finish": "the bowl is in the tray and the fingers are open; the task is done",
}
# 意図ごとの行き先。行き先の無い意図では、向きの問いの答えを使わない
INTENT_TARGETS = {
    "approach": "the bowl to pick up",
    "descend": "the bowl to pick up",
    "carry": "the tray",
    "lower": "the tray",
}


def move_questions(instruction: str, target: str) -> dict[str, Question]:
    qs: dict[str, Question] = {
        "target_in_wrist": Noul(
            instructions=(
                f"Task: {instruction}. Is {target} visible in the wrist camera image?"
            ),
        ),
    }
    for image, mark in (("wrist", "the red cross"), ("fixed", "the yellow dot")):
        name = "wrist camera" if image == "wrist" else "fixed camera"
        for axis, (a, b) in {"h": ("left", "right"), "v": ("up", "down")}.items():
            word = "horizontally" if axis == "h" else "vertically"
            qs[f"{image}_{axis}"] = Choice(
                instructions=(
                    f"Task: {instruction}. In the {name} image, to move {mark} onto "
                    f"{target}, which way should it move {word}?"
                ),
                criteria={
                    a: None,
                    "none": f"{mark} is already {word} at {target}",
                    b: None,
                },
            )
    qs["height"] = Choice(
        instructions=(
            f"Task: {instruction}. Should the gripper move down toward the table, "
            "stay at its height, or move up in the next step?"
        ),
        criteria={"down": None, "stay": None, "up": None},
    )
    qs["gripper"] = Choice(
        instructions=(
            f"Task: {instruction}. Should the fingers be open or closed after the next step?"
        ),
        criteria={
            "open": (
                "no object is between the fingers yet, "
                "or the held object has reached where it should be put"
            ),
            "closed": (
                "the object to pick up is between the fingers, "
                "or it is held and has not reached where it should be put"
            ),
        },
    )
    qs["done"] = Noul(
        instructions=f"Task: {instruction}. Is the task complete?",
        criteria={
            "true": "the goal of the task is achieved and the robot has let go",
            "false": "the goal of the task is not achieved yet",
        },
    )
    return qs


def intent_question(instruction: str) -> dict[str, Question]:
    return {
        "intent": Choice(
            instructions=(
                f"Task: {instruction}. The robot does the task in phases. "
                "Looking at the images and the robot state, which phase should the robot do next?"
            ),
            criteria=INTENTS,
        )
    }


class JevMarkedPolicy:
    def __init__(
        self,
        client: TypeSafeClient,
        instruction: str,
        camera_matrix: np.ndarray,
        *,
        fixed_camera: str = DEFAULT_FIXED_CAMERA,
        two_call: bool = False,
        step_m: float = 0.02,
        down_timeout_steps: int = 40,
        gripper_threshold: float = 0.7,
        done_threshold: float = 0.8,
        visible_threshold: float = 0.5,
    ) -> None:
        self.client = client
        self.instruction = instruction
        self.matrix = camera_matrix
        self.fixed_camera = fixed_camera
        self.two_call = two_call
        self.step_m = step_m
        self.down_timeout_steps = down_timeout_steps
        self.gripper_threshold = gripper_threshold
        self.done_threshold = done_threshold
        self.visible_threshold = visible_threshold
        self.started = False
        self.gripper_closed = (
            False  # 最後に送った指の命令。sim は reset 直後に指を開いている
        )
        self.history: deque[str] = deque(maxlen=HISTORY)
        self._next_id = 1

    def state(self, obs: Observation) -> list[Any]:
        robot = obs.robot_state
        eef = np.asarray(robot["eef"]["pos"])
        lines = [
            f"Task: {self.instruction}",
            (
                f"Robot state: fingers {'closed' if self.gripper_closed else 'open'} "
                f"(opening {robot['gripper_width'] * 100:.1f} cm; 8 cm fully open), "
                f"gripper {(eef[2] - TABLE_Z) * 100:.0f} cm above the table."
            ),
        ]
        if self.history:
            lines.append("Previous steps (oldest first): " + "; ".join(self.history))
        return [
            "\n".join(lines),
            FIXED_CAPTION,
            jev.image_content(
                fixed_view(obs.images[self.fixed_camera], self.matrix, eef)
            ),
            WRIST_CAPTION,
            jev.image_content(wrist_view(obs.images[WRIST_CAMERA], CROSS_UV)),
        ]

    def decide(self, obs: Observation) -> Decision:
        if not self.started:
            # 手先を下向きにそろえる。Jev は呼ばない
            self.started = True
            return Decision(
                self._new(
                    {
                        "type": "move_to",
                        "pos": obs.robot_state["eef"]["pos"],
                        "quat": TOP_DOWN,
                    }
                ),
                {"obs_step": obs.step, "intent": "setup"},
            )
        state = self.state(obs)
        record: dict[str, Any] = {"obs_step": obs.step, "latency_ms": {}, "calls": {}}
        target = DEFAULT_TARGET
        if self.two_call:
            answer, ms = jev.ask(self.client, state, intent_question(self.instruction))
            intent = answer.choices["intent"].choice
            record["latency_ms"]["intent"] = round(ms)
            record["calls"]["intent"] = jev.call_record(answer, ms)
            record["intent"] = intent
            record["intent_probabilities"] = {
                k: round(v, 3)
                for k, v in answer.choices["intent"].probabilities.items()
            }
            if intent == "finish":
                return Decision(None, record)
            target = INTENT_TARGETS.get(intent, target)
            state = [*state, f"Current phase: {intent} ({INTENTS[intent]})."]
        answer, ms = jev.ask(
            self.client, state, move_questions(self.instruction, target)
        )
        record["latency_ms"]["move"] = round(ms)
        record["calls"]["move"] = jev.call_record(answer, ms)
        choices = {name: a.choice for name, a in answer.choices.items()}
        nouls = {name: round(a.noul, 3) for name, a in answer.nouls.items()}
        record["choices"] = choices
        record["nouls"] = nouls
        record["gripper_probabilities"] = {
            k: round(v, 3) for k, v in answer.choices["gripper"].probabilities.items()
        }
        if nouls["done"] >= self.done_threshold:
            return Decision(None, record)
        command = self._command(
            choices,
            nouls,
            answer.choices["gripper"].probabilities,
            np.asarray(obs.robot_state["eef"]["pos"]),
            record,
        )
        record["command"] = command
        return Decision(command, record)

    def on_result(self, result: dict[str, Any], command: dict[str, Any]) -> None:
        """命令の結果を、次の判断の state に入れる履歴に足す。"""
        if command["type"] == "gripper":
            action = "close fingers" if command["closed"] else "open fingers"
        elif command["type"] == "move_delta":
            dz = command["dpos"][2]
            action = "move" + (" down" if dz < 0 else " up" if dz > 0 else "")
        else:
            action = command["type"]
        status = {"reached": "done", "timeout": "blocked"}.get(
            result["status"], result["status"]
        )
        self.history.append(f"{action} -> {status}")

    def _command(
        self,
        choices: dict[str, str],
        nouls: dict[str, float],
        gripper_probs: dict[str, float],
        eef: np.ndarray,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        closed = choices["gripper"] == "closed"
        if (
            closed != self.gripper_closed
            and gripper_probs[choices["gripper"]] >= self.gripper_threshold
        ):
            self.gripper_closed = closed
            return self._new({"type": "gripper", "closed": closed})
        intent = record.get("intent")
        xy = np.zeros(2)
        if intent is None or intent in INTENT_TARGETS:
            if nouls["target_in_wrist"] >= self.visible_threshold:
                record["xy_from"] = "wrist"
                d = (
                    IMAGE_TO_WORLD[choices["wrist_h"]]
                    + IMAGE_TO_WORLD[choices["wrist_v"]]
                )
                xy = d[:2]
            else:
                record["xy_from"] = "fixed"
                xy = fixed_direction(
                    self.matrix, eef, choices["fixed_h"], choices["fixed_v"]
                )
        dz = {"down": -1.0, "stay": 0.0, "up": 1.0}[choices["height"]]
        dpos = np.r_[xy, dz] * self.step_m
        if not dpos.any():
            return self._new({"type": "hold"})
        command: dict[str, Any] = {"type": "move_delta", "dpos": dpos.tolist()}
        if dz < 0:
            # 下げる命令は、当たって動けなくなったら timeout で止める
            command["timeout_steps"] = self.down_timeout_steps
        return self._new(command)

    def _new(self, command: dict[str, Any]) -> dict[str, Any]:
        command = {"id": self._next_id, **command}
        self._next_id += 1
        return command
