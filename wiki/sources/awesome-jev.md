---
type: Source
title: Awesome Jev
description: Frank-ZY-Dou/awesome-jev (GitHub Pages) による、TypeSafe AI の Jev をロボット制御、3D、ゲームなどに使った公開事例の一覧。各事例の入力の作り方、報告された数値、GitHub のリポジトリをまとめたもの
resource: https://frank-zy-dou.github.io/awesome-jev/
tags: [jev, robotics, libero, mujoco]
---

# Awesome Jev

TypeSafe AI が 2026-09-15 に出した Jev を、ロボット制御、3D とアニメーション、関連する制御に使った公開事例の一覧。各事例に元の投稿へのリンク、作者、日付を付け、主張と数値は作者の言葉を引用し、デモの動画と画像をリポジトリに保存している。リンクはすべて 2026-09-19 に開いて読んだと書かれている (一部の GitHub リポジトリは 2026-09-20 に確認)。投稿に書かれていないこと (ロボットの機種、シミュレーションかどうか、画像をどうモデルに渡したか) は、推測せずに「書かれていない」と記している。

## Jev について

- TypeSafe AI の最初の「System One」モデルで、創業者の Diogo Almeida が 2026-09-15 に「available today in early access」として発表した。ベンダーの説明は「Think of Jev as a frontier-intelligence function call: unstructured state in, typed probabilistic decisions out.」。「Reinforcement Learning for Calibrated Decisions (RLCD)」で学習している
- 2026-09-19 にベンダーの文書から読んだ事実として、次を挙げる
  - **インターフェース**: `POST /v1/systemone` の 1 つの endpoint に、Noul (yes の確率を返す yes/no の問い)、Choice (定義した選択肢から 1 つを選び、全体の確率分布を返す)、Score (定義した rubric で状態を評価する) の 3 種類の問いがある。「Jev supports a cardinality up to 255」
  - **入力**: 「Text only. String, JSON object, or array of text values. No image, audio, or video input.」。文脈は「64k tokens per request; 32k tokens for state plus the longest question」。この一覧のロボットの投稿がすべてカメラ画像ではなく構造化した状態を渡しているのはこのためだ、としている
  - **版**: 現行は「Jev 1.13」(`jev-1.13.0`) で、`jev-latest` がこれを指す。確信度のしきい値を特定の版に合わせて調整したなら版を固定するよう、文書が勧めている
  - **料金と上限**: 入力 10 億 / 100 万 token あたり「$42 / $0.042」、出力 token は無料。レート制限は「250,000 tokens per second / 1,200 requests per minute」で、「can change without notice」
  - **速さと費用 (ベンダーの主張)**: 「End-to-end response time is 70ms-500ms for TypeSafe.」。ホームページの「193.6x Faster, 444.6x Cheaper」は自社のワークフローでの測定で、launch post は「are on the higher end of real world gains」と書く
  - **「calibrated」の意味**: 「Calibration is measured across groups of predictions; it does not guarantee that an individual answer is correct.」。確信度は振り分けに使う想定で、高ければ自動で実行し、低ければ実行せず人や別の仕組みに回す
  - **苦手なこと (ベンダーが jev-1.13 について挙げたもの、2026-09-17 確認)**: 「It struggles with tasks that require numeric precision」「Jev is not a calculator」「jev-1.13 does not count reliably」「Jev suffers from context rot, so unrelated material in the state costs you accuracy」。確認した文書には、ロボットや物理的な安全についての指針は無い
- 一覧の投稿は同じ使い方をしている: アプリやシミュレータが構造化した状態 (JSON、文章、選択肢の一覧) を送り、Jev が確率付きの型付きの選択を 1 つ返し、動きや編集は別のコードが実行する

## 実機のロボット制御 (2 件)

- **SO-101 がボールをボウルに入れる** (Daniiar Abdiev、X、2026-09-18): 「Two USB cameras, an SO-101, and @typesafeai's Jev choosing the next move at ~2 decisions a second.」。動画には「Supervised prototype」「Edited real footage」の字幕がある。カメラ画像をどう Jev の入力にしたかは書かれていない
- **学習した方策なしの zero-shot 制御** (Zaid Bulbul、X、2026-09-18): アームの機種と行動のインターフェースは書かれていない

## シミュレーションでのロボット制御 (8 件)

Jev が構造化した状態から離散的な行動や目標を選び、シミュレータやスクリプトが実行する。

- **Askable Arm** (Tarun Tomar、LinkedIn、2026-09-18、[jev-askable-arm](https://github.com/TarunTomar122/jev-askable-arm)): 英語の目標から、固定の primitive (README によると「menu of ~30 primitives」) を Jev がつなぐ。「Jev never outputs torques or a trajectory. It picks one primitive per step」「No images go to Jev」(シミュレータの真値を受け取る)。ManiSkill の PickCube-v1 と ResetButton-v7、seed 0、Franka Panda。「~1 second per Jev pick」
- **1 回の更新を 2 回の呼び出しに分ける** (Dmytro Hrybov、X、2026-09-18): MuJoCo で、最初はうまくいかなかったので、「decide what to do next, then decide how to move the arm and gripper」の 2 回に分けた。「Jev doesn't accept images, it gets simplified geometry and contacts as text here.」
- **MakerMods Metal arm** (Isaac Sin、X、2026-09-18): シミュレータが場面の状態を JSON で渡し、カメラ画像は渡さない。Jev は「picks the next bounded action (hover, descend, grasp, lift, place) as a typed choice with a confidence score」。「Put the red apple in the blue bin」で「9 decisions at ~150 ms each」。場面に対応づけられない作業は推測せずに断る
- **apple-to-plate での比較** (OpenRoboto、X、2026-09-19、[jev-robot-control](https://github.com/openroboto-ai/jev-robot-control)): 「Each model chooses intent → X/Y/Z direction + gripper open/hold/close.」。Jev 1.13 は 113 cycle (226 calls) で $0.018825、181.847 s で置けた。GPT-6 Astra は 106 cycle (212 calls) で $5.933624、707.274 s。GPT-4.1 mini は「160-cycle limit reached」で $0.288512。「These are one seed-0 trial per controller, not success-rate estimates」で、観測は「are not camera perception」
- **確信度で区切る多段の操作** (Jony Shaik、X、2026-09-18): 「Jev handles the high-level task transitions and confidence gating at each boundary, while deterministic physics guards manage execution.」。動画はシミュレーションの人型ロボットが注ぐ作業
- **MOSS のごみ拾い** (metr0x、X、2026-09-18、[moss-jev](https://github.com/metrox-eth/moss-jev)): Jev が拾う対象を選ぶ。今のページは「LIVE API OFF · REPLAY ONLY」で、3 つの作業を MuJoCo で実際の Jev の判断で 1 回ずつ動かした記録を再生する
- **初期のアームの実験** (Arpan、X、2026-09-18): 「Seems Jev can control robot arms. Need more iterations to make its degrees of freedom broader.」
- **Microduck が障害物を避けて目的地へ行く** (ostyn、X、2026-09-18): 数日の実験で「only spent $0.34」。センサと低レベルの制御器は書かれていない

## 3D、アニメーション、仮想カメラ (4 件)

- Blender の飛行機のモデル (Har、2026-09-18): 形は別のチャットモデルが作り、Jev は評価に使う
- 3D キャラクターの表情と体 (Joao Bortotti、2026-09-18): 「ten decisions per message」「No preset expressions.」
- 1 つの 3D 環境に 500 の agent (Cris Lenta、2026-09-17): 「500ms average latency, 35 API calls/s」
- 動画編集ツールのカメラの動き (Alex Carrabre、2026-09-18): 自然言語のカメラの指示を、いくつかの多肢選択 (動きの種類、カメラの軸ごとの向きと大きさの段階) に答えさせて keyframe にする。軌跡は時刻、方位角、仰角、距離で表し、描画の前に検査する。「~230x faster planning」と書くが、比較の基準は書かれていない

## 乗り物、ドローン、ゲーム (8 件、すべてシミュレーション)

運転シミュレータ (Justin Schroeder、2026-09-16。Cipher、2026-09-18 は車線変更、ブレーキ、加速、減速を選ぶ)、小惑星帯のドローン (Mahmoud、2026-09-18。「300ms decisions」、確信度が低いときは大きなモデルに任せ、「99% of the time, Jev steered the drone on its own」)、Kerbal Space Program のロケット (TextLayer)、クジラの上の街のゲーム (gokaygokay。世界は GPT 6 Astra が作り、行動は Jev が選ぶ)、Sentinel の戦術判断 (Adi)、Manhattan の経路探索で Jev が好みを与える (Shivam Chauhan)、厨房の優先度の判断 (JollyRojak。早い試験で消火 66%、注文 33%、warm で約 200 ms)。

## デザインツールとロボットのデータ (3 件)

Figma の音声操作 (mikegee、「$0.01」)、Figma で要件の文書とデザインを照合するプラグイン (Furkan)、人型ロボットの遠隔操作データの評価 (Anto Patrex、LinkedIn、2026-09-19。「99% label consistency. 91% annotation completeness.」、42 秒の両腕の作業を 20 区間に分け、時間の 98.5% にラベルを付けた。作者は「'n' is minimum」と書く。制御ではなくオフラインの評価)。

## 報告された数値

- **ベンダーの評価** ([evals.typesafe.ai](https://evals.typesafe.ai/)): Jev のワークフローは一致率 67.8%、$0.0004、0.4 s。同じ表で opus 5 は 73.1%、$0.1761、37.8 s、sol は 74.1%、$0.0836、23.3 s、terra は 67.9%、$0.0304、10.1 s。正解のラベルは GPT-6 Astra と Claude Fable 5.1 (どちらも high thinking) の回答の平均で作る
- **シミュレーションでの独立した測定**
  - OpenRoboto の apple-to-plate: 前述
  - Fazal Ali ([jev-robotics-demo](https://github.com/FazalAAli/jev-robotics-demo)): MuJoCo の Franka と Allegro hand で立方体を積む。Jev は 19.1 s、$0.0006、Claude Opus 5 は 158.8 s、$0.75 (Opus は 1 回やり直し、やり直しなしなら約 55 s、$0.19)。「One recorded run each」
  - Roman Slack ([jev-drone](https://github.com/RomanSlack/jev-drone)): MuJoCo の Skydio X2。Jev は約 2.5 Hz で、50 Hz の反射層が「keeps the veto」。Jev ありで「77.5 m (whole course)」、基準の 3 回は 17.7 m。「80 calls over 65 s, 0.11 s median latency」。それより単純な場では、3 seed を揃えた比較で Jev の優位は無かった
- 投稿の数値は作者の報告で、成功率ではない
- 2026-09-19 に arXiv で「TypeSafe」「Jev」を検索し、査読された評価は見つからなかった

## GitHub のリポジトリ

前述のもののほか、次を挙げる。

- [kxzk/typesafe-jev-drone-demo](https://github.com/kxzk/typesafe-jev-drone-demo): Three.js のドローンで、`jev-latest` が移動を選ぶ
- [RomanSlack/jev-drone](https://github.com/RomanSlack/jev-drone): 「Camera-only autonomous drone in MuJoCo」だが、「Jev is not a vision model. It takes JSON and returns typed answers with probabilities.」
- [AliUraish/Jev_SO101](https://github.com/AliUraish/Jev_SO101): 「Astra interprets both views, Jev selects a typed skill and evaluates unsafe/done questions」。「The demo is synthetic orchestration, not a physics simulation or proof of grasp success.」
- [JacobEGarcia/jev-robot-arm](https://github.com/JacobEGarcia/jev-robot-arm): ブロックを運ぶ 2 回呼び出しの方策 (README は空)
- 2026-09-20 に README を確認し、作者が測った実行が載るもの (実験は再現していない)
  - [Dimweaker/jev-libero](https://github.com/Dimweaker/jev-libero): 「Jev selects an intent, a contact/motion family, and an input, with each choice informing the next.」。LIBERO/MuJoCo で「single-target Panda/OSC interface」。「One successful example from each bundled task:」として、microwave は 14 decisions、111 environment steps、$0.001249、top drawer は 20、155、$0.001418。「Videos follow simulation time, with decision and physics-preview waiting omitted.」
  - [Foadsf/jev-for-engineers](https://github.com/Foadsf/jev-for-engineers): noul、choice、score を使う工学の判断の例が 8 つ。「That is a demonstration, not a calibration.」
  - [grmkris/robo-harness](https://github.com/grmkris/robo-harness): 実機の SO-101 と Pi のカメラ 2 台。Jev が範囲を決めた関節の小さな動きを選ぶ。受け入れ記録では Jev の choice が「5/5, 14.2 s, $0.00028」
  - [amazedsaint/jevduck](https://github.com/amazedsaint/jevduck): MuJoCo WebAssembly で、Jev が群れへの指示を選び、関節は元の ONNX の方策が動かす。「No controlled comparison yet shows that Jev outperforms a deterministic supervisor.」
  - [GY19A/jev-stage](https://github.com/GY19A/jev-stage): 選択を動きのクリップに対応させる。167〜305 ms
  - [atarikcaliskan/jevball](https://github.com/atarikcaliskan/jevball): 「Jev only picks among typed, pre-computed candidates and returns probabilities.」。「70 calls, 0 errors, 0 invalid answers, 366 ms average latency」、$0.0051。「not a benchmark」
  - [kavehmz/typesafe-playground](https://github.com/kavehmz/typesafe-playground): 車線と目標速度を選ぶ。「Jev receives structured simulated sensor observations rather than camera images.」
  - [robokrunch/jev-physical-ai](https://github.com/robokrunch/jev-physical-ai): ロボット群の障害の振り分けで 3 つの判断を同時に問う。「300 / 300」、team の一致「274 / 300 (91.3%)」、p50「0.527 s」。「no probability-calibration study」
- Jev で実際に動かした記録が無い統合: [FBddcz/embodied-jev](https://github.com/FBddcz/embodied-jev) (MuJoCo と Franka Panda、模擬応答の試験だけ)、[rokbenko/quackd](https://github.com/rokbenko/quackd)
- Jev の周辺の道具: [BillionsBobby/JevRouter](https://github.com/BillionsBobby/JevRouter) (モデル、subagent、skill、MCP の道具などを 1 つの候補集合にして Jev の Choice で選ぶ。Toolathlon の 10 タスクで先頭 5 回の道具呼び出しの位置ごとの一致は Jev serial 38%、Jev decompose + thread 44%、DeepSeek 24%)
- ベンダーのコード: typesafe-sdk-python、typesafe-sdk-js、skills、system-one-adapter-python (「Drop-in TypeSafeClient replacement backed by LLM APIs」)

## 一覧のサイトと記事

- [jevable.com](https://jevable.com/): Jev のプロジェクトの独立した一覧
- [systemonemodels.org](https://systemonemodels.org/): TypeSafe AI と無関係な個人のサイト。実時間制御のページを、Jev をロボットにつなぐ前に読むよう勧める。「Hard real-time control is out of scope entirely. A loop that must hold a deadline every cycle cannot depend on a network request, whatever the median latency is.」
- LiteLLM の記事 (2026-09-20): 「v1.103.0-rc」で Jev の endpoint を proxy する
- Langfuse の記事 (2026-09-18): 保存した trace を Jev で採点して書き戻す。「It gives you no reasoning back.」
- 他の awesome-jev の一覧と、YouTube の紹介動画 3 本
