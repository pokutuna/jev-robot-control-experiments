<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 004: 003 に段階を選ぶ呼び出しを足し、2 回呼び出しで回す

ID: 05-exp004-two-call-image
Bunch: ../20261027-image-only-jev.md

## Goal

003 の問いの前に、段階 (approach、descend、grasp、lift、carry、lower、release、finish) を選ぶ呼び出しを足し、段階ごとに行き先を問いの文に書けば、003 の「ボウルの上に着く前に指を閉じる」失敗が減るかを init state 0〜9 で確かめる。

## Done When

- `experiments/004-marked-two-call/` に dataflow、init state 0〜9 の記録、`results.md` がある
- README に条件、結果、Jev とコードの分担、失敗の仕方、003 との違いが書かれている

## Context

- 方策は `s1cap.jev_marked.JevMarkedPolicy` (POLICY: marked2、`two_call=True`)
- 段階が approach、descend なら行き先を「the bowl to pick up」、carry、lower なら「the tray」として問う。それ以外の段階では横には動かさない
- 003 の結果は [experiments/003-marked-image/README.md](../../../experiments/003-marked-image/README.md)

## Result

004 は 0/10。段階を先に選ばせても、手先がテーブルから 15〜22 cm の高さにあるうちに grasp を選んで指を閉じた。段階は approach、descend、grasp の間を行き来し、lower 以降は一度も選ばなかった。結果は [experiments/004-marked-two-call/README.md](../../../experiments/004-marked-two-call/README.md)。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 08:58 init 0〜9 を回し、README に結果、段階の選び方、失敗の仕方、003 との違いを書いた
  - summary の mean_latency_ms は判断ごとの合計だった。results.md の列名を「判断ごとの平均レイテンシ」にし、001 の README の「1 回の呼び出し」の記述を直した
