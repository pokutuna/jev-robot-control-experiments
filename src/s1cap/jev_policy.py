"""Jev に手先の移動方向と指の開閉を選ばせる方策 (計画の C2)。

1 回の判断で、Jev に 5 つの問いを 1 リクエストで送る。

- x、y、z: 手先をその軸の + / - に 1 歩 (既定 2 cm) 動かすか、動かさないか (Choice)。
  軸は世界座標ではなく、ロボットの正面から見た向きで示す (JEV_TO_WORLD)
- gripper: 指を開いた状態にするか、閉じた状態にするか (Choice)
- done: タスクが終わったか (Noul)

答えから sim への命令を 1 つ作る。指の答えが今の指の状態と違うときは、その回は指の命令だけを送り、
手先は動かさない。指の問いを「開く / 閉じる / そのまま」の動作で聞くと、Jev は毎回開くと閉じるを
交互に選び、手先が動かなかった。このため、あるべき状態で聞き、今の状態と比べる。
あるべき状態で聞いても、開きと閉じの確率は 0.5 前後で揺れた。今の状態から変えるのは、
変えた先の確率が gripper_threshold (既定 0.7) 以上のときだけにする。

move_delta には小さな tol (1 mm) と短い timeout_steps (40 step、2 秒) を付ける。テーブルに
押し付ける向きを選んだときに、既定の 200 step (10 秒) を待たずに次の判断に移るため。

Jev に渡す state は入力の条件で変える。

- json: 指示文、ロボットの状態、物体の位置の真値 (JSON 入力条件)
- image: 指示文、ロボットの状態、カメラ画像
- image_json: 両方

どの条件でも、直前の数回の判断と結果を state に入れる。Jev は前の判断を覚えていないので、
同じ場所を行き来しないための手がかりにする。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typesafe_sdk import Choice, Noul, Question, TypeSafeClient

from s1cap import jev

INPUT_MODES = ("json", "image", "image_json")
OVERLAYS = ("axes", "below")
HISTORY = 5

# Jev には、LIBERO の世界座標 (ロボットの正面が +x、左が +y、上が +z) ではなく、ロボットの正面に立って
# ロボットの方を向いた人から見た向きで示す。右 (ロボットの左) が +x、手前 (ロボットの台座から離れる向き)
# が +y、上が +z で、ロボットの正面から見る固定カメラ (agentview) の画像では x が右、y が下、z が上に写る。
# 画像座標と同じく x が右、y が下なので、高さを +z にすると左手系になる。Jev に示すのは各軸が画像の
# どちらに写るかだけで、手の向きは問わない。固定カメラを quarterview に置いても軸は変えない。
# Jev の (x, y, z) は世界座標の (y, x, z) にあたる。
# 世界座標の軸、Y-up と Z-up の右手系も試したが、どれも前後の正解率は当て推量と変わらなかった
# (wiki/findings/jev-c2-direction-policy.md)
JEV_TO_WORLD = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.float64)

COORDINATE_GUIDE = (
    "Coordinate system, as seen by a viewer standing in front of the robot and facing it: "
    "+x points to the viewer's right (the robot's left), -x to the viewer's left. "
    "+y points toward the viewer (away from the robot base), "
    "-y away from the viewer (toward the robot base). "
    "+z points up, away from the table, -z down toward the table. "
    "x and y are parallel to the table."
)
AXIS_CRITERIA = {
    "x": {
        "plus": "+x: move to the viewer's right (the robot's left)",
        "stay": "do not move along x",
        "minus": "-x: move to the viewer's left (the robot's right)",
    },
    "y": {
        "plus": "+y: move toward the viewer, away from the robot base",
        "stay": "do not move along y",
        "minus": "-y: move away from the viewer, toward the robot base",
    },
    "z": {
        "plus": "+z: move up, away from the table",
        "stay": "do not move along z",
        "minus": "-z: move down, toward the table",
    },
}
GRIPPER_CRITERIA = {
    "open": "the fingers should be open (not holding anything, or releasing what is held)",
    "closed": "the fingers should be closed (grasping an object between them)",
}
SIGN = {"plus": 1.0, "stay": 0.0, "minus": -1.0}


def questions(instruction: str, step_m: float) -> dict[str, Question]:
    cm = round(step_m * 100, 1)
    qs: dict[str, Question] = {
        axis: Choice(
            instructions=(
                f"Task: {instruction}. The robot moves its gripper {cm} cm per step. "
                f"Which way should the gripper move along the {axis} axis in the next step?"
            ),
            criteria=criteria,
        )
        for axis, criteria in AXIS_CRITERIA.items()
    }
    qs["gripper"] = Choice(
        instructions=(
            f"Task: {instruction}. Should the fingers be open or closed after the next step?"
        ),
        criteria=GRIPPER_CRITERIA,
    )
    qs["done"] = Noul(
        instructions=f"Task: {instruction}. Is the task complete?",
        criteria={
            "true": "the goal of the task is achieved and the robot has let go",
            "false": "the goal of the task is not achieved yet",
        },
    )
    return qs


@dataclass
class Observation:
    step: int  # sim の step 番号
    robot_state: dict[str, Any]  # Percept.to_dict()
    images: dict[str, np.ndarray] = field(default_factory=dict)  # カメラ名 -> 画像
    objects: dict[str, Any] | None = None  # 物体の姿勢の真値 (JSON 入力条件だけ)


@dataclass
class Decision:
    command: dict[str, Any] | None  # sim への命令。None ならエピソードを終える
    record: dict[str, Any]  # 記録用。選んだもの、確率、レイテンシ、使った観測の step


class JevDirectionPolicy:
    def __init__(
        self,
        client: TypeSafeClient,
        instruction: str,
        *,
        input_mode: str = "image",
        overlays: tuple[str, ...] = (),
        step_m: float = 0.02,
        tol: float = 0.001,
        timeout_steps: int = 40,
        gripper_threshold: float = 0.7,
        done_threshold: float = 0.8,
    ) -> None:
        if input_mode not in INPUT_MODES:
            raise ValueError(f"input_mode は {INPUT_MODES} のどれか: {input_mode!r}")
        if unknown := set(overlays) - set(OVERLAYS):
            raise ValueError(f"overlays は {OVERLAYS} から選ぶ: {sorted(unknown)}")
        self.overlays = tuple(overlays)
        self.client = client
        self.instruction = instruction
        self.input_mode = input_mode
        self.step_m = step_m
        self.tol = tol
        self.timeout_steps = timeout_steps
        self.gripper_threshold = gripper_threshold
        self.done_threshold = done_threshold
        self.questions = questions(instruction, step_m)
        self.history: deque[str] = deque(maxlen=HISTORY)
        self.gripper_closed = (
            False  # 最後に送った指の命令。sim は reset 直後に指を開いている
        )
        self._next_id = 1

    def state(self, obs: Observation) -> list[Any]:
        robot = obs.robot_state
        lines = [
            f"Task: {self.instruction}",
            COORDINATE_GUIDE,
            (
                "Robot state (meters, in the coordinate system above): "
                f"gripper position {self._jev_vector(robot['eef']['pos'])}, "
                f"finger opening {robot['gripper_width']} m (0.08 fully open, 0 closed)."
            ),
        ]
        if self.history:
            lines.append("Previous steps (oldest first): " + "; ".join(self.history))
        state: list[Any] = ["\n".join(lines)]
        if self.input_mode in ("json", "image_json"):
            if obs.objects is None:
                raise ValueError("JSON 入力条件には物体の姿勢が要る")
            positions = {
                name: self._jev_vector(pose["pos"])
                for name, pose in obs.objects.items()
            }
            state.append(
                f"Object positions (meters, in the coordinate system above): {positions}"
            )
        if self.input_mode in ("image", "image_json"):
            for camera, image in obs.images.items():
                if camera == WRIST_CAMERA:
                    image = np.rot90(image, 2)
                image = draw_overlays(camera, image, self.overlays)
                caption = CAMERA_CAPTIONS.get(camera, f"Camera {camera}:")
                notes = [OVERLAY_NOTES[o] for o in self.overlays if o in MARKS[camera]]
                if notes:
                    caption = f"{caption.removesuffix(':')}. {' '.join(notes).removesuffix('.')}:"
                state.append(caption)
                state.append(jev.image_content(image))
        return state

    def decide(self, obs: Observation) -> Decision:
        response, latency_ms = jev.ask(self.client, self.state(obs), self.questions)
        choices = {name: a.choice for name, a in response.choices.items()}
        done = response.nouls["done"].noul
        record = {
            "obs_step": obs.step,
            "latency_ms": round(latency_ms),
            "choices": choices,
            "probabilities": {
                name: {k: round(v, 3) for k, v in a.probabilities.items()}
                for name, a in response.choices.items()
            },
            "done": round(done, 3),
            "calls": {"move": jev.call_record(response, latency_ms)},
        }
        if done >= self.done_threshold:
            return Decision(None, record)
        command = self._command(choices, response.choices["gripper"].probabilities)
        record["command"] = command
        return Decision(command, record)

    def on_result(self, result: dict[str, Any], command: dict[str, Any]) -> None:
        """命令の結果を、次の判断の state に入れる履歴に足す。"""
        if command["type"] == "gripper":
            action = "close fingers" if command["closed"] else "open fingers"
        elif command["type"] == "move_delta":
            jev_dpos = JEV_TO_WORLD.T @ np.array(command["dpos"])
            action = "move " + " ".join(
                f"{d:+.0f}cm {axis}" for axis, d in zip("xyz", jev_dpos * 100) if d
            )
        else:
            action = command["type"]
        self.history.append(f"{action} -> {result['status']}")

    def _jev_vector(self, world: Any) -> list[float]:
        """世界座標のベクトルを、Jev に示す座標系に直す。"""
        return [round(float(v), 3) for v in JEV_TO_WORLD.T @ np.asarray(world)]

    def _command(
        self, choices: dict[str, str], gripper_probs: dict[str, float]
    ) -> dict[str, Any]:
        command_id = self._next_id
        self._next_id += 1
        closed = choices["gripper"] == "closed"
        if (
            closed != self.gripper_closed
            and gripper_probs[choices["gripper"]] >= self.gripper_threshold
        ):
            self.gripper_closed = closed
            return {"id": command_id, "type": "gripper", "closed": closed}
        jev_dpos = np.array([SIGN[choices[axis]] * self.step_m for axis in "xyz"])
        dpos = (JEV_TO_WORLD @ jev_dpos).tolist()
        if not any(dpos):
            return {"id": command_id, "type": "hold"}
        return {
            "id": command_id,
            "type": "move_delta",
            "dpos": dpos,
            "tol": self.tol,
            "timeout_steps": self.timeout_steps,
        }


# 画像ごとに、その画像での軸の向きを添える。キーは固定カメラの置き方 (s1cap.sim.FIXED_VIEWS) か
# カメラ名。quarterview はロボットの正面と左の間の斜め上から見るので、+x が画像の右下、+y が左下、
# +z が上に写る。手首カメラの画像は agentview に対して 180° 回っていて、画像の上が世界座標の +x
# (Jev の +y)、右が世界座標の -y (Jev の -x) になる (libero_goal で、皿 (ボウルの +x 側) が上、
# クリームチーズ (+y 側) が左に写る)。Jev には 180° 回して渡し、agentview と同じく x が右、y が下に
# 写るようにする
WRIST_CAMERA = "robot0_eye_in_hand"
CAMERA_CAPTIONS = {
    "agentview": (
        "Fixed camera, looking at the robot from the front, from where the viewer stands. "
        "In this image, +x points right, +y points down (toward this camera), "
        "and +z points up:"
    ),
    "quarterview": (
        "Fixed camera, looking down diagonally at the table from the viewer's right "
        "(the robot's front left). In this image, +x points to the lower right, "
        "+y points to the lower left, and +z points up:"
    ),
    WRIST_CAMERA: (
        "Wrist camera, looking straight down (-z) from the gripper. "
        "In this image, +x points right and +y points down:"
    ),
}


# 画像に描く印 (overlays)。
#   axes:  画像の隅に、各軸の + の向きを矢印で描く。向きは画像での向き (右が +u、下が +v) の単位ベクトルで、
#          libero_90 60 のボウルの 10 cm 上の点で測った。手首カメラの z はカメラの方を向くので描かない
#   below: 手首カメラの画像に、手先の真下の点を十字で描く。手首カメラは手先の中心から 5.5 cm 横にずれて
#          いるので、真下の点は画像の中心より上 (180° 回した後) に写り、高さで動く (手先から 3 cm 下で
#          v=0.25、10 cm で 0.35、25 cm で 0.43)。10 cm 下の点に描く
AXIS_DIRECTIONS = {
    "agentview": {"x": (1.0, 0.0), "y": (-0.25, 0.97), "z": (-0.1, -1.0)},
    "quarterview": {"x": (0.86, 0.51), "y": (-0.89, 0.45), "z": (-0.07, -1.0)},
    WRIST_CAMERA: {"x": (1.0, 0.0), "y": (0.0, 1.0)},
}
BELOW_GRIPPER_UV = (0.5, 0.35)
MARKS = {
    "agentview": ("axes",),
    "quarterview": ("axes",),
    WRIST_CAMERA: ("axes", "below"),
}
OVERLAY_NOTES = {
    "axes": "The arrows in the top left corner show the + direction of each axis.",
    "below": "The red cross marks the point directly below the gripper.",
}
AXIS_COLORS = {"x": (230, 40, 40), "y": (30, 190, 30), "z": (40, 90, 255)}


def draw_overlays(
    camera: str,
    image: np.ndarray,
    overlays: tuple[str, ...],
    below_uv: tuple[float, float] = BELOW_GRIPPER_UV,
) -> np.ndarray:
    marks = [o for o in overlays if o in MARKS.get(camera, ())]
    if not marks:
        return image
    im = Image.fromarray(np.ascontiguousarray(image))
    draw = ImageDraw.Draw(im)
    w, h = im.size
    if "axes" in marks:
        # 左上の隅の白い四角の中に描く。y が左下を向く画像もあるので原点は四角の中央に置く
        box = 0.2 * w
        draw.rectangle([0, 0, box, box], fill=(255, 255, 255))
        o = np.array([box / 2, box / 2])
        length = 0.065 * w
        font = ImageFont.load_default(size=round(0.05 * w))
        for axis, d in AXIS_DIRECTIONS[camera].items():
            tip = o + length * np.array(d)
            draw.line([tuple(o), tuple(tip)], fill=AXIS_COLORS[axis], width=3)
            draw.text(
                tuple(tip + 0.035 * w * np.array(d) - [4, 6]),
                f"+{axis}",
                fill=AXIS_COLORS[axis],
                font=font,
            )
    if "below" in marks:
        u, v = below_uv[0] * w, below_uv[1] * h
        r = 0.04 * w
        draw.line([(u - r, v), (u + r, v)], fill=(255, 0, 0), width=2)
        draw.line([(u, v - r), (u, v + r)], fill=(255, 0, 0), width=2)
    return np.asarray(im)


def wrist_view(image: np.ndarray, cross_uv: tuple[float, float]) -> np.ndarray:
    """手首カメラの画像を 180° 回し (指が上、画像の右が +y)、cross_uv に赤い × を描く。"""
    return draw_overlays(
        WRIST_CAMERA, np.rot90(image, 2), ("below",), below_uv=cross_uv
    )
