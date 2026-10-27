"""Jev (TypeSafe AI の System 1 モデル) を OpenRouter 経由で呼ぶ。

API キーは環境変数 OPENROUTER_API_KEY から読む。typesafe-sdk の送り先 (base URL) を OpenRouter に
向けると、SDK の `system_one` がそのまま使える。

画像は SDK の `Image` では送れない。`Image` は multipart で送られ、OpenRouter が 400
(invalid content-type) を返す。代わりに `image_content` で data URL の `image_url` にして state に入れる。
"""

from __future__ import annotations

import base64
import os
import time
from collections.abc import Mapping
from typing import Any

import imageio.v3 as iio
import numpy as np
from typesafe_sdk import Question, SystemOneResponse, TypeSafeClient

OPENROUTER_BASE_URL = "https://openrouter.ai/api"
DEFAULT_MODEL = "typesafe/jev-1.14"


def client(model: str = DEFAULT_MODEL) -> TypeSafeClient:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY が無い。.env に書き、--env-file .env で渡す"
        )
    return TypeSafeClient(api_key=api_key, base_url=OPENROUTER_BASE_URL, model=model)


def image_content(image: np.ndarray, extension: str = ".png") -> dict[str, Any]:
    """uint8 の画像 (H, W, 3) を、state に入れられる data URL の image_url にする。

    Jev が受け付ける画像は一辺 256〜1568 px の PNG か JPEG。
    """
    data = iio.imwrite("<bytes>", image, extension=extension)
    mime = "image/png" if extension == ".png" else "image/jpeg"
    url = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    return {"type": "image_url", "image_url": {"url": url}}


def ask(
    jev: TypeSafeClient, state: Any, questions: Mapping[str, Question]
) -> tuple[SystemOneResponse, float]:
    """問いを送り、答えと、かかった時間 [ms] を返す。"""
    started = time.perf_counter()
    response = jev.system_one(state=state, questions=questions)
    return response, (time.perf_counter() - started) * 1e3


def call_record(response: SystemOneResponse, latency_ms: float) -> dict[str, Any]:
    """1 回の呼び出しのレイテンシ [ms] とトークン数。方策の判断の記録の calls に入れる。"""
    return {
        "latency_ms": round(latency_ms),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
