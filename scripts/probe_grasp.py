"""手先を運ぶ物の上の決まった位置から下ろして指を閉じ、持ち上げられるかを、ずれごとに数える。Jev は呼ばない。

    uv run --env-file .env scripts/probe_grasp.py run experiments/015-grasp-tolerance --task 61 --inits 0-4
    uv run scripts/probe_grasp.py summary experiments/015-grasp-tolerance
    uv run --env-file .env scripts/probe_grasp.py reach experiments/015-grasp-tolerance --task 62

init state ごとに reset し、始めの高さで、運ぶ物の位置 (真値) から (dx, --center-dy + dy) ずらした真上に手先を置く。
ボウル (task 60) は縁を掴むので、--center-dy で縁の点 (中心から y に ±6 cm) を中心にする。
そこから手順の骨組みと同じ動きをする: 3 cm ずつ下ろして当たって止まった所から RISE だけ上げ、指を閉じ、
始めの高さまで持ち上げる。命令は dora の実験と同じ RobotDriver で送る。
運ぶ物が LIFTED 以上持ち上がり、指の開きが HELD_WIDTH より大きければ掴めたとする。

記録は <実験>/probe/<name>.jsonl に 1 回の試行を 1 行で書き、表を <実験>/probe/<name>.md に書く。

reach は、手先が下向きのまま卓まで下りられる範囲を測る。init state 0 で、運ぶ物の位置から y に --reach-dy
ずらした (物の無い) 列で、x を REACH_DX だけずらした点ごとに、始めの高さから同じように下ろし、止まった高さを
<実験>/probe/reach_<task>.md に書く。
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from s1cap.driver import RobotDriver
from s1cap.sim import LiberoEnv
from s1cap.tasks import task_spec

SUITE = "libero_90"
DX = (-0.04, -0.02, 0.0, 0.02, 0.04)
DY = (-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03)
DOWN_M = 0.03  # 1 回に下ろす量 (s1cap.jev_staged、cap と同じ)
DOWN_TIMEOUT_STEPS = 40
RISE = 0.015  # 当たって止まった所から上げる量 (s1cap.jev_staged.GRASP_RISE)
HELD_WIDTH = 0.003
LIFTED = 0.05  # 運ぶ物が初めの高さからこれだけ上がったら持ち上げたとする [m]
TOP_DOWN = [1.0, 0.0, 0.0, 0.0]
REACH_DX = (-0.04, 0.0, 0.04, 0.08, 0.12)


def parse_inits(text: str) -> list[int]:
    inits: list[int] = []
    for part in text.split(","):
        first, _, last = part.partition("-")
        inits += range(int(first), int(last or first) + 1)
    return inits


def execute(driver: RobotDriver, command: dict[str, Any]) -> str:
    """命令を送り、結果が出るまで step を進めて status を返す。"""
    results = driver.submit({"id": 0, **command})
    while not results:
        _, result = driver.step()
        if result is not None:
            results = [result]
    return results[-1].status


def trial(
    driver: RobotDriver,
    body: str,
    z0: float,
    dx: float,
    dy: float,
    rise: float,
) -> dict[str, Any]:
    gt = driver.ground_truth().objects
    obj0 = np.asarray(gt[body].pos)
    start = [float(obj0[0] + dx), float(obj0[1] + dy), z0]
    placed = execute(driver, {"type": "move_to", "pos": start, "quat": TOP_DOWN})
    downs = go_down(driver)
    stop_z = float(driver.env.perceive().eef.pos[2])
    execute(driver, {"type": "move_delta", "dpos": [0.0, 0.0, rise]})
    execute(driver, {"type": "gripper", "closed": True})
    width_closed = float(driver.env.perceive().gripper_width)
    up = z0 - float(driver.env.perceive().eef.pos[2])
    execute(driver, {"type": "move_delta", "dpos": [0.0, 0.0, up]})
    percept = driver.env.perceive()
    obj1 = np.asarray(driver.ground_truth().objects[body].pos)
    lift = float(obj1[2] - obj0[2])
    width = float(percept.gripper_width)
    return {
        "placed": placed,
        "downs": downs,
        "stop_z": round(stop_z, 4),
        "obj0": [round(float(v), 4) for v in obj0],
        "width_closed": round(width_closed, 4),
        "width": round(width, 4),
        "lift": round(lift, 4),
        "held": bool(lift > LIFTED and width > HELD_WIDTH),
    }


def go_down(driver: RobotDriver) -> int:
    """当たって止まるか届かなくなるまで DOWN_M ずつ下ろし、下ろした回数を返す。"""
    downs = 0
    while downs < 10:
        downs += 1
        status = execute(
            driver,
            {
                "type": "move_delta",
                "dpos": [0.0, 0.0, -DOWN_M],
                "timeout_steps": DOWN_TIMEOUT_STEPS,
            },
        )
        if status != "reached":
            break
    return downs


def reach(args: argparse.Namespace) -> None:
    spec = task_spec(SUITE, args.task)
    env = LiberoEnv(
        SUITE, args.task, image_size=64, horizon=100_000, fixed_view="quarterview"
    )
    driver = RobotDriver(env)
    rows = []
    for dx in REACH_DX:
        percept = driver.reset(0)
        z0 = float(percept.eef.pos[2])
        obj = np.asarray(driver.ground_truth().objects[spec.object_body].pos)
        start = [float(obj[0] + dx), float(obj[1] + args.reach_dy), z0]
        execute(driver, {"type": "move_to", "pos": start, "quat": TOP_DOWN})
        go_down(driver)
        rows.append((float(obj[0] + dx), float(driver.env.perceive().eef.pos[2])))
    env.close()
    lines = [
        f"# 手先が下向きのまま下りられる高さ (libero_90 {args.task})",
        "",
        (
            f"`scripts/probe_grasp.py reach` が書く表。init 0 で、{spec.object_body} の位置から y に "
            f"{args.reach_dy * 100:+.0f} cm ずらした物の無い列で、始めの高さから 3 cm ずつ下ろして止まった高さ。"
            "卓の上面は z 約 0.437。"
        ),
        "",
        "| x [m] | 運ぶ物の x からのずれ [cm] | 止まった z [m] |",
        "| --- | --- | --- |",
    ]
    for (x, z), dx in zip(rows, REACH_DX, strict=True):
        lines.append(f"| {x:.3f} | {dx * 100:+.0f} | {z:.3f} |")
    path = args.experiment / "probe" / f"reach_{args.task}.md"
    path.write_text("\n".join(lines) + "\n")
    print(path.read_text())


def run(args: argparse.Namespace) -> None:
    spec = task_spec(SUITE, args.task)
    out = args.experiment / "probe"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{args.name}.jsonl"
    env = LiberoEnv(
        SUITE, args.task, image_size=64, horizon=100_000, fixed_view="quarterview"
    )
    driver = RobotDriver(env)
    with path.open("a") as f:
        for init in args.inits:
            for dx in DX:
                for dy in DY:
                    percept = driver.reset(init)
                    z0 = float(percept.eef.pos[2])
                    row = {
                        "task": args.task,
                        "init": init,
                        "dx": dx,
                        "dy": dy,
                        "center_dy": args.center_dy,
                        "rise": args.rise,
                        **trial(
                            driver,
                            spec.object_body,
                            z0,
                            dx,
                            args.center_dy + dy,
                            args.rise,
                        ),
                    }
                    f.write(json.dumps(row) + "\n")
                    f.flush()
            print(f"init {init} done", flush=True)
    env.close()
    summary(args)


def summary(args: argparse.Namespace) -> None:
    out = args.experiment / "probe"
    for path in sorted(out.glob("*.jsonl")):
        rows = [json.loads(line) for line in path.open()]
        (out / f"{path.stem}.md").write_text(report(path.stem, rows))
        print(f"wrote {out / f'{path.stem}.md'}")


def report(name: str, rows: list[dict[str, Any]]) -> str:
    table: dict[tuple[float, float], list[bool]] = defaultdict(list)
    for r in rows:
        table[(r["dx"], r["dy"])].append(r["held"])
    dxs = sorted({r["dx"] for r in rows})
    dys = sorted({r["dy"] for r in rows})
    task = rows[0]["task"]
    lines = [
        f"# 掴めた割合 ({name})",
        "",
        (
            f"`scripts/probe_grasp.py` が書く表。libero_90 {task}、init {sorted({r['init'] for r in rows})}、"
            f"当たって止まった所から {rows[0]['rise'] * 100:.1f} cm 上げて閉じる。"
        ),
        f"行は運ぶ物の位置からの x のずれ、列は y のずれ [cm] (y は位置から {rows[0].get('center_dy', 0) * 100:+.0f} cm の点から)。セルは掴んで {LIFTED * 100:.0f} cm 以上持ち上げた回数 / 試行数。",
        "指は y の向きに閉じる。",
        "",
        "| dx \\ dy | " + " | ".join(f"{dy * 100:+.0f}" for dy in dys) + " |",
        "|---|" + "---|" * len(dys),
    ]
    for dx in dxs:
        cells = [f"{sum(table[(dx, dy)])}/{len(table[(dx, dy)])}" for dy in dys]
        lines.append(f"| {dx * 100:+.0f} | " + " | ".join(cells) + " |")
    held = sum(r["held"] for r in rows)
    lines += ["", f"全体: {held}/{len(rows)}", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("experiment", type=Path)
    run_parser.add_argument("--task", type=int, default=61)
    run_parser.add_argument("--inits", type=parse_inits, default=parse_inits("0-4"))
    run_parser.add_argument("--rise", type=float, default=RISE)
    run_parser.add_argument("--center-dy", type=float, default=0.0)
    run_parser.add_argument("--name", default="grasp")
    reach_parser = sub.add_parser("reach")
    reach_parser.add_argument("experiment", type=Path)
    reach_parser.add_argument("--task", type=int, default=62)
    reach_parser.add_argument("--reach-dy", type=float, default=0.2)
    summary_parser = sub.add_parser("summary")
    summary_parser.add_argument("experiment", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        run(args)
    elif args.command == "reach":
        reach(args)
    else:
        summary(args)


if __name__ == "__main__":
    main()
