"""ノード間で値を受け渡すための、numpy 配列や dict と Arrow 配列の変換。"""

import json
from typing import Any

import numpy as np
import pyarrow as pa


def encode_image(image: np.ndarray) -> tuple[pa.Array, dict[str, Any]]:
    """画像を 1 次元の Arrow 配列にし、shape をメタデータで返す。"""
    return pa.array(image.ravel()), {"shape": list(image.shape)}


def decode_image(value: pa.Array, metadata: dict[str, Any]) -> np.ndarray:
    return value.to_numpy().reshape(metadata["shape"])


def encode_json(data: dict[str, Any]) -> pa.Array:
    return pa.array([json.dumps(data)])


def decode_json(value: pa.Array) -> dict[str, Any]:
    return json.loads(value[0].as_py())
