---
type: Finding
title: LIBERO を新しい Python 環境で動かすときの制約と注意点
description: LIBERO (robosuite 1.4、MuJoCo) を Python 3.14 と uv で動かしたときに分かった、依存の版の上限、import の方法、画像や四元数の向き、reset の乱数、速度
tags: [robotics, libero, mujoco]
---

# LIBERO を新しい Python 環境で動かすときの制約と注意点

2026-10-26 に、LIBERO の commit `8f1084e` を macOS (Apple Silicon) の Python 3.14 で動かして分かったこと。手順は [docs/setup.md](../../docs/setup.md)、実装は `src/s1cap/sim.py` にある。

## 依存の版

| パッケージ | 動いた版 | 上限の理由 |
| --- | --- | --- |
| Python | 3.14 | torch 2.14.1 には Python 3.15 用の wheel が無い。uv は既定で 3.15 を選ぶので、`.python-version` で 3.14 に固定する |
| robosuite | 1.4.1 | LIBERO は robosuite 1.4 の API を使う |
| mujoco | 3.9.0 | 下の表のとおり、3.10 以降では robosuite 1.4 が動かない |
| numpy | 2.5.4 | 制限なし |
| torch | 2.14.1 | 制限なし。init state の読み込みだけに使う |

mujoco の版ごとに試した結果は次のとおり。

| mujoco | 結果 |
| --- | --- |
| 3.9.0 | 環境の作成、step、描画が動く |
| 3.10 | OSC コントローラの `mj_fullM(m, dst, qM)` が `incompatible function arguments` で落ちる。引数が `(m, d, dst)` に変わった |
| 3.11 | `MjData.qM` が無くなる |
| 3.12 以降 | `model.jnt_type[j] in (mjtJoint...)` が常に偽になり、robosuite の `get_joint_qpos_addr` の assert で落ちる |

## import と設定

- LIBERO は `setup.py` の `install_requires` が空で、pip で入れても `import libero` が通らない。clone のパスを `sys.path` に足して import する
- LIBERO は初回の import で `~/.libero/config.yaml` を探し、無ければ標準入力で問い合わせる。以前に別の場所の LIBERO を使っていると、`~/.libero/config.yaml` はその古いパスを指したまま残る。このため `config.yaml` を自分で書き、`LIBERO_CONFIG_PATH` でその場所を渡す
- `benchmark.get_task_init_states` は `torch.load` を `weights_only` の既定値で呼ぶので、torch 2.6 以降では init state を読めない。自分で `weights_only=False` を付けて読む
- macOS のオフスクリーン描画は `MUJOCO_GL=cgl` で動く
- gym 0.26 の NumPy 2 非対応の警告と robosuite の「No private macro file found!」の警告は出るが、動作には影響しなかった

## 観測の向き

- カメラ画像は上下が逆に返る。`np.flipud` で直す
- 観測の `robot0_eef_quat` は xyzw、MuJoCo の `data.body_xquat` と free joint の qpos は wxyz
- OSC_POSE の action は `[dx, dy, dz, dax, day, daz, gripper]` で、gripper は -1 で開き +1 で閉じる。既定の出力範囲は action 1 あたり位置 0.05 m、回転 0.5 rad
- 指の開き (`robot0_gripper_qpos` の絶対値の和) は全開で約 0.08 m

## reset の乱数

LIBERO は reset のたびに固定物 (キャビネットなど) の位置を大域の `np.random` で引き直し、その位置は init state に含まれない。`env.seed()` だけでは揃わず、reset の前に `np.random.seed(seed)` を呼ぶと、同じ seed で同じ配置になり、違う seed で配置が変わることを確かめた。

## 物体の姿勢を直接置く

動かせる物体は free joint を 1 つ持つ (`objects_dict[name].joints[0]`)。`sim.data.set_joint_qpos` で位置と wxyz の四元数を書き、`regenerate_obs_from_state` で観測を作り直す。LIBERO-Goal の「put the bowl on the plate」で、ボウルを皿の 3 cm 上に置いて 20 step 待つと BDDL の成功判定が真になった。

## 固定物と関節

LIBERO-Goal のシーンでは、`fixtures_dict` に `wooden_cabinet_1`、`flat_stove_1`、`wine_rack_1` が入り、テーブルは入らない。固定物の可動部の関節として、`wooden_cabinet_1_top_level`、`wooden_cabinet_1_middle_level`、`wooden_cabinet_1_bottom_level` (slide) と `flat_stove_1_button` (hinge) がある。

## 速度

512×512 のカメラ 2 台で、環境の作成と reset に約 9 秒、step は約 53 step/秒だった。LIBERO の環境は `hard_reset=True` で、reset のたびに MuJoCo のモデルを作り直す。
