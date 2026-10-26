"""OSC_POSE の action で手先を動かす単純な制御。"""

from __future__ import annotations

import numpy as np
from robosuite.utils import transform_utils as T

from s1cap.sim import LiberoEnv, Observation

# 手先を真下に向けた姿勢 (xyzw)。LIBERO の Panda の初期姿勢に近い
TOP_DOWN_QUAT = np.array([1.0, 0.0, 0.0, 0.0])

# OSC_POSE の既定の出力範囲は、action 1 あたり位置 0.05 m、回転 0.5 rad。
# 誤差がこれ以上なら action が飽和する
KP_POS = 1 / 0.05
KP_ORI = 1 / 0.5


def pose_action(
    obs: Observation, pos: np.ndarray, quat: np.ndarray, gripper: float
) -> np.ndarray:
    """目標の手先姿勢へ向かう P 制御の action。"""
    pos_err = np.asarray(pos) - obs.eef.pos
    # world 座標系での回転誤差 target * current^-1 を軸角で表す
    ori_err = T.quat2axisangle(
        T.quat_multiply(np.asarray(quat), T.quat_inverse(obs.eef.quat))
    )
    return np.concatenate(
        [
            np.clip(KP_POS * pos_err, -1, 1),
            np.clip(KP_ORI * ori_err, -1, 1),
            [gripper],
        ]
    )


def move_to(
    env: LiberoEnv,
    pos: np.ndarray,
    quat: np.ndarray = TOP_DOWN_QUAT,
    *,
    gripper: float = -1.0,
    tol: float = 0.005,
    max_steps: int = 200,
) -> tuple[Observation, bool]:
    """手先を pos に動かす。tol 以内に入ったら (観測, True)、max_steps で届かなければ False を返す。"""
    obs = env.observe()
    for _ in range(max_steps):
        if np.linalg.norm(np.asarray(pos) - obs.eef.pos) < tol:
            return obs, True
        obs = env.step(pose_action(obs, pos, quat, gripper))
    return obs, bool(np.linalg.norm(np.asarray(pos) - obs.eef.pos) < tol)
