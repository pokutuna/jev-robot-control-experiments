"""動画に使う録画と Jev の判断の記録を、実験のディレクトリから video/resources/ へ書き出す。

    uv run python video/scripts/export_resources.py

録画は各実験の videos/ にあるもの (左が固定カメラ、右が手首カメラ、20 fps、1 フレームが 1 step) を使う。
動画の 1 フレームと Remotion の 1 フレームを揃えるため、CLIPS の倍速を掛けた 30 fps の動画にして書き出す。
実験 023 以降の録画は下に判断の欄を描いているので、上のカメラの部分 (896×448) だけを切り出す。
判断の記録は runs/<init>-*/events.jsonl から読み、判断ごとに次を JSON に書く。

- obs: Jev に渡した画像の step。step: 命令を出した step
- text: 動画の下に出す 1 行の要約 (問いと回答)
- calls: 問いごとの関数名、引数、選択肢の確率 (確率を記録した実験 023 以降のみ)
- stage: スケルトンの段階の番号 (スケルトンの実験のみ。STAGES の順)

ffmpeg が必要。
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

FPS = 30  # Remotion の動画の fps
ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = ROOT / "experiments"
OUT = ROOT / "video" / "resources"

# (書き出す名前, 実験のディレクトリ, init, スケルトンの段階を付けるか, 倍速, 使う秒数 (None は全体))
CLIPS = [
    ("023-init0", "023-skeleton-jev-phases", 0, True, 1.5, None),
    ("013-init0", "013-text-baseline", 0, False, 8, None),
    ("014-init0", "014-image-direction", 0, False, 6, 60),
    ("024-init0", "024-skeleton-jev-phases-task60", 0, True, 4, None),
    ("025-init7", "025-skeleton-bowl-left-right", 7, True, 8, None),
    ("025-init4", "025-skeleton-bowl-left-right", 4, True, 8, None),
    ("025-init3", "025-skeleton-bowl-left-right", 3, True, 8, None),
    ("025-init5", "025-skeleton-bowl-left-right", 5, True, 8, None),
    ("021-init0", "021-cap-task61-full", 0, False, 4, None),
    ("021-init1", "021-cap-task61-full", 1, False, 4, None),
    ("022-init6", "022-cap-task60-full", 6, False, 4, None),
    ("022-init3", "022-cap-task60-full", 3, False, 4, None),
]

# レポートの図をそのまま使う静止画
IMAGES = [
    "scene-quarterview.png",
    "023-init0-d02-fixed.png",
    "023-init0-d02-wrist.png",
]

# 実験 016 で Jev に問うた静止画 (書き出し先の名前: outputs/probe_targets/ からの位置)。
# outputs/ は git に入れないので、先に experiments/016-target-wording/README.md の
# probe_targets.py run を実行しておく
PROBE_IMAGES = {
    "016-init0-dy4-fixed.png": "pudding_fixed/init0_dx0_dy4_fixed.png",
    "016-init0-dy4-wrist.png": "pudding/init0_dx0_dy4_wrist.png",
    "016-init0-dy-4-wrist.png": "pudding/init0_dx0_dy-4_wrist.png",
}

# スケルトンの段階 (レポートの 5.4 節の段階の順)
STAGES = [
    "対象物へ寄せる",
    "掴む",
    "持ち上げる",
    "置き場所へ寄せる",
    "置く",
    "完了を確認",
]

JEV_FUNCTIONS = {
    "fixed_direction",
    "wrist_direction",
    "wrist_step",
    "check",
    "in_wrist_view",
}
SIGN = {1: "+", -1: "-", 0: "0"}


def run_dir(experiment: str, init: int) -> Path:
    runs = sorted((EXPERIMENTS / experiment / "runs").glob(f"init{init}-*"))
    assert len(runs) == 1, runs
    return runs[0]


def export_video(
    experiment: str, init: int, name: str, speed: float, seconds: float | None
) -> None:
    src = EXPERIMENTS / experiment / "videos" / f"init{init}.mp4"
    dst = OUT / "clips" / f"{name}.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            *(["-t", str(seconds)] if seconds else []),
            "-i",
            str(src),
            "-vf",
            f"crop=896:448:0:0,setpts=PTS/{speed},fps={FPS}",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(dst),
        ],
        check=True,
    )


def describe_api(call: dict) -> str:
    fn, args, answers = call["fn"], call.get("args", []), call.get("answers") or {}
    target = args[0] if args else ""
    if fn in ("fixed_direction", "wrist_direction"):
        return f'{fn}("{target}") → h: {answers.get("h")}, v: {answers.get("v")}'
    if fn == "wrist_step":
        return f'wrist_step("{target}") → {answers.get("action")} (h: {answers.get("h")}, v: {answers.get("v")})'
    if fn == "check":
        return f'check("{target}") → {call.get("result")}'
    return f"{fn}()"


def describe(decision: dict) -> str:
    if "api" in decision:  # スケルトンと CaP (Jev への問いを関数で呼ぶ)
        calls = [c for c in decision["api"] if c["fn"] in JEV_FUNCTIONS]
        if not calls:
            calls = [
                c
                for c in decision["api"]
                if c["fn"] in ("close_gripper", "open_gripper")
            ]
        return " / ".join(describe_api(c) for c in calls)
    if "motor" in decision:  # 実験 013: 位置の差をテキストで渡す
        m = decision["motor"]
        short = {"positive": "+", "negative": "-", "hold": "0"}
        return (
            f"意図: {decision['intent']} / x: {short.get(m['x'], m['x'])}, "
            f"y: {short.get(m['y'], m['y'])}, z: {short.get(m['z'], m['z'])}, "
            f"gripper: {m['gripper']}"
        )
    if "choices" in decision:  # 実験 014: 画像で x、y、z の向きを問う
        c = decision["choices"]
        return f"x: {c['x']}, y: {c['y']}, z: {c['z']}, gripper: {c['gripper']}"
    return ""


def describe_command(command: dict, skeleton: bool) -> str:
    kind = command["type"]
    if kind == "move_delta":
        dx, dy, dz = (round(v * 100) for v in command["dpos"])
        if dx == dy == dz == 0:
            return "動かさない"
        if dx == dy == 0:
            return f"{abs(dz)} cm 下ろす" if dz < 0 else f"{dz} cm 上げる"
        moves = [f"{a} {d:+d} cm" for a, d in (("x", dx), ("y", dy)) if d]
        return f"水平に {'、'.join(moves)} 動かす"
    if kind == "gripper":
        return "グリッパーを閉じる" if command["closed"] else "グリッパーを開く"
    if kind == "move_to":
        # スケルトンの move_to は、閉じた後と開いた後に始めの高さへ戻す go_up だけ
        return "始めの高さまで上げる" if skeleton else "指定の位置へ動かす"
    return kind


def stage_of(decision: dict, holding: bool) -> int | None:
    fns = [c["fn"] for c in decision.get("api", [])]
    if "check" in fns:
        return 5
    if "open_gripper" in fns:
        return 4
    if "close_gripper" in fns:
        return 2
    if "wrist_step" in fns:
        return 4 if holding else 1
    if "fixed_direction" in fns or "wrist_direction" in fns:
        return 3 if holding else 0
    return None


def export_decisions(
    experiment: str,
    init: int,
    name: str,
    skeleton: bool,
    speed: float,
    seconds: float | None,
) -> None:
    run = run_dir(experiment, init)
    events = [json.loads(line) for line in (run / "events.jsonl").open()]
    summary = json.loads((run / "summary.json").read_text())
    decisions = []
    holding = False
    for e in events:
        if e["kind"] != "decision" or "obs_step" not in e:
            continue
        text = describe(e)
        if not text:
            continue
        item = {"obs": e["obs_step"], "step": e["step"], "text": text}
        if e.get("command"):
            item["command"] = describe_command(e["command"], skeleton)
        if any("p" in (c.get("answers") or {}) for c in e.get("api", [])):
            item["calls"] = [
                {"fn": c["fn"], "args": c.get("args", []), "answers": c["answers"]}
                for c in e["api"]
                if c["fn"] in JEV_FUNCTIONS
            ]
        if skeleton:
            fns = [c["fn"] for c in e["api"]]
            if "close_gripper" in fns:
                holding = True
            if "open_gripper" in fns and stage_of(e, holding) != 4:
                holding = False
            item["stage"] = stage_of(e, holding)
        decisions.append(item)
    data = {
        "experiment": experiment,
        "init": init,
        "instruction": summary.get("instruction"),
        "fps": 20,
        "steps": summary["steps"],
        "speed": speed,
        # 書き出した動画に入っている step 数
        "clip_steps": min(summary["steps"], int(seconds * 20)) if seconds else summary["steps"],
        "success": summary.get("success"),
        "decisions": decisions,
    }
    if skeleton:
        data["stages"] = STAGES
    (OUT / "clips" / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1)
    )


def main() -> None:
    (OUT / "clips").mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    for name, experiment, init, skeleton, speed, seconds in CLIPS:
        export_video(experiment, init, name, speed, seconds)
        export_decisions(experiment, init, name, skeleton, speed, seconds)
        print(name)
    for image in IMAGES:
        shutil.copy(ROOT / "report" / "images" / image, OUT / "images" / image)
    for image, source in PROBE_IMAGES.items():
        shutil.copy(ROOT / "outputs" / "probe_targets" / source, OUT / "images" / image)


if __name__ == "__main__":
    main()
