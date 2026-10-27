"""シミュレータのロボットを、実機のロボットドライバと同じ形で動かす。

ドライバは制御器 (`PoseController`) を持ち、外から step を進めるたびに、制御器の目標へ向かう
action を 1 つ送る。命令は制御器の目標を書き換えるだけで、命令が来ない間も最後の目標を保つ。

命令は JSON にできる dict で、ROS 2 の action のように、受け付けた後に完了・打ち切りの結果を返す。

    {"id": 1, "type": "move_to", "pos": [x, y, z], "quat": [x, y, z, w], "gripper": 1.0}
    {"id": 2, "type": "move_delta", "dpos": [dx, dy, dz]}
    {"id": 3, "type": "gripper", "closed": true}
    {"id": 4, "type": "hold"}

- move_to: 手先を pos へ動かす。quat と gripper は省略でき、省略すると今の目標の向きと最後の指の指令を保つ
- move_delta: 手先を今の位置から dpos [m] 動かす。向きと指の指令は保つ
- gripper: 手先の目標を保ったまま、指を閉じる (closed=true) か開く
- hold: 今の手先の姿勢で止まる

move_to と move_delta は、手先の位置が目標から tol (既定 0.005 m) 以内に入ると reached、
timeout_steps (既定 200) step で届かなければ timeout で終わる。timeout のときは、その場の姿勢で止まる。
gripper は GRIPPER_STEPS step、hold は 0 step で reached になる。
実行中に次の命令が来ると、実行中の命令は preempted で終わり、次の命令に切り替わる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from s1cap.control import GRIPPER_CLOSE, GRIPPER_OPEN, PoseController
from s1cap.sim import GroundTruth, LiberoEnv, Percept

# 指を開閉しきるまでの step 数 (control.set_gripper と同じ)
GRIPPER_STEPS = 15
DEFAULT_TOL = 0.005
DEFAULT_TIMEOUT_STEPS = 200

COMMAND_TYPES = ("move_to", "move_delta", "gripper", "hold")


@dataclass
class CommandResult:
    id: Any  # 命令の id をそのまま返す
    status: str  # reached / timeout / preempted / rejected
    started_step: int  # 命令を受け付けた step
    steps: int  # 命令を受けてから終わるまでの step 数
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "started_step": self.started_step,
            "steps": self.steps,
            "message": self.message,
        }


@dataclass
class _Running:
    command: dict[str, Any]
    started_step: int
    tol: float
    timeout_steps: int


class RobotDriver:
    def __init__(self, env: LiberoEnv) -> None:
        self.env = env
        self.step_count = 0
        self.ctrl: PoseController | None = None
        self.percept: Percept | None = None
        self._running: _Running | None = None

    def reset(self, init_index: int = 0, *, seed: int = 0) -> Percept:
        """エピソードを始め直す。制御器は reset 直後の手先の姿勢を保つ。"""
        self.percept = self.env.reset(init_index, seed=seed)
        self.ctrl = PoseController.hold(self.percept, self.env.gripper_command)
        self.step_count = 0
        self._running = None
        return self.percept

    def submit(self, command: dict[str, Any]) -> list[CommandResult]:
        """命令を受け付け、制御器の目標を書き換える。

        実行中の命令の preempted や、受け付けられない命令の rejected、0 step で終わる命令の
        reached など、この時点で決まった結果を返す。
        """
        ctrl, percept = self._ready()
        results = []
        try:
            target = self._target(command, ctrl, percept)
        except (KeyError, TypeError, ValueError) as e:
            return [
                CommandResult(command.get("id"), "rejected", self.step_count, 0, str(e))
            ]

        if self._running is not None:
            results.append(self._finish("preempted"))
        ctrl.pos, ctrl.quat, ctrl.gripper = target
        self._running = _Running(
            command,
            self.step_count,
            float(command.get("tol", DEFAULT_TOL)),
            int(command.get("timeout_steps", DEFAULT_TIMEOUT_STEPS)),
        )
        if command["type"] == "hold":
            results.append(self._finish("reached"))
        return results

    def step(self) -> tuple[Percept, CommandResult | None]:
        """制御器の目標へ向かう action で 1 step 進める。実行中の命令が終わったら結果を返す。"""
        ctrl, percept = self._ready()
        self.percept = self.env.step(ctrl.action(percept))
        self.step_count += 1
        return self.percept, self._check()

    def ground_truth(self) -> GroundTruth:
        return self.env.ground_truth()

    def _ready(self) -> tuple[PoseController, Percept]:
        if self.ctrl is None or self.percept is None:
            raise RuntimeError("reset を先に呼ぶ")
        return self.ctrl, self.percept

    def _target(
        self, command: dict[str, Any], ctrl: PoseController, percept: Percept
    ) -> tuple[np.ndarray, np.ndarray, float]:
        kind = command["type"]
        pos, quat, gripper = ctrl.pos, ctrl.quat, ctrl.gripper
        if kind == "move_to":
            pos = _vector(command["pos"], 3)
            if command.get("quat") is not None:
                quat = _vector(command["quat"], 4)
            if command.get("gripper") is not None:
                gripper = float(command["gripper"])
        elif kind == "move_delta":
            pos = percept.eef.pos + _vector(command["dpos"], 3)
        elif kind == "gripper":
            gripper = GRIPPER_CLOSE if command["closed"] else GRIPPER_OPEN
        elif kind == "hold":
            pos, quat = percept.eef.pos.copy(), percept.eef.quat.copy()
        else:
            raise ValueError(f"unknown command type {kind!r} (one of {COMMAND_TYPES})")
        return pos, quat, gripper

    def _check(self) -> CommandResult | None:
        running = self._running
        if running is None:
            return None
        ctrl, percept = self._ready()
        elapsed = self.step_count - running.started_step
        if running.command["type"] == "gripper":
            return self._finish("reached") if elapsed >= GRIPPER_STEPS else None
        if ctrl.reached(percept, running.tol):
            return self._finish("reached")
        if elapsed >= running.timeout_steps:
            # 届かない目標に向かい続けないよう、その場の姿勢で止まる
            ctrl.pos, ctrl.quat = percept.eef.pos.copy(), percept.eef.quat.copy()
            return self._finish("timeout")
        return None

    def _finish(self, status: str) -> CommandResult:
        assert self._running is not None
        result = CommandResult(
            self._running.command.get("id"),
            status,
            self._running.started_step,
            self.step_count - self._running.started_step,
        )
        self._running = None
        return result


def _vector(value: Any, size: int) -> np.ndarray:
    v = np.asarray(value, dtype=np.float64)
    if v.shape != (size,):
        raise ValueError(f"expected {size} numbers, got {value!r}")
    return v
