# 環境構築

LIBERO (robosuite 1.4、MuJoCo、Franka Panda) をローカルで動かし、カメラ画像と物体の真値を取るまでの手順。

動作を確認した環境は macOS (Apple Silicon、CPU で描画) である。Linux では `MUJOCO_GL=egl` などで動くはずだが、確認していない。

## 必要なもの

- [uv](https://docs.astral.sh/uv/)
- LIBERO の clone (このリポジトリには含めない)

## 外部のリソース

| 何を | どこから | どこに置くか | 渡し方 |
| --- | --- | --- | --- |
| LIBERO | https://github.com/Lifelong-Robot-Learning/LIBERO の commit `8f1084e` | 任意の場所 | 環境変数 `LIBERO_ROOT` |

LIBERO は `pip install` しない。`setup.py` の `install_requires` が空で、パッケージとして入れても `import libero` が通らないため、`s1cap.sim.setup_libero()` が `LIBERO_ROOT` を `sys.path` に足して import する。
シーンのアセット (約 405 MB) は LIBERO のリポジトリに含まれているので、別にダウンロードするものは無い。データセット (デモ) は使わない。

## 手順

```sh
# LIBERO を clone する (場所は任意)
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git ~/src/LIBERO
git -C ~/src/LIBERO checkout 8f1084e

# Python の環境を作る (.python-version の 3.14 を uv が用意する)
uv sync

# LIBERO の場所を渡す。.env に書いて uv run --env-file .env で渡してもよい
export LIBERO_ROOT=~/src/LIBERO

# LIBERO-Goal の「put the bowl on the plate」を reset し、画像と真値を保存する
uv run scripts/probe_scene.py --suite libero_goal --task 8
```

`outputs/probe/libero_goal_08_put_the_bowl_on_the_plate/init00/` に次のファイルができる。

- `agentview.png`: 斜め上からの固定カメラの画像 (既定 512×512)
- `robot0_eye_in_hand.png`: 手首カメラの画像
- `scene.json`: タスクの指示文と、次の 2 つ
  - `percept`: ロボットの知覚。手先の姿勢 (位置 [m] と xyzw の四元数)、指の開き [m]、腕の 7 関節の角度 [rad]
  - `ground_truth`: シミュレータの真値。物体と固定物の姿勢、引き出しやつまみの関節値、BDDL の成功判定

## ビューワで動きを見る

`scripts/viewer.py` は、MuJoCo のビューワでシーンを表示し、Python の対話シェルを開く。シェルで打った命令でロボットが動き、その様子がビューワに表示される。macOS では、ビューワを開くために `python` ではなく mujoco に付属する `mjpython` で起動する。

```sh
uv run mjpython scripts/viewer.py --suite libero_goal --task 8
```

```python
>>> move_to(env, pos("akita_black_bowl_1") + [0, 0, 0.12])  # ボウルの 12 cm 上へ手先を動かす
>>> set_gripper(env, True)                                   # 指を閉じる
>>> env.set_object_pose("akita_black_bowl_1", pos("plate_1") + [0, 0, 0.03], settle_steps=20)
>>> env.success()
True
>>> env.reset(1)                                             # 別の init state から始め直す
```

シェルで使える名前は `scripts/viewer.py` の冒頭に書いてある。ビューワのマウスとキーの操作と注意点は [wiki/guides/mujoco-viewer.md](../wiki/guides/mujoco-viewer.md) にある。

## ノードに分けて動かす (dora)

`dataflows/` の yaml は、シミュレーションを dora-rs のノード (`nodes/`) に分けて動かす。

| dataflow | 構成 |
| --- | --- |
| `dataflows/sim_eval.yml` | sim と evaluator だけ。ロボットは reset 直後の姿勢を保ったまま 100 step (5 秒) 進む |
| `dataflows/scripted_json.yml` | 手書きの policy を加え、「put the bowl on the plate」を行う。policy は物体の姿勢を真値から受け取る (JSON 入力条件) |
| `dataflows/jev_c2_image.yml` | Jev (`typesafe/jev-1.14`) に、指示文、手先の状態、カメラ画像から手先の移動方向と指の開閉を選ばせる。`.env` に `OPENROUTER_API_KEY` が要る |
| `dataflows/jev_c2_json.yml` | `jev_c2_image.yml` の画像の代わりに、物体の位置の真値を JSON で Jev に渡す |
| `dataflows/jev_c2_staged.yml` | libero_90 60 で、Jev に手首カメラの画像の中の位置関係と固定カメラの画像の状態を問い、その答えから意図 (近づく、下ろす、掴むなど) を選ばせる。動きは意図ごとにコードで決める。`.env` に `OPENROUTER_API_KEY` が要る |

```sh
uv run --env-file .env dora run dataflows/scripted_json.yml --log-level info
```

- sim ノード (`nodes/sim.py`) は 50 ms ごとに 1 step 進め、カメラ画像、ロボットの状態、真値を流す。タスクや step 数は yaml の `env:` で変える
- sim ノードの `FIXED_VIEW: quarterview` で、固定カメラをロボットの正面左の斜め上に置く。Jev の policy ノードの `OVERLAY` で、Jev に渡す画像に軸の矢印 (`axes`) や手先の真下の印 (`below`) を描く。どちらも yaml の `env:` に書く
- evaluator ノード (`nodes/evaluator.py`) は `outputs/runs/<日時>/` に、2 台のカメラの画像を横に並べた動画 (`episode.mp4`)、step ごとの真値 (`ground_truth.jsonl`) とロボットの状態 (`robot_state.jsonl`)、命令とその結果などの出来事 (`events.jsonl`)、まとめ (`summary.json`) を書く。まとめには成功したかと、エピソードを終えた理由 (`end_reason`) が入る
- `dataflows/jev_c2_staged.yml` では、evaluator の環境変数 `WRIST_CROSS_UV` により、動画の手首の画像を Jev に渡すときと同じ向き (180° 回す) にし、同じ位置に赤い × を描く。この設定の前に録画した動画には、`uv run scripts/draw_cross.py outputs/runs/<日時>` で × を描いた `episode_cross.mp4` を作れる
- evaluator の環境変数 `FIXED_MARK: "1"` で、動画の固定カメラの画像に、Jev に渡すときと同じ手先の印 (`s1cap.marks`) を描く (実験 003〜007 の dataflow)
- `--log-level info` にすると、dora の細かいログとノードの `print` が消え、ノードが `node.log` で送ったメッセージが残る

ノードの入出力と命令の形式は [wiki/guides/dora-nodes.md](../wiki/guides/dora-nodes.md)、dora の挙動と注意点は [wiki/findings/dora-dataflow.md](../wiki/findings/dora-dataflow.md) にある。

## 実験を回す

実験ごとの dataflow と記録は `experiments/NNN-slug/` に置く (構成は [experiments/README.md](../experiments/README.md))。`scripts/run_experiment.py` は、実験の `dataflow.yml` を init state ごとに回し、記録を `runs/init<N>-<日時>/` に置いて、結果の表を `results.md` に書く。

```sh
uv run --env-file .env scripts/run_experiment.py run experiments/005-staged-guide --inits 0-9
uv run scripts/run_experiment.py summary experiments/005-staged-guide   # 表だけを書き直す
```

`--inits` は `0-9` や `0,2,5` の形で書く。sim は 50 ms ごとに 1 step 進めるので、1 エピソードは長くても sim ノードの `MAX_STEPS` (Jev の dataflow では 7000 step) の 350 秒で終わる。

`scripts/direction_accuracy.py` は、記録の真値から、方策が送った横の移動が行き先 (ボウルかトレイの中心) へ近づく向きだったかを数える。真値の記録 (`ground_truth.jsonl`、`robot_state.jsonl`) は大きいので git の管理から外している。数えるのに使った判断ごとの手先、行き先、送った向きを `runs/*/direction.jsonl` に書き、真値の記録が無い run はこのファイルから数える。

```sh
uv run scripts/direction_accuracy.py experiments/002-image-direction
```

Code as Policies の実験 (`experiments/007-cap`) では、回す前に、LLM に手順のプログラムを init state ごとに書かせ、policy ノードの `PROGRAM_DIR` (既定 `programs/`) に置く。LLM のモデルは policy ノードの `CODE_MODEL` (既定 `deepseek/deepseek-v4.1-flash-1017`) で、OpenRouter 経由で呼ぶ。生成したプログラムは、回す前に読む。`run_experiment.py` は、init state ごとに `programs/init<N>.py` を policy ノードに渡す。

```sh
uv run --env-file .env scripts/generate_programs.py experiments/007-cap --inits 0-9   # 既にあるものは書き直さない (--force で書き直す)
uv run --env-file .env scripts/run_experiment.py run experiments/007-cap --inits 0-9
```

`experiments/009-cap-fixed-targets` は 007 のプログラムをそのまま使う (dataflow の `PROGRAM_DIR` が `../007-cap/programs`)。policy ノードの `FIXED_TARGETS=1` で、向きの関数が Jev に渡す行き先の言い方を 006 と同じものに置き換える。

```sh
uv run --env-file .env scripts/run_experiment.py run experiments/009-cap-fixed-targets --inits 0-9
```

`experiments/010-rim-target` は 006 の dataflow に、policy ノードの `RIM_TARGET: left` を足したものである。ボウルの中心に合わせた後、手首の画像で −y の側の縁へ寄せる向きを問い、y だけを合わせてから下ろす。

```sh
uv run --env-file .env scripts/run_experiment.py run experiments/010-rim-target --inits 0-9
```

`scripts/intent_rules.py` は、005、006、010 の記録で、Jev が選んだ段が問いに書いた条件の成り立つ段だったかを数える。

```sh
uv run scripts/intent_rules.py experiments/005-staged-guide experiments/006-fixed-carry experiments/010-rim-target
```

`scripts/probe_directions.py` は、エピソードを回さずに、手先を決まった位置に置いた静止画で、問い方ごとに Jev に向きを問う (`experiments/008-direction-probe`)。記録は `probe/*.jsonl`、表は `probe/*.md` に書き、問いに使った画像は `outputs/probe_directions/` に書く。

```sh
uv run --env-file .env scripts/probe_directions.py run experiments/008-direction-probe
uv run --env-file .env scripts/probe_directions.py run experiments/008-direction-probe \
    --dz 0.10 --conditions wrist_center,world_target --name low
```

`--center-dy` は手先を置く位置の中心を、掴むボウルの中心から y にずらす。004-2 では掴む縁 (±6 cm) の周りに置き、縁を行き先にして問う。

```sh
uv run --env-file .env scripts/probe_directions.py run experiments/004-2-rim-probe \
    --center-dy 0.06 --conditions wrist_rim_right_edge,wrist_rim_right_rim --name rim_plus
uv run --env-file .env scripts/probe_directions.py run experiments/004-2-rim-probe \
    --center-dy -0.06 --conditions wrist_rim_left_edge,wrist_rim_left_rim --name rim_minus
```

## 環境変数

| 変数 | 必須 | 内容 |
| --- | --- | --- |
| `LIBERO_ROOT` | ◯ | LIBERO の clone のパス |
| `OPENROUTER_API_KEY` | Jev か LLM を使うとき | OpenRouter の API キー。Jev (`typesafe/jev-1.14`) と、Code as Policies のプログラムを書く LLM を OpenRouter 経由で呼ぶ (`src/s1cap/jev.py`、`src/s1cap/cap.py`)。設定は [wiki/findings/jev-openrouter.md](../wiki/findings/jev-openrouter.md) |
| `MUJOCO_GL` | | オフスクリーン描画のバックエンド。macOS では未設定なら `cgl` にする。robosuite 1.4 は macOS ではこの値を見ずに GLFW で描画するので、`setup_libero()` が robosuite の描画を CGL に差し替える |
| `XDG_CACHE_HOME` | | LIBERO 用の `config.yaml` を `$XDG_CACHE_HOME/s1cap/libero/` (既定は `~/.cache/s1cap/libero/`) に書く |

LIBERO は初回の import で `~/.libero/config.yaml` を探し、無ければ標準入力で設定を問い合わせる。`setup_libero()` は `LIBERO_ROOT` から `config.yaml` を作り、`LIBERO_CONFIG_PATH` でその場所を渡すので、`~/.libero/` は読みも書きもしない。

## 依存パッケージの版

なるべく新しい版を使い、LIBERO が動かない部分だけ版を絞っている。

| パッケージ | 版 | 理由 |
| --- | --- | --- |
| Python | 3.14 | torch 2.14 には Python 3.15 用の wheel が無い |
| robosuite | 1.4 系 | LIBERO は robosuite 1.4 の環境とコントローラの API に依存する。1.5 で API が変わった |
| mujoco | 3.9 系 | robosuite 1.4 の OSC コントローラが動く最後の版。3.10 で `mj_fullM` の引数が変わった。3.11 で `MjData.qM` が無くなった。3.12 以降では関節の型の判定 (`jnt_type in (...)`) が常に偽になる |
| torch | 制限なし | LIBERO の init state (`*.pruned_init`) の読み込みだけに使う。torch 2.6 以降の `torch.load` は既定で `weights_only=True` になり、init state を読めない。このため `LiberoEnv` が `weights_only=False` を付けて読む |

gym 0.26 は import 時に「NumPy 2 に対応していない」という警告を出すが、LIBERO の環境の作成と実行には使われないので無視してよい。robosuite の「No private macro file found!」の警告も無害である。
