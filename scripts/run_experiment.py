"""実験のディレクトリ (experiments/NNN-slug/) の dataflow を init state ごとに回し、結果の表を書く。

    uv run --env-file .env scripts/run_experiment.py run experiments/005-staged-guide --inits 0-9
    uv run scripts/run_experiment.py summary experiments/005-staged-guide

run は、実験のディレクトリの dataflow.yml の sim ノードの INIT と evaluator ノードの OUT_DIR を書き換えた
yml を同じディレクトリに一時的に作り、dora run で回す。記録は runs/init<N>-<日時>/ に置き、dora の
ログは同じ所の dora.log に書く。policy ノードに PROGRAM_DIR があれば (CaP)、PROGRAM に
そのディレクトリの init<N>.py を書く。PROGRAM_DIR が無く PROGRAM があれば (手順の骨組み)、
, で区切った実験のディレクトリからのパスを絶対パスに直す。全部回したら summary と同じ表を書く。
summary は、runs/ の下の summary.json を集めて results.md に表を書く。

成功しなかったエピソードを比べるため、運ぶ物をトレイに入れるタスクの進み具合を
ground_truth.jsonl と robot_state.jsonl から測り、各記録の progress.json に書いて表に足す。
運ぶ物、置き場所、掴む点は summary.json のタスクの s1cap.tasks.TaskSpec で決める。
ground_truth.jsonl は git に入れないので、progress.json があればそれを使う。
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

from s1cap.tasks import TaskSpec, spec_of_run

DATAFLOW = "dataflow.yml"
COLUMNS = {
    "init": "init",
    "run": "run",
    "success": "成功",
    "first_success_step": "成功した step",
    "steps": "step",
    "decisions": "判断",
    "jev_calls": "Jev 呼び出し",
    "mean_latency_ms": "判断ごとの平均レイテンシ [ms]",
    "input_tokens": "入力トークン",
    "output_tokens": "出力トークン",
    "end_reason": "終わり方",
    "grasp_point_cm": "掴む点への最短 [cm]",
    "object_lift_cm": "運ぶ物の持ち上げ [cm]",
    "object_tray_cm": "最後の運ぶ物とトレイ [cm]",
    "tray_lift_cm": "トレイの持ち上げ [cm]",
}


def parse_inits(text: str) -> list[int]:
    """ "0-9" や "0,2,5" を init state の番号の並びにする。"""
    inits: list[int] = []
    for part in text.split(","):
        first, _, last = part.partition("-")
        inits += range(int(first), int(last or first) + 1)
    return inits


def node(dataflow: dict, node_id: str) -> dict:
    return next(n for n in dataflow["nodes"] if n["id"] == node_id)


def run(exp_dir: Path, inits: list[int]) -> None:
    dataflow = yaml.safe_load((exp_dir / DATAFLOW).read_text())
    for init in inits:
        out_dir = (
            exp_dir / "runs" / f"init{init}-{datetime.now():%Y%m%d-%H%M%S}"
        ).resolve()
        out_dir.mkdir(parents=True)
        node(dataflow, "sim").setdefault("env", {})["INIT"] = str(init)
        node(dataflow, "evaluator").setdefault("env", {})["OUT_DIR"] = str(out_dir)
        policy_env = node(dataflow, "policy").setdefault("env", {})
        if "PROGRAM_DIR" in policy_env:  # CaP: init state ごとに生成したプログラム
            program = exp_dir / policy_env["PROGRAM_DIR"] / f"init{init}.py"
            policy_env["PROGRAM"] = str(program.resolve())
        elif (
            "PROGRAM" in policy_env
        ):  # 手順の骨組み: 実験のディレクトリからのパスを並べたもの
            policy_env["PROGRAM"] = ",".join(
                str((exp_dir / p).resolve()) for p in policy_env["PROGRAM"].split(",")
            )
        # ノードの path は yml の場所から解決されるので、一時的な yml も同じディレクトリに置く
        tmp = exp_dir / f".dataflow-init{init}.yml"
        tmp.write_text(yaml.safe_dump(dataflow, sort_keys=False))
        print(f"init {init} -> {out_dir}", flush=True)
        try:
            with (out_dir / "dora.log").open("w") as log:
                subprocess.run(
                    ["dora", "run", tmp.name, "--log-level", "info"],
                    cwd=exp_dir,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
        finally:
            tmp.unlink()
        if (out_dir / "summary.json").exists():
            print(row(json.loads((out_dir / "summary.json").read_text()), out_dir))
        else:
            print(f"  summary.json が無い。{out_dir / 'dora.log'} を見る")
    summary(exp_dir)


def progress(run_dir: Path, s: dict) -> dict:
    """進み具合。掴む点 (運ぶ物の位置 + TaskSpec.grasp_offset) と手先の最短距離、運ぶ物とトレイを
    初めの高さから最も持ち上げた量、最後の運ぶ物の位置とトレイの位置の横の距離 [cm]。"""
    path = run_dir / "progress.json"
    if path.exists():
        result = json.loads(path.read_text())
        # 運ぶ物がボウルだけだったときの名前
        for old, new in (
            ("bowl_lift_cm", "object_lift_cm"),
            ("bowl_tray_cm", "object_tray_cm"),
        ):
            if old in result:
                result[new] = result.pop(old)
        return result
    if not (run_dir / "ground_truth.jsonl").exists():
        return {}
    gt = [json.loads(line) for line in (run_dir / "ground_truth.jsonl").open()]
    eef = {
        r["step"]: r["eef"]["pos"]
        for r in map(json.loads, (run_dir / "robot_state.jsonl").open())
    }
    spec = spec_of_run(s)
    obj = np.array([g["objects"][spec.object_body]["pos"] for g in gt])
    tray = np.array([g["objects"][spec.target_body]["pos"] for g in gt])
    tcp = np.array([eef.get(g["step"], [np.nan] * 3) for g in gt])
    result = {
        "grasp_point_cm": np.nanmin(
            np.linalg.norm(obj + spec.grasp_offset - tcp, axis=1)
        ),
        "object_lift_cm": obj[:, 2].max() - obj[0, 2],
        "object_tray_cm": np.linalg.norm(obj[-1, :2] - tray[-1, :2]),
        "tray_lift_cm": tray[:, 2].max() - tray[0, 2],
    }
    result = {k: round(float(v) * 100, 1) for k, v in result.items()}
    path.write_text(json.dumps(result) + "\n")
    return result


def row(s: dict, run_dir: Path) -> dict:
    s = {**s, **progress(run_dir, s)}
    return {
        **{key: s.get(key) for key in COLUMNS},
        "init": int(run_dir.name.removeprefix("init").split("-")[0]),
        "run": run_dir.name,
    }


def grasp_point_note(spec: TaskSpec) -> str:
    x, y, z = (round(float(v) * 100, 1) for v in spec.grasp_offset)
    return f"{spec.object_body} の位置から x {x:+} cm、y {y:+} cm、z {z:+} cm"


def summary(exp_dir: Path) -> None:
    summaries = {
        path.parent: json.loads(path.read_text())
        for path in (exp_dir / "runs").glob("*/summary.json")
    }
    rows = sorted(
        (row(s, run_dir) for run_dir, s in summaries.items()),
        key=lambda r: (r["init"], r["run"]),
    )
    if not rows:
        print(f"{exp_dir / 'runs'} に記録が無い")
        return
    successes = sum(bool(r["success"]) for r in rows)
    lines = [
        f"# {exp_dir.name} の結果",
        "",
        "scripts/run_experiment.py が runs/*/summary.json と progress.json から書いた表。成功は LIBERO の判定。",
        f"掴む点への最短は手先と掴む点 ({grasp_point_note(spec_of_run(next(iter(summaries.values()))))}) の最短距離。",
        "判断ごとの平均レイテンシは、1 回の判断で Jev を呼んだ時間 (何回か呼ぶ方策はその合計) の平均。",
        "",
        f"成功 {successes}/{len(rows)}",
        "",
        "| " + " | ".join(COLUMNS.values()) + " |",
        "|" + "---|" * len(COLUMNS),
    ]
    for r in rows:
        cells = ["-" if v is None else str(v) for v in r.values()]
        lines.append("| " + " | ".join(cells) + " |")
    (exp_dir / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[4:]))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="init state ごとに回し、表を書く")
    run_parser.add_argument("exp_dir", type=Path)
    run_parser.add_argument(
        "--inits", default="0-9", help='init state の番号。"0-9" や "0,2,5" (既定 0-9)'
    )
    summary_parser = sub.add_parser("summary", help="記録から表を書く")
    summary_parser.add_argument("exp_dir", type=Path)
    args = parser.parse_args()

    if args.command == "run":
        run(args.exp_dir, parse_inits(args.inits))
    else:
        summary(args.exp_dir)


if __name__ == "__main__":
    main()
