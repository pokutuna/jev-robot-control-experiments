<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# Jev に次の動作を選ばせる policy ノードを作る

ID: 06-jev-policy
Bunch: ../20261026-dora-nodes.md

## Goal

計画の C (Jev による直接操作) を dora の policy ノードとして動かす。Jev が毎回の判断で、ロボットの知覚 (画像と手先の状態) とタスクの指示文から次の動作を選び、sim に命令を送る。まず C1 (primitive 選択) で task 8 (put the bowl on the plate) を回し、成功・失敗と所要時間、失敗の仕方を記録する。

## Done When

- Jev を OpenRouter 経由で呼ぶ部分が `src/s1cap/` にあり、API キーは `.env` の `OPENROUTER_API_KEY` から読む。テキストだけ、画像付きの両方で呼べることと、1 回のレイテンシを確かめている
- Jev の policy ノードと dataflow があり、`dora run` で task 8 の 1 エピソードを最後まで回せる (成功しなくてよい)。入力の条件 (JSON、画像、画像 + JSON) を dataflow の設定で切り替えられる
- 判断ごとの入力、問い、答え、確率、レイテンシが記録に残り、失敗したときに何を選んだかを追える
- 使い方と分かったことを wiki と `docs/setup.md` に書く。ruff が通る

## Context

- 09 の成果: policy は `task`、`image_agentview`、`robot_state` を `queue_size: 1` で購読すると最新の観測を受けられる。小さな `move_delta` を続けるときは `tol` を 1 mm にする。差し替えの注意は `wiki/guides/dora-nodes.md` の「policy を差し替えるとき」
- Jev と OpenRouter: モデルは `typesafe/jev-1.14` (`~typesafe/jev-latest`)。`typesafe-sdk` は `TYPESAFE_BASE_URL` に `/v1/systemone` を付けて送るので、base URL を `https://openrouter.ai/api` にすると OpenRouter に向く。OpenRouter の案内 (https://openrouter.ai/docs/guides/community/jev) では、画像は `state` に `image_url` で入れ、画像付きのリクエストは長文脈モード (遅く、精度も下がる) になる。`TypeSafe-Danger-Zone-Images` ヘッダが OpenRouter で要るかは未確認
- 計画 (`docs/cap-libero-idea.md`): C1 は `hover / descend / grasp / lift / place / release` などから選ぶ。C2 は x, y, z を `+ / 0 / -`、指を `open / close / stay` から選ぶ。入力は JSON、画像、画像 + JSON の 3 通り。画像は一辺 280〜1568 px
- JSON 入力条件は、物体の名前と姿勢の真値を policy に渡す (04 の `scene` と同じく dataflow で明示的に配線する)
- API キーは `.env` (gitignore 済み) にだけ置き、ログや記録に出さない

## Result

Jev の policy ノード (`nodes/jev_policy.py`) を作り、2 つの方策を載せた。どちらも libero_90 60 (黒いボウルをトレイに入れる) で動かした。

- `POLICY: direction` (`src/s1cap/jev_policy.py`): Jev に x、y、z の向きと指を選ばせる。入力は JSON、画像、画像 + JSON を切り替えられる。どの条件でも成功しなかった。画像から 3 次元の向き、特に前後を選べない ([jev-c2-direction-policy.md](../../../wiki/findings/jev-c2-direction-policy.md))
- `POLICY: staged` (`src/s1cap/jev_staged.py`): Jev には画像の中の位置関係 (手首の画像に描いた × から見て目標はどちらか) と意図を問い、動きはコードで決める。LIBERO の判定で 6 回中 5 回成功した。ただし動きの大半は人が書いたルールで、Jev は知覚と条件の当てはめだけを担う ([jev-c2-staged-policy.md](../../../wiki/findings/jev-c2-staged-policy.md))

判断ごとの入力、問い、答え、確率、レイテンシは evaluator の `events.jsonl` に残る。Jev の呼び方は [jev-openrouter.md](../../../wiki/findings/jev-openrouter.md)。C1 (primitive 選択) と task 8 での実行は行わず、後続の Bunch (`../20261027-image-only-jev.md`) で実験を組み直す。

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-26 12:09 Jev を OpenRouter 経由で呼べることを確かめ、src/s1cap/jev.py (client、image_content、ask) にまとめた。キーは .env の OPENROUTER_API_KEY。typesafe-sdk を依存に足した
  - SDK の Image は multipart で送られ OpenRouter が 400 を返す。state に data URL の image_url を入れると通る (ヘッダ不要)。画像 2 枚 (agentview と手首) も 1 回で送れる
  - レイテンシはテキスト 470〜1374 ms、画像 1〜2 枚 (320 px) で 494〜787 ms。画像 1 枚で約 $0.00003
  - 詳細は wiki/findings/jev-openrouter.md
- 2026-10-26 12:18 ユーザの指示で C2 (移動方向の選択) から作ることにした。C1 は行き先の座標をどこから取るか (計画は真値、Approach は真値を購読しない) が未決
- 2026-10-26 12:18 src/s1cap/jev_policy.py (JevDirectionPolicy)、nodes/jev_policy.py、dataflows/jev_c2_image.yml と jev_c2_json.yml を作った。1 回の判断で x / y / z / gripper の Choice と done の Noul を 1 リクエストで聞く。判断の記録は decision 出力で evaluator の events.jsonl に入る
  - 指を「開く / 閉じる / そのまま」で聞くと毎回開閉を交互に選び手先が動かなかった。あるべき状態 (open / closed) で聞き、変える先の確率が 0.7 以上のときだけ変える
  - テーブルに押し付ける向きを選ぶと既定の 200 step 待つので、move_delta に timeout_steps 40 を付けた
  - MAX_STEPS 3000 で sim が「executing action in terminated episode」で落ちた。LIBERO の horizon (既定 1000) を超えたため。LiberoEnv に horizon を足し、sim ノードは MAX_STEPS を渡す
- 2026-10-26 12:18 30 判断ずつ回した。どちらも最後まで回り、成功しなかった
  - image (agentview と手首、320 px): 判断 588 ms。前と下を選び続け、ボウルが指の間に入った場面 (step 430 付近) でも closed は 0.09。その後は下に押し付けて timeout を繰り返した (30 回中 22 回)
  - json: 判断 359 ms。ほぼ毎回 +x と下を選び、指を閉じなかった (timeout 17 回)
- 2026-10-26 12:20 前の記録の「ボウルが指の間に入った」は誤り。フレームと真値を見直すと、手先は +x と -y を選び続けて斜めに進み、step 470 付近でボウルの縁にぶつかって押しのけた (ボウルが 3.4 cm ずれ、一時 1 cm 浮いた)。その後は皿の方へ進み、下に押し付けた
  - 手首カメラの画像は agentview に対して 180° 回っている (画像の上が +x、右が -y)。問いの選択肢は agentview の画像での向きしか書いていないので、手首の画像からは逆の手がかりになりうる
  - 手先の軌跡は記録していない (evaluator は robot_state を購読していない)
- 2026-10-26 12:24 evaluator が robot_state を robot_state.jsonl に記録するようにし、固定カメラだけ (CAMERAS=agentview、30 判断) で回した (outputs/runs/20261026-122143/)
  - 0〜99 step で +x と下に寄せ、ボウルとの差は dx +0.007 m、dy -0.011 m まで近づいた。その後も +x と -y を選び続けてボウルを通り過ぎた
  - 363〜417 step でボウルより約 10 cm 先で下降し、その後は皿の方へ +x に流れて押し付け、timeout が続いた (reached 12、timeout 18)。p(closed) は最大 0.49 で指を閉じなかった
  - 手首カメラを外しても x の行き過ぎと斜め -y が出るので、手首画像の向きの食い違いだけが原因ではない。Jev は位置が合っても stay を選ばない
- 2026-10-26 12:33 カメラ画像の説明に画像での軸の向き (agentview は下が +x、右が +y。手首は上が +x、右が -y) を足し、両カメラで回した (outputs/runs/20261026-122435/)。30 回すべて x=plus、z=minus を選び、確率もほぼ一定 (x=plus 0.55〜0.68、z=minus 0.9 前後)。timeout 25 回
  - y が -0.055 で止まったのは棚 (wooden_cabinet) の角への衝突 (動画で確認)。step 87 など初めの timeout は手先が宙にあり、原因は未確認
  ユーザの提案で、固定物の無いシーン libero_90 60 (LIVING_ROOM_SCENE4、左の黒いボウルをトレイへ) に替えて回した (outputs/runs/20261026-123150/)。挙動は変わらず、+x と下を選び続けてテーブルに当たり、そのまま +x に引きずった。指は step 0 で閉じた
  - 対象は akita_black_bowl_1 (y -0.127)。このシーンのテーブル面は z ≈ 0.41 で、state の「table surface is at z = 0.90」は誤り。シーンごとに変える必要がある
  - end_reason が policy_end ではなく policy_closed になった。policy が end を送ってすぐ終わると sim に end より先に INPUT_CLOSED が届く場合がある (未調査)
  - 回転の命令は C2 に無い (手先の向きは初期の下向きのまま)。ボウルは上から掴めるので、一旦このまま
- 2026-10-26 12:38 Jev が軸の向きを分かっているかを、dora を通さずに調べた (libero_90 60、手先をボウル (akita_black_bowl_1) の上 15 cm で ±8 cm の 9 か所に置く)
  - 今の問い (世界座標の x/y で選ばせる): 位置に関係なく x=plus (0.45〜0.52)、y はほぼ minus。正解の向きは x 3/9、y 3/9
  - 手首画像での位置を Choice で問う (上/中/下、左/中/右): 横はすべて left、縦は 5/9。こちらも画像によって答えがほとんど変わらない
  - 同じ画像で Box ("Where is the black bowl in this image?") を問うと、9 枚中 6〜7 枚でボウルの位置を正しく囲んだ。外れは、もう 1 つのボウルが画像の端に写っているときにそちらを囲んだもの。確信度は 0.1〜0.6 と低い
  - 指示文を付けて「掴むべきボウル」を Box で問うた回は、確信度 (0.08〜0.8) しか表示しておらず、box の値は確かめていない
  - Jev は画像のどこにボウルがあるかは Box で答えられるが、それを動く向きの選択に結びつけられない。向きを Choice で選ばせる C2 の形は、問いの書き方を変えても効きにくいと考える
- 2026-10-26 12:42 ユーザの指示で、Jev に示す座標系を、固定カメラから見た Y-up の右手系 (画面の右が +x、上が +y、カメラ側が +z) に変えた。policy が答えを世界座標に直す (JEV_TO_WORLD)。state の冒頭に座標系の説明を入れ、手先の位置もこの座標系で渡す。テーブルの高さの記述は消した (知覚から得られる値ではなく、Jev も使っていなかった)
  - 同じ 9 か所の調べ方で、左右 (Jev の x) は 4/9 正解。確率は位置に応じて少し動く (正解が -x の所で minus 0.68〜0.78、+x の所で plus 0.27〜0.40)
  - 奥行き (Jev の z) は 2/9。確率は plus 0.41〜0.53、minus 0.33〜0.51 で、位置にほとんど関係しない
- 2026-10-26 12:46 ユーザの依頼で、ここまでの試行を wiki/findings/jev-c2-direction-policy.md にまとめた (レポートに使う想定)。jev-openrouter.md の Box の項からリンクした
- 2026-10-26 12:48 ユーザの指示で、固定カメラをクオータービューに置ける設定を加えた (LiberoEnv の fixed_view、sim ノードの FIXED_VIEW=quarterview。task 出力に fixed_view を入れ、policy は画像の説明を置き方で変える)。Jev の座標系の説明は「ロボットの正面に立つ人から見た向き」に書き直した
  - 9 か所の調べ方で、agentview は左右 4/9、前後 2/9 (前回と同じ)、quarterview も左右 4/9、前後 2/9。quarterview の確率はむしろ一様に近い。当て推量 (3/9) と大差ない
  - wiki/findings/jev-c2-direction-policy.md に追記した
- 2026-10-26 12:57 正解率が低い理由を切り分けた (libero_90 60、ボウルを 1 つだけ残し、他の物体はテーブルの外に移す)
  - 知覚だけを問う: ボウルを動かした 9 枚ずつ (agentview ±15 cm、手首 ±6 cm) で、画像のどこにボウルがあるかを Choice (左/中/右、上/中/下) と Box で、各 5 回問った。指示文なし / 「on the left」入りの指示文 / 「left」なしの指示文の 3 条件
    - agentview の Choice は投影位置を 3 等分した正解に対し左右 40/45、上下 42〜45/45。手首は正解が全部「中」になる幅だったが、答えは投影位置 u=0.34→left、0.5→middle、0.65→right と位置の順に並んだ
    - 5 回の答えはほぼ同じ。「on the left」の有無は境目の数枚だけを left に寄せた
    - Box の中心の誤差は平均 0.02〜0.07 (画像の幅と高さに対する比)
  - 今の policy の問い (Y-up の座標系で移動の向きを選ぶ) を、ボウル 1 つ、指示文から「on the left」を外して各 3 回問った
    - agentview: 左右 6/9 (揃っている所は 3 か所とも stay。ずれている所は向きによらず minus)、前後 2/9
    - quarterview: 左右 4/9、前後 3/9
  - Choice は画像を見ており、答えは揺れない。外れるのは、ボウルと手先の位置関係を 3 次元の移動の向きの符号に直す段階と考える
- 2026-10-26 14:04 ユーザの指摘 (z が上のイメージ) で、Jev に示す座標系を Z-up の右手系 (見ている人の右が +x、奥が +y、上が +z、世界座標の (y, -x, z)) に変えた。JEV_TO_WORLD、座標系の説明、選択肢、画像ごとの説明を書き換えた
  - 9 か所 × 3 回 (多数決): agentview はボウル 1 つで左右 6/9・前後 4/9、2 つで 5/9・3/9。quarterview は 1 つで 5/9・3/9、2 つで 3/9・3/9
  - 前後はほぼすべて minus (ロボットの正面へ進む向き) を選び、位置に関係しない。世界座標で問ったときの +x への偏りと同じで、軸の名前は原因ではない
  - wiki/findings/jev-c2-direction-policy.md に「Z-up の右手系」を追記した
- 2026-10-26 14:13 ユーザの指摘で quarterview のカメラを寄せた (注視点を台座から (0.45, 0.03, 0.08) m、仰角 40°、距離 0.8 m)。前は 320 px の画像でボウルが約 30 px だった
  ユーザの指示で、Jev に示す軸を「正面から見て x が右、y が手前 (画像の下)、z が上」に変えた (左手系、世界座標の (y, x, z))。quarterview でも軸は変えず、画像では x が右下、y が左下に写る
  - 途中で、カメラごとに x と y を水平に回して画像の右と下に揃える形も作ったが、ユーザの指示で固定の軸に戻した。その形の前後は 3〜5/9
  - 9 か所 × 3 回 (多数決): agentview はボウル 1 つで左右 5/9・前後 3/9、2 つで 3/9・1/9。quarterview も同じ数
  - 前後は agentview ではおもに plus (手前)、quarterview ではおもに minus (奥) で、位置に関係しない
  - wiki/findings/jev-c2-direction-policy.md に追記した
- 2026-10-26 14:16 ユーザの提案で、手首カメラの画像を 180° 回して Jev に渡すようにした (policy の中で回す。sim の出力と録画はそのまま)。手首の画像でも x が右、y が下に写り、固定カメラと向きが揃う
  - 9 か所 × 3 回 (多数決): ボウル 1 つでは左右が agentview、quarterview とも 9/9 (27 回すべて正解)。前後は agentview 4/9 (ほぼ plus)、quarterview 5/9 (正解が minus の 3 か所と plus の 2 か所が当たり、stay の 3 か所は外れ)
  - ボウル 2 つ (指示文に「on the left」) では左右 agentview 6/9、quarterview 3/9、前後 3/9
  - 左右が当たらなかった主な原因は、手首の画像と固定カメラの画像で左右が逆に写っていたことと考える
  - 手先がボウルの真上にあるとき、手首の画像でボウルは中心より上 (回す前は v 0.61、回した後は 0.39) に写る。カメラが手先の中心からずれているためで、Jev が stay を選べない原因かもしれない (未確認)
- 2026-10-26 14:22 今の設定 (軸固定、手首画像 180° 回転、FIXED_VIEW=quarterview、libero_90 60、40 判断) でエピソードを回した (outputs/runs/20261026-141909/)。失敗、reached 14、timeout 26
  - 最初の判断で指を閉じた (closed 0.78)
  - 前半は x-、y-、z- (左、奥、下) を選び、手先はボウルを越えて奥へ 12 cm、右へ 7 cm 進み、テーブルの高さまで下りた
  - 判断 14 以降は x-、y+、z- を続けた。y+ (手前) はボウルへ戻る向きだが、下に押し付けたまま動かず timeout が続いた (step 600〜1976 で手先の x は 0.9 cm しか動いていない)
  - 判断を書き込み、手首を Jev に渡す向きに回した動画を作業用に作った
- 2026-10-26 14:29 画像に印を描く overlays (axes: 左上に軸の矢印、below: 手首の画像に手先の真下の赤 ×) を JevDirectionPolicy と OVERLAY 環境変数に追加し、quarterview の 9 か所 × 3 回で比べた
  - どの印でも前後は良くならない (ボウル 1 つ: なし 5/9, axes 2/9, below 5/9, 両方 3/9)。左右は 1 つで 7〜8/9 に少し下がる
  - below はボウル真上で「動かさない」を選ぶようになったが、他の位置でも stay が出て正解は増えず。axes は plus に偏る
  - 印の既定は無し (OVERLAY 空) のままにする。結果は wiki の findings に記録
- 2026-10-26 14:31 ここまでの記録を整えた: docs/setup.md に jev_c2 の dataflow、FIXED_VIEW と OVERLAY、robot_state.jsonl を書き、wiki/guides/dora-nodes.md の task に fixed_view を足した。wiki の findings のエピソード表に quarterview のエピソードを足した
- 2026-10-26 14:33 ユーザの依頼で awesome-jev (Jev の公開事例の一覧) を wiki/sources/awesome-jev.md に取り込んだ
  - ロボット制御の事例はどれもカメラ画像を渡さず、構造化した状態から primitive / 意図 / 向きを選ばせている。jev-libero は LIBERO で、シミュレータの分岐で候補の効果を先に試してから Jev に選ばせる
- 2026-10-26 14:39 ユーザの依頼で、awesome-jev に載ったロボット制御のリポジトリ 8 つのコードを読み、Jev への入力を wiki/research/jev-robot-control-inputs.md にまとめた
  - 画像をそのまま Jev に渡す事例は無い。目標物の位置はどれも Jev の外で求める (真値、GPT-6 Astra に画像の画素を選ばせて深度で戻す、手首画像の塊の検出)
  - 向きを選ばせる事例は、目標との差を軸ごとの符号付きの数値で渡し、問いの文に選び方まで書く。robo-harness は手首画像での塊と掴む点 (画像中心からずれた位置) の差と、前の一歩で塊が画像上でどう動いたかを渡す
- 2026-10-26 14:50 手首の画像で、ボウルが赤 × (手先の真下) のどちら側に見えるかを問うプローブを試した。左右と上下とも大きく当たるようになった
  - 9 か所 × 3 回の多数決。ボウル 1 つは位置の言い方で 9/9, 9/9。ボウル 2 つは向きの言い方 (× をどちらへ動かすか) で 8/9, 8/9
  - 移動の向きを選ばせたときの前後 (1〜5/9) より大きく良い。外れの原因は画像の中の位置を 3 次元の向きに直す段階と判断した
  - 次の段: OpenRoboto のように意図 (approach / descend / grasp / ...) を選ばせ、知覚の答えから動きを決める policy を組む
  - 結果は wiki/findings/jev-c2-direction-policy.md に記録
- 2026-10-26 14:57 2 段 policy の前提を確かめた: 開始姿勢の手首画像にボウル 2 つとトレイが写る。高さは問わず、当たるまで下ろす形で掴める
  - 手先の真下の点が写る縦位置は深さで 0.164〜0.399 と変わり、手首画像 1 枚では前後と高さを分けられない。横合わせは開始の高さで行い、× は縦 0.399 に描く
  - 3 cm ずつ下ろして timeout で止め、1.5 cm 上げて閉じる → 横ずれ 8 通り中 7 通りで持ち上がった
  - × を寄せる先は、縁 (左右 6/9、上下 3/9) より中心 (9/9、8/9) が当たる。中心に揃えて +y に 6 cm ずらす形にする (6 cm は固定値)
- 2026-10-26 15:16 2 段の policy (src/s1cap/jev_staged.py、dataflows/jev_c2_staged.yml) を作り、libero_90 60 init 0 で成功した (44 回の判断、50 秒)
  - 知覚 (手首の画像で × をボウル / トレイの中心へ動かす向き、固定カメラでトレイにボウルがあるか) → 意図 (Choice、条件の bool を文で渡す) → 動きはコード
  - 「掴んでいるか」は固定カメラの Noul では掴んでいる間も 0.02〜0.52 と揺れたので、指を閉じた後の開き (> 3 mm) で決めた
  - 掴んだボウルは手先から 6 cm 横にぶら下がるので、トレイに下ろす前にも 6 cm ずらす。ずらさないとトレイの縁に乗った
  - 「the bowl to pick up はトレイの中か」はトレイに置いた後も 0.04〜0.12。「トレイにボウルがあるか」なら 0.92〜0.97 で、finish を選べた
  - recorder が latency_ms の無い記録 (続けて送る命令) で落ちたので、無い記録を飛ばし、段ごとの dict は合計する
- 2026-10-26 15:28 2 段の policy を init 0〜4 と init 0 (2 回目) で回し、6 回中 5 回成功した
  - 成功した 4 回は 44〜55 回の判断。init 4 は上限 120 回の直前に成功、init 1 は失敗
  - 失敗と遅れの原因は運ぶ段: 持ち上げた位置から手首の画像にトレイが写らず、トレイへの向きの答えが入れ替わり続けた
  - 結果は wiki/findings/jev-c2-staged-policy.md に新しいページとして記録
- 2026-10-26 15:40 動画の手首の画像を Jev が見るのと同じ向きにし、赤い × を描くようにした
  - evaluator の環境変数 WRIST_CROSS_UV (jev_c2_staged.yml で 0.5,0.40)。描画は s1cap.jev_policy.wrist_view を staged policy と共用
  - 録画済みの 6 本には scripts/draw_cross.py で episode_cross.mp4 を作った
- 2026-10-26 15:45 2 段の policy の評価: 動きの大半は人が書いたルールで、Jev は知覚 (目標が × のどちら側か、トレイにボウルがあるか) と、条件の表を引くのと同じ意図の選択しかしていない
  - 5/6 の成功は「Jev が動きを決められる」ことを示していない。6 cm のずれと × の位置は libero_90 60 専用の値
  - 次の進め方は未定。候補は、ルールの部分 (掴む場所、下ろすのを止める所、掴めたか) を Jev の判断に置き換えて成功率の変化を見ること、または今の形を「Jev を知覚にだけ使う」比較例として扱い C3 と比べること
  - wiki/findings/jev-c2-staged-policy.md に「Jev が決めていることと、コードが決めていること」の節を足した
- 2026-10-26 15:49 6 本の記録を真値と照らし合わせ、2 つの問題を見つけた
  - init 0 (1 回目) と 2 では、放した後に手先を上げると、ボウルとトレイが手先に付いたまま 22 cm 持ち上がった (指は開いている)。当たるまで押し付けて下ろしたため、めり込んだと推測。LIBERO の判定は成功のままなので、置けたのは実際には 3/6
  - トレイへの向きの答え: トレイが写らない回では、遠ざかる向き (左上) も多かった。上下は、トレイの中心が 7〜10 cm 下にあっても「動かさない」と答えがち。ボウルの左右は全問正解
  - 照合のスクリプトは scratchpad の t06/check_dirs.py
- 2026-10-26 15:52 2 段の policy の成功数を 3/6 とする。トレイごと持ち上げて終わった 2 回は、LIBERO の判定が成功でも失敗に数える。wiki の表に「結果」の列を足した
- 2026-10-26 15:54 成功は LIBERO の判定で数える (ユーザの判断)。2 段の policy は 5/6 成功。トレイごと持ち上げた 2 回は wiki の表の「終わったときのトレイ」に残す
