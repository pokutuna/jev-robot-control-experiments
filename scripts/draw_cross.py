"""録画済みのエピソードの動画の手首の画像に、Jev に渡すときと同じ赤い × を描いた動画を作る。

動画は左に固定カメラ、右に手首カメラの画像を同じ幅で並べたもの (nodes/evaluator.py が書く形)。
手首の画像を 180° 回し、--cross の位置 (画像の幅と高さに対する割合) に × を描いて、
同じディレクトリに episode_cross.mp4 を書く。

    uv run scripts/draw_cross.py outputs/runs/20261026-151515
"""

import argparse
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

from s1cap.jev_policy import wrist_view
from s1cap.jev_staged import CROSS_UV
from s1cap.recorder import FPS


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("run_dirs", nargs="+", type=Path, help="outputs/runs/<日時>")
    parser.add_argument(
        "--cross",
        default=",".join(map(str, CROSS_UV)),
        help="× の位置 (横,縦)。既定は s1cap.jev_staged.CROSS_UV",
    )
    args = parser.parse_args()
    cross_uv = tuple(float(v) for v in args.cross.split(","))

    for run_dir in args.run_dirs:
        reader = imageio.get_reader(run_dir / "episode.mp4")
        out = run_dir / "episode_cross.mp4"
        writer = imageio.get_writer(out, fps=FPS, macro_block_size=1)
        for frame in reader:
            half = frame.shape[1] // 2
            wrist = wrist_view(frame[:, half:], cross_uv)
            writer.append_data(np.concatenate([frame[:, :half], wrist], axis=1))
        writer.close()
        reader.close()
        print(out)


if __name__ == "__main__":
    main()
