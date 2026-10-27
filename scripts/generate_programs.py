"""実験のディレクトリの CaP のプログラムを、init state ごとに LLM に書かせる (s1cap.cap)。

    uv run --env-file .env scripts/generate_programs.py experiments/007-cap --inits 0-9

LLM には init state の情報を渡さないので、プロンプトはどの init state でも同じになる。init state ごとに
1 本ずつ書かせ、書かれるプログラムのばらつきも結果に含める。

dataflow.yml の sim ノードの SUITE と TASK から指示文を読み、policy ノードの CODE_MODEL、JEV_BUDGET、
MAX_MOVES をプロンプトに入れる。プログラムは policy ノードの PROGRAM_DIR (既定 programs) に
init<N>.py として書き、モデル、トークン数、費用、時間を init<N>.json に書く。プロンプトは prompt.md に書く。
既にあるプログラムは書き直さない (--force で書き直す)。
"""

import argparse
import json
from pathlib import Path

import yaml

from s1cap import cap
from s1cap.sim import setup_libero


def parse_inits(text: str) -> list[int]:
    """ "0-9" や "0,2,5" を init state の番号の並びにする (scripts/run_experiment.py と同じ)。"""
    inits: list[int] = []
    for part in text.split(","):
        first, _, last = part.partition("-")
        inits += range(int(first), int(last or first) + 1)
    return inits


def instruction(suite: str, task_id: int) -> str:
    setup_libero()
    from libero.libero import benchmark

    return benchmark.get_benchmark_dict()[suite]().get_task(task_id).language


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("exp_dir", type=Path)
    parser.add_argument("--inits", default="0-9")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    dataflow = yaml.safe_load((args.exp_dir / "dataflow.yml").read_text())
    nodes = {n["id"]: n.get("env", {}) for n in dataflow["nodes"]}
    sim, policy = nodes["sim"], nodes["policy"]
    model = policy.get("CODE_MODEL", cap.DEFAULT_CODE_MODEL)
    text = cap.prompt(
        instruction(sim["SUITE"], int(sim["TASK"])),
        jev_budget=int(policy.get("JEV_BUDGET", cap.DEFAULT_JEV_BUDGET)),
        max_moves=int(policy.get("MAX_MOVES", cap.DEFAULT_MAX_MOVES)),
    )
    out = args.exp_dir / policy.get("PROGRAM_DIR", "programs")
    out.mkdir(exist_ok=True)
    (out / "prompt.md").write_text(text)
    for init in parse_inits(args.inits):
        path = out / f"init{init}.py"
        if path.exists() and not args.force:
            print(f"{path} は既にある")
            continue
        code, meta = cap.generate(text, model)
        path.write_text(code)
        (out / f"init{init}.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(f"{path}: {meta}", flush=True)


if __name__ == "__main__":
    main()
