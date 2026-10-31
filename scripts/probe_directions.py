"""手先をボウルの上の決まった位置に置いた静止画で、Jev への問い方ごとに、答えた向きがボウルへ向かうかを数える。

    uv run --env-file .env scripts/probe_directions.py run experiments/008-direction-probe
    uv run --env-file .env scripts/probe_directions.py run experiments/008-direction-probe \\
        --dz 0.10 --conditions wrist_center --name low
    uv run scripts/probe_directions.py summary experiments/008-direction-probe
    uv run --env-file .env scripts/probe_directions.py run experiments/004-2-rim-probe \\
        --center-dy 0.06 --conditions wrist_rim_right_edge,wrist_rim_right_rim --name rim_plus

libero_90 60 の init state ごとに reset し、手先を始めの高さ (と、--dz だけ下げた高さ) で、掴むボウル
(akita_black_bowl_1) の中心から (dx, --center-dy + dy) ずらした位置に置く。その位置の画像と手先の状態だけから、
CONDITIONS の問い方で Jev に問う。エピソードは回さないので、問い方の違いだけを、同じ画像で比べられる。
ボウルの位置の真値は、答えを採点するときだけに使い、Jev には渡さない。

答えは世界座標の水平の向き (x、y の符号) に直し、軸ごとに、手先から行き先への差と比べる。行き先は、
問い方ごとにボウルの中心か、中心から y に TARGET_DY ずらした縁の点である。
差が OFF_TARGET 以上の軸は近づく (toward)、動かさない (still)、遠ざかる (away) に分け、ALIGNED 未満の軸は
動かさない答え (none) を正しいとする。

記録は <実験>/probe/<name>.jsonl に 1 回の問いを 1 行で書き、表を <実験>/probe/<name>.md に書く。
問いに使った画像は outputs/probe_directions/ に書く (git に入れない)。
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from typesafe_sdk import Choice, Question

from s1cap import jev
from s1cap.cap import direction_questions
from s1cap.control import move_to
from s1cap.jev_policy import (
    AXIS_CRITERIA,
    JEV_TO_WORLD,
    SIGN,
    WRIST_CAMERA,
    JevDirectionPolicy,
    Observation,
    questions,
    wrist_view,
)
from s1cap.jev_staged import (
    CROSS_UV,
    IMAGE_TO_WORLD,
    TARGETS,
    WRIST_CAPTION,
    marked_questions,
    wrist_questions,
)
from s1cap.marks import FIXED_CAPTION, fixed_direction, fixed_view
from s1cap.sim import LiberoEnv
from s1cap.tasks import TASKS

# libero_90 60 の黒いボウルとトレイ
BOWL = TASKS[("libero_90", 60)].object_body
TRAY = TASKS[("libero_90", 60)].target_body
SUITE, TASK = "libero_90", 60
IMAGE_SIZE = 320
OTHER_BOWL = "akita_black_bowl_2"
DX = (-0.04, 0.0, 0.04)
DY = (-0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06)
OFF_TARGET = 0.02  # この差より遠い軸だけを、近づくか遠ざかるかで数える [m]
ALIGNED = 0.01  # この差より近い軸は、動かさない答えを正しいとする [m]
STEP_M = 0.02  # 実験 002 の 1 歩
RIM_DY = 0.06  # 掴む縁の点。ボウルの中心から y にこれだけ離れている [m] (s1cap.jev_staged.RIM_OFFSET)
IMAGE_DIR = Path("outputs/probe_directions")


def world_target_questions(instruction: str, target: str) -> dict[str, Question]:
    """実験 002 の世界座標の軸の問いの、行き先を書いた形。"""
    return {
        axis: Choice(
            instructions=(
                f"Task: {instruction}. Which way should the gripper move along the {axis} axis "
                f"to get directly above {target}?"
            ),
            criteria=AXIS_CRITERIA[axis],
        )
        for axis in ("x", "y")
    }


def world_answer(r: Any) -> np.ndarray:
    jev_xyz = np.array([SIGN[r.choices[a].choice] for a in ("x", "y")] + [0.0])
    return (JEV_TO_WORLD @ jev_xyz)[:2]


def wrist_answer(h: str, v: str) -> np.ndarray:
    return (IMAGE_TO_WORLD[h] + IMAGE_TO_WORLD[v])[:2]


# 問い方の名前 -> (説明, 画像と状態から state と問いを作る関数, 答えを世界座標の向きに直す関数)
# 作る関数は (instruction, scene) を受ける。scene は wrist、fixed (印を描いた画像)、raw (印の無い画像)、eef、matrix を持つ
Builder = Callable[[str, dict[str, Any]], tuple[list[Any], dict[str, Question]]]
Reader = Callable[[Any, dict[str, Any]], np.ndarray]


def _world_002(instr: str, s: dict[str, Any]) -> tuple[list[Any], dict[str, Question]]:
    return s["state_002"], questions(instr, STEP_M)


def _world_target(
    instr: str, s: dict[str, Any]
) -> tuple[list[Any], dict[str, Question]]:
    return s["state_002"], world_target_questions(instr, TARGETS["bowl"])


def _wrist_006(instr: str, s: dict[str, Any]) -> tuple[list[Any], dict[str, Question]]:
    return s["wrist_state"], {**wrist_questions(instr), **marked_questions(instr)[0]}


def _wrist(target: str) -> Builder:
    def build(instr: str, s: dict[str, Any]) -> tuple[list[Any], dict[str, Question]]:
        return s["wrist_state"], direction_questions(
            instr, "wrist", "red cross", target
        )

    return build


def _fixed(instr: str, s: dict[str, Any]) -> tuple[list[Any], dict[str, Question]]:
    return s["fixed_state"], direction_questions(
        instr, "fixed", "yellow dot", TARGETS["bowl"]
    )


def _read_hv(h: str, v: str) -> Reader:
    return lambda r, s: wrist_answer(r.choices[h].choice, r.choices[v].choice)


def _read_fixed(r: Any, s: dict[str, Any]) -> np.ndarray:
    return fixed_direction(
        s["matrix"], s["eef"], r.choices["h"].choice, r.choices["v"].choice
    )


CONDITIONS: dict[str, tuple[str, Builder, Reader]] = {
    "world_002": (
        "実験 002 の問い。両方の画像、座標の説明、手先の位置。世界座標の軸ごとの向き、指、完了の 5 問",
        _world_002,
        lambda r, s: world_answer(r),
    ),
    "world_target": (
        "world_002 と同じ state。行き先 (掴むボウルの中心の真上) を書いた x、y の 2 問",
        _world_target,
        lambda r, s: world_answer(r),
    ),
    "wrist_006": (
        "実験 006 の手首の画像への呼び出し。ボウルとトレイへの画像の向き 4 問とトレイが写っているかの 1 問",
        _wrist_006,
        _read_hv("bowl_h", "bowl_v"),
    ),
    "wrist_center": (
        f"手首の画像。行き先 {TARGETS['bowl']!r} への画像の向き 2 問",
        _wrist(TARGETS["bowl"]),
        _read_hv("h", "v"),
    ),
    "wrist_left": (
        "手首の画像。行き先 'the black bowl on the left' (007 の多くのプログラム) への画像の向き 2 問",
        _wrist("the black bowl on the left"),
        _read_hv("h", "v"),
    ),
    "wrist_left_center": (
        "手首の画像。行き先 'the center of the black bowl on the left' (007 の一部のプログラム) への画像の向き 2 問",
        _wrist("the center of the black bowl on the left"),
        _read_hv("h", "v"),
    ),
    "fixed_center": (
        f"固定カメラの画像 (手先の印)。行き先 {TARGETS['bowl']!r} への画像の向き 2 問",
        _fixed,
        _read_fixed,
    ),
}
# 縁を行き先にする問い方。回した手首の画像では、右が世界の +y、左が -y
RIM_TARGETS = {
    "wrist_rim_right_edge": ("the right edge of the bowl to pick up", RIM_DY),
    "wrist_rim_right_rim": ("the right rim of the bowl to pick up", RIM_DY),
    "wrist_rim_left_edge": ("the left edge of the bowl to pick up", -RIM_DY),
    "wrist_rim_left_rim": ("the left rim of the bowl to pick up", -RIM_DY),
}
for _name, (_target, _dy) in RIM_TARGETS.items():
    CONDITIONS[_name] = (
        f"手首の画像。行き先 {_target!r} (中心から y に {_dy * 100:+.0f} cm の縁) への画像の向き 2 問",
        _wrist(_target),
        _read_hv("h", "v"),
    )
# 問い方ごとの行き先の、ボウルの中心からの y のずれ [m]。無いものは中心
TARGET_DY = {name: dy for name, (_, dy) in RIM_TARGETS.items()}


def scene(
    env: LiberoEnv, percept: Any, policy_002: JevDirectionPolicy
) -> dict[str, Any]:
    instr = env.instruction
    eef = np.asarray(percept.eef.pos)
    matrix = env.camera_matrix("agentview")
    raw = percept.images["agentview"]
    wrist = wrist_view(percept.images[WRIST_CAMERA], CROSS_UV)
    fixed = fixed_view(raw, matrix, eef)
    obs = Observation(
        step=0,
        robot_state=percept.to_dict(),
        images={"quarterview": raw, WRIST_CAMERA: percept.images[WRIST_CAMERA]},
    )
    return {
        "eef": eef,
        "matrix": matrix,
        "images": {"wrist": wrist, "fixed": fixed},
        "wrist_state": [f"Task: {instr}", WRIST_CAPTION, jev.image_content(wrist)],
        "fixed_state": [f"Task: {instr}", FIXED_CAPTION, jev.image_content(fixed)],
        "state_002": policy_002.state(obs),
    }


def ask(client: Any, condition: str, instr: str, s: dict[str, Any]) -> dict[str, Any]:
    _, build, read = CONDITIONS[condition]
    state, qs = build(instr, s)
    for attempt in range(3):
        try:
            r, ms = jev.ask(client, state, qs)
            break
        except Exception as e:  # noqa: BLE001  API の一時的な失敗は問い直す
            if attempt == 2:
                return {"error": repr(e)}
            time.sleep(2 * (attempt + 1))
    return {
        "answer": [int(v) for v in read(r, s)],
        "choices": {
            n: {
                "choice": a.choice,
                "p": {k: round(p, 3) for k, p in a.probabilities.items()},
            }
            for n, a in r.choices.items()
        },
        "nouls": {n: round(a.noul, 3) for n, a in r.nouls.items()},
        **jev.call_record(r, ms),
    }


def run(args: argparse.Namespace) -> None:
    out = args.experiment / "probe"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{args.name}.jsonl"
    done = set()
    if path.exists():
        for row in map(json.loads, path.open()):
            if "answer" in row:
                done.add(
                    tuple(
                        row[k]
                        for k in ("init", "dz", "dx", "dy", "condition", "repeat")
                    )
                )
    conditions = args.conditions.split(",") if args.conditions else list(CONDITIONS)
    env = LiberoEnv(
        SUITE, TASK, image_size=IMAGE_SIZE, horizon=100_000, fixed_view="quarterview"
    )
    client = jev.client()
    policy_002 = JevDirectionPolicy(
        client, env.instruction, input_mode="image", overlays=(), step_m=STEP_M
    )
    pool = ThreadPoolExecutor(max_workers=args.workers)
    jobs: list[tuple[dict[str, Any], Future]] = []
    with path.open("a") as f:
        for init in args.inits:
            percept = env.reset(init)
            z0 = float(percept.eef.pos[2])
            for dx in DX:
                for dy in DY:
                    gt = env.ground_truth().objects
                    bowl = gt[BOWL].pos
                    goal = [bowl[0] + dx, bowl[1] + args.center_dy + dy, z0 - args.dz]
                    percept, reached = move_to(env, goal, gripper=-1.0, max_steps=300)
                    gt = env.ground_truth().objects
                    s = scene(env, percept, policy_002)
                    key = f"init{init}_dz{round(args.dz * 100)}_dx{round(dx * 100)}_dy{round(dy * 100)}"
                    img_dir = IMAGE_DIR / args.name
                    img_dir.mkdir(parents=True, exist_ok=True)
                    for kind, image in s["images"].items():
                        Image.fromarray(image).save(img_dir / f"{key}_{kind}.png")
                    base = {
                        "init": init,
                        "dz": args.dz,
                        "dx": dx,
                        "dy": dy,
                        "center_dy": args.center_dy,
                        "reached": reached,
                        "eef": [round(float(v), 4) for v in percept.eef.pos],
                        "bowl": [round(float(v), 4) for v in gt[BOWL].pos],
                        "other_bowl": [round(float(v), 4) for v in gt[OTHER_BOWL].pos],
                        "tray": [round(float(v), 4) for v in gt[TRAY].pos],
                    }
                    for condition in conditions:
                        for repeat in range(args.repeats):
                            if (init, args.dz, dx, dy, condition, repeat) in done:
                                continue
                            bowl_xy = base["bowl"][:2]
                            target = [
                                bowl_xy[0],
                                round(bowl_xy[1] + TARGET_DY.get(condition, 0.0), 4),
                            ]
                            row = {
                                **base,
                                "condition": condition,
                                "repeat": repeat,
                                "target": target,
                            }
                            jobs.append(
                                (
                                    row,
                                    pool.submit(
                                        ask, client, condition, env.instruction, s
                                    ),
                                )
                            )
            print(f"init {init}: {len(jobs)} 問を送った", flush=True)
            # 1 つの init の問いを書き終えてから次へ進み、途中で止まっても続きから回せるようにする
            for row, job in jobs:
                f.write(json.dumps({**row, **job.result()}, ensure_ascii=False) + "\n")
            f.flush()
            jobs.clear()
    pool.shutdown()
    env.close()
    summary(args)


def judge(answer: int, diff: float) -> str | None:
    if abs(diff) >= OFF_TARGET:
        return (
            "still"
            if answer == 0
            else ("toward" if np.sign(answer) == np.sign(diff) else "away")
        )
    if abs(diff) < ALIGNED:
        return "none" if answer == 0 else "moved"
    return None


def summary(args: argparse.Namespace) -> None:
    out = args.experiment / "probe"
    for path in sorted(out.glob("*.jsonl")):
        rows = [r for r in map(json.loads, path.open()) if "answer" in r]
        errors = sum(1 for r in map(json.loads, path.open()) if "error" in r)
        (out / f"{path.stem}.md").write_text(report(path.stem, rows, errors))
        print(f"wrote {out / f'{path.stem}.md'}")


def pct(n: int, total: int) -> str:
    return f"{n} ({100 * n / total:.0f}%)" if total else "-"


def report(name: str, rows: list[dict[str, Any]], errors: int) -> str:
    """問い方ごとに、軸ごとの答えの内訳と、ボウルの +y の側 (もう 1 つのボウルの側) での答えを表にする。"""
    conditions = [c for c in CONDITIONS if any(r["condition"] == c for r in rows)]
    lines = [
        f"# 静止画での向きの答え ({name})",
        "",
        "`scripts/probe_directions.py` が書く表。手先から行き先 (掴むボウルの中心か縁の点) への差 (真値) と、答えを世界座標に直した向きを、軸ごとに比べる。",
        f"差が {OFF_TARGET * 100:.0f} cm 以上の軸は近づく、動かさない、遠ざかるに分け、{ALIGNED * 100:.0f} cm 未満の軸は動かさない答えを正しいとする。",
        "",
        f"- 問いの数: {len(rows)} (失敗して記録の無いもの {errors})",
        f"- init: {sorted({r['init'] for r in rows})}、高さ: 始めの高さから {sorted({round(r['dz'] * 100) for r in rows})} cm 下",
        f"- 届かなかった位置: {sum(1 for r in rows if not r['reached'])} 問",
        "",
        "## 問い方",
        "",
        "| 名前 | 内容 |",
        "| --- | --- |",
        *[f"| `{c}` | {CONDITIONS[c][0]} |" for c in conditions],
        "",
        f"## 軸ごとの答え (差が {OFF_TARGET * 100:.0f} cm 以上)",
        "",
        "| 問い方 | 軸 | 数 | 近づく | 動かさない | 遠ざかる |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    table: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        diff = np.array(r.get("target", r["bowl"])[:2]) - np.array(r["eef"][:2])
        for i, axis in enumerate("xy"):
            j = judge(r["answer"][i], diff[i])
            if j:
                table[(r["condition"], axis)][j] += 1
    for c in conditions:
        for axis in "xy":
            t = table[(c, axis)]
            n = t["toward"] + t["still"] + t["away"]
            lines.append(
                f"| `{c}` | {axis} | {n} | {pct(t['toward'], n)} | {pct(t['still'], n)} | {pct(t['away'], n)} |"
            )
    lines += [
        "",
        f"## 合っている軸で動かさないと答えた割合 (差が {ALIGNED * 100:.0f} cm 未満)",
        "",
        "| 問い方 | x | y |",
        "| --- | --- | --- |",
    ]
    for c in conditions:
        cells = []
        for axis in "xy":
            t = table[(c, axis)]
            cells.append(pct(t["none"], t["none"] + t["moved"]))
        lines.append(f"| `{c}` | {' | '.join(cells)} |")
    dys = sorted({r["dy"] for r in rows})
    lines += [
        "",
        "## 手先の y のずれごとの y の答え",
        "",
        (
            "手先を置く位置の中心 (掴むボウルの中心から y に --center-dy) から y にずらした量ごとに、y の答えが近づく、動かさない、遠ざかるの割合。"
            "行き先が置く位置の中心と同じ問い方だけが正しく数えられる。+y の側にもう 1 つのボウルがある。"
        ),
        "",
        "| 問い方 | " + " | ".join(f"{dy * 100:+.0f} cm" for dy in dys) + " |",
        "| --- | " + " | ".join("---" for _ in dys) + " |",
    ]
    for c in conditions:
        cells = []
        for dy in dys:
            sel = [r for r in rows if r["condition"] == c and r["dy"] == dy]
            k: dict[str, int] = defaultdict(int)
            for r in sel:
                # 動かした後の手先は目標から数 mm ずれるので、差の大きさではなく、ずらした量の向きで数える
                a = r["answer"][1]
                if dy == 0:
                    k["none" if a == 0 else "moved"] += 1
                else:
                    k[
                        "still"
                        if a == 0
                        else ("toward" if a == -np.sign(dy) else "away")
                    ] += 1
            n = sum(k.values())
            if not n:
                cells.append("-")
            elif dy != 0:
                cells.append(f"{k['toward']}/{k['still']}/{k['away']}")
            else:
                cells.append(f"none {k['none']}/{n}")
        lines.append(f"| `{c}` | {' | '.join(cells)} |")
    lines += [
        "",
        (
            "0 以外の列は 近づく/動かさない/遠ざかる の数、0 の列は動かさないと答えた数。この表だけは、記録した手先の位置ではなく、"
            "ずらした量の向きで数える (動かした後の手先は目標から数 mm ずれ、2 cm ずらした位置が 2 cm 未満になることがある)。"
        ),
        "",
        "## レイテンシとトークン",
        "",
        "| 問い方 | レイテンシの中央値 [ms] | 入力トークンの平均 | 出力トークンの平均 |",
        "| --- | --- | --- | --- |",
    ]
    for c in conditions:
        sel = [r for r in rows if r["condition"] == c]
        lines.append(
            f"| `{c}` | {np.median([r['latency_ms'] for r in sel]):.0f} | "
            f"{np.mean([r['input_tokens'] for r in sel]):.0f} | {np.mean([r['output_tokens'] for r in sel]):.0f} |"
        )
    return "\n".join(lines) + "\n"


def parse_inits(text: str) -> list[int]:
    if "-" in text:
        a, b = text.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(v) for v in text.split(",")]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("experiment", type=Path)
    p_run.add_argument("--inits", type=parse_inits, default=list(range(10)))
    p_run.add_argument(
        "--dz", type=float, default=0.0, help="始めの高さから下げる量 [m]"
    )
    p_run.add_argument(
        "--conditions", default="", help="問い方の名前をコンマで区切る。既定は全部"
    )
    p_run.add_argument(
        "--center-dy",
        type=float,
        default=0.0,
        help="手先を置く位置の中心を、ボウルの中心から y にずらす量 [m]",
    )
    p_run.add_argument("--repeats", type=int, default=3)
    p_run.add_argument("--workers", type=int, default=12)
    p_run.add_argument("--name", default="start", help="記録のファイル名")
    p_sum = sub.add_parser("summary")
    p_sum.add_argument("experiment", type=Path)
    args = parser.parse_args()
    run(args) if args.command == "run" else summary(args)


if __name__ == "__main__":
    main()
