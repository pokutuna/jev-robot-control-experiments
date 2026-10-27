---
type: Finding
title: Jev を OpenRouter 経由で呼ぶときの設定と挙動
description: TypeSafe AI の Jev を OpenRouter の API キーで typesafe-sdk から呼ぶ設定。画像の渡し方 (SDK の Image は使えず data URL で渡す)、画像 2 枚の同時入力、Box の精度、レイテンシと料金
tags: [jev, openrouter]
---

# Jev を OpenRouter 経由で呼ぶときの設定と挙動

2026-10-26 に、typesafe-sdk 0.7.5 から OpenRouter の API キーで `typesafe/jev-1.14` を呼んだ結果。呼び出しは `src/s1cap/jev.py` にまとめてある。

## 設定

OpenRouter は Jev を 2 つの送り先で提供している ([Jev on OpenRouter](https://openrouter.ai/docs/guides/community/jev))。

| 送り先 | 形式 |
| --- | --- |
| `POST https://openrouter.ai/api/v1/systemone` | TypeSafe の System One API と同じ形式。typesafe-sdk から使える |
| `POST https://openrouter.ai/api/alpha/decisions` | OpenRouter の Decisions API (alpha)。本文は `model`、`state`、`questions` |

typesafe-sdk は `base_url` に `/v1/systemone` を付けた URL に送り、API キーを `Authorization: Bearer` で付ける。`base_url="https://openrouter.ai/api"` と OpenRouter の API キーを渡すと、OpenRouter の System One の送り先に届く。SDK は環境変数 `TYPESAFE_BASE_URL` と `TYPESAFE_API_KEY` も読むが、このリポジトリでは `.env` の `OPENROUTER_API_KEY` を読み、`TypeSafeClient(api_key=..., base_url=...)` に明示して渡す。

モデルは `typesafe/jev-1.14` (現行)、`~typesafe/jev-latest` (最新版の別名)、`typesafe/jev-1.13` を指定できる。1.13 は Box の問いに答えない。

## 画像の渡し方

- SDK の `Image` で画像を渡すと、SDK は multipart/form-data で送り、OpenRouter は `400 invalid content-type: multipart/form-data` を返す。`TypeSafe-Danger-Zone-Images: true` ヘッダを付けても同じだった
- `state` の配列に `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}` を入れると、SDK からでも Decisions API からでも通る。このとき SDK は JSON で送る。ヘッダは要らなかった
- TypeSafe の文書は 2026-09-19 の時点で、入力を「Text only」「No image, audio, or video input.」とし、現行を jev-1.13 としていた ([awesome-jev.md](../sources/awesome-jev.md))。ここでの結果は 2026-10-26 に `typesafe/jev-1.14` で試したもの
- 1 回の問いに画像を 2 枚 (agentview と手首カメラ、どちらも 320 px) 入れられた。手首カメラの画像についての問い (「手首カメラの画像にボウルが写っているか」) に 0.97〜0.98 で答えた

## 答えとレイテンシ

LIBERO-Goal の「put the bowl on the plate」の初期状態 (task 8、init state 0) を使い、同じ問いを 3 回ずつ送った。レイテンシは手元の Mac から測った往復の時間である。

| 入力 | 送り先 | レイテンシ | 入力トークン |
| --- | --- | --- | --- |
| JSON (物体の位置の真値) | SDK (`v1/systemone`) | 470〜1374 ms | 423 |
| 画像 1 枚 (agentview、320 px) | Decisions API | 494〜569 ms | 約 725 |
| 画像 1 枚 (agentview、320 px) | `v1/systemone` | 677〜787 ms | 約 725 |
| 画像 2 枚 (agentview と手首、320 px) | SDK (`v1/systemone`) | 539〜702 ms | 約 1030 |

- 画像付きのリクエストは長文脈モードで処理され、TypeSafe は既定のモードより遅く精度も下がるとしている。320 px の画像 1〜2 枚では、テキストだけの場合と同程度の時間で返った
- 料金は `usage.cost` で返り、画像 1 枚の問いで約 $0.00003 だった
- 次の primitive を選ぶ Choice は、JSON 入力では `approach_bowl` に 0.97〜0.98、画像入力では 0.57〜0.71 (次点の `grasp` が 0.23〜0.33) だった。3 回とも同じ答えを選んだ
- agentview の画像でボウルの Box を問うと、`top 0.51〜0.52, bottom 0.58〜0.60, left 0.41〜0.43, right 0.53〜0.55` (画像の幅と高さに対する比) を確信度 0.78〜0.82 で返した。画像で見たボウルの位置とほぼ合っていた。手首カメラの画像で問った結果と、Choice で移動方向を選ばせたときとの違いは [jev-c2-direction-policy.md](jev-c2-direction-policy.md)
