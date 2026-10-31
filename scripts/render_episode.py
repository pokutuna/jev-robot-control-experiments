"""記録した sim の状態 (sim_states.npz) から、エピソードの動画を描き直す。

    uv run --env-file .env scripts/render_episode.py experiments/NNN-slug/runs/init0-<日時> \\
        --size 480 --marks --out outputs/videos/init0.mp4

evaluator ノードは step ごとの MuJoCo の状態を sim_states.npz に書く。このスクリプトは、summary.json の
suite、task_id、init、seed、fixed_view で同じ場面を作り直し、記録した状態を 1 step ずつ戻してカメラを描画する。
カメラの大きさは実験のときと変えてよい。固定物の位置は状態に含まれず、reset のときの seed で決まるので、
記録の seed で reset してから戻す。

動画は固定カメラと手首カメラの画像を --layout の向きにつなぐ (h は横、v は縦)。手首カメラの画像は 180° 回し、
画像の左右を固定カメラにそろえる。--marks を付けると、Jev に渡す画像と同じ印 (固定カメラの手先の印、
手首カメラの赤い ×) を描く。--start、--end で step の範囲を、--every で何 step ごとに 1 フレームにするかを選ぶ
(動画は 20 fps なので、--every 2 で 2 倍速になる)。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

from s1cap.jev_policy import WRIST_CAMERA, wrist_view
from s1cap.marks import fixed_view
from s1cap.recorder import FPS
from s1cap.sim import LiberoEnv

FIXED_CAMERA = "agentview"
# 実験の evaluator と同じ × の位置 (画像の幅と高さに対する割合)
CROSS_UV = (0.5, 0.40)


def frame(env: LiberoEnv, state: np.ndarray, layout: str, marks: bool) -> np.ndarray:
    percept = env.restore(state)
    fixed = percept.images[FIXED_CAMERA]
    wrist = percept.images[WRIST_CAMERA]
    if marks:
        fixed = fixed_view(fixed, env.camera_matrix(FIXED_CAMERA), percept.eef.pos)
        wrist = wrist_view(wrist, CROSS_UV)
    else:
        wrist = np.rot90(wrist, 2)
    return np.concatenate([fixed, wrist], axis=1 if layout == "h" else 0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("run", type=Path, help="1 エピソードの記録のディレクトリ")
    parser.add_argument("--out", type=Path, help="既定は <run>/render.mp4")
    parser.add_argument("--size", type=int, default=480, help="カメラ 1 枚の一辺 [px]")
    parser.add_argument("--layout", choices=("h", "v"), default="h")
    parser.add_argument("--marks", action="store_true")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, help="この step まで描く (含む)")
    parser.add_argument("--every", type=int, default=1)
    args = parser.parse_args()

    summary = json.loads((args.run / "summary.json").read_text())
    record = np.load(args.run / "sim_states.npz")
    steps, states = record["steps"], record["states"]
    end = steps[-1] if args.end is None else args.end
    keep = (steps >= args.start) & (steps <= end)
    steps, states = steps[keep][:: args.every], states[keep][:: args.every]

    env = LiberoEnv(
        summary["suite"],
        summary["task_id"],
        image_size=args.size,
        cameras=(FIXED_CAMERA, WRIST_CAMERA),
        fixed_view=summary["fixed_view"],
    )
    env.reset(summary["init"], seed=summary["seed"])
    out = args.out or args.run / "render.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(out, fps=FPS, macro_block_size=1) as writer:
        for state in states:
            writer.append_data(frame(env, state, args.layout, args.marks))
    env.close()
    print(f"{len(steps)} frames (step {steps[0]}〜{steps[-1]}) -> {out}")


if __name__ == "__main__":
    main()
