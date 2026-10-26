"""LIBERO (robosuite 1.4, MuJoCo) の環境を作り、画像と物体の真値を取り出す。

LIBERO はこのリポジトリに含めず、環境変数 LIBERO_ROOT で clone の場所を受け取る (docs/setup.md)。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_CAMERAS = ("agentview", "robot0_eye_in_hand")

# LIBERO の評価スクリプトと同じく、reset 直後に物体が落ち着くまで何もしない step を回す
SETTLE_STEPS = 10
# OSC_POSE の action は [dx, dy, dz, dax, day, daz, gripper]。gripper は -1 で開き +1 で閉じる
NOOP_ACTION = np.array([0, 0, 0, 0, 0, 0, -1], dtype=np.float64)


def setup_libero() -> Path:
    """LIBERO を import できるようにする。libero を import する前に呼ぶ。

    LIBERO は初回 import 時に ~/.libero/config.yaml を探し、無ければ標準入力で問い合わせる。
    これを避けるため、LIBERO_ROOT から作った config.yaml を LIBERO_CONFIG_PATH で渡す。
    """
    root = os.environ.get("LIBERO_ROOT")
    if not root:
        raise RuntimeError(
            "環境変数 LIBERO_ROOT に LIBERO の clone のパスを設定する (docs/setup.md)"
        )
    root_path = Path(root).expanduser().resolve()
    pkg = root_path / "libero" / "libero"
    if not (pkg / "bddl_files").is_dir():
        raise RuntimeError(
            f"LIBERO_ROOT={root_path} に libero/libero/bddl_files が無い"
        )

    if sys.platform == "darwin":
        # macOS のオフスクリーン描画は CGL。egl と osmesa は使えない
        os.environ.setdefault("MUJOCO_GL", "cgl")

    cache = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "s1cap"
        / "libero"
    )
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "config.yaml").write_text(
        "".join(
            f"{key}: {path}\n"
            for key, path in {
                "benchmark_root": pkg,
                "bddl_files": pkg / "bddl_files",
                "init_states": pkg / "init_files",
                "datasets": root_path / "libero" / "datasets",
                "assets": pkg / "assets",
            }.items()
        )
    )
    os.environ["LIBERO_CONFIG_PATH"] = str(cache)

    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))
    return root_path


@dataclass
class Pose:
    pos: np.ndarray  # (3,) world 座標 [m]
    quat: np.ndarray  # (4,) xyzw

    def to_dict(self) -> dict[str, list[float]]:
        return {"pos": _round(self.pos), "quat": _round(self.quat)}


@dataclass
class Observation:
    images: dict[str, np.ndarray]  # カメラ名 -> (H, W, 3) uint8。上下を直した向き
    objects: dict[str, Pose]  # 動かせる物体
    fixtures: dict[str, Pose]  # 固定物 (テーブル、キャビネット、コンロなど)
    # 固定物の可動部の関節値 (引き出しの slide [m]、つまみの hinge [rad])
    joints: dict[str, float]
    eef: Pose
    gripper_qpos: np.ndarray  # (2,) 左右の指の関節値

    @property
    def gripper_width(self) -> float:
        """指の開き [m]。全開で約 0.08、閉じると 0。"""
        return float(np.abs(self.gripper_qpos).sum())

    def to_dict(self) -> dict[str, Any]:
        """画像を除いた JSON にできる dict。"""
        return {
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "fixtures": {k: v.to_dict() for k, v in self.fixtures.items()},
            "joints": {k: round(v, 4) for k, v in self.joints.items()},
            "eef": self.eef.to_dict(),
            "gripper_width": round(self.gripper_width, 4),
        }


class LiberoEnv:
    """LIBERO の 1 タスクの環境。観測を Observation で返す。"""

    def __init__(
        self,
        suite: str,
        task_id: int,
        *,
        image_size: int = 512,
        cameras: tuple[str, ...] = DEFAULT_CAMERAS,
    ) -> None:
        setup_libero()
        import torch
        from libero.libero import benchmark, get_libero_path
        from libero.libero.envs import OffScreenRenderEnv

        bench = benchmark.get_benchmark_dict()[suite]()
        task = bench.get_task(task_id)
        self.suite = suite
        self.task_name: str = task.name
        self.instruction: str = task.language
        self.cameras = cameras
        # benchmark.get_task_init_states は torch.load を weights_only の既定値 (torch>=2.6 で True) で呼び、
        # numpy 配列の pickle を読めないので、自分で読む
        self.init_states: np.ndarray = torch.load(
            Path(get_libero_path("init_states"))
            / task.problem_folder
            / task.init_states_file,
            weights_only=False,
        )
        self._env = OffScreenRenderEnv(
            bddl_file_name=bench.get_task_bddl_file_path(task_id),
            camera_names=list(cameras),
            camera_heights=image_size,
            camera_widths=image_size,
        )
        self._raw_obs: dict[str, Any] = {}

    @property
    def raw(self) -> Any:
        """LIBERO の問題クラス (robosuite の環境)。objects_dict や sim を持つ。"""
        return self._env.env

    @property
    def sim(self) -> Any:
        return self._env.sim

    def reset(self, init_index: int = 0, *, seed: int = 0) -> Observation:
        """init state の init_index 番目から始める。

        LIBERO は reset のたびに固定物の位置を大域の np.random で引き直し、その位置は
        init state に含まれない。同じ seed で同じ配置になるよう、reset の前に大域の乱数を固定する。
        """
        np.random.seed(seed)
        self._env.seed(seed)
        self._env.reset()
        self._raw_obs = self._env.set_init_state(self.init_states[init_index])
        for _ in range(SETTLE_STEPS):
            self._raw_obs, *_ = self._env.step(NOOP_ACTION)
        return self.observe()

    def step(self, action: np.ndarray) -> Observation:
        """OSC_POSE の 7 次元 action で 1 step (1/20 秒) 進める。"""
        self._raw_obs, *_ = self._env.step(np.asarray(action, dtype=np.float64))
        return self.observe()

    def success(self) -> bool:
        """BDDL の goal を満たしているか。"""
        return bool(self._env.check_success())

    def set_object_pose(
        self,
        name: str,
        pos: np.ndarray,
        quat: np.ndarray | None = None,
        *,
        settle_steps: int = 0,
    ) -> Observation:
        """動かせる物体を指定の姿勢に直接置く。quat は xyzw で、省略すると今の向きのまま。"""
        obj = self.raw.objects_dict[name]
        joint = obj.joints[0]  # 動かせる物体は free joint を 1 つ持つ
        if quat is None:
            quat = self.observe().objects[name].quat
        qpos = np.concatenate(
            [np.asarray(pos, dtype=np.float64), _xyzw_to_wxyz(np.asarray(quat))]
        )
        self.sim.data.set_joint_qpos(joint, qpos)
        self.sim.data.set_joint_qvel(joint, np.zeros(6))
        self._raw_obs = self._env.regenerate_obs_from_state(self._env.get_sim_state())
        for _ in range(settle_steps):
            self._raw_obs, *_ = self._env.step(NOOP_ACTION)
        return self.observe()

    def observe(self) -> Observation:
        model, data = self.sim.model, self.sim.data
        body_id = self.raw.obj_body_id

        def body_pose(name: str) -> Pose:
            i = body_id[name]
            return Pose(
                pos=data.body_xpos[i].copy(), quat=_wxyz_to_xyzw(data.body_xquat[i])
            )

        joints = {}
        for fixture in self.raw.fixtures_dict:
            for j in range(model.njnt):
                jname = model.joint_id2name(j)
                if (
                    jname
                    and jname.startswith(f"{fixture}_")
                    and model.jnt_type[j] in (2, 3)
                ):  # slide, hinge
                    joints[jname] = float(data.qpos[model.jnt_qposadr[j]])

        obs = self._raw_obs
        return Observation(
            images={cam: np.flipud(obs[f"{cam}_image"]).copy() for cam in self.cameras},
            objects={name: body_pose(name) for name in self.raw.objects_dict},
            fixtures={name: body_pose(name) for name in self.raw.fixtures_dict},
            joints=joints,
            eef=Pose(
                pos=obs["robot0_eef_pos"].copy(), quat=obs["robot0_eef_quat"].copy()
            ),
            gripper_qpos=obs["robot0_gripper_qpos"].copy(),
        )

    def close(self) -> None:
        self._env.close()


def _wxyz_to_xyzw(q: np.ndarray) -> np.ndarray:
    return np.array([q[1], q[2], q[3], q[0]], dtype=np.float64)


def _xyzw_to_wxyz(q: np.ndarray) -> np.ndarray:
    return np.array([q[3], q[0], q[1], q[2]], dtype=np.float64)


def _round(a: np.ndarray, ndigits: int = 4) -> list[float]:
    return [round(float(x), ndigits) for x in a]
