<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# 実験 007: LLM に手順のプログラムを書かせ、プログラムの中で Jev に画像を問う

ID: 10-exp007-cap
Bunch: ../20261027-image-only-jev.md

## Goal

005 と 006 では、手順と段階を選ぶ条件を人が書いたコードで与えた。007 では、ロボットを動かす関数と Jev に画像を問う関数、ロボットとシーンについての事実を LLM に渡し、手順を Python のプログラムで書かせる (Code as Policies)。真値を渡さずに libero_90 60 をどこまで解けるかを init state 0〜9 で確かめる。

## Done When

- `experiments/007-cap/` に dataflow、生成したプログラム (programs/)、init state 0〜9 の記録、`results.md` がある
- README に、LLM に渡したもの (関数、事実、測った傾向)、生成したプログラムの形、結果、失敗の仕方、005 と 006 との違いが書かれている

## Context

- 方策は `s1cap.cap.CaPPolicy` (POLICY: cap)。プログラムは `scripts/generate_programs.py` で実行の前に生成し、読んでから回す
- コード生成のモデルは deepseek/deepseek-v4.1-flash-1017 (OpenRouter、入力 $0.15/M、出力 $0.6/M)。費用を抑えるため、ユーザが指定した
- few-shot の例は渡さず、生成し直しもしない (1 回の生成で書かれたものをそのまま回す)
- dora run は同時に 2 つ回さない。006 が終わってから回す

## Result

成功 2/10 (LIBERO の判定)。詳細は `experiments/007-cap/README.md`。Done When を満たした。

- LLM は 10 本とも人が書いた手順とほぼ同じ流れのコードを書き、例外や上限で止まらず最後まで動いた。生成は 1 本 $0.012、約 60 秒
- 失敗の主因は、手首の画像でボウルの上に合わせる所が +y に 2.6〜5.1 cm ずれて止まったこと (006 は 0.5〜3.0 cm)。縁へ 6 cm ずらすと指は 2 つのボウルの間に下り、両方を持ち上げる (3、7) か、もう 1 つのボウルを運んだ (1、5、6、9)。8 は掴み損ね、4 は上げる途中で落とした
- 運ぶ段は 006 と同じく、トレイから遠ざかる判断が無かった
- 006 より合わせる所が早く止まる理由は確かめていない (目標の言い方、1 回の呼び出しで問う数が違う)

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-27 10:22 s1cap.cap (CaPPolicy、プロンプト、OpenRouter の chat completions)、scripts/generate_programs.py、policy ノードの POLICY=cap、run_experiment.py の PROGRAM_DIR を実装した
  - プログラムは別スレッドで動かし、移動と指の関数で命令を 1 つ渡して結果と次の観測を待つ。Jev の呼び出しは判断の記録の calls に入れ、コード生成の記録は programs/init<N>.json に分ける
  - builtins を絞って exec する。上限 (Jev 360 回、命令 120 回) を超えると BaseException で止める。スタブの Jev で受け渡しと上限を確かめた
  - deepseek/deepseek-v4.1-flash-1017 で init 0〜7 を生成し、読んだ。1 本 $0.009〜0.015、50〜75 秒、出力 1.9〜3.1 万トークン (推論を含む)。import などの危ない処理は無い
- 2026-10-27 10:33 init 0〜9 を回して真値と動画で失敗を分類し、README を書いた。動画は init 2、7、9 を videos/ に置いた
  - 掴んだときの指の幅を close+20 step で測ると開き直した後の値になることがあったので、幅は報告に使わず、コードが読んだ gripper_opening を使った
