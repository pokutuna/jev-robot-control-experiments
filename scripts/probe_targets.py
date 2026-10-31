"""手先を物の近くの決まった位置に置いた静止画で、行き先の言い方ごとに、Jev の答えた向きが物へ向かうかを数える。

    uv run --env-file .env scripts/probe_targets.py run experiments/016-target-wording --task 61 \\
        --phrases "the chocolate pudding box,the brown box,the box" --name pudding
    uv run scripts/probe_targets.py summary experiments/016-target-wording

init state ごとに reset し、手先を始めの高さで、--around の物 (既定はタスクの運ぶ物) の位置 (真値) から
(dx, dy) ずらした真上に置く。その位置の画像を、CaP と手順の骨組みが使う向きの関数と同じ問い
(s1cap.cap.direction_questions) で、--phrases の言い方ごとに Jev に問う。--camera fixed では固定カメラの画像
(手先の印) で問う。答えは世界座標の水平の向きに直し、軸ごとに、手先から採点する物への差と比べる。
採点する物は --score で言い方ごとに選べる (左右のボウルを指す言い方を、それぞれのボウルで採点するため)。
物の位置の真値は、手先を置くことと採点にだけ使い、Jev には渡さない。

差が OFF_TARGET 以上の軸は近づく (toward)、動かさない (still)、遠ざかる (away) に分け、ALIGNED 未満の軸は
動かさない答え (none) を正しいとする (scripts/probe_directions.py と同じ)。
記録は <実験>/probe/<name>.jsonl、表は <実験>/probe/<name>.md に書く。画像は outputs/probe_targets/ に書く。
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from s1cap import jev
from s1cap.cap import direction_questions
from s1cap.control import move_to
from s1cap.jev_policy import WRIST_CAMERA, wrist_view
from s1cap.jev_staged import CROSS_UV, IMAGE_TO_WORLD, WRIST_CAPTION
from s1cap.marks import FIXED_CAPTION, fixed_direction, fixed_view
from s1cap.sim import LiberoEnv
from s1cap.tasks import task_spec

SUITE = "libero_90"
IMAGE_SIZE = 448  # 実験 012
DX = (-0.04, 0.0, 0.04)
DY = (-0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06)
OFF_TARGET = 0.02
ALIGNED = 0.01
IMAGE_DIR = Path("outputs/probe_targets")


def parse_inits(text: str) -> list[int]:
    inits: list[int] = []
    for part in text.split(","):
        first, _, last = part.partition("-")
        inits += range(int(first), int(last or first) + 1)
    return inits


def ask(
    client: Any, instruction: str, camera: str, phrase: str, s: dict[str, Any]
) -> dict[str, Any]:
    if camera == "wrist":
        qs = direction_questions(instruction, "wrist", "red cross", phrase)
        state = [f"Task: {instruction}", WRIST_CAPTION, s["wrist"]]
    else:
        qs = direction_questions(instruction, "fixed", "yellow dot", phrase)
        state = [f"Task: {instruction}", FIXED_CAPTION, s["fixed"]]
    for attempt in range(3):
        try:
            r, ms = jev.ask(client, state, qs)
            break
        except Exception as e:  # noqa: BLE001  API の一時的な失敗は問い直す
            if attempt == 2:
                return {"error": repr(e)}
            time.sleep(2 * (attempt + 1))
    h, v = r.choices["h"].choice, r.choices["v"].choice
    if camera == "wrist":
        answer = (IMAGE_TO_WORLD[h] + IMAGE_TO_WORLD[v])[:2]
    else:
        answer = fixed_direction(s["matrix"], s["eef"], h, v)
    return {
        "answer": [int(a) for a in answer],
        "h": h,
        "v": v,
        "p": {
            n: {k: round(p, 3) for k, p in a.probabilities.items()}
            for n, a in r.choices.items()
        },
        **jev.call_record(r, ms),
    }


def run(args: argparse.Namespace) -> None:
    spec = task_spec(SUITE, args.task)
    around = args.around or spec.object_body
    phrases = [p.strip() for p in args.phrases.split(",")]
    scores = [s.strip() for s in args.score.split(",")] if args.score else []
    score_of = {
        p: (scores[i] if i < len(scores) else around) for i, p in enumerate(phrases)
    }
    out = args.experiment / "probe"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{args.name}.jsonl"
    env = LiberoEnv(
        SUITE,
        args.task,
        image_size=IMAGE_SIZE,
        horizon=100_000,
        fixed_view="quarterview",
    )
    client = jev.client()
    pool = ThreadPoolExecutor(max_workers=args.workers)
    img_dir = IMAGE_DIR / args.name
    img_dir.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for init in args.inits:
            jobs: list[tuple[dict[str, Any], Future]] = []
            percept = env.reset(init)
            z0 = float(percept.eef.pos[2])
            for dx in DX:
                for dy in DY:
                    center = env.ground_truth().objects[around].pos
                    goal = [center[0] + dx, center[1] + args.center_dy + dy, z0]
                    percept, reached = move_to(env, goal, gripper=-1.0, max_steps=300)
                    gt = env.ground_truth().objects
                    eef = np.asarray(percept.eef.pos)
                    matrix = env.camera_matrix("agentview")
                    wrist = wrist_view(percept.images[WRIST_CAMERA], CROSS_UV)
                    fixed = fixed_view(percept.images["agentview"], matrix, eef)
                    key = f"init{init}_dx{round(dx * 100)}_dy{round(dy * 100)}"
                    Image.fromarray(wrist).save(img_dir / f"{key}_wrist.png")
                    Image.fromarray(fixed).save(img_dir / f"{key}_fixed.png")
                    s = {
                        "eef": eef,
                        "matrix": matrix,
                        "wrist": jev.image_content(wrist),
                        "fixed": jev.image_content(fixed),
                    }
                    for phrase in phrases:
                        body = score_of[phrase]
                        row = {
                            "task": args.task,
                            "init": init,
                            "dx": dx,
                            "dy": dy,
                            "center_dy": args.center_dy,
                            "camera": args.camera,
                            "phrase": phrase,
                            "score": body,
                            "reached": reached,
                            "eef": [round(float(v), 4) for v in eef],
                            "target": [round(float(v), 4) for v in gt[body].pos],
                        }
                        for repeat in range(args.repeats):
                            jobs.append(
                                (
                                    {**row, "repeat": repeat},
                                    pool.submit(
                                        ask,
                                        client,
                                        env.instruction,
                                        args.camera,
                                        phrase,
                                        s,
                                    ),
                                )
                            )
            for row, job in jobs:
                f.write(json.dumps({**row, **job.result()}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"init {init}: {len(jobs)} 問", flush=True)
    pool.shutdown()
    env.close()
    summary(args)


def judge(answer: int, diff: float) -> str | None:
    if abs(diff) >= OFF_TARGET:
        if answer == 0:
            return "still"
        return "toward" if np.sign(answer) == np.sign(diff) else "away"
    if abs(diff) < ALIGNED:
        return "none" if answer == 0 else "moved"
    return None


def pct(n: int, total: int) -> str:
    return f"{n} ({100 * n / total:.0f}%)" if total else "-"


def report(name: str, rows: list[dict[str, Any]], errors: int) -> str:
    keys = list(dict.fromkeys((r["phrase"], r["score"]) for r in rows))
    lines = [
        f"# 言い方ごとの向きの答え ({name})",
        "",
        "`scripts/probe_targets.py` が書く表。手先から採点する物の位置 (真値) への差と、答えを世界座標に直した向きを、軸ごとに比べる。",
        f"差が {OFF_TARGET * 100:.0f} cm 以上の軸は近づく、動かさない、遠ざかるに分け、{ALIGNED * 100:.0f} cm 未満の軸は動かさない答えを正しいとする。",
        "",
        f"- libero_90 {rows[0]['task']}、カメラ {rows[0]['camera']}、init {sorted({r['init'] for r in rows})}",
        f"- 問いの数: {len(rows)} (失敗して記録の無いもの {errors})、届かなかった位置: {sum(1 for r in rows if not r['reached'])} 問",
        "",
        "| 言い方 | 採点する物 | 軸 | 数 | 近づく | 動かさない | 遠ざかる | 合っている軸で動かさない |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    table: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for r in rows:
        diff = np.array(r["target"][:2]) - np.array(r["eef"][:2])
        for i, axis in enumerate("xy"):
            j = judge(r["answer"][i], diff[i])
            if j:
                table[(r["phrase"], r["score"], axis)][j] += 1
    for phrase, body in keys:
        for axis in "xy":
            t = table[(phrase, body, axis)]
            n = t["toward"] + t["still"] + t["away"]
            lines.append(
                f"| {phrase} | {body} | {axis} | {n} | {pct(t['toward'], n)} | {pct(t['still'], n)} | "
                f"{pct(t['away'], n)} | {pct(t['none'], t['none'] + t['moved'])} |"
            )
    lines += [
        "",
        "| 言い方 | レイテンシの中央値 [ms] | 入力トークンの平均 |",
        "| --- | --- | --- |",
    ]
    for phrase, body in keys:
        sel = [r for r in rows if r["phrase"] == phrase and r["score"] == body]
        lines.append(
            f"| {phrase} | {np.median([r['latency_ms'] for r in sel]):.0f} | "
            f"{np.mean([r['input_tokens'] for r in sel]):.0f} |"
        )
    return "\n".join(lines) + "\n"


def summary(args: argparse.Namespace) -> None:
    out = args.experiment / "probe"
    for path in sorted(out.glob("*.jsonl")):
        all_rows = [json.loads(line) for line in path.open()]
        rows = [r for r in all_rows if "answer" in r]
        (out / f"{path.stem}.md").write_text(
            report(path.stem, rows, len(all_rows) - len(rows))
        )
        print(f"wrote {out / f'{path.stem}.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("experiment", type=Path)
    p_run.add_argument("--task", type=int, default=61)
    p_run.add_argument("--inits", type=parse_inits, default=parse_inits("0-4"))
    p_run.add_argument(
        "--phrases", required=True, help="行き先の言い方をコンマで区切る"
    )
    p_run.add_argument(
        "--score",
        default="",
        help="言い方ごとに採点する物の真値の名前 (コンマ区切り、既定は --around)",
    )
    p_run.add_argument("--around", default="", help="手先を置く位置の中心にする物")
    p_run.add_argument("--center-dy", type=float, default=0.0)
    p_run.add_argument("--camera", choices=("wrist", "fixed"), default="wrist")
    p_run.add_argument("--repeats", type=int, default=1)
    p_run.add_argument("--workers", type=int, default=12)
    p_run.add_argument("--name", required=True)
    p_sum = sub.add_parser("summary")
    p_sum.add_argument("experiment", type=Path)
    args = parser.parse_args()
    run(args) if args.command == "run" else summary(args)


if __name__ == "__main__":
    main()
