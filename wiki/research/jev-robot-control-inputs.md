---
type: Research
title: 公開されている Jev のロボット制御で Jev に渡している入力
description: awesome-jev に載ったロボット制御のリポジトリのコードを読み、目標物の位置をどの形で Jev に渡しているか、位置をどこから得ているか、Jev に何を選ばせているかを比べた結果
tags: [jev, robotics, libero, mujoco]
---

# 公開されている Jev のロボット制御で Jev に渡している入力

[awesome-jev](../sources/awesome-jev.md) に載ったロボット制御のうち、コードが公開されているものを 2026-10-26 に clone し、Jev に送る `state` と問い (`questions`) を作るコードを読んだ。各リポジトリの版は脚注に書く。

## まとめ

| 事例 | 目標物の位置の出どころ | Jev に渡す位置の形 | Jev が選ぶもの |
|---|---|---|---|
| Askable Arm | シミュレータの真値 | 物体ごとの世界座標 (m) と手先からの距離 (cm) | 約 30 の primitive と対象物体 |
| OpenRoboto | シミュレータの真値 | 目標 − 手先の差を軸ごとに符号付きの mm で、問いの文にも書く | 意図 → 軸ごとの negative / hold / positive と指 |
| Fazal Ali | シミュレータの真値 | 「3.2 cm forward, 1.0 cm left」のような残りの距離の文と、候補ごとに先読みした結果の文 | 目標点、先読み済みの移動、掴む / 離す |
| jev-libero | シミュレータの真値と先読み | 位置は渡さない。候補ごとに先読みした効果 (位置合わせの改善量 mm など) | 意図 → 方針 → 候補の入力 1 つ |
| embodied-jev (LIBERO) | GPT-6 Astra が画像の画素を選び、深度で世界座標に戻す | 目標 − 手先の差を軸ごとに符号付きの m で、問いの文にも書く | 6 軸それぞれの negative / hold / positive と指 |
| robo-harness (実機) | 手首カメラの画像から明るい塊を検出するコード | 塊の画像上の位置と掴む点の差 (`blob_dx`, `blob_dy`) と、前の一歩で塊が画像上でどれだけ動いたか | 関節ごとの小さな一歩 |
| Jev_SO101 (実機) | GPT-6 Astra が 2 視点の画像を読む | 位置は渡さない。「グラスが立っている」などの真偽と物体の説明 | スキルを実行するか、観測し直すか、止めるか |
| jev-drone | 前方カメラの深度とセグメンテーションを処理するコード | 方角ごとの空き距離 (m)、目標の方位 (°) と距離 | 回避の仕方、危険度、見失ったか |

- 画像をそのまま Jev に渡している事例は無い
- 目標物の位置は、どの事例でも Jev の外で求めている。真値を使うもの、別の LLM (GPT-6 Astra) に画像を読ませるもの、画像処理のコードで検出するものがある
- 移動の向きを Jev に選ばせる事例 (OpenRoboto、embodied-jev、robo-harness) は、目標との差を軸ごと、または画像の軸ごとに符号付きの数値で渡している。OpenRoboto と embodied-jev は、問いの文に「誤差が正なら positive」と選び方まで書いている
- jev-libero と Fazal Ali は、候補の動きをシミュレータで先に試し、その結果を選択肢の説明に書いている。Jev は結果の良い候補を選ぶだけになる

## 事例ごとの入力

### Askable Arm (ManiSkill)

`build_ask_state` が `state` を作る[^askable]。

- `robot`: 手先の位置 `tcp_position_m` (3 桁に丸めた m)、指の開閉、掴んでいる物体
- `objects`: 物体ごとに `position` (世界座標) と `distance_cm` (手先からの距離)、`grasped`、`pressed`
- `how_to_act`: 「To pick something up: open_gripper, hover_over it, descend_onto it, close_gripper, then up_5cm.」のような手順の文
- 直近 12 個の primitive

問いは `kind` (primitive) と `target` (対象物体) の 2 つ。primitive は「forward_1cm (+x)」のような向きと幅の決まった移動と、`hover_over`、`descend_onto`、`approach` のような物体を指定する動作である。物体を指定する動作では、移動先をコードが物体の位置から計算する。`target` の選択肢の説明には「red_cube is 12.3 cm from the fingertip (free).」のように距離を書く。

### OpenRoboto (MuJoCo、apple-to-plate)

`observe` が `state` を作る[^openroboto]。冒頭に `'source': 'MuJoCo geometry + contacts, not camera vision'` と書いている。

- 手先、りんご、掴む位置、皿の中心、離す位置の座標 (mm)
- `fruit_grasp_minus_tcp_mm`、`plate_release_minus_tcp_mm`: 目標 − 手先の差 (mm)
- `alignment`: 軸ごとの誤差と、`grasp_pose_reached` (xy が 4 mm 以内、z が 2 mm 以内)、`over_plate`、`at_release_height` などの真偽。判定はコードがする
- 指の接触、掴めているか (`grasp_secured`)、皿の中に入ったか

1 サイクルで 2 回問う。1 回目は意図 (approach、grasp、lift、carry、lower、release、withdraw、finish) を選ばせる。各意図の説明に「grasp_pose_reached is TRUE」のような条件を書く。2 回目は x、y、z を別々の問いにし、問いの文に「Current X=… mm. Fruit grasp X=… mm. Fruit grasp minus current on this axis=… mm.」と、その軸の値を書く。選択肢は negative / hold / positive で、説明に「Correct when the relevant target X is below current X beyond tolerance」と書く。

### Fazal Ali (MuJoCo、立方体を積む)

docstring に「code owns the math, Jev owns the judgment」とある[^fazal]。

- 目標点 (「15 cm above the red cube」など) を、コードが立方体の真値から作る
- 残りの距離を `words()` で「3.2 cm forward (away from base), 1.0 cm left」のような文にする
- 移動の候補 (目標へまっすぐ 2〜20 cm、高さを保って水平に、上下、横へずらす) を、物理シミュレーションの複製で先に動かす。立方体を倒す、掴んだ物を落とす、届かない候補は捨てる。残った候補には「then 1.2 cm down to go; touches the red cube」のような結果を付けて Jev に選ばせる
- 掴む / 離すも先に試し、「hand holds the blue cube firmly」のような結果を選択肢に書く。Jev が「act」に 0.75 以上を付けたときだけ実行する

### jev-libero (LIBERO)

記録された API のリクエスト (`examples/records/alphabet_soup_seed1/api.jsonl.gz`) を見た[^jevlibero]。

- 3 層に分けて問う。`intent` 層は、指の接触、指の開き、位置合わせの誤差 (`grasp_alignment_mm`)、目標までの距離などの測定値を受け取る。`strategy` 層は接触の種類と動きの種類 (並進か回転か) を選ぶ。`motor` 層は 1 つの入力を選ぶ
- `motor` 層の選択肢は「x+40mm」「y-10mm」のような入力で、各選択肢に、その入力をシミュレータで先に試した結果を書く。例えば `target_alignment_mm: 239.13`、`alignment_gain_mm: 27.74`、`bilateral_fingerpad_contact: false`
- 物体や手先の座標そのものは渡さない。測定と先読みはシミュレータの状態を使う

### embodied-jev (LIBERO、画像から)

画像を使い、物体の真値を使わない構成である[^embodied]。

- 上位 (GPT-6 Astra) が、外部カメラと手首カメラの RGB 画像を見て、目標の画素 `[u, v]` と、そこからのずらし `offset_m`、指の目標 (open / close / hold) を JSON で返す。画像には 64 px ごとの格子と画素の番号、手先の投影位置のシアンの十字を描く
- コードが、その画素の深度とカメラの内部 / 外部パラメータから世界座標に戻し、ずらしを足して目標点にする
- Jev には `position_error_m` (目標 − 手先、m) と目標点、手先の位置を渡す。x、y、z、rx、ry、rz を別々の問いにし、問いの文に「signed target-current error=+0.01234; tolerance +/-0.005. Choose positive if error>0.005, negative if error<-0.005, hold within tolerance.」と書く
- 結果の文書は、Jev の 1344 回の軸の選択がすべて誤差の向きと許容幅に合っていたとし、失敗は上位の目標点や接触の判断の問題と見ている。libero_90 の task 0 (引き出しを閉める) で GPT-6 + Jev が成功した[^embodied-results]

### robo-harness (実機の SO-101)

- 手首カメラの画像から、明るい塊を検出するコード (`blob.ts`) が物体を見つける[^robo]
- Jev には `blob_dx`、`blob_dy` (塊の画像上の位置 − 掴む点) と、`blob_change_since_last_step` (前の関節の一歩で塊が画像上でどれだけ動いたか) を渡す。画像上の位置は、画像の中心を 0、端を ±1 にした値である。掴む点は画像の中心ではなく、既定で (−0.16, 0.09) に置いている
- 段階の説明は「Centre the piece at the grasp point in the wrist camera: drive blob_dx and blob_dy toward 0.」で、タスクの説明に「Pixel offsets are image coordinates, not robot coordinates.」と書く
- Jev は関節ごとの小さな一歩を選ぶ。どの関節を動かすと塊が画像のどちらへ動くかは、前の一歩の変化から読ませる

### Jev_SO101 (実機の SO-101)

- GPT-6 Astra が上からと手首の画像 (と、教えた配置の参照画像) を読み、物体の説明、画像上の領域、「glass_upright」「block_in_gripper」などの真偽を返す[^so101]
- Jev に送る前に、画像上の領域を消す。コードのコメントは「Pixel boxes and joint angles cannot establish path clearance without camera calibration and kinematics. Preserve every observed fact/description; leave numeric control to the controller.」
- Jev は、予定のスキルを実行するか、観測し直す (`observe`) か、止める (`hold`) かと、危険かどうか (Noul) を答える。腕の動きは教えた姿勢へ動くコードが受け持つ

### jev-drone (MuJoCo のドローン)

- 前方カメラの深度とセグメンテーションの画像を処理して、方角ごとの空き距離、上 / 同じ高さ / 下の前方の空き、上下左右の余裕、最も近い障害物の距離と方位、目標の方位と距離を作る[^drone]。物体の真値は使わない
- Jev には任務の文、機体の能力 (上昇できる高さなど)、この観測を渡し、回避の仕方 (直進、左右の隙間、上昇、減速、探し直し) を選ばせる
- 衝突を避ける 50 Hz の反射層が別にあり、Jev の判断より優先する

## コードを読めなかった事例

- MakerMods Metal arm と Dmytro Hrybov の 2 回呼び出しはコードが公開されていない。投稿によると、前者は場面の状態を JSON で渡し、後者は「simplified geometry and contacts as text」を渡す ([awesome-jev.md](../sources/awesome-jev.md))
- JacobEGarcia/jev-robot-arm はリポジトリにコードが無かった

[^askable]: https://github.com/TarunTomar122/jev-askable-arm (bef98b3) の `jev_robotics/primitives.py` (`build_ask_state`、`scene_objects`、`target_criteria`、`KINDS`、`PrimitiveChooser.select`)
[^openroboto]: https://github.com/openroboto-ai/jev-robot-control (7a4ed8b) の `incremental_env.py` (`observe`) と `incremental_policy.py` (`INTENTS`、`MOTOR_INSTRUCTIONS`、`motor`)
[^fazal]: https://github.com/FazalAAli/jev-robotics-demo (531de61) の `jev_agent.py`
[^jevlibero]: https://github.com/Dimweaker/jev-libero (3bdad98) の `examples/records/alphabet_soup_seed1/api.jsonl.gz` と README
[^embodied]: https://github.com/FBddcz/embodied-jev (f08de2e) の `src/embodied_jev/libero_policy.py` (`PLANNER_SYSTEM`、`annotated_image`、`resolve_plan`、`local_state`、`motor_questions`)
[^embodied-results]: https://github.com/FBddcz/embodied-jev (f08de2e) の `docs/results/libero-vision/RESULTS.md`。示された記録は、GPT-6 のみが 2/2、GPT-6 + Jev が 1/1 で、GPT-6 + Jev の電子レンジは 1120 step、1200 秒で終わらず再測定中と書かれている
[^robo]: https://github.com/grmkris/robo-harness (ac75f4b) の `apps/server/src/decision/blob.ts`、`pickup.ts`、`tasks.ts`、`jev.ts`
[^so101]: https://github.com/AliUraish/Jev_SO101 (933403d) の `jev_arm/clients.py` (`AstraVision`、`JevJudge`、`questions`) と `jev_arm/models.py`
[^drone]: https://github.com/RomanSlack/jev-drone (974b473) の `tactics.py` と `flight.py`
