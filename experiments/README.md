# 実験

計画 ([docs/cap-libero-idea.md](../docs/cap-libero-idea.md)) の実験を、1 つの実験につき 1 つのディレクトリに置く。実験に共通の実装は `src/s1cap/` と `nodes/` にあり、ここには実験ごとの設定と記録だけを置く。

## ディレクトリの構成

```
experiments/NNN-slug/
├── README.md       課題、仮説、方法、結果、結論、次へ
├── dataflow.yml    dora の dataflow。ノードの path は ../../nodes/...
├── results.md      scripts/run_experiment.py が書く結果の表
├── runs/
│   └── init<N>-<日時>/   1 エピソードの記録 (evaluator ノードが書く)
└── videos/         README から参照する代表的な動画
```

エピソードを回さない実験 (静止画で問う 004-2、008、016、掴む動きだけを繰り返す 015) は、`runs/` と `videos/` の代わりに次を置く。

```
experiments/NNN-slug/
├── probe/          scripts/probe_directions.py、probe_targets.py、probe_grasp.py が書く記録 (*.jsonl) と表 (*.md)
└── images/         README から参照する代表的な画像
```

通信の不調で止まったエピソードや、方策を直す前のエピソードのように、`results.md` の表に入れない記録は `excluded-runs/` に移し、外した理由を README に書く。

- `NNN` は実験の番号、`slug` は条件を表す短い kebab-case の語にする
- 012 以降の `dataflow.yml` は、sim の出力 `sim_state` を evaluator の入力につなぐ。evaluator が `runs/*/sim_states.npz` に書いた状態から、`scripts/render_episode.py` で動画を描き直せる ([docs/setup.md の「動画を描き直す」](../docs/setup.md#動画を描き直す))。エピソードの動画は全部を git に入れず、レポートと動画に使うものだけを描き直して `videos/` に置く
- `dataflow.yml` は `scripts/run_experiment.py` で回す。sim ノードの `INIT` と evaluator ノードの `OUT_DIR` はランナーが書き換えるので、yml には書かなくてよい。回し方は [docs/setup.md の「実験を回す」](../docs/setup.md#実験を回す) にある

## README に書くこと

- 課題: 前の実験で何が残ったか
- 仮説: 何を変えれば課題が解けると考えるか。何を測って確かめるか
- 方法: タスク、init state、Jev に渡すもの (画像、印、文)、Jev への問い、判断の上限。前の実験との違いが分かるように書く。1 つの実験で変えたことが 2 つ以上あるときは、すべて挙げる
- Jev が決めていることと、コードが決めていること
- 結果: 成功率 (LIBERO の判定)、判断の回数、Jev の呼び出しの回数、トークン数、レイテンシ。`results.md` の表へのリンクと、要約
- 失敗の仕方: 動画と真値で確かめた、どの段でどう失敗したか
- 結論: 仮説に対して何が言えるか。試した構成で言えることに留め、分けていない要因は分けていないと書く
- 次へ: 次の実験で何を確かめるか

成功は LIBERO の判定で数える。ただし判定が成功でも、動画と真値で終わったときの状態を確かめ、判定と見た目が食い違うときは README に書く。

## git に入れるもの

1 エピソードの記録は 3〜4 MB あるので、全部は git に入れない。

| ファイル | git |
| --- | --- |
| `runs/*/summary.json` | 入れる。エピソードのまとめ |
| `runs/*/events.jsonl` | 入れる。Jev の答え、命令、命令の結果 |
| `runs/*/sim_states.npz` | 入れる。step ごとの MuJoCo の状態。動画を描き直すのに使う (012 以降。1000 step で約 0.4 MB) |
| `runs/*/episode.mp4`、`ground_truth.jsonl`、`robot_state.jsonl` | 入れない (大きい) |
| `runs/*/dora.log` | 入れない (手元の絶対パスを含む) |
| `videos/*.mp4` | 代表的なものだけを入れる |
