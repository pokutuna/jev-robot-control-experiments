"""LIBERO のタスクを 1 つ reset し、カメラ画像、ロボットの知覚、シミュレータの真値を保存する。

uv run scripts/probe_scene.py --suite libero_goal --task 8
"""

import argparse
import json
from pathlib import Path

from PIL import Image

from s1cap.sim import LiberoEnv


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task", type=int, default=8, help="suite 内のタスク番号")
    parser.add_argument("--init", type=int, default=0, help="init state の番号")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--size", type=int, default=512, help="カメラ画像の一辺 [px]")
    parser.add_argument("--out", type=Path, default=Path("outputs/probe"))
    args = parser.parse_args()

    env = LiberoEnv(args.suite, args.task, image_size=args.size)
    percept = env.reset(args.init, seed=args.seed)

    out = (
        args.out
        / f"{args.suite}_{args.task:02d}_{env.task_name}"
        / f"init{args.init:02d}"
    )
    out.mkdir(parents=True, exist_ok=True)
    for cam, image in percept.images.items():
        Image.fromarray(image).save(out / f"{cam}.png")
    scene = {
        "suite": args.suite,
        "task_id": args.task,
        "task_name": env.task_name,
        "instruction": env.instruction,
        "init_index": args.init,
        "seed": args.seed,
        "percept": percept.to_dict(),
        "ground_truth": env.ground_truth().to_dict(),
    }
    (out / "scene.json").write_text(
        json.dumps(scene, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(scene, indent=2, ensure_ascii=False))
    print(f"saved to {out}")
    env.close()


if __name__ == "__main__":
    main()
