<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 015、016: 段ごとの小さな作業を確かめる

ID: 04-micro-probes
Bunch: ../20261031-report-experiments.md

## Goal

アウトラインの実験 3。手順の骨組み (05) と CaP (07) が頼る小さな作業が、task 61、62、60 で成り立つかを、タスクを最後まで回さずに確かめる。掴めるか (物の位置からのずれと掴めた割合) と、行き先の言い方ごとに手首の画像の向きの答えが物へ向かうか、を測る。

## Done When

- `experiments/015-grasp-tolerance/` と `experiments/016-target-wording/` に probe の記録 (jsonl) と表 (md) と README がある
- 骨組みに埋める値 (言い方、掴む場所のずらし、下ろした後に上げる量) を README の結論から選べる

## Context

- 掴めるか: `scripts/probe_grasp.py` (Jev を呼ばない)。下ろして当たって止まった所から RISE 上げて閉じ、始めの高さまで持ち上げる
- 言い方: `scripts/probe_targets.py`。008 と同じ格子に手先を置き、`s1cap.cap.direction_questions` で問う
- 画像の中の向きの確かめは 004、008 (予備実験) の結果を使う

## Result

015 と 016 の README、probe の記録と表がそろった。骨組みに埋める値は次のとおり。

- 言い方 (016): task 61「the chocolate pudding box」、task 60「the center of the bowl to pick up」。固定カメラは粗く寄せる段にだけ使う
- 掴む点 (015): task 61 は箱の中心 (`GRASP_SHIFT` 0、y -2〜+1 cm で掴める)、task 60 は中心から y に -6 cm (そこから ±2 cm、±3 cm で 102/105)。RISE は 1.5 cm のまま
- task 62 の瓶は、瓶の x で手先が 0.62 m より下に下りられず掴めない (11/175)。骨組みと CaP からは外し、実験 3 の結果として報告する

CaP に渡す知見は `s1cap.cap.KNOWLEDGE["016"]` に書いた (019 で使う)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-31 17:00 015 (掴めるか: pudding、dressing、dressing_rise0、bowl_rim_minus) と 016 (言い方: pudding、pudding_fixed、dressing、bowl_left_right) を init 0〜4 で回し始めた
  - 016 pudding: 手首の画像では言い方によらず y は 92〜100% 近づく。x は 53〜73% で、残りは動かさない (箱は x に 8 cm あり、015 では x のずれ ±4 cm でも掴めるので害は小さい)
  - 016 pudding_fixed: 物から ±4〜6 cm では固定カメラの答えは 9 割が動かさない。固定カメラは粗く寄せる段にだけ使う
- 2026-10-31 17:36 015 bowl_rim_minus 156/175、README を書いた。KNOWLEDGE["016"] に掴めるかの結果を入れた
  - dressing_rise0 は途中で止め、記録は使わない (瓶は下りられないことが原因なので RISE を変えても意味が無い)
  - 016 の README で task 62 を外したことを書いた
