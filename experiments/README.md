# 実験

計画 ([docs/cap-libero-idea.md](../docs/cap-libero-idea.md)) の実験を、1 つの実験につき 1 つのディレクトリに置く。実験に共通の実装は `src/s1cap/` と `nodes/` にあり、ここには実験ごとの設定と記録だけを置く。

## ディレクトリの構成

```
experiments/NNN-slug/
├── README.md       目的、条件、結果、考察
├── dataflow.yml    dora の dataflow。ノードの path は ../../nodes/...
├── results.md      scripts/run_experiment.py が書く結果の表
├── runs/
│   └── init<N>-<日時>/   1 エピソードの記録 (evaluator ノードが書く)
└── videos/         README から参照する代表的な動画
```

- `NNN` は実験の番号、`slug` は条件を表す短い kebab-case の語にする
- `dataflow.yml` は `scripts/run_experiment.py` で回す。sim ノードの `INIT` と evaluator ノードの `OUT_DIR` はランナーが書き換えるので、yml には書かなくてよい。回し方は [docs/setup.md の「実験を回す」](../docs/setup.md#実験を回す) にある

## README に書くこと

- 目的: 前の実験から何を変え、何を確かめるか
- 条件: タスク、init state、Jev に渡すもの (画像、印、文)、Jev への問い、判断の上限。前の実験との違いが分かるように書く
- Jev が決めていることと、コードが決めていること
- 結果: 成功率 (LIBERO の判定)、判断の回数、Jev の呼び出しの回数、トークン数、レイテンシ。`results.md` の表へのリンクと、要約
- 失敗の仕方: 動画と真値で確かめた、どの段でどう失敗したか
- 分かったこと、次の実験に引き継ぐこと

成功は LIBERO の判定で数える。ただし判定が成功でも、動画と真値で終わったときの状態を確かめ、判定と見た目が食い違うときは README に書く。

## git に入れるもの

1 エピソードの記録は 3〜4 MB あるので、全部は git に入れない。

| ファイル | git |
| --- | --- |
| `runs/*/summary.json` | 入れる。エピソードのまとめ |
| `runs/*/events.jsonl` | 入れる。Jev の答え、命令、命令の結果 |
| `runs/*/episode.mp4`、`ground_truth.jsonl`、`robot_state.jsonl` | 入れない (大きい) |
| `runs/*/dora.log` | 入れない (手元の絶対パスを含む) |
| `videos/*.mp4` | 代表的なものだけを入れる |
