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
- `scene.json`: タスクの指示文、物体と固定物の姿勢 (位置 [m] と xyzw の四元数)、引き出しやつまみの関節値、手先の姿勢、指の開き [m]、BDDL の成功判定

## 環境変数

| 変数 | 必須 | 内容 |
| --- | --- | --- |
| `LIBERO_ROOT` | ◯ | LIBERO の clone のパス |
| `MUJOCO_GL` | | オフスクリーン描画のバックエンド。macOS では未設定なら `cgl` にする |
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
