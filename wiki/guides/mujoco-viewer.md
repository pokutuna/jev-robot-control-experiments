---
type: Guide
title: MuJoCo のビューワの使い方
description: MuJoCo 付属のビューワ (simulate) で LIBERO のシーンを表示し、対話シェルから命令を送って動きを見る方法と、ビューワのマウス・キー操作、LIBERO と組み合わせるときの注意
tags: [robotics, mujoco, libero]
---

# MuJoCo のビューワの使い方

## ビューワとは

MuJoCo には `simulate` という対話型のビューワが付属し、Python からは `mujoco.viewer` で使える。UI は MuJoCo 自身が OpenGL で描き、ウィンドウは GLFW で作る。robosuite や LIBERO の UI ではない[^python-doc]。

起動の方法は 2 つある[^python-doc]。

- `mujoco.viewer.launch(model, data)`: ビューワが物理シミュレーションも進める。呼び出し元は閉じるまで戻らない
- `mujoco.viewer.launch_passive(model, data)`: ビューワは表示と入力だけを受け持ち、すぐに戻る。シミュレーションを進めるのは呼び出し元のコードで、`viewer.sync()` を呼んだときにだけ、表示が更新され、GUI の入力が `mjModel` と `mjData` に反映される

このプロジェクトでは、LIBERO の環境 (`env.step()`) でシミュレーションを進めるので `launch_passive` を使う。

## 起動する

```sh
uv run --env-file .env mjpython scripts/viewer.py --suite libero_goal --task 8
```

- macOS では、`launch_passive` を使うスクリプトは `python` ではなく、mujoco に付属する `mjpython` で起動する[^python-doc]。uv で入れた Python 3.14 の venv でも `uv run mjpython` で動いた
- `.env` には `LIBERO_ROOT` を書いておく ([docs/setup.md](../../docs/setup.md))
- ウィンドウと一緒に Python の対話シェルが開く。シェルに打った命令でロボットが動き、ビューワに表示される

シェルで使える名前は `scripts/viewer.py` の冒頭に書いてある。座標系や action などロボットの動かし方は [LIBERO のロボットの動かし方](robot-control.md) にある。例:

```python
move_to(env, pos("akita_black_bowl_1") + [0, 0, 0.12])   # 手先をボウルの 12 cm 上へ
set_gripper(env, True)                                    # 指を閉じる
env.set_object_pose("akita_black_bowl_1", pos("plate_1") + [0, 0, 0.03], settle_steps=20)
env.success()
env.reset(1)                                              # 別の init state から始め直す
```

`exit()` か Ctrl-D でシェルを終えると、ビューワも閉じる。

## マウスとキーの操作

ビューワの Help に出る操作の一覧[^help]。

| 操作 | 入力 |
| --- | --- |
| 視点を回す | 左ドラッグ |
| 視点を平行に動かす | 右ドラッグ。Shift を押すと床と平行な面の中で動く |
| ズーム | スクロール、中ボタンのドラッグ |
| 物体を選ぶ | ダブルクリック |
| 選んだ物体の親を選ぶ | Page Up |
| 視点の中心を動かす | 右ダブルクリック |
| 物体を追う視点にする | Ctrl + 右ダブルクリック |
| 選んだ物体を回す | Ctrl + ドラッグ (Shift を押すと別の向きに回る) |
| 選んだ物体を押す | Ctrl + 右ドラッグ (Shift を押すと床と平行な面の中で押す) |
| モデルのカメラを順に切り替える | `[` `]` |
| 自由な視点に戻る | Esc |
| 左右のパネルを表示・非表示 | Tab / Shift-Tab |
| Help、Info、Profiler、Sensor、全画面 | F1〜F5 (未確認) |
| パネルの項目のショートカットを表示 | パネル上で右ボタンを押し続ける |
| パネルの節をすべて開く・閉じる | 節の題をダブルクリック |

トラックパッドでは、2 本指でクリックしたままドラッグすると右ドラッグになる。

再生・一時停止 (Space)、速度 (`+` `-`)、コマ送り (左右の矢印) はビューワが物理を進めるときの操作で、`launch_passive` では使わない。

## カメラ

`[` `]` で、モデルに定義されたカメラの視点に切り替えられる。左パネルの Rendering の Camera からも選べる。LIBERO のシーンでは、`agentview` (斜め上の固定カメラ) と `robot0_eye_in_hand` (手首のカメラ) が `LiberoEnv` の画像と同じ視点になる。

ビューワの表示は確認用で、プログラムが使う画像は `env.perceive().images[...]` で取る。

## LIBERO と組み合わせるときの注意

`LiberoEnv.launch_viewer()` (`src/s1cap/sim.py`) は、次の点に対処している。

- **衝突判定の形状:** robosuite のモデルは、見た目用の形状 (geom group 1) と衝突判定用の形状 (group 0) を同じ位置に重ねて持つ。衝突判定用の形状は、ロボットでは緑に塗られている[^collision-color]。robosuite のカメラは group 0 を描かないが[^robosuite-geomgroup]、ビューワは既定で描く。このためロボットが緑と白のまだら模様に、皿に灰色の多角形が重なって表示される。`launch_viewer()` は `viewer.opt.geomgroup[0] = 0` で group 0 を隠す。左パネルの Group enable から表示を切り替えられる
- **reset で開き直す:** LIBERO の reset は MuJoCo のモデルを作り直すので、`env.reset()` はビューワを閉じて開き直す。ビューワの Reset ボタンは robosuite の状態を介さずに `mjData` を戻すので使わない (動作は未確認)
- **入力が反映される時:** `sync()` は `env.step()` の中でしか呼ばれない。命令を実行していない間は物理が進まないので、Ctrl + ドラッグで物体を押しても、次に命令を実行するまで動かない。右パネルの Control で関節の制御入力を変えても、robosuite が step のたびに上書きする
- **カメラ画像の描画:** robosuite 1.4 は macOS でカメラ画像を GLFW で描画し、`mjpython` と一緒に使うと落ちる。対処は [LIBERO を新しい Python 環境で動かすときの制約と注意点](../findings/libero-sim-setup.md) にある

[^python-doc]: MuJoCo のドキュメントの Python の Interactive viewer の節。https://mujoco.readthedocs.io/en/stable/python.html#interactive-viewer
[^help]: mujoco 3.9.0 の `mujoco/_simulate.cpython-314-darwin.so` に含まれる Help の文字列。F1〜F5 の割り当ては文字列から読み取れず、確かめていない。パネル上で右ボタンを押し続けると各項目のショートカットが表示される
[^collision-color]: robosuite 1.4.1 の `robosuite/models/robots/robot_model.py` の `contact_geom_rgba` (`ROBOT_COLLISION_COLOR`)
[^robosuite-geomgroup]: robosuite 1.4.1 の `robosuite/environments/base.py` の 300〜301 行目。`render_collision_mesh` が偽なら group 0 を描かない
