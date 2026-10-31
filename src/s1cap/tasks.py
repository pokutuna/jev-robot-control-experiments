"""タスクごとの物体の名前と、真値から掴む点と離す点を決める値。

どれも真値を使う所 (評価と、真値を文で渡す実験 001、013 の方策) のための値で、画像だけで動く方策には渡さない。
物体の大きさは libero_90 61 の init 0 で、衝突の形の外接箱を測った (x × y × 高さ)。

- プリンの箱: 8.0 × 4.6 × 2.7 cm。位置 (pos) は箱の中心
- ドレッシングの瓶: 3.6 × 5.3 × 14.6 cm。位置は底から 2.3 cm の高さ
- 黒いボウル: 10.7 × 10.7 × 5.1 cm。位置は底の近く
- トレイ: 29.7 × 16.7 × 8.2 cm。位置は底

指は世界座標の y の向きに閉じ、開いたときの幅は約 8 cm。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TaskSpec:
    object_body: str  # 運ぶ物の、真値 (ground_truth の objects) での名前
    target_body: str  # 置き場所の名前
    object_word: str  # 方策の文に書く運ぶ物の名前
    grasp_offset: np.ndarray  # 掴む手先の位置 (運ぶ物の位置から)
    release_offset: (
        np.ndarray
    )  # 離す手先の位置 (置き場所の位置から)。運ぶ物が置き場所の中心の上に来る


TRAY = "wooden_tray_1"

TASKS = {
    # 黒いボウルは指より大きいので、+y 側の縁を掴む。s1cap.scripted と同じ値
    ("libero_90", 60): TaskSpec(
        object_body="akita_black_bowl_1",
        target_body=TRAY,
        object_word="bowl",
        grasp_offset=np.array([0.0, 0.06, 0.03]),
        release_offset=np.array([0.0, 0.06, 0.06]),
    ),
    # 箱の中心の高さで挟む
    ("libero_90", 61): TaskSpec(
        object_body="chocolate_pudding_1",
        target_body=TRAY,
        object_word="pudding box",
        grasp_offset=np.array([0.0, 0.0, 0.0]),
        release_offset=np.array([0.0, 0.0, 0.05]),
    ),
    # 瓶の底から 6 cm の高さで挟む
    ("libero_90", 62): TaskSpec(
        object_body="new_salad_dressing_1",
        target_body=TRAY,
        object_word="dressing bottle",
        grasp_offset=np.array([0.0, 0.0, 0.037]),
        release_offset=np.array([0.0, 0.0, 0.08]),
    ),
}


def task_spec(suite: str, task_id: int) -> TaskSpec:
    try:
        return TASKS[(suite, int(task_id))]
    except KeyError:
        raise KeyError(
            f"{suite} {task_id} の TaskSpec が s1cap.tasks.TASKS に無い"
        ) from None


def spec_of_run(summary: dict) -> TaskSpec:
    """記録の summary.json のタスクの TaskSpec。task_id を記録する前の実験はどれも libero_90 60。"""
    return task_spec(summary.get("suite", "libero_90"), summary.get("task_id", 60))
