"""OSC_POSE の action で手先を動かす単純な制御。

`PoseController` は目標の手先姿勢と指の指令を保ち、ロボットの知覚 (`Percept`) だけから
毎 step の action を計算する。`move_to`、`move_delta`、`set_gripper` はその上に作った
同期的な命令で、目標に届くか step 数の上限に達するまで `env.step` を回す。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from robosuite.utils import transform_utils as T

from s1cap.sim import LiberoEnv, Percept

# 手先を真下に向けた姿勢 (xyzw)。LIBERO の Panda の初期姿勢に近い
TOP_DOWN_QUAT = np.array([1.0, 0.0, 0.0, 0.0])

# OSC_POSE の既定の出力範囲は、action 1 あたり位置 0.05 m、回転 0.5 rad。
# 誤差がこれ以上なら action が飽和する
KP_POS = 1 / 0.05
KP_ORI = 1 / 0.5

GRIPPER_OPEN = -1.0
GRIPPER_CLOSE = 1.0


def pose_action(
    percept: Percept, pos: np.ndarray, quat: np.ndarray, gripper: float
) -> np.ndarray:
    """目標の手先姿勢へ向かう P 制御の action。"""
    pos_err = np.asarray(pos) - percept.eef.pos
    # world 座標系での回転誤差 target * current^-1 を軸角で表す
    ori_err = T.quat2axisangle(
        T.quat_multiply(np.asarray(quat), T.quat_inverse(percept.eef.quat))
    )
    return np.concatenate(
        [
            np.clip(KP_POS * pos_err, -1, 1),
            np.clip(KP_ORI * ori_err, -1, 1),
            [gripper],
        ]
    )


@dataclass
class PoseController:
    """目標の手先姿勢 (pos、xyzw の quat) と指の指令 (-1 で開き +1 で閉じる) を保つ制御器。

    目標を変えない限り、同じ姿勢を保つ action を出し続ける。
    """

    pos: np.ndarray
    quat: np.ndarray
    gripper: float = GRIPPER_OPEN

    @classmethod
    def hold(cls, percept: Percept, gripper: float = GRIPPER_OPEN) -> PoseController:
        """今の手先の姿勢を目標にする。"""
        return cls(percept.eef.pos.copy(), percept.eef.quat.copy(), gripper)

    def action(self, percept: Percept) -> np.ndarray:
        return pose_action(percept, self.pos, self.quat, self.gripper)

    def reached(self, percept: Percept, tol: float = 0.005) -> bool:
        """手先の位置が目標から tol [m] 以内にあるか。向きは見ない。"""
        return bool(np.linalg.norm(self.pos - percept.eef.pos) < tol)


def move_to(
    env: LiberoEnv,
    pos: np.ndarray,
    quat: np.ndarray = TOP_DOWN_QUAT,
    *,
    gripper: float | None = None,
    tol: float = 0.005,
    max_steps: int = 200,
) -> tuple[Percept, bool]:
    """手先を pos に動かす。tol 以内に入ったら (知覚, True)、max_steps で届かなければ False を返す。

    gripper を省略すると、最後に送った指の指令を保つ (掴んだ物を離さない)。
    """
    ctrl = PoseController(
        np.asarray(pos, dtype=np.float64),
        np.asarray(quat, dtype=np.float64),
        env.gripper_command if gripper is None else gripper,
    )
    return _run(env, ctrl, tol=tol, max_steps=max_steps)


def move_delta(
    env: LiberoEnv,
    dpos: np.ndarray,
    *,
    gripper: float | None = None,
    tol: float = 0.005,
    max_steps: int = 200,
) -> tuple[Percept, bool]:
    """手先を今の位置から dpos [m] だけ動かす。向きは今のまま保つ。"""
    percept = env.perceive()
    return move_to(
        env,
        percept.eef.pos + np.asarray(dpos, dtype=np.float64),
        percept.eef.quat,
        gripper=gripper,
        tol=tol,
        max_steps=max_steps,
    )


def set_gripper(env: LiberoEnv, closed: bool, *, steps: int = 15) -> Percept:
    """手先の位置と向きを保ったまま、指を閉じる (closed=True) か開く。"""
    percept = env.perceive()
    ctrl = PoseController.hold(percept, GRIPPER_CLOSE if closed else GRIPPER_OPEN)
    for _ in range(steps):
        percept = env.step(ctrl.action(percept))
    return percept


def _run(
    env: LiberoEnv, ctrl: PoseController, *, tol: float, max_steps: int
) -> tuple[Percept, bool]:
    percept = env.perceive()
    for _ in range(max_steps):
        if ctrl.reached(percept, tol):
            return percept, True
        percept = env.step(ctrl.action(percept))
    return percept, ctrl.reached(percept, tol)
