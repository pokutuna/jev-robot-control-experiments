"""LIBERO のタスクを MuJoCo のビューワで表示し、対話シェルから命令を送る。

macOS ではビューワを開くために mjpython で起動する。

    uv run mjpython scripts/viewer.py --suite libero_goal --task 8

シェルでは次の名前が使える。

    env         LiberoEnv。env.perceive()、env.ground_truth()、env.step(action)、env.reset() など
    move_to     手先を目標の位置に動かす。move_to(env, [x, y, z])
    move_delta  手先を今の位置から動かす。move_delta(env, [0, 0, 0.1])
    set_gripper 指を閉じる・開く。set_gripper(env, True)
    pos(name)   物体や固定物の位置 (シミュレータの真値)。pos("akita_black_bowl_1")
    np          numpy
"""

import argparse
import code

import numpy as np

from s1cap.control import move_delta, move_to, set_gripper
from s1cap.sim import LiberoEnv


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task", type=int, default=8, help="suite 内のタスク番号")
    parser.add_argument("--init", type=int, default=0, help="init state の番号")
    parser.add_argument("--seed", type=int, default=0)
    # ビューワとは別に描画するカメラ画像の一辺 [px]。小さいほど step が速い
    parser.add_argument("--size", type=int, default=128, help="カメラ画像の一辺 [px]")
    args = parser.parse_args()

    env = LiberoEnv(args.suite, args.task, image_size=args.size)
    env.reset(args.init, seed=args.seed)
    env.launch_viewer()

    def pos(name: str) -> np.ndarray:
        gt = env.ground_truth()
        return {**gt.objects, **gt.fixtures}[name].pos

    gt = env.ground_truth()
    banner = "\n".join(
        [
            f"task: {env.task_name}",
            f"instruction: {env.instruction}",
            f"objects: {', '.join(gt.objects)}",
            f"fixtures: {', '.join(gt.fixtures)}",
            'example: move_to(env, pos("akita_black_bowl_1") + [0, 0, 0.1])',
        ]
    )
    namespace = {
        "env": env,
        "move_to": move_to,
        "move_delta": move_delta,
        "set_gripper": set_gripper,
        "pos": pos,
        "np": np,
    }
    try:
        code.interact(banner=banner, local=namespace, exitmsg="")
    finally:
        env.close()


if __name__ == "__main__":
    main()
