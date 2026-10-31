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

# 固定カメラ (agentview) の置き方。agentview は LIBERO のシーンの既定の位置 (ロボットの正面から斜めに
# 見下ろす)。quarterview は agentview のカメラを動かし、ロボットの台座から見た作業域の中心を、
# ロボットの正面と左の間 (方位 45°) の斜め上 (仰角 40°) から見下ろす。正面からの画像では奥行きが
# 上下の動きと重なるのに対し、quarterview では前後、左右、上下が画像の別々の向きに写る
FIXED_VIEWS = ("agentview", "quarterview")
QUARTERVIEW_AZIMUTH_DEG = (
    45.0  # 世界座標の +x (ロボットの正面) から +y (ロボットの左) へ測る
)
QUARTERVIEW_ELEVATION_DEG = 40.0
QUARTERVIEW_DISTANCE = 0.8  # 注視点からカメラまで [m]
# 注視点。ロボットの台座からの位置 [m]。libero_90 60 と libero_goal 8 で、物体は台座から前に
# 0.28〜0.72 m、左右に -0.2〜+0.25 m にある。この範囲と手先が画像に収まるように選んだ
QUARTERVIEW_TARGET = np.array([0.45, 0.03, 0.08])


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
        _use_cgl_offscreen()

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


def _use_cgl_offscreen() -> None:
    """macOS で robosuite のカメラ描画に CGL を使わせる。

    robosuite 1.4 は macOS では MUJOCO_GL の値によらず、非表示の GLFW ウィンドウを作って
    カメラを描画する。GLFW のウィンドウはメインスレッドでしか作れないため、ユーザーのコードを
    メインスレッド以外で動かす mjpython (MuJoCo のビューワ) と一緒に使うと落ちる。
    CGL はウィンドウを作らないので、どのスレッドからでも描画できる。
    """
    os.environ.setdefault("MUJOCO_GL", "cgl")
    import mujoco.cgl
    from robosuite.utils import binding_utils

    class CGLContext(mujoco.cgl.GLContext):
        def __init__(self, max_width: int, max_height: int, device_id: int = 0):
            super().__init__(max_width, max_height)

    binding_utils.GLContext = CGLContext


@dataclass
class Pose:
    pos: np.ndarray  # (3,) world 座標 [m]
    quat: np.ndarray  # (4,) xyzw

    def to_dict(self) -> dict[str, list[float]]:
        return {"pos": _round(self.pos), "quat": _round(self.quat)}


@dataclass
class Percept:
    """ロボットが自分のセンサで得られる観測。方策にはこれだけを渡す。"""

    images: dict[str, np.ndarray]  # カメラ名 -> (H, W, 3) uint8。上下を直した向き
    eef: Pose  # 手先の姿勢
    gripper_qpos: np.ndarray  # (2,) 左右の指の関節値
    arm_qpos: np.ndarray  # (7,) 腕の関節角 [rad]

    @property
    def gripper_width(self) -> float:
        """指の開き [m]。全開で約 0.08、閉じると 0。"""
        return float(np.abs(self.gripper_qpos).sum())

    def to_dict(self) -> dict[str, Any]:
        """画像を除いた JSON にできる dict。"""
        return {
            "eef": self.eef.to_dict(),
            "gripper_width": round(self.gripper_width, 4),
            "arm_qpos": _round(self.arm_qpos),
        }


@dataclass
class GroundTruth:
    """シミュレータだけが知っている真値。評価、デバッグ、比較用の条件にだけ使う。"""

    objects: dict[str, Pose]  # 動かせる物体
    fixtures: dict[str, Pose]  # 固定物 (キャビネット、コンロなど。テーブルは含まない)
    # 固定物の可動部の関節値 (引き出しの slide [m]、つまみの hinge [rad])
    joints: dict[str, float]
    success: bool  # BDDL の goal を満たしているか

    def to_dict(self) -> dict[str, Any]:
        return {
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "fixtures": {k: v.to_dict() for k, v in self.fixtures.items()},
            "joints": {k: round(v, 4) for k, v in self.joints.items()},
            "success": self.success,
        }


class LiberoEnv:
    """LIBERO の 1 タスクの環境。

    観測は、ロボットの知覚 (perceive) とシミュレータの真値 (ground_truth) に分けて返す。
    """

    def __init__(
        self,
        suite: str,
        task_id: int,
        *,
        image_size: int = 512,
        cameras: tuple[str, ...] = DEFAULT_CAMERAS,
        horizon: int | None = None,
        fixed_view: str = "agentview",
    ) -> None:
        """horizon はエピソードの step 数の上限。超えて step を呼ぶと robosuite が例外を出す。
        None なら LIBERO の既定値 (1000) を使う。fixed_view は固定カメラの置き方 (FIXED_VIEWS)。"""
        if fixed_view not in FIXED_VIEWS:
            raise ValueError(f"fixed_view は {FIXED_VIEWS} のどれか: {fixed_view!r}")
        setup_libero()
        import torch
        from libero.libero import benchmark, get_libero_path
        from libero.libero.envs import OffScreenRenderEnv

        bench = benchmark.get_benchmark_dict()[suite]()
        task = bench.get_task(task_id)
        self.suite = suite
        self.task_id = task_id
        self.task_name: str = task.name
        self.instruction: str = task.language
        self.cameras = cameras
        self.fixed_view = fixed_view
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
            **({} if horizon is None else {"horizon": horizon}),
        )
        self._raw_obs: dict[str, Any] = {}
        self._viewer: Any = None
        # 最後に送った action の指の指令。-1 で開き +1 で閉じる
        self.gripper_command: float = float(NOOP_ACTION[-1])

    @property
    def raw(self) -> Any:
        """LIBERO の問題クラス (robosuite の環境)。objects_dict や sim を持つ。"""
        return self._env.env

    @property
    def sim(self) -> Any:
        return self._env.sim

    def reset(self, init_index: int = 0, *, seed: int = 0) -> Percept:
        """init state の init_index 番目から始める。

        LIBERO は reset のたびに固定物の位置を大域の np.random で引き直し、その位置は
        init state に含まれない。同じ seed で同じ配置になるよう、reset の前に大域の乱数を固定する。
        """
        # LIBERO の reset は MuJoCo のモデルを作り直すので、ビューワは開き直す
        viewer_open = self._viewer is not None
        self.close_viewer()
        np.random.seed(seed)
        self._env.seed(seed)
        self._env.reset()
        if self.fixed_view == "quarterview":
            self._place_quarterview()
        self._raw_obs = self._env.set_init_state(self.init_states[init_index])
        for _ in range(SETTLE_STEPS):
            self._raw_obs, *_ = self._env.step(NOOP_ACTION)
        self.gripper_command = float(NOOP_ACTION[-1])
        if viewer_open:
            self.launch_viewer()
        return self.perceive()

    def step(self, action: np.ndarray) -> Percept:
        """OSC_POSE の 7 次元 action で 1 step (1/20 秒) 進める。"""
        action = np.asarray(action, dtype=np.float64)
        self._raw_obs, *_ = self._env.step(action)
        self.gripper_command = float(action[-1])
        self._sync_viewer()
        return self.perceive()

    def _place_quarterview(self) -> None:
        # LIBERO の reset は MuJoCo のモデルを作り直すので、reset のたびにカメラを置き直す
        model = self.sim.model
        base = self.sim.data.body_xpos[model.body_name2id("robot0_base")]
        target = base + QUARTERVIEW_TARGET
        az = np.radians(QUARTERVIEW_AZIMUTH_DEG)
        el = np.radians(QUARTERVIEW_ELEVATION_DEG)
        pos = target + QUARTERVIEW_DISTANCE * np.array(
            [np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)]
        )
        i = model.camera_name2id("agentview")
        model.cam_pos[i] = pos
        model.cam_quat[i] = _look_at_quat(pos, target)

    def camera_matrix(self, camera: str) -> np.ndarray:
        """カメラの射影行列 (3x4)。カメラの校正値にあたる。

        世界座標の点 [x, y, z, 1] に掛けた (a, b, w) から、images の画像 (上下を直した向き) の
        画素 (u, v) = (a / w, b / w) が求まる。u は右、v は下へ増える。
        """
        model, data = self.sim.model, self.sim.data
        i = model.camera_name2id(camera)
        size = self.raw.camera_heights[0]
        f = 0.5 * size / np.tan(np.radians(model.cam_fovy[i]) / 2)
        k = np.array([[f, 0, size / 2], [0, f, size / 2], [0, 0, 1]])
        # MuJoCo のカメラは -z を向き +y が上。画像の向き (+z が奥、+y が下) に直す
        r = data.cam_xmat[i].reshape(3, 3) @ np.diag([1.0, -1.0, -1.0])
        return k @ np.hstack([r.T, -r.T @ data.cam_xpos[i][:, None]])

    def launch_viewer(self) -> None:
        """MuJoCo のビューワを開き、以後の step を表示する。macOS では mjpython で動かす必要がある。"""
        import mujoco.viewer

        self._viewer = mujoco.viewer.launch_passive(
            self.sim.model._model, self.sim.data._data
        )
        # robosuite のカメラ画像と同じく、衝突判定用の形状 (geom group 0) を隠す。
        # 見た目用の形状 (group 1) と重なって表示が崩れるため
        with self._viewer.lock():
            self._viewer.opt.geomgroup[0] = 0

    def close_viewer(self) -> None:
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None

    def _sync_viewer(self) -> None:
        # ウィンドウが閉じられた後は何もしない
        if self._viewer is not None and self._viewer.is_running():
            self._viewer.sync()

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
    ) -> Percept:
        """動かせる物体を指定の姿勢に直接置く。quat は xyzw で、省略すると今の向きのまま。

        評価用の場面を作るための操作で、方策からは使わない。
        """
        obj = self.raw.objects_dict[name]
        joint = obj.joints[0]  # 動かせる物体は free joint を 1 つ持つ
        if quat is None:
            quat = self.ground_truth().objects[name].quat
        qpos = np.concatenate(
            [np.asarray(pos, dtype=np.float64), _xyzw_to_wxyz(np.asarray(quat))]
        )
        self.sim.data.set_joint_qpos(joint, qpos)
        self.sim.data.set_joint_qvel(joint, np.zeros(6))
        self._raw_obs = self._env.regenerate_obs_from_state(self._env.get_sim_state())
        self._sync_viewer()
        hold = np.append(NOOP_ACTION[:-1], self.gripper_command)
        for _ in range(settle_steps):
            self.step(hold)
        return self.perceive()

    def sim_state(self) -> np.ndarray:
        """MuJoCo の状態 (時刻、qpos、qvel) を 1 次元にしたもの。restore に渡すとこの状態に戻る。

        固定物の位置は状態に含まれないので、戻す前に同じ init と seed で reset しておく。
        """
        return np.asarray(self._env.get_sim_state(), dtype=np.float64)

    def restore(self, state: np.ndarray) -> Percept:
        """sim_state で得た状態に戻し、その状態の知覚を返す。記録したエピソードを描き直すのに使う。"""
        self._raw_obs = self._env.regenerate_obs_from_state(state)
        self._sync_viewer()
        return self.perceive()

    def perceive(self) -> Percept:
        """ロボットの知覚: カメラ画像、手先の姿勢、指と腕の関節値。"""
        obs = self._raw_obs
        robot = self.raw.robots[0]
        return Percept(
            images={cam: np.flipud(obs[f"{cam}_image"]).copy() for cam in self.cameras},
            eef=Pose(
                pos=obs["robot0_eef_pos"].copy(), quat=obs["robot0_eef_quat"].copy()
            ),
            gripper_qpos=obs["robot0_gripper_qpos"].copy(),
            arm_qpos=self.sim.data.qpos[robot._ref_joint_pos_indexes].copy(),
        )

    def ground_truth(self) -> GroundTruth:
        """シミュレータの真値: 物体と固定物の姿勢、固定物の関節値、成功判定。"""
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

        return GroundTruth(
            objects={name: body_pose(name) for name in self.raw.objects_dict},
            fixtures={name: body_pose(name) for name in self.raw.fixtures_dict},
            joints=joints,
            success=self.success(),
        )

    def close(self) -> None:
        self.close_viewer()
        self._env.close()


def _look_at_quat(pos: np.ndarray, target: np.ndarray) -> np.ndarray:
    """pos から target を向き、画像の上が世界座標の上側になる MuJoCo のカメラの向き (wxyz)。

    MuJoCo のカメラは自身の -z の向きを見て、+x が画像の右、+y が画像の上になる。
    """
    import mujoco

    z = pos - target
    z = z / np.linalg.norm(z)
    x = np.cross([0.0, 0.0, 1.0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    quat = np.zeros(4)
    mujoco.mju_mat2Quat(quat, np.column_stack([x, y, z]).ravel())
    return quat


def _wxyz_to_xyzw(q: np.ndarray) -> np.ndarray:
    return np.array([q[1], q[2], q[3], q[0]], dtype=np.float64)


def _xyzw_to_wxyz(q: np.ndarray) -> np.ndarray:
    return np.array([q[3], q[0], q[1], q[2]], dtype=np.float64)


def _round(a: np.ndarray, ndigits: int = 4) -> list[float]:
    return [round(float(x), ndigits) for x in a]
