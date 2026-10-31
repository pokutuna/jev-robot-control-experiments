"""固定カメラの画像を大きさを変えて Jev に送り、入力トークン数、レイテンシ、答えを比べる。

    uv run --env-file .env scripts/probe_resolution.py experiments/012-image-resolution

libero_90 61 の init state 0 を quarterview で RENDER_SIZE px に描画し、SIZES の各大きさに縮めて (Lanczos)
1 枚ずつ送る。問いは QUESTIONS の 2 つで、大きさごとに REPEATS 回送る。手先の印は描かない。

記録は <実験>/probe/resolution.jsonl に 1 回の問いを 1 行で書き、表を <実験>/probe/resolution.md に書く。
送った画像は outputs/probe_resolution/ に書き (git に入れない)、大きさごとの見え方を並べた図を
<実験>/images/montage.png に書く。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from typesafe_sdk import Choice, Noul, Question

from s1cap import jev
from s1cap.sim import LiberoEnv

SUITE, TASK, INIT = "libero_90", 61, 0
RENDER_SIZE = 1120
SIZES = (280, 336, 448, 560, 672, 896, 1120)
REPEATS = 3
CAPTION = "Fixed camera image of a robot table scene:"
QUESTIONS: dict[str, Question] = {
    "visible": Noul(instructions="Is the chocolate pudding box visible in the image?"),
    "side": Choice(
        instructions="Is the chocolate pudding box on the left or right half of the image?",
        criteria={"left": None, "right": None},
    ),
}
# 図に並べる大きさと、プリンの箱の周りを切り出す範囲 (画像の幅と高さに対する比。左、上、右、下)
MONTAGE_SIZES = (280, 336, 448, 560, 896)
MONTAGE_CROP = (0.0, 0.40, 0.25, 0.65)
IMAGE_DIR = Path("outputs/probe_resolution")


def answer_record(answer: Any) -> dict[str, Any]:
    if answer.type == "noul":
        return {"noul": answer.noul}
    return {"choice": answer.choice, "confidence": answer.confidence}


def montage(images: dict[int, np.ndarray], path: Path) -> None:
    """大きさごとに、画像全体とプリンの箱の周りを、同じ表示幅まで最近傍で拡大して縦に並べる。"""
    full_w, crop_w, label_h, gap = 560, 420, 40, 30
    rows = []
    for size in MONTAGE_SIZES:
        im = Image.fromarray(images[size])
        full = im.resize((full_w, full_w), Image.NEAREST)
        crop = im.crop(tuple(int(v * size) for v in MONTAGE_CROP))
        crop = crop.resize(
            (crop_w, round(crop_w * crop.height / crop.width)), Image.NEAREST
        )
        row = Image.new("RGB", (full_w + gap + crop_w, label_h + full_w), "white")
        row.paste(full, (0, label_h))
        row.paste(crop, (full_w + gap, label_h))
        ImageDraw.Draw(row).text(
            (8, 10),
            f"{size} px  (left: whole image, right: around the pudding box; "
            "both enlarged by nearest neighbor)",
            fill="black",
        )
        rows.append(row)
    out = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), "white")
    y = 0
    for row in rows:
        out.paste(row, (0, y))
        y += row.height
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)


def table(records: list[dict[str, Any]]) -> str:
    lines = [
        "| 一辺 | 入力トークン | レイテンシ [ms] | visible (Noul) | side (Choice) |",
        "| --- | --- | --- | --- | --- |",
    ]

    def span(values: list[float], fmt: str = "{:.0f}") -> str:
        lo, hi = min(values), max(values)
        return fmt.format(lo) if lo == hi else f"{fmt.format(lo)}〜{fmt.format(hi)}"

    for size in SIZES:
        rs = [r for r in records if r["size"] == size]
        sides = [r["answers"]["side"]["choice"] for r in rs]
        lines.append(
            f"| {size} px | {span([r['input_tokens'] for r in rs])} "
            f"| {span([r['latency_ms'] for r in rs])} "
            f"| {span([r['answers']['visible']['noul'] for r in rs], '{:.2f}')} "
            f"| {', '.join(sides)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("experiment", type=Path)
    args = parser.parse_args()

    env = LiberoEnv(SUITE, TASK, image_size=RENDER_SIZE, fixed_view="quarterview")
    rendered = env.reset(INIT).images["agentview"]
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    images = {
        size: np.asarray(Image.fromarray(rendered).resize((size, size), Image.LANCZOS))
        for size in SIZES
    }
    client = jev.client()
    records = []
    for size, image in images.items():
        Image.fromarray(image).save(IMAGE_DIR / f"{size}.png")
        for rep in range(REPEATS):
            response, ms = jev.ask(
                client, [CAPTION, jev.image_content(image)], QUESTIONS
            )
            record = {
                "size": size,
                "rep": rep,
                **jev.call_record(response, ms),
                "answers": {k: answer_record(v) for k, v in response.answers.items()},
            }
            print(json.dumps(record), flush=True)
            records.append(record)

    probe = args.experiment / "probe"
    probe.mkdir(parents=True, exist_ok=True)
    (probe / "resolution.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records)
    )
    (probe / "resolution.md").write_text(table(records))
    montage(images, args.experiment / "images" / "montage.png")


if __name__ == "__main__":
    main()
