"""実験の記録から、方策が選んだ横の向き (x、y) が行き先へ向かっていたかを数える。

    uv run scripts/direction_accuracy.py experiments/002-image-direction
    uv run scripts/direction_accuracy.py experiments/001-text-baseline --offset 0,0.06

libero_90 60 (黒いボウルをトレイに入れる) で、ボウルを持ち上げる前の行き先を掴むボウルの中心、
持ち上げた後をトレイの中心とする。ボウルが初めより LIFTED 以上高く、向きが 30° 以上傾いていないときに
持ち上げたとする (押されて傾いただけのボウルは持ち上げていない)。--offset (x,y [m]) を与えると、どちらの行き先もその分ずらす。
ボウルの縁を掴む方策 (実験 001 は +y に 6 cm) で使う。判断に使った観測の step (decision の obs_step) の真値から、
手先から行き先への差を軸ごとに求め、その判断で送った move_delta の向きと比べる。
差が OFF_TARGET 以上の軸だけを数え、送った向きが行き先へ近づく (toward)、その軸を動かさない (still)、
遠ざかる (away) に分ける。行き先の近くでの微調整は数えない。move_delta 以外の命令 (指、hold など) を
送った判断と、ボウルを持ち上げた後に指を開いてからの判断は数えない。行き先は方策の段 (近づく、持ち上げる、運ぶ) によらず真値で決めるので、
持ち上げる段で横を動かさない判断も still に入る。
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from s1cap.jev_text import BOWL, TRAY

OFF_TARGET = 0.02  # [m]
RESULTS = ("toward", "still", "away")
LIFTED = 0.03  # ボウルが初めの高さからこれだけ上がったら持ち上げたとする [m]
# ボウルの向きが初めからこれ以上傾いていたら、押されて傾いただけで、持ち上げてはいないとする
TILTED = np.cos(np.radians(30))


def up_axis(quat: list[float]) -> np.ndarray:
    """xyzw の四元数で回した物体の z 軸の、世界座標の向き。"""
    x, y, z, w = quat
    return np.array([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)])


def judge(run_dir: Path, offset: np.ndarray) -> Counter:
    gt = {
        g["step"]: g["objects"]
        for g in map(json.loads, (run_dir / "ground_truth.jsonl").open())
    }
    eef = {
        r["step"]: np.array(r["eef"]["pos"])
        for r in map(json.loads, (run_dir / "robot_state.jsonl").open())
    }
    bowl_z0 = gt[min(gt)][BOWL]["pos"][2]
    bowl_up0 = up_axis(gt[min(gt)][BOWL]["quat"])
    events = [json.loads(line) for line in (run_dir / "events.jsonl").open()]
    commands = {e["step"]: e for e in events if e["kind"] == "command"}
    count: Counter = Counter()
    lifted = False  # 一度持ち上げたら、以後は運ぶ段とする
    for d in events:
        released = d["kind"] == "command" and d["type"] == "gripper" and not d["closed"]
        if lifted and released:
            break  # 離した後の判断は数えない
        if d["kind"] != "decision" or "obs_step" not in d:
            continue
        command = commands.get(d["step"])
        step = d["obs_step"]
        if command is None or command["type"] != "move_delta" or step not in eef:
            continue
        objects = gt[step]
        bowl = objects[BOWL]
        lifted = lifted or (
            bowl["pos"][2] - bowl_z0 > LIFTED
            and up_axis(bowl["quat"]) @ bowl_up0 > TILTED
        )
        target = np.array(objects[TRAY if lifted else BOWL]["pos"][:2]) + offset
        diff = target - eef[step][:2]
        got = np.sign(np.array(command["dpos"][:2])) * np.sign(diff)
        phase = "carry" if lifted else "approach"
        for axis, off, g in zip("xy", np.abs(diff) >= OFF_TARGET, got):
            if off:
                count[(phase, axis, RESULTS[1 - int(g)])] += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("exp_dir", type=Path)
    parser.add_argument(
        "--offset", default="0,0", help="行き先のずらし x,y [m] (既定 0,0)"
    )
    args = parser.parse_args()
    offset = np.array([float(v) for v in args.offset.split(",")])
    total: Counter = Counter()
    for run_dir in sorted((args.exp_dir / "runs").glob("init*")):
        if (run_dir / "summary.json").exists() and (
            run_dir / "ground_truth.jsonl"
        ).exists():
            total += judge(run_dir, offset)
    print(f"行き先から {OFF_TARGET * 100:.0f} cm 以上ずれている軸の、判断の数 (割合)")
    print()
    print("| 段 | 軸 | 判断 | " + " | ".join(RESULTS) + " |")
    print("|---|---|---|---|---|---|")
    for phase in ("approach", "carry"):
        for axis in "xy":
            n = sum(total[(phase, axis, r)] for r in RESULTS)
            if n:
                cells = [
                    f"{total[(phase, axis, r)]} ({total[(phase, axis, r)] / n:.0%})"
                    for r in RESULTS
                ]
                print(f"| {phase} | {axis} | {n} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
