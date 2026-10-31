"""Code as Policies: LLM が書いた手順のプログラムを動かし、プログラムの中で Jev に画像を問う方策 (実験 007、009、011)。

LLM (CODE_MODEL、既定は deepseek/deepseek-v4.1-flash-1017) には、タスクの指示文、ロボットを動かす関数と
Jev に画像を問う関数の一覧、ロボットとシーンについての事実と測った答えの傾向 (PROMPT、KNOWLEDGE) を渡し、
手順を Python のプログラムで書かせる。プログラムは scripts/generate_programs.py で実行の前に生成してファイルに置き、読んでから動かす。
物体の位置を返す関数は無く、物体の位置の真値も渡さない。

プログラムは別スレッドで上から順に動く。移動や指の関数を呼ぶと、その命令を policy ノードに渡し、
sim の結果と次の観測が届くまで待つ。policy ノードから見ると、decide() 1 回が命令 1 つにあたる。
画像を問う関数は、その時点の観測 (直前の命令の結果より後の観測) の画像で Jev を呼ぶ。

プログラムは builtins を絞った名前空間で exec する。import は使えず、math と np (numpy) を渡す。
これは誤って外部に触れないための制限で、安全な sandbox ではない。生成したプログラムは実行の前に読む。
"""

from __future__ import annotations

import builtins
import json
import math
import os
import queue
import re
import threading
import time
import traceback
import urllib.request
from typing import Any

import numpy as np
from typesafe_sdk import Choice, Noul, Question, TypeSafeClient

from s1cap import jev
from s1cap.jev_policy import WRIST_CAMERA, Decision, Observation, wrist_view
from s1cap.jev_staged import (
    CROSS_UV,
    DEFAULT_FIXED_CAMERA,
    IMAGE_TO_WORLD,
    TARGETS,
    TOP_DOWN,
    WRIST_CAPTION,
)
from s1cap.marks import FIXED_CAPTION as MARKED_FIXED_CAPTION
from s1cap.marks import fixed_direction, fixed_view

DEFAULT_CODE_MODEL = "deepseek/deepseek-v4.1-flash-1017"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_JEV_BUDGET = 360  # 005 の上限 (120 回の判断で 3 回ずつ) と同じ
DEFAULT_MAX_MOVES = 120
# 下ろす命令を打ち切る step 数。jev_staged と同じく、当たって止まったら 2 秒で次へ進む
DOWN_TIMEOUT_STEPS = 40
# プログラムが命令を出さずにこの秒数を超えたら止める (Jev を呼ばない無限ループなど)
WAIT_S = 300.0

# PROMPT の「Facts」と「Reliability」は KNOWLEDGE から選ぶ
PROMPT = """\
Write a Python program that controls a robot arm in a simulator to do this task:
"{instruction}"

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
{facts}
## Reliability of the vision answers (measured on this task)
{reliability}
## Limits
- At most {jev_budget} vision calls and {max_moves} motion calls in total. The program is stopped when
  it goes over either limit.
- Answers can be wrong or flip back and forth. Make sure the program does not get stuck.

Output only the Python code, with no explanation.
"""

# プロンプトに入れる、このロボットと場面についての知識。キーはその知識を得た実験
KNOWLEDGE = {
    # 「Facts」は 005 (s1cap.jev_staged) のコードに書いた値、「Reliability」は 003〜006 で測った傾向 (実験 007)
    "006": {
        "facts": """\
- The fingers close along the world y axis.
- Grip the bowl by its rim. The rim to grip is 6 cm from the bowl center in +y.
- The red cross of wrist_direction is placed for the start height. Do horizontal alignment at the
  start height, then go down.
- To go down onto something, move down 3 cm at a time until move_by returns False.
- Before closing the fingers, move up 1.5 cm from where the downward move stopped.
- After close_gripper(), gripper_opening() greater than 0.003 means something is held. A smaller
  value means the grasp missed.
- While the bowl is held by its rim, the bowl center is 6 cm in -y from the gripper.
- Carry objects at the start height.
""",
        "reliability": """\
- Each answer is a direction only, not a distance. Move about 2 cm per step and ask again after
  each step.
- wrist_direction is mostly correct when the target is visible in the wrist camera image.
- fixed_direction toward the tray is mostly correct while the gripper is more than about 12 cm from
  the tray center. Near the tray it often answers (0, 0). Toward a bowl it is often wrong.
- in_wrist_view sometimes answers high for the tray when the tray is not in the image.
""",
    },
    # 006 に、008 (行き先の言い方)、004-2 (縁を行き先にした答え)、010 (縁の側と、縁への問いで合わせた結果) で
    # 分かったことを足す (実験 011)。掴む縁は 010 と同じ -y の側にし、縁の位置 (中心から 6 cm) は渡さない
    "010": {
        "facts": """\
- The fingers close along the world y axis.
- The bowl is wider than the open fingers. Grip the bowl by its rim on the -y side. The wrist camera
  image is turned so that its right is +y and its bottom is +x, so this rim is the left edge of the
  bowl in the wrist camera image.
- The red cross of wrist_direction is placed for the start height. Do horizontal alignment at the
  start height, then go down.
- To go down onto something, move down 3 cm at a time until move_by returns False.
- Before closing the fingers, move up 1.5 cm from where the downward move stopped.
- After close_gripper(), gripper_opening() greater than 0.003 means something is held. A smaller
  value means the grasp missed.
- While the bowl is held by its -y rim, the bowl center is about 6 cm in +y from the gripper.
- Carry objects at the start height.
""",
        "reliability": """\
- Each answer is a direction only, not a distance. Move about 2 cm per step and ask again after
  each step.
- wrist_direction is mostly correct when the target is visible in the wrist camera image. It almost
  never answers a direction away from the target. On an axis where the cross is within about 2 cm
  of the target, it often answers 0.
- The answers of wrist_direction depend on the target phrase. With "the center of the bowl to pick
  up", it answered toward the bowl center in most cases when the cross was 4 cm or more away. With
  "the black bowl on the left", it answered 0 in most cases even when the cross was 4 cm away.
- Aligning the cross on "the center of the bowl to pick up" by 2 cm steps stopped 0 to 3 cm from
  the bowl center.
- With a rim as the target, such as "the left edge of the bowl to pick up", wrist_direction answered
  the y sign toward that rim, but almost always answered 0 for x, even when the cross was 4 cm away
  in x.
- fixed_direction toward the tray is mostly correct while the gripper is more than about 12 cm from
  the tray center. Near the tray it often answers (0, 0). Toward a bowl it is often wrong.
- in_wrist_view sometimes answers high for the tray when the tray is not in the image.
""",
    },
    # レポートの実験 (019、020)。段ごとの小さな作業の確かめ (015 の掴めるか、016 の言い方) で分かったことを、
    # この場面 (libero_90 60〜62 の LIVING_ROOM_SCENE4) の物ごとに渡す。手順と値はどのタスクでも LLM が決める
    "016": {
        "facts": """\
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
""",
        "reliability": """\
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
""",
    },
}
# レポートの実験 (021、022)。016 に、手順の骨組みを task 61、60 で回して分かったこと (017、018) を足す。
# 骨組みを直すのに人が使った知見を、LLM にも同じだけ渡す
KNOWLEDGE["017"] = {
    "facts": KNOWLEDGE["016"]["facts"]
    + """\
- When placing the pudding box in the tray, the fingers opened only to 6.8 cm where the downward
  move stopped, pressing against the tray dividers, and lifting afterwards raised the tray by 21-22
  cm (2 of 10 runs). Moving up 3 cm from where the downward move stopped before opening did not
  raise the tray in 20 runs.
""",
    "reliability": KNOWLEDGE["016"]["reliability"]
    + """\
Measured in full pick-and-place runs while an object was held:
- The held object appears just -x of the red cross in the wrist camera image and hides that area.
- Holding the pudding box (20 runs): fixed_direction answered (0, 0) for the center of the tray with
  the gripper 0.7 to 4.7 cm in x and -2.0 to -5.9 cm in y from it. After that, wrist_direction
  toward the tray answered x away from the tray in 71 of 102 cases (toward it in 8, 0 in 23), and y
  toward it in 23, 0 in 29, never away.
- Holding the black bowl by its rim (10 runs): fixed_direction answered (0, 0) for the center of the
  tray with the gripper -6.7 to -15.0 cm in x and -6.0 to -9.8 cm in y from it. After that,
  wrist_direction toward the tray answered y toward it in 6 of 16 cases and 0 in 10.
""",
}
DEFAULT_KNOWLEDGE = "006"

SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in [
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "float",
        "int",
        "isinstance",
        "len",
        "list",
        "max",
        "min",
        "range",
        "reversed",
        "round",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
        "Exception",
        "ValueError",
        "RuntimeError",
        "TypeError",
        "KeyError",
        "IndexError",
        "ZeroDivisionError",
        "type",
        "__build_class__",
    ]
}


def prompt(
    instruction: str,
    *,
    jev_budget: int = DEFAULT_JEV_BUDGET,
    max_moves: int = DEFAULT_MAX_MOVES,
    knowledge: str = DEFAULT_KNOWLEDGE,
) -> str:
    return PROMPT.format(
        instruction=instruction,
        jev_budget=jev_budget,
        max_moves=max_moves,
        **KNOWLEDGE[knowledge],
    )


class EmptyAnswer(RuntimeError):
    """LLM の答えの本文が空だった。"""


def generate(text: str, model: str = DEFAULT_CODE_MODEL) -> tuple[str, dict[str, Any]]:
    """OpenRouter の chat completions で prompt からプログラムを書かせ、コードと記録 (モデル、トークン数、
    費用 [USD]、時間 [ms]) を返す。"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY が無い。.env に書き、--env-file .env で渡す"
        )
    body = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
        "usage": {"include": True},
    }
    request = urllib.request.Request(
        CHAT_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read())
    latency_ms = (time.perf_counter() - started) * 1e3
    choice = result["choices"][0]
    content = choice["message"]["content"]
    if not content:
        # 考える途中で出力の長さの上限に達すると、答えの本文が空で返る
        raise EmptyAnswer(f"答えが空 (finish_reason: {choice.get('finish_reason')})")
    usage = result.get("usage", {})
    return extract_code(content), {
        "model": result.get("model", model),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "cost_usd": usage.get("cost"),
        "latency_ms": round(latency_ms),
    }


def extract_code(content: str) -> str:
    """答えにコードブロックがあれば、その中身を返す。"""
    blocks = re.findall(r"```(?:python)?\n(.*?)```", content, re.DOTALL)
    return ("\n".join(blocks) if blocks else content).strip() + "\n"


class Stop(BaseException):
    """上限を超えたときにプログラムを止める。プログラムの except Exception で捕まらないよう BaseException にする。"""


def direction_questions(
    instruction: str, camera: str, mark: str, target: str
) -> dict[str, Question]:
    qs: dict[str, Question] = {}
    for axis, (a, b) in {"h": ("left", "right"), "v": ("up", "down")}.items():
        word = "horizontally" if axis == "h" else "vertically"
        qs[axis] = Choice(
            instructions=(
                f"Task: {instruction}. In the {camera} camera image, to move the {mark} "
                f"onto {target}, which way should it move {word}?"
            ),
            criteria={
                a: None,
                "none": f"the {mark} is already {word} at {target}",
                b: None,
            },
        )
    return qs


class CaPPolicy:
    def __init__(
        self,
        client: TypeSafeClient,
        instruction: str,
        program: str,
        camera_matrix: np.ndarray,
        *,
        program_name: str = "<program>",
        fixed_camera: str = DEFAULT_FIXED_CAMERA,
        jev_budget: int = DEFAULT_JEV_BUDGET,
        max_moves: int = DEFAULT_MAX_MOVES,
        fixed_targets: bool = False,
    ) -> None:
        """fixed_targets にすると、向きの関数 (wrist_direction、fixed_direction) は、プログラムが渡した行き先の
        言い方を使わず、実験 006 の言い方 (s1cap.jev_staged.TARGETS) で Jev に問う。行き先に tray を含めば
        トレイの中心、bowl を含めばボウルの中心にする。手順は同じまま、問いの言い方だけを 006 にそろえる比較に使う。"""
        self.client = client
        self.fixed_targets = fixed_targets
        self.instruction = instruction
        self.code = compile(program, program_name, "exec")
        self.camera_matrix = camera_matrix
        self.fixed_camera = fixed_camera
        self.jev_budget = jev_budget
        self.max_moves = max_moves
        self.started = (
            False  # 最初の判断で手先を下向きにそろえてから、プログラムを動かす
        )
        self.obs: Observation | None = None
        self.status = "none"  # 直前の命令の結果
        self.jev_calls = 0
        self.moves = 0
        self.thread: threading.Thread | None = None
        self.to_program: queue.Queue[None] = queue.Queue()
        self.to_node: queue.Queue[tuple[str, Any]] = queue.Queue()
        # 次の命令までに呼んだ関数と Jev の呼び出し。命令を出すときに判断の記録に入れて空にする
        self.api_log: list[dict[str, Any]] = []
        self.calls: dict[str, dict[str, Any]] = {}
        self.prints: list[str] = []
        self.images: dict[str, Any] = {}  # 今の観測の画像の image_content
        self._next_id = 1

    def decide(self, obs: Observation) -> Decision:
        self.obs = obs
        self.images = {}
        if not self.started:
            self.started = True
            eef = obs.robot_state["eef"]["pos"]
            return Decision(
                self._new({"type": "move_to", "pos": eef, "quat": TOP_DOWN}),
                {"obs_step": obs.step, "intent": "setup"},
            )
        if self.thread is None:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        else:
            self.to_program.put(
                None
            )  # 待っている移動の関数に、結果と次の観測が届いたことを伝える
        try:
            kind, value = self.to_node.get(timeout=WAIT_S)
        except queue.Empty:
            kind, value = "end", f"no command for {WAIT_S:.0f} s"
        record: dict[str, Any] = {"obs_step": obs.step, "api": self.api_log}
        if self.calls:
            record["calls"] = self.calls
            record["latency_ms"] = {k: c["latency_ms"] for k, c in self.calls.items()}
        if self.prints:
            record["print"] = self.prints
        self.api_log, self.calls, self.prints = [], {}, []
        if kind == "end":
            record["done"] = value
            return Decision(None, record)
        record["command"] = value
        return Decision(value, record)

    def on_result(self, result: dict[str, Any], command: dict[str, Any]) -> None:
        self.status = result["status"]

    # プログラムのスレッド

    def _run(self) -> None:
        namespace = {
            "__builtins__": SAFE_BUILTINS,
            "__name__": "__main__",
            **self._api(),
        }
        try:
            exec(self.code, namespace)  # noqa: S102  生成したプログラムは実行の前に読む
            reason = "program finished"
        except Stop as e:
            reason = f"stopped: {e}"
        except Exception:  # noqa: BLE001  プログラムの誤りはエピソードの終わり方として記録する
            reason = "program error: " + traceback.format_exc(limit=-1).strip()
        self.to_node.put(("end", reason))

    def _api(self) -> dict[str, Any]:
        return {
            "gripper_position": self.gripper_position,
            "gripper_opening": self.gripper_opening,
            "move_by": self.move_by,
            "move_to": self.move_to,
            "open_gripper": self.open_gripper,
            "close_gripper": self.close_gripper,
            "wrist_direction": self.wrist_direction,
            "fixed_direction": self.fixed_direction,
            "in_wrist_view": self.in_wrist_view,
            "check": self.check,
            "print": self._print,
            "math": math,
            "np": np,
        }

    def gripper_position(self) -> tuple[float, float, float]:
        assert self.obs is not None
        x, y, z = self.obs.robot_state["eef"]["pos"]
        return (float(x), float(y), float(z))

    def gripper_opening(self) -> float:
        assert self.obs is not None
        return float(self.obs.robot_state["gripper_width"])

    def move_by(self, dx: float, dy: float, dz: float) -> bool:
        dpos = [float(dx), float(dy), float(dz)]
        command: dict[str, Any] = {"type": "move_delta", "dpos": dpos}
        if dpos[2] < 0:
            command["timeout_steps"] = DOWN_TIMEOUT_STEPS
        reached = self._send(command) == "reached"
        self._log("move_by", dpos, reached)
        return reached

    def move_to(self, x: float, y: float, z: float) -> bool:
        pos = [float(x), float(y), float(z)]
        command: dict[str, Any] = {"type": "move_to", "pos": pos, "quat": TOP_DOWN}
        if pos[2] < self.gripper_position()[2] - 1e-3:
            command["timeout_steps"] = DOWN_TIMEOUT_STEPS
        reached = self._send(command) == "reached"
        self._log("move_to", pos, reached)
        return reached

    def open_gripper(self) -> None:
        self._send({"type": "gripper", "closed": False})
        self._log("open_gripper", [], None)

    def close_gripper(self) -> None:
        self._send({"type": "gripper", "closed": True})
        self._log("close_gripper", [], None)

    def wrist_direction(self, target: str) -> tuple[int, int]:
        qs = direction_questions(
            self.instruction, "wrist", "red cross", self._direction_target(target)
        )
        r = self._ask("wrist_direction", self._wrist_state(), qs)
        h, v = r.choices["h"].choice, r.choices["v"].choice
        d = IMAGE_TO_WORLD[h] + IMAGE_TO_WORLD[v]
        result = (int(d[0]), int(d[1]))
        answers = {"h": h, "v": v}
        if self.fixed_targets:
            answers["asked"] = self._direction_target(target)
        self._log("wrist_direction", [target], result, answers)
        return result

    def fixed_direction(self, target: str) -> tuple[int, int]:
        qs = direction_questions(
            self.instruction, "fixed", "yellow dot", self._direction_target(target)
        )
        r = self._ask("fixed_direction", self._fixed_state(), qs)
        h, v = r.choices["h"].choice, r.choices["v"].choice
        eef = np.asarray(self.gripper_position())
        d = fixed_direction(self.camera_matrix, eef, h, v)
        result = (int(d[0]), int(d[1]))
        answers = {"h": h, "v": v}
        if self.fixed_targets:
            answers["asked"] = self._direction_target(target)
        self._log("fixed_direction", [target], result, answers)
        return result

    def in_wrist_view(self, target: str) -> float:
        q = Noul(
            instructions=f"Task: {self.instruction}. Is {target} visible in the wrist camera image?"
        )
        r = self._ask("in_wrist_view", self._wrist_state(), {"q": q})
        result = round(r.nouls["q"].noul, 3)
        self._log("in_wrist_view", [target], result)
        return result

    def check(self, question: str) -> float:
        q = Noul(instructions=f"Task: {self.instruction}. {question}")
        state = [*self._fixed_state(), *self._wrist_state()[1:]]
        r = self._ask("check", state, {"q": q})
        result = round(r.nouls["q"].noul, 3)
        self._log("check", [question], result)
        return result

    def _direction_target(self, target: str) -> str:
        target = str(target)
        if not self.fixed_targets:
            return target
        if "tray" in target.lower():
            return TARGETS["tray"]
        if "bowl" in target.lower():
            return TARGETS["bowl"]
        return target

    def _print(self, *args: Any, **kwargs: Any) -> None:
        self.prints.append(" ".join(str(a) for a in args))

    def _send(self, command: dict[str, Any]) -> str:
        if self.moves >= self.max_moves:
            raise Stop(f"more than {self.max_moves} motion calls")
        self.moves += 1
        self.to_node.put(("command", self._new(command)))
        self.to_program.get()
        return self.status

    def _ask(self, kind: str, state: list[Any], questions: dict[str, Question]) -> Any:
        if self.jev_calls >= self.jev_budget:
            raise Stop(f"more than {self.jev_budget} vision calls")
        self.jev_calls += 1
        response, latency_ms = jev.ask(self.client, state, questions)
        self.calls[f"{kind}_{self.jev_calls}"] = jev.call_record(response, latency_ms)
        return response

    def _log(
        self, fn: str, args: list[Any], result: Any, answers: dict | None = None
    ) -> None:
        entry: dict[str, Any] = {"fn": fn, "args": args, "result": result}
        if answers:
            entry["answers"] = answers
        self.api_log.append(entry)

    def _wrist_state(self) -> list[Any]:
        if "wrist" not in self.images:
            assert self.obs is not None
            image = wrist_view(self.obs.images[WRIST_CAMERA], CROSS_UV)
            self.images["wrist"] = jev.image_content(image)
        return [f"Task: {self.instruction}", WRIST_CAPTION, self.images["wrist"]]

    def _fixed_state(self) -> list[Any]:
        if "fixed" not in self.images:
            assert self.obs is not None
            image = fixed_view(
                self.obs.images[self.fixed_camera],
                self.camera_matrix,
                np.asarray(self.obs.robot_state["eef"]["pos"]),
            )
            self.images["fixed"] = jev.image_content(image)
        return [f"Task: {self.instruction}", MARKED_FIXED_CAPTION, self.images["fixed"]]

    def _new(self, command: dict[str, Any]) -> dict[str, Any]:
        command = {"id": self._next_id, **command}
        self._next_id += 1
        return command
