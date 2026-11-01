"""CaP の方策 (POLICY: cap) のエピソードを、判断ごとの Jev の問いと答え、送った命令を添えて描き直す。

    uv run --env-file .env scripts/render_cycles.py experiments/017-skeleton/runs/init0-<日時> \\
        --out docs/walkthrough/017-init0.mp4 --stills docs/walkthrough/017-init0 --decisions 3,14,15

動画は、上に固定カメラと手首カメラの画像 (Jev に渡す画像と同じ印を描く)、下にその step で進んでいる判断を描く。
判断は events.jsonl の decision の記録から読む。観測の step (obs_step) から判断を出した step までは、
プログラムが Jev に問うている間 (asking)、その後は命令を動かしている間 (moving) として、問いと答え、命令、
命令の結果を書く。選択肢の確率を記録している呼び出し (実験 023 から) は、問いごとに選択肢と確率を棒で描き、
選んだ選択肢を濃い色にする。確率の記録が無い呼び出し (022 まで) は、選んだ選択肢だけを書く。
手首の × を手先の高さごとに描いた実験 (023 から) は --cross-by-height を付ける。

--decisions を付けると、その番号 (1 から数えた判断の順) の判断が使った観測の画像を、Jev に渡したものと
同じ形 (印を描き、手首の画像は 180° 回す) で --stills のディレクトリに PNG で書く。画像は記録した sim の状態から
描き直したもので、実験のときに Jev へ送った画像そのものではない。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from s1cap.jev_policy import WRIST_CAMERA, wrist_view
from s1cap.marks import fixed_view, wrist_cross_uv
from s1cap.recorder import FPS
from s1cap.sim import LiberoEnv

FIXED_CAMERA = "agentview"
CROSS_UV = (0.5, 0.40)  # 実験の evaluator と同じ × の位置
JEV_FUNCTIONS = (
    "wrist_direction",
    "fixed_direction",
    "in_wrist_view",
    "check",
    "wrist_step",
)
MAX_PANEL_H = 0.6  # パネルの高さの上限 (画像の高さに対する割合)


def load_decisions(run: Path) -> list[dict]:
    events = [json.loads(line) for line in (run / "events.jsonl").open()]
    results = {e["id"]: e for e in events if e["kind"] == "command_result"}
    decisions = []
    for e in events:
        if e["kind"] != "decision":
            continue
        command = e.get("command")
        e["result"] = results.get(command["id"]) if command else None
        decisions.append(e)
    return decisions


def describe_call(call: dict) -> str:
    """問いの 1 行目。確率の記録が無い呼び出し (実験 022 まで) は、選んだ答えもこの行に書く。"""
    fn, args, answers = call["fn"], call["args"], call.get("answers") or {}
    if fn == "wrist_step":
        head = f'{fn}: {args[1]} -> "{args[0]}"'
    else:
        head = f'{fn}("{args[0]}")'
    if "p" in answers:
        result = call["result"]
        return f"{head}  => {tuple(result[:2])}" if fn != "wrist_step" else head
    if "h" in answers:
        return f"{head}: h={answers['h']}, v={answers['v']} => {tuple(call['result'])}"
    return head


def describe_command(command: dict | None) -> str:
    if not command:
        return "(no command)"
    kind = command["type"]
    if kind == "move_delta":
        return "move_by(" + ", ".join(f"{v:+.3f}" for v in command["dpos"]) + ")"
    if kind == "move_to":
        return "move_to(" + ", ".join(f"{v:.3f}" for v in command["pos"]) + ")"
    if kind == "gripper":
        return "close_gripper()" if command["closed"] else "open_gripper()"
    return kind


QUESTION_LABELS = {"h": "horizontal", "v": "vertical", "action": "action"}


def call_rows(call: dict) -> list[tuple]:
    """Jev の 1 回の呼び出しを、パネルの行 (文の行と、選択肢の確率の行) にする。"""
    rows: list[tuple] = [("text", "  " + describe_call(call), "title")]
    answers = call.get("answers") or {}
    for q, probs in answers.get("p", {}).items():
        bars = [(name, p, name == answers.get(q)) for name, p in probs.items()]
        rows.append(("bars", QUESTION_LABELS.get(q, q), bars))
    if call["fn"] in ("in_wrist_view", "check"):
        rows.append(("bars", "yes", [("yes", float(call["result"]), True)]))
    return rows


def panel_rows(decisions: list[dict], step: int) -> list[tuple]:
    current = None
    for n, d in enumerate(decisions, 1):
        if d["obs_step"] <= step:
            current = (n, d)
    if current is None:
        return [("text", f"step {step}", "head")]
    n, d = current
    phase = "asking Jev" if step < d["step"] else "moving"
    rows: list[tuple] = [
        (
            "text",
            f"step {step}   decision #{n} (image of step {d['obs_step']})   {phase}",
            "head",
        )
    ]
    calls = [c for c in d.get("api", []) if c["fn"] in JEV_FUNCTIONS]
    for c in calls:
        rows += call_rows(c)
    if not calls:
        rows.append(("text", "  (no question to Jev)", "muted"))
    if step >= d["step"]:
        result = d["result"]
        status = f"  [{result['status']}]" if result and step >= result["step"] else ""
        rows.append(
            ("text", f"  cmd  {describe_command(d.get('command'))}{status}", "cmd")
        )
    for p in d.get("print", []):
        rows.append(("text", f"  print  {p}", "muted"))
    return rows


def jev_images(
    env: LiberoEnv, state: np.ndarray, by_height: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    percept = env.restore(state)
    cross_uv = wrist_cross_uv(percept.eef.pos[2]) if by_height else CROSS_UV
    fixed = fixed_view(
        percept.images[FIXED_CAMERA],
        env.camera_matrix(FIXED_CAMERA),
        percept.eef.pos,
    )
    return fixed, wrist_view(percept.images[WRIST_CAMERA], cross_uv)


# パネルの色 (背景、文字、薄い文字、選んだ選択肢の棒、他の選択肢の棒、棒の地)
BG, INK, MUTED = (245, 243, 238), (40, 52, 48), (125, 135, 135)
CHOSEN, OTHER, TRACK = (79, 122, 99), (155, 176, 184), (224, 224, 219)
TEXT_STYLE = {"head": INK, "title": INK, "cmd": INK, "muted": MUTED}


def row_height(row: tuple, size: int) -> int:
    return round(size * 1.35) if row[0] == "text" else round(size * 1.75)


def draw_panel(rows: list[tuple], width: int, height: int, size: int) -> Image.Image:
    panel = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(panel)
    font = ImageFont.load_default(size=size)
    small = ImageFont.load_default(size=round(size * 0.85))
    pad = size // 2
    label_w = size * 7
    y = pad
    for row in rows:
        if y + row_height(row, size) > height:
            break
        if row[0] == "text":
            draw.text((pad, y), row[1], fill=TEXT_STYLE[row[2]], font=font)
        else:
            _, label, bars = row
            draw.text((pad + size, y), label, fill=MUTED, font=small)
            x0 = pad + size + label_w
            cell = (width - x0 - pad) / max(len(bars), 3)
            for i, (name, p, chosen) in enumerate(bars):
                x = x0 + i * cell
                color = INK if chosen else MUTED
                draw.text((x, y), name, fill=color, font=small)
                draw.text(
                    (x + cell * 0.88, y),
                    f"{p * 100:.0f}%",
                    fill=color,
                    font=small,
                    anchor="ra",
                )
                bar_y = y + round(size * 1.1)
                bar_w = cell * 0.88
                draw.rectangle([x, bar_y, x + bar_w, bar_y + size // 4], fill=TRACK)
                if p > 0:
                    draw.rectangle(
                        [x, bar_y, x + bar_w * p, bar_y + size // 4],
                        fill=CHOSEN if chosen else OTHER,
                    )
        y += row_height(row, size)
    return panel


def frame(
    images: tuple[np.ndarray, np.ndarray], rows: list[tuple], panel_h: int, size: int
) -> np.ndarray:
    top = np.concatenate(images, axis=1)
    panel = draw_panel(rows, top.shape[1], panel_h, size)
    return np.concatenate([top, np.asarray(panel)], axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("run", type=Path, help="1 エピソードの記録のディレクトリ")
    parser.add_argument("--out", type=Path, help="既定は <run>/cycles.mp4")
    parser.add_argument("--size", type=int, default=448, help="カメラ 1 枚の一辺 [px]")
    parser.add_argument("--every", type=int, default=1)
    parser.add_argument(
        "--cross-by-height",
        action="store_true",
        help="手首の × を手先の高さごとに描く (policy の CROSS: height、実験 023 から)",
    )
    parser.add_argument("--stills", type=Path, help="判断の画像を書くディレクトリ")
    parser.add_argument(
        "--decisions", default="", help="画像を書く判断の番号 (, 区切り)"
    )
    args = parser.parse_args()

    summary = json.loads((args.run / "summary.json").read_text())
    decisions = load_decisions(args.run)
    record = np.load(args.run / "sim_states.npz")
    steps, states = record["steps"], record["states"]
    index = {int(s): i for i, s in enumerate(steps)}

    env = LiberoEnv(
        summary["suite"],
        summary["task_id"],
        image_size=args.size,
        cameras=(FIXED_CAMERA, WRIST_CAMERA),
        fixed_view=summary["fixed_view"],
    )
    env.reset(summary["init"], seed=summary["seed"])

    if args.decisions:
        stills = args.stills or args.run / "stills"
        stills.mkdir(parents=True, exist_ok=True)
        for n in (int(x) for x in args.decisions.split(",")):
            obs_step = decisions[n - 1]["obs_step"]
            fixed, wrist = jev_images(
                env, states[index[obs_step]], args.cross_by_height
            )
            imageio.imwrite(stills / f"d{n:02d}-fixed.png", fixed)
            imageio.imwrite(stills / f"d{n:02d}-wrist.png", wrist)
        print(f"{args.decisions} -> {stills}")

    # パネルの高さは、どの判断の行も収まる高さにそろえる (上限 MAX_PANEL_H)
    size = max(12, 2 * args.size // 56)
    panel_h = size + max(
        sum(
            row_height(r, size)
            for r in panel_rows(
                decisions, d["result"]["step"] if d["result"] else d["step"]
            )
        )
        for d in decisions
    )
    panel_h = min(panel_h, round(args.size * MAX_PANEL_H))
    out = args.out or args.run / "cycles.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(out, fps=FPS, macro_block_size=1) as writer:
        for step, state in zip(steps[:: args.every], states[:: args.every]):
            images = jev_images(env, state, args.cross_by_height)
            writer.append_data(
                frame(images, panel_rows(decisions, int(step)), panel_h, size)
            )
    env.close()
    print(f"{len(steps[:: args.every])} frames -> {out}")


if __name__ == "__main__":
    main()
