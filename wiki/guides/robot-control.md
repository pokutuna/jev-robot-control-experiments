---
type: Guide
title: LIBERO のロボットの動かし方
description: LiberoEnv の Franka Panda を動かす方法。座標系、知覚と真値の取り方、OSC_POSE の 7 次元 action、PoseController と move_to / move_delta / set_gripper の使い方、届く範囲と制約
tags: [robotics, libero]
---

# LIBERO のロボットの動かし方

`LiberoEnv` (`src/s1cap/sim.py`) と `src/s1cap/control.py` で、LIBERO の Franka Panda を動かす方法。ビューワで動きを見ながら試す方法は [MuJoCo のビューワの使い方](mujoco-viewer.md) にある。

数値は、2026-10-26 に LIBERO-Goal の「put the bowl on the plate」(task 8) で測ったもの。

## 座標系

位置はすべて世界座標で、単位は m。

| 軸 | 向き |
| --- | --- |
| +x | ロボットから見て前 (テーブルの奥へ向かう向き) |
| +y | ロボットから見て左。`agentview` の画像では右 |
| +z | 上 |

- ロボットの土台は `[-0.66, 0, 0.912]` にある
- テーブルの上面は z = 0.9 で、テーブル上の物体はおよそ z = 0.9〜0.95 にある
- reset 直後の手先は `[-0.21, 0.00, 1.18]` あたりにある

## 知覚と真値

`LiberoEnv` は観測を 2 つに分けて返す。

| メソッド | 型 | 中身 |
| --- | --- | --- |
| `env.perceive()` | `Percept` | ロボット自身のセンサで分かるもの。カメラ画像 (`images`)、手先の姿勢 (`eef.pos`、xyzw の `eef.quat`)、指の関節値と開き (`gripper_width`)、腕の 7 関節の角度 (`arm_qpos`) |
| `env.ground_truth()` | `GroundTruth` | シミュレータだけが知っているもの。物体と固定物の姿勢 (`objects`、`fixtures`)、引き出しやつまみの関節値 (`joints`)、BDDL の成功判定 (`success`) |

`env.step` と `env.reset` は `Percept` を返す。方策には `Percept` だけを渡し、`GroundTruth` は評価、デバッグ、場面づくりに使う。

物体と固定物の位置は、ビューワのシェルでは `pos("akita_black_bowl_1")`、コードでは `env.ground_truth().objects[name].pos` で取れる。

### カメラの射影行列

`env.camera_matrix(camera)` は、世界座標の点を `images` の画像 (上下を直した向き) の画素に移す 3x4 の射影行列を返す。カメラの校正値にあたるので、知覚の側に入れてよい値として扱い、sim ノードは固定カメラの行列を `task` で policy に渡す ([dora-nodes.md](dora-nodes.md))。点 `[x, y, z, 1]` に掛けた `(a, b, w)` から、画素は `(a / w, b / w)` で、u は右、v は下へ増える。

MuJoCo のカメラの位置 (`data.cam_xpos`)、向き (`data.cam_xmat`)、縦の画角 (`model.cam_fovy`) から作る。MuJoCo のカメラは −z を向き、+y が画像の上なので、y と z の符号を反転して画像の向きに直す。robosuite の `get_camera_transform_matrix` は h5py を import するので使っていない。libero_90 60 の quarterview で、手先と物体の位置を画像に打って、写っている位置に重なることを目で確かめた (2026-10-27)。

`src/s1cap/marks.py` は、この行列で手先の位置と、手先の真下のテーブルの点を固定カメラの画像に描く。テーブルの高さ (`TABLE_Z = 0.44`) はシーンごとの値で、libero_90 60 の物体の置かれた高さから決めた。

## 動かし方

### 位置を指定する: `move_to`

```python
move_to(env, [-0.1, 0.0, 1.05])                         # 座標を直接指定
move_to(env, pos("akita_black_bowl_1") + [0, 0, 0.12])  # 物体の 12 cm 上
move_to(env, [-0.1, 0.0, 1.05], gripper=1.0)            # 指を閉じて動かす
```

- 手先と目標の差に比例した action を毎 step 送る P 制御である (後述の `PoseController`)
- 目標から 5 mm 以内に入ると `(知覚, True)` を返す。200 step (10 秒) で届かなければ `(知覚, False)` を返す
- 手先の向きは `quat` 引数 (xyzw の四元数) で指定する。既定値 `TOP_DOWN_QUAT = [1, 0, 0, 0]` は指先が真下を向く姿勢で、reset 直後の向きに近い
- `gripper` は動いている間の指の指令で、-1 で開き、+1 で閉じる。省略すると、最後に送った指令 (`env.gripper_command`) を保つ。reset 直後は -1 (開く)

### 今の位置から動かす: `move_delta`

```python
move_delta(env, [0, 0, 0.1])     # 10 cm 上へ
move_delta(env, [0.05, 0, 0])    # 5 cm 前へ
```

今の手先の位置に `dpos` [m] を足した位置へ `move_to` で動かす。向きは今のまま保つ。指の指令も、`gripper` を省略すると最後の指令を保つので、掴んだ物を持ったまま動かせる。

### 1 step ずつ動かす: `env.step`

`env.step(action)` は 7 次元の action を送り、1 step (1/20 秒) 進めて `Percept` を返す。

```python
for _ in range(20):
    env.step([0.3, 0, 0, 0, 0, 0, -1])   # 前へ動かす
for _ in range(20):
    env.step([0, 0, 0, 0, 0, 0.5, -1])   # 手首を z 軸まわりに回す
```

action は `[dx, dy, dz, dax, day, daz, gripper]` である。

- `dx, dy, dz`: 位置の変化。-1〜1 に切り詰められる
- `dax, day, daz`: 回転の変化 (軸角)。-1〜1 に切り詰められる
- `gripper`: -1 で開き、+1 で閉じる

robosuite の OSC_POSE コントローラは、位置の 1 を 0.05 m、回転の 1 を 0.5 rad に換算する。この量は「今の位置からどれだけ先を目標にするか」で、1 step で実際に動く量ではない。測った値は次のとおりで、1 step で動くのは目標までの一部である。

| action | 動いた量 |
| --- | --- |
| `dx = 1` を 1 step | x に 0.7 cm |
| `dx = 0.3` を 20 step | x に 6.9 cm |
| `dy = 1` を 20 step | y に 24.8 cm |

### 指を開閉する: `set_gripper`

```python
set_gripper(env, True)    # 閉じる
set_gripper(env, False)   # 開く
```

手先の位置と向きを保ったまま、15 step かけて指を動かす。指の開き (`env.perceive().gripper_width`) は、全開で約 0.078 m、何も掴まずに閉じると約 0.002 m になった。

### 目標を保つ制御器: `PoseController`

`move_to`、`move_delta`、`set_gripper` は `PoseController` の上に作ってある。`PoseController` は目標の手先の位置 `pos`、向き `quat` (xyzw)、指の指令 `gripper` を持ち、`Percept` から毎 step の action を計算する。目標を変えない限り、同じ姿勢を保つ action を出し続ける。

```python
ctrl = PoseController.hold(env.perceive())      # 今の手先の姿勢を目標にする
ctrl.pos = ctrl.pos + [0, 0, 0.05]
p = env.perceive()
while not ctrl.reached(p):                       # 位置が 5 mm 以内か。向きは見ない
    p = env.step(ctrl.action(p))
```

`move_to` などは目標に届くまで `env.step` を回してから戻る同期的な命令である。step を外から回す使い方 (dora のノードで毎 tick 1 step 進めるなど) では、`PoseController` を直接使う。

### 物体を直接置く: `env.set_object_pose`

ロボットを使わずに、物体を指定の姿勢に置く。述語の判定や画像の確認のために場面を作るときに使う。

```python
env.set_object_pose("akita_black_bowl_1", pos("plate_1") + [0, 0, 0.03], settle_steps=20)
env.success()   # → True
```

### 始め直す: `env.reset`

```python
env.reset()      # init state 0 から始める
env.reset(1)     # init state 1 から始める
```

LIBERO-Goal の各タスクには init state (物体の初期配置) が 50 個あり、`reset(0)`〜`reset(49)` で選べる。キャビネットなどの固定物の位置は `seed` で決まる ([LIBERO を新しい Python 環境で動かすときの制約と注意点](../findings/libero-sim-setup.md))。

## 制約と注意

- **障害物を避けない:** `move_to` は目標へまっすぐ向かう。途中にテーブルやキャビネットがあればぶつかる。物体の上へ一度上げてから下ろす
- **テーブルより下には行けない:** z = 0.80 を目標にすると、手先はテーブルの上面 (z ≈ 0.91) で止まり、`False` が返った
- **遠すぎる目標:** `[0.25, 0, 1.0]` (土台から水平に約 0.9 m) は届かず、手先は x = 0.185 で止まり、z が 0.91 まで下がった。届かない目標を指示すると、手先の向きも崩れる (指先が真下から約 40° 傾いた)
- **関節ごとには動かせない:** LIBERO の環境は OSC_POSE コントローラを使う。手先の位置と向きを指定する方式で、関節の角度を 1 つずつ指定する命令は無い
- **物を掴んで運ぶ流れ:** 物体の上へ `move_to` → 下ろす → `set_gripper(env, True)` → `move_delta` で持ち上げる、の順になる。ボウルでは次の流れで init state 0〜2 のすべてで成功した (1 回あたり約 2.5 秒)
  ```python
  rim = pos("akita_black_bowl_1") + [0, 0.06, 0.03]   # ボウルの +y 側の縁
  move_to(env, rim + [0, 0, 0.1]); move_to(env, rim); set_gripper(env, True)
  move_delta(env, [0, 0, 0.15])
  move_to(env, pos("plate_1") + [0, 0.06, 0.18])
  move_delta(env, [0, 0, -0.12]); set_gripper(env, False)
  ```
  - ボウルの中心 (5 cm 上) や、+x 側と -x 側の縁 (6 cm 外、3 cm 上) では、指が空を掴んで持ち上がらなかった。`TOP_DOWN_QUAT` の向きでは指が y 方向に閉じるため、+y 側の縁の壁を挟めたと考えられる (未確認)
