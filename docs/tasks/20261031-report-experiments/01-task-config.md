<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# ボウルとトレイを前提にした値をタスクごとの設定に分ける

ID: 01-task-config
Bunch: ../20261031-report-experiments.md

## Goal

task 61、62、60 で、真値を使う方策 (001 の形) と結果の表 (進み具合) を、コードを書き換えずに切り替えられるようにする。画像だけで動く方策の、タスクに固有の値 (言い方、掴む場所) は 05 の骨組みで扱う。

## Done When

- `src/s1cap/tasks.py` にタスクごとの値 (運ぶ物と置き場所の真値の名前、掴む点と離す点) があり、`jev_text.py` と `scripts/run_experiment.py` がそれを使う
- task 61 の sim の task と真値で、text 方策の状態と進み具合が計算できる (短い確認)
- 既存の実験 (task 60) の表が書き直しても変わらない

## Context

- 物体の名前と大きさは task 61 の init 0 で測った (tasks.py の docstring)
- sim の task の JSON に suite と task_id が入る (前の作業で足した)。古い記録の summary.json には無いので、無ければ libero_90 60 とみなす
- 固定カメラの印の卓の高さ (`marks.TABLE_Z`) は scene 4 の値。引き出しのタスク (08) で必要になったら切り替える
- CaP の部品 (`cap.py`) は行き先を文字列で受けるので、そのままタスクを替えられる。`jev_staged.py` と `cap.KNOWLEDGE` は予備実験の記録として残す

## Result

`src/s1cap/tasks.py` の TaskSpec を、真値を使う方策 (`jev_text.py`) と結果の集計 (`scripts/run_experiment.py`、`scripts/direction_accuracy.py`) が使う。記録の summary.json の suite と task_id から決まり、task_id の無い古い記録は libero_90 60 になる。表の進み具合の列は「運ぶ物の持ち上げ」「最後の運ぶ物とトレイ」に名前を変えた。画像だけで動く方策のタスクに固有の値は 05 の骨組みのプログラムに書く。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-31 16:50 src/s1cap/tasks.py に TaskSpec (運ぶ物と置き場所の真値の名前、文に書く名前、掴む点と離す点) を作り、jev_text、run_experiment、direction_accuracy、policy ノードが使うようにした
  - 物の大きさを sim で測った: プリンの箱 8.0 × 4.6 × 2.7 cm、ドレッシング 3.6 × 5.3 × 14.6 cm
  - 011 の表を書き直して値が変わらないこと、006 の向きの集計が動くことを確かめた (表の見出しだけ「運ぶ物」に変わるので、既存の results.md は書き直さずに戻した)
  - task 61、62 で text 方策の状態と問いの文ができることを確かめた。bowl では 001 と同じ文になる
