"""固定カメラの画像に手先の印を描き、画像の中の向きを世界座標の向きに直す。

手先の位置はロボット自身の状態で、画像への投影はカメラの校正値 (射影行列、sim の task の camera_matrix) で行う。
物体の位置は使わない。

- 手先の位置に赤い丸、手先の真下のテーブルの点に黄色い点を描き、線で結ぶ
- 「黄色い点を画像の左右と上下のどちらへ動かすか」の答えを、黄色い点の位置で、テーブルの面の上の動きが
  画像の上でどう動くか (射影のヤコビアン) の逆で世界座標の水平の向きに直す
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

# 手先の真下の点を描くテーブルの面の高さ [m]。libero_90 60 で、テーブルに置いたボウルとトレイの中心がこの高さにある
TABLE_Z = 0.44
# 画像の向きを世界座標の向きに直したとき、この割合より小さい成分の軸は動かさない
AXIS_MIN = 0.4
FIXED_CAPTION = (
    "Fixed camera, looking down diagonally at the table. The red circle marks the gripper. "
    "The yellow dot marks the point on the table directly below the gripper "
    "(the yellow line connects them):"
)
IMAGE_H = {"left": -1.0, "none": 0.0, "right": 1.0}
IMAGE_V = {"up": -1.0, "none": 0.0, "down": 1.0}


def project(matrix: np.ndarray, point: np.ndarray) -> np.ndarray:
    """世界座標の点を、射影行列で画像の画素 (u, v) に移す。"""
    a, b, w = matrix @ np.append(point, 1.0)
    return np.array([a / w, b / w])


def fixed_view(image: np.ndarray, matrix: np.ndarray, eef: np.ndarray) -> np.ndarray:
    """固定カメラの画像に、手先 (赤い丸) と手先の真下のテーブルの点 (黄色い点) を描く。"""
    im = Image.fromarray(np.ascontiguousarray(image))
    draw = ImageDraw.Draw(im)
    w = im.size[0]
    tip = project(matrix, eef)
    foot = project(matrix, np.array([eef[0], eef[1], TABLE_Z]))
    draw.line([tuple(tip), tuple(foot)], fill=(255, 220, 0), width=2)
    r = 0.025 * w
    draw.ellipse([*(foot - r / 2), *(foot + r / 2)], fill=(255, 220, 0))
    draw.ellipse([*(tip - r), *(tip + r)], outline=(255, 0, 0), width=3)
    return np.asarray(im)


def image_to_world(matrix: np.ndarray, eef: np.ndarray, duv: np.ndarray) -> np.ndarray:
    """固定カメラの画像の向き duv を、手先の真下のテーブルの点での世界座標の水平の向き (x, y) に直す。
    大きい方の成分が 1 になるようにそろえる。"""
    foot = np.array([eef[0], eef[1], TABLE_Z])
    eps = 0.01
    base = project(matrix, foot)
    jac = np.column_stack(
        [(project(matrix, foot + eps * e) - base) / eps for e in np.eye(3)[:2]]
    )
    d = np.linalg.solve(jac, duv)
    return d / np.abs(d).max()


def fixed_direction(
    matrix: np.ndarray, eef: np.ndarray, horizontal: str, vertical: str
) -> np.ndarray:
    """黄色い点を動かす画像の向き (left/none/right、up/none/down) を、軸ごとに -1、0、1 の
    世界座標の水平の向き (x, y) にする。"""
    duv = np.array([IMAGE_H[horizontal], IMAGE_V[vertical]])
    if not duv.any():
        return np.zeros(2)
    d = image_to_world(matrix, eef, duv)
    return np.where(np.abs(d) >= AXIS_MIN, np.sign(d), 0.0)


# 手首カメラの画像 (180° 回した後) で、手先の真下の点が写る縦の位置 (画像の高さに対する割合)。手先からの深さ [m]
# ごとに、手先を下向きにした姿勢で手首カメラの射影行列から求めた (libero_90 61 init 0、60 init 3 で同じ値)。
# 横の位置は 0.5 で変わらない
WRIST_CROSS_DEPTH = np.array(
    [0.0, 0.02, 0.04, 0.06, 0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.22, 0.24, 0.26, 0.28, 0.3]
)
WRIST_CROSS_V = np.array(
    [0.164, 0.228, 0.273, 0.306, 0.332, 0.353, 0.37, 0.384, 0.396, 0.406, 0.415, 0.422, 0.429, 0.435, 0.44, 0.445]
)


def wrist_cross_uv(eef_z: float) -> tuple[float, float]:
    """手先の高さ eef_z [m] で、手先の真下のテーブルの点 (高さ TABLE_Z) が手首の画像に写る位置。"""
    depth = max(eef_z - TABLE_Z, 0.0)
    return (0.5, float(np.interp(depth, WRIST_CROSS_DEPTH, WRIST_CROSS_V)))
