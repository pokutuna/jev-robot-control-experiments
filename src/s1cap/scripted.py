"""手書きの方策: 決めた順に命令を出し、前の命令の結果を受けてから次を出す。

物体の位置を画像から推定しないので、物体の姿勢は「JSON 入力」条件として外から受け取る。
"""

from __future__ import annotations

from typing import Any

import numpy as np

# ボウルの +y 側の縁を掴む位置 (ボウルの中心から)。TOP_DOWN の向きでは指が y 方向に閉じる
BOWL_GRASP_OFFSET = np.array([0.0, 0.06, 0.03])
APPROACH_HEIGHT = 0.10
LIFT_HEIGHT = 0.15
PLACE_HEIGHT = 0.06  # 皿の上で離す高さ (皿の中心からの z)


def bowl_on_plate_commands(objects: dict[str, Any]) -> list[dict[str, Any]]:
    """LIBERO-Goal の「put the bowl on the plate」の命令列。objects は物体名 → {"pos": [...]}。"""
    bowl = np.asarray(objects["akita_black_bowl_1"]["pos"])
    plate = np.asarray(objects["plate_1"]["pos"])
    grasp = bowl + BOWL_GRASP_OFFSET
    place = plate + [0.0, BOWL_GRASP_OFFSET[1], PLACE_HEIGHT]
    top_down = [1.0, 0.0, 0.0, 0.0]
    return [
        {"type": "gripper", "closed": False},
        {"type": "move_to", "pos": grasp + [0, 0, APPROACH_HEIGHT], "quat": top_down},
        {"type": "move_to", "pos": grasp},
        {"type": "gripper", "closed": True},
        {"type": "move_delta", "dpos": [0, 0, LIFT_HEIGHT]},
        {"type": "move_to", "pos": place + [0, 0, LIFT_HEIGHT]},
        {"type": "move_to", "pos": place},
        {"type": "gripper", "closed": False},
        {"type": "move_delta", "dpos": [0, 0, APPROACH_HEIGHT]},
    ]


class ScriptedPolicy:
    """命令列を 1 つずつ出す。命令の結果 (reached 以外も) を受けたら次を出す。"""

    def __init__(self, commands: list[dict[str, Any]]) -> None:
        self.commands = [
            {"id": i, **_jsonable(c)} for i, c in enumerate(commands, start=1)
        ]
        self._next = 0
        self.results: list[dict[str, Any]] = []

    def start(self) -> dict[str, Any] | None:
        return self._advance()

    def on_result(self, result: dict[str, Any]) -> dict[str, Any] | None:
        """出した命令の結果を受け、次の命令を返す。命令列を出し終えたら None。"""
        if self._next == 0 or result["id"] != self.commands[self._next - 1]["id"]:
            return None  # 自分が今待っている命令の結果ではない
        self.results.append(result)
        return self._advance()

    @property
    def done(self) -> bool:
        return len(self.results) == len(self.commands)

    def _advance(self) -> dict[str, Any] | None:
        if self._next >= len(self.commands):
            return None
        command = self.commands[self._next]
        self._next += 1
        return command


def _jsonable(command: dict[str, Any]) -> dict[str, Any]:
    return {
        k: [float(x) for x in v] if isinstance(v, (list, np.ndarray)) else v
        for k, v in command.items()
    }
