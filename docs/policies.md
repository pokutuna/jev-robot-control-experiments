# 実験ごとの方策と Jev への問い

実験 001〜011 で、それぞれ何を確かめようとし、どんな方策を作り、Jev に何を渡して何を問い、何が分かったかをまとめる。冒頭に全体像と実験のつながりを置き、その後に実験ごとの詳細を並べる。

## 全体像

### 問い

Franka Panda が LIBERO のシミュレータで、黒いボウルをトレイに入れる (libero_90 の task 60、指示文「pick up the black bowl on the left and put it in the tray」)。System 1 モデルの Jev に、カメラ画像とロボット自身の状態 (手先の位置、指の開き) を渡し、その答えでロボットを動かせるかを試す ([計画](cap-libero-idea.md))。

001 を除き、実行中の物体の位置の真値は方策に渡さず、画像から物体の位置を推定する処理も作らない。その代わり、既知のカメラの校正値と、人が決めたこのタスクの手順と掴み方を補う。答えたい問いは次の 2 つである。

1. Jev の画像への答えのうち、どの問い方の答えなら、ロボットの動きに使えるか
2. このタスクを終えるまでに、Jev の答えのほかに何を人 (または LLM) が補う必要があったか

各実験は、前の実験で残った課題に対して仮説を立て、方策を変えて確かめた。ただし、1 つの実験で変えたことが 1 つとは限らない (005 は多くを同時に変えた)。このため一連の実験は、要因を 1 つずつ確かめたものではなく、失敗を見て人が受け持つ範囲を広げていった探索の記録である。結論は「試した構成ではできた、できなかった」の形で書く。

### タスク

001〜011 は同じタスクを使う。task 60 (LIVING_ROOM_SCENE4) を選んだのは、棚などの固定の家具が無く、手先が家具に当たらないためである。場面にある物は、黒いボウル 2 つ、木のトレイ、ドレッシング、プリンだけである。

このタスクには、後の実験で失敗の原因になった性質が 2 つある。どちらもタスクを選んだ理由ではなく、場面に元からあるものである。

- ボウルの直径は、指を最大に開いた幅 (8 cm) より大きい。中心の上から指を閉じても掴めないので、縁を指で挟む。005〜009 は、ボウルの中心の上に合わせてから縁の方へ +y に 6 cm ずらして掴む。010 は、中心に合わせた後、手首の画像で −y の側の縁へ寄せる向きを問い、y だけを合わせて掴む。011 では LLM が同じ形の手順を書いた
- 掴むボウル (`akita_black_bowl_1`) から y に 18 cm 離れた所に、同じ形のボウル (`akita_black_bowl_2`) がある。指示文の「on the left」はこの 2 つを区別する。中心に合わせる所が 2〜5 cm ずれると、縁へずらした後に 2 つのボウルの間に下り、もう 1 つのボウルを掴むことがある (006 の init 9、007)

002〜004 では、Jev に掴み方 (縁を挟むこと) を伝えていない。このため、向きの答えが正しくても成功しにくい。この 3 つの実験で主に測ったのは、向きの答えである。

### 実験のつながり

| 実験 | 課題 | 仮説 | 変えたこと | 成功 | 結論 |
| --- | --- | --- | --- | --- | --- |
| 001 | 先行事例の問いの形は LIBERO でも働くか | 真値から作った目標、条件の真偽、条件と動きの対応を文で渡せば、Jev はそれを読んでタスクを終える | (基準) 真値を文で渡す。意図の呼び出しと動きの呼び出し | 10/10 | 働いた。Jev は文の符号と真偽を読んでいて、知覚は担っていない |
| 002 | 真値を画像に替えても、動く向きを決められるか | 画像と座標系の説明を渡せば、世界座標の軸ごとに近づく向きを答える | 真値、条件、意図の呼び出しを外し、画像 2 枚を渡す | 0/10 | 向きの答えはボウルの位置によらず偏った。静止画でも同じ (008) |
| 003 | 世界座標の軸ではなく、画像の中の向きなら答えられるか | 画像に手先の印を描き、画像の中の向きで問えば、近づく向きを答える | 印を描き、画像の中の向きで問う。世界座標への変換はコード | 0/10 | 手首の画像の向きは遠ざかる向きをほぼ答えないが、動かさない答えが多い。失敗は指を閉じる時機で起きた |
| 004 | 003 で指を閉じるのが早い | 先に段階を選ばせれば、指を閉じる時機が合う | 段階を選ぶ呼び出しを先に足す (条件は書かない) | 0/10 | 段階を先に選び、文で伝えるだけでは改善しなかった |
| 004-2 | ボウルは指の開きより大きく、縁を挟んで掴む。掴む縁そのものを行き先にして問えるか | 縁を行き先にしても、中心と同じ程度にずれに合った向きを答える | エピソードを回さず、静止画で行き先を縁にして問う (009 の後に行った) | (静止画) | 縁を行き先にすると x (前後) の向きをほとんど答えなかった。y は答えた。中心に合わせてから縁へ移る形にする |
| 005 | 下りる時機、指を閉じる時機、段階を、Jev は画像から決められなかった | それらを人が手順として書き、Jev には画像の中の位置関係だけを問えば、タスクを終える | 手順、掴み方、段階を選ぶ条件をコードに書く。ほかにも同時に変えた | 8/10 | 人が設計した手順と掴み方に Jev の答えを組み込むと、終えられた。段階の呼び出しは条件の表引きと同じ結果になった |
| 006 | 005 の運ぶ段で、手先がトレイから遠い所を行き来した | 運ぶ段の向きを固定カメラの画像の答えで決めれば、行き来が無くなる | 運ぶ段の向きの決め方だけ | 9/10 | 運ぶ段から抜けられないエピソードは 2 → 0。ボウルに合わせる精度と、掴んだ物を確かめないことが残った |
| 007 | 005、006 の手順は人が書いた | 関数とこのタスクの事実を渡せば、LLM は 006 と同程度に動く手順を書く | 手順を LLM に書かせる (Code-as-Policies) | 2/10 | LLM は人とほぼ同じ流れを書いた。ボウルに合わせる所が 006 より 2〜3 cm ずれた |
| 008 | 向きの答えのよしあしを、エピソードの中では他の判断と分けられない | 世界座標の軸の問いは静止画でも外れる。007 のずれは行き先の言い方による | エピソードを回さず、静止画で問い方を比べる | (静止画) | 世界座標の軸の問いは静止画でも外れた。行き先の言い方で答えが大きく変わった |
| 009 | 007 のずれの原因は、手順か、行き先の言い方か | 関数の中の言い方を 006 にそろえれば、同じプログラムで成功が増える | 007 のプログラムのまま、行き先の言い方だけ変える | 7/10 | 成功は 2/10 から 7/10 に増え、合わせる所のずれは 006 と同じ範囲に戻った。007 と 006 の差の大部分は行き先の言い方による |
| 010 | 006、009 の残った失敗は、中心に合わせた所の +y のずれに、決まった距離 (+y に 6 cm) を足して掴んだことによる | 中心に合わせた後、手首の画像で −y の縁へ寄せる左右の向きを問って y を合わせれば、ずれが直り、もう 1 つのボウルから離れた所を掴む | 006 の下ろす段の初めのずらしを、縁への問いに替える。掴む縁を −y にする | 10/10 | 下ろし始めた所の y は −3.4〜−5.1 cm にそろい、もう 1 つのボウルを掴む失敗は無くなった。トレイが持ち上がる終わり方も無かった |
| 011 | 007 の LLM には、008〜010 で分かったこと (言い方による答えの違い、縁への問いの性質、−y の縁の掴み方) を渡していなかった | これらを測った傾向と掴む縁の側としてプロンプトに書けば、LLM は 010 と同じ形の手順を書き、掴み方の失敗が無くなる | 007 のプロンプトの「Facts」と「Reliability」だけを替えて、プログラムを書かせ直す | 6/10 | LLM は 10 本とも、中心に合わせてから縁への問いで y を合わせ直す手順を書き、9/10 で掴むはずのボウルの縁を掴んだ。失敗は運ぶ段と置く段に移った |

次の実験へのつながりは次のとおりである。

- 001 → 002: 001 で Jev が読んでいたのは、真値から作った文だった。真値を外して画像を渡すと、まず動く向きを決められるかを確かめる
- 002 → 003: 世界座標の軸の向きは外れた。2026-10-26 の予備試行では、同じ手首の画像でも、画像の中の向きで問うと 7〜8/9 が当たった。そこで画像の中の向きで問い、世界座標への変換をコードが受け持つ
- 003 → 004: 向きよりも、指を閉じる時機と下り続けることで失敗した。001 と同じく、段階を先に選ばせる
- 004 → 005: 段階を選ばせても改善しなかった。Jev が決められなかったこと (下りる時機、指を閉じる時機、段階) は人が手順として書き、Jev には向きのように答えられたことだけを問う
- 004-2 → 005: 手首の画像で掴む縁を行き先にすると、x の向きを答えなかった。005 では中心に合わせ、そこから縁へ決まった距離 (+y に 6 cm) ずらす。この判断は 2026-10-26 の 9 か所の予備試行で行い、009 の後に 004-2 で数を増やして確かめた
- 005 → 006: 残った失敗は運ぶ段の行き来で、原因は向きを決める画像の切り替えだった。切り替えをやめる
- 006 → 007: 手順を人が書いた場合の到達点が得られた。同じ手順を LLM に書かせられるかを確かめる
- 007 → 008、009: 007 の失敗は、ボウルの上に合わせる所のずれで決まった。原因の候補 (行き先の言い方、1 回に問う数) を静止画で比べ (008)、言い方だけを変えて 007 のプログラムを回し直す (009)
- 006、009、004-2 → 010: 006 と 009 に残った失敗は、中心に合わせた所の +y のずれに、決まった距離 (+y に 6 cm) を足して掴んだことによる。004-2 では縁を行き先にすると y の向きは答えた。中心に合わせた後のずらしを、−y の縁への問いに替える
- 007、008、010、004-2 → 011: 007 の LLM に渡したのは 006 までの知識だった。008 の言い方の傾向、004-2 の縁への問いの性質、010 の −y の縁の掴み方をプロンプトに書き、LLM が手順に取り入れるかを確かめる

### 全体から言えること

- Jev の答えが動きに使えたのは、手首の画像に描いた × を行き先へ寄せる、画像の中の向きだった。静止画で 870 問のうち遠ざかる向きは 0 で、ずれが 2 cm 程度になると「動かさない」と答える (008)。固定カメラの画像では、大きなトレイへ寄せる向きは近づく向きだったが、ボウルへ寄せる向きは多くが「動かさない」だった
- 世界座標の軸の向きを問うと、静止画でも手先の位置に合った向きを答えなかった (002、008)。ただし、座標系の対応が原因か、入力の多さが原因かは分けていない
- 下りる時機、指を閉じる時機、段階は、試した問い方では画像から決められなかった (003、004)。005 以降は人が手順として書いた。005、006 の段階の呼び出しは、条件が 1 つでも成り立つ判断では 1088 回すべてで条件どおりの段階を選び、コードの表引きと同じ結果になった。005、006 で Jev の答えが動きを変えているのは、画像への問いだけである
- 行き先の言い方 (「the center of the bowl to pick up」と「the black bowl on the left」) で、同じ画像への向きの答えが大きく変わった (008、009)。行き先をボウルの縁にすると、x (前後) の向きをほとんど答えなかった (004-2)。中心で x と y を合わせた後に、縁への問いで y だけを合わせ直すと、10/10 で、もう 1 つのボウルから離れた所を掴んだ (010)。この掴む縁の側と測った傾向をプロンプトに書くと、LLM は 10 本ともこの形の手順を書いた (011)
- 005〜011 は、カメラの校正値、× の位置、印の基準平面の高さ、手順、このボウルの掴み方を人が補っている。別の物や別の配置に一般化する方策ではない ([計画の「タスクに固有の知識」](cap-libero-idea.md#タスクに固有の知識))
- 成功は LIBERO の判定 (終わったときにボウルがトレイの中にあるか) で数える。判定が成功でも、離した後にトレイが持ち上がったまま終わったものや、指を閉じたまま終えたものがある。「掴むはずのボウルを掴み、指を開いて離し、トレイを元の位置に残して終えた」エピソードを、成功と分けて数える

### 成功と、終わり方の問題

真値の記録と動画で確かめた。「きれいに終えた」は、掴むはずのボウルだけを持ち上げてトレイに入れ、終わったときに指が開いていて、トレイが元の高さにあるもの。

| 実験 | 成功 (LIBERO) | きれいに終えた | 判定は成功だが問題のあるもの | 失敗 |
| --- | --- | --- | --- | --- |
| 001 | 10/10 | 10 | (離した直後にトレイが 2〜12 cm 浮き、最後には戻った: 9) | |
| 002〜004 | 0/10 | 0 | | 30 (どれも判断の上限) |
| 005 | 8/10 | 6 (init 0、1、3、6、8、9) | トレイが約 22 cm 持ち上がったまま終わった: init 2、5 | 運ぶ段から抜けられない: init 4、7 |
| 006 | 9/10 | 5 (init 1、3、4、7、8) | トレイが約 22 cm 持ち上がったまま終わった: init 0、2、6。指を閉じたまま終えた: init 5 | もう 1 つのボウルを運んだ: init 9 |
| 007 | 2/10 | 1 (init 2) | 2 つのボウルを一緒に持ち上げた: init 0 | 8 (007 の節) |
| 009 | 7/10 | 4 (init 2、6、7、8) | トレイが 20〜22 cm 持ち上がったまま終わった: init 3、4、5 | 2 つのボウルを一緒に持ち上げた: init 0。もう 1 つのボウルを運んだ: init 1、9 |
| 010 | 10/10 | 10 | | |
| 011 | 6/10 | 5 (init 1、3、4、6、8) | トレイが 21.3 cm 持ち上がったまま終わった: init 0 | トレイでない所に置いた: init 5、7、9。掴み損ね、step の上限: init 2 |

トレイが持ち上がったエピソードでは、終わったときの指の開きは 7.0〜7.3 cm で、動画では開いた指がボウルの中に残ったまま手先が上がっている。原因 (指とボウルの接触か、ボウルとトレイの接触か) は確かめていない。007 では、もう 1 つのボウル (`akita_black_bowl_2`) が約 20 cm 持ち上がったエピソードが 7 つある。010 では、トレイが持ち上がったまま終わったエピソードは無かった。010 は掴む縁の側とトレイに下ろす前のずらしの向きを同時に変えたので、どちらによるかは分けていない。

## 方策の一覧

| 実験 | 方策 (`POLICY`) | 物体の位置 | Jev の呼び出し / 判断 | Jev が選ぶもの | 手順を決めるもの | 成功 |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | `text` (`JevTextPolicy`) | 真値を文で渡す | 2 回 (意図 1 問 → 動き 4 問) | 意図、x/y/z の向き、指 | 意図の説明文に書いた条件。条件の真偽は真値からコードが計算する | 10/10 |
| 002 | `direction` (`JevDirectionPolicy`) | 渡さない (画像 2 枚) | 1 回 (5 問) | x/y/z の向き、指、終わったか | Jev | 0/10 |
| 003 | `marked` (`JevMarkedPolicy`) | 渡さない (印を描いた画像 2 枚) | 1 回 (7 問) | 画像の中の向き、高さ、指、終わったか | Jev | 0/10 |
| 004 | `marked2` (`JevMarkedPolicy`、2 回呼ぶ) | 同上 | 2 回 (段階 1 問 → 動き 7 問) | 段階、画像の中の向き、高さ、指 | Jev (段階を画像から選ぶ) | 0/10 |
| 005 | `staged` (`JevStagedPolicy`、`CARRY_VIEW: wrist`) | 同上 | 3 回 (手首の画像 5 問と固定カメラの画像 3 問を並べて送る → 意図 1 問) | 画像の中の向き、写っているか、意図 | 人が書いた手順。意図の条件の真偽は、Jev の答えとロボットの状態からコードが計算する | 8/10 |
| 006 | `staged` (`CARRY_VIEW: fixed`) | 同上 | 3 回 | 同上 | 同上 | 9/10 |
| 007 | `cap` (`CaPPolicy`) | 同上 | 関数を呼ぶたびに 1 回 | 画像の中の向き (関数の戻り値) | LLM が書いたプログラム | 2/10 |
| 009 | `cap` (`FIXED_TARGETS: 1`) | 同上 | 同上 | 同上 | 007 と同じプログラム | 7/10 |
| 010 | `staged` (`CARRY_VIEW: fixed`、`RIM_TARGET: left`) | 渡さない (印を描いた画像 2 枚) | 006 と同じ。縁へ寄せる間は手首の画像に 1 問 | 006 と同じ。縁へ寄せる左右の向き | 006 と同じ | 10/10 |
| 011 | `cap` (`KNOWLEDGE: "010"`) | 渡さない (印を描いた画像 2 枚) | 関数を呼ぶたびに 1 回 | 画像の中の向き (関数の戻り値) | 010 までの知識で LLM が書いたプログラム | 6/10 |

004-2 と 008 はエピソードを回さない静止画の実験なので、方策は無い ([004-2 の README](../experiments/004-2-rim-probe/README.md)、[008 の README](../experiments/008-direction-probe/README.md))。

## 共通の条件と読み方

- 環境: quarterview の固定カメラと手首カメラ、320 px、20 Hz、`typesafe/jev-1.14` (OpenRouter 経由)。詳しくは [計画](cap-libero-idea.md)
- どの方策も、最初の判断で手先を下向きにそろえる `move_to` を送る (Jev は呼ばない。002 だけはこの命令を送らない)。判断の上限は 120 回 (`MAX_DECISIONS`。007、009 は最初の `move_to` の分を足して 121 回)
- 命令は sim ノードが実行する。`move_delta` (相対移動)、`move_to` (絶対位置)、`gripper` (指の開閉)、`hold` (何もしない) の 4 種で、結果は `reached` か `timeout` で返る
- 「判断」は、方策が sim に命令を 1 つ送るまでの処理を指す。1 回の判断で Jev を何回呼ぶかは方策による。1 回の呼び出しで、いくつかの問いをまとめて送ることがある
- 各実験の節は、課題と仮説、判断 1 回の流れ、Jev に渡す state と問い、記録の例、コードが決めていること、結果、結論と次への順に並べる
- 問いと state の文はコードから書き出したもので、`{...}` 以外は Jev に送る文そのままである。記録の例はどれも init 0 から取った
- 結果は各実験の README と `results.md` の要約で、数値の出典はそちらにある

---

## 001 物体の位置の真値を文で渡す

コード: `src/s1cap/jev_text.py`。[README](../experiments/001-text-baseline/README.md)

### 課題と仮説

- 課題: Jev をロボットの制御に使った先行事例 (OpenRoboto の incremental_policy) の問いの形は、LIBERO のこのタスクでも働くか。働くなら、以後の実験と比べる基準にする
- 仮説: 真値から作った目標、条件の真偽、条件と動きの対応 (どの意図ならどの軸をどちらへ動かすか) を文で渡せば、Jev はそれを読み取ってタスクを終える

先行事例と同じ実験の再現ではなく、問いの構造 (意図の呼び出しと動きの呼び出し、条件の真偽、目標との差) を LIBERO に移したものである。

### 判断 1 回の流れ

1 回の判断 (sim に命令を 1 つ送るまで) で、Jev を 2 回呼ぶ。1 回目で意図を 1 問、2 回目で x、y、z、指の 4 問をまとめて問う。

1. コードが真値から state (JSON) を作る。ボウルとトレイの位置、掴む手先の位置 (ボウルの中心から +y 6 cm、+z 3 cm)、離す手先の位置、差、位置が合っているかの真偽 (`alignment`) を入れる
2. 1 回目の呼び出し: 意図を 8 つから選ばせる (`intent`)
3. 2 回目の呼び出し: 1 回目で選んだ意図を state に足し、x、y、z、指の 4 問を 1 回の呼び出しで問う (`motor`)。軸の問いの文に、その軸の今の位置、目標、差を mm で書く
4. コードが命令にする。指の答えが今の指と違えば `gripper` (その判断では動かない)。そうでなければ、3 軸の符号に、目標までの距離で決めた歩幅を掛けて `move_delta`。意図が `finish` なら終わる

### state (例: 130 step の判断)

```json
{
 "task": "pick up the black bowl on the left and put it in the tray",
 "source": "LIBERO simulator ground-truth object positions, not camera vision",
 "units": "millimetres; robot base coordinates; +Z is up",
 "tcp_mm": [-94.6, -63.5, 662.9],
 "bowl_mm": [-95.3, -127.0, 435.2],
 "grasp_tcp_mm": [-95.3, -67.0, 465.2],
 "tray_center_mm": [9.5, 251.6, 437.4],
 "release_tcp_mm": [9.5, 311.6, 497.4],
 "bowl_grasp_minus_tcp_mm": [-0.7, -3.5, -197.7],
 "tray_release_minus_tcp_mm": [104.1, 375.1, -165.5],
 "alignment": {
  "grasp_x_error_mm": -0.7, "grasp_y_error_mm": -3.5, "grasp_z_error_mm": -197.7,
  "grasp_pose_reached": false, "over_tray": false,
  "at_travel_height": true, "at_release_height": false
 },
 "travel_tcp_z_mm": 615.2,
 "gripper_command": "open",
 "finger_width_mm": 80.0,
 "held": false,
 "bowl_in_tray": false,
 "previous_intent": "approach",
 "feedback": "move_delta reached"
}
```

2 回目の呼び出しでは、この JSON に `"selected_intent": "approach"` を足して渡す。

### 問い

**`intent`** (Choice)

```text
Choose the next immediate INTENT for this robot from the actual current geometry.
There is one bowl to pick up and one tray. A held bowl has a closed gripper command and a finger width above 3 mm; closed fingers alone do not imply held.
Use the option conditions. They define a feedback policy, not an obligation to stay in the previous intent.
The alignment fields are measured geometric checks, not previous commands. If grasp_pose_reached is false and the bowl is not held, APPROACH rather than GRASP. If the gripper is closed but the bowl is not held, APPROACH (it opens the gripper). If over_tray is false, do not LOWER or RELEASE.
When the bowl is already released in the tray, withdraw then finish; do not approach or regrasp it.
After a grasp, lift at the source, carry at travel height, then lower at the tray.
When held AND already aligned over the tray, lower/release takes priority over lifting back to travel height.
Relative errors are desired position MINUS current TCP, in millimetres. Conditions use absolute magnitudes.
No teleportation or complete pick/place skill exists. Each update only executes a small Cartesian increment.
```

- `approach`: Bowl not held and not already released in the tray. Open the gripper and align with the bowl grasp pose. Descend only after XY alignment.
- `grasp`: Bowl not held, gripper open, AND alignment.grasp_pose_reached is TRUE. Hold all XYZ and close the fingers. Do not close early above the bowl.
- `lift`: Bowl held, away from the tray, and at_travel_height is FALSE. Keep fingers closed and lift vertically to travel height before moving sideways.
- `carry`: Bowl held, at_travel_height is TRUE, and over_tray is FALSE. Carry horizontally above the release pose with fingers closed.
- `lower`: Bowl held AND alignment.over_tray is TRUE AND at_release_height is FALSE. Lower vertically with fingers closed. Never lower when away from the tray.
- `release`: Bowl held AND alignment.over_tray is TRUE AND alignment.at_release_height is TRUE. Open the fingers; hold XYZ. Never release away from the tray.
- `withdraw`: Bowl already released inside the tray, gripper open, at_travel_height is FALSE. Raise the open gripper vertically without regrasping.
- `finish`: Bowl released in the tray, gripper open, and at_travel_height is TRUE. The task is physically complete.

**`x`** (Choice。`y`、`z` も同じ形で、最後の 1 文がその軸の値になる)

```text
Choose the next small motor increment for the given intent and current geometry.
Axis labels refer to the robot base frame. positive increases that coordinate; negative decreases it; hold leaves it unchanged.
Read the signed target-minus-TCP errors. A positive error requires positive motion; a negative error requires negative motion. Within 5 mm of the target, hold that axis.
APPROACH: open fingers; correct X and Y using bowl_grasp_minus_tcp_mm. If either XY error exceeds 8 mm, HOLD Z; once aligned, correct Z toward grasp_tcp.
GRASP: HOLD all XYZ and CLOSE fingers.
LIFT: HOLD X/Y, keep fingers CLOSED, increase Z to travel_tcp_z_mm.
CARRY: keep fingers CLOSED, correct X/Y toward release_tcp_mm; maintain Z at travel_tcp_z_mm.
LOWER: keep fingers CLOSED, correct X/Y toward release_tcp_mm if necessary; decrease Z toward release_tcp_mm[2].
RELEASE: HOLD XYZ and OPEN fingers.
WITHDRAW: HOLD X/Y, keep fingers OPEN, raise Z to travel height.
FINISH: HOLD all XYZ and keep fingers OPEN.
The motion must follow the selected intent. Do not keep descending once the grasp or release height is reached.
CURRENT INTENT: APPROACH. This question controls ONLY X. Current X=-94.6 mm. Bowl grasp X=-95.3 mm. Bowl grasp minus current on this axis=-0.7 mm. Tray release X=9.5 mm. Tray release minus current on this axis=104.1 mm. Use ONLY this axis for this answer; do not answer for another axis.
```

- `negative`: Move X toward a SMALLER coordinate. Correct when the relevant target X is below current X beyond tolerance, and intent permits motion on this axis.
- `hold`: Do not move X. Correct if intent requires holding this axis or relevant target error is within tolerance.
- `positive`: Move X toward a LARGER coordinate. Correct when the relevant target X is above current X beyond tolerance, and intent permits motion on this axis.

**`gripper`** (Choice。文は上と同じ 13 行の後に `CURRENT INTENT: APPROACH. Decide only the gripper.`)

- `open`: Open the fingers. / `hold`: Keep the current finger command. / `close`: Close the fingers.

### 記録の例 (130 step の判断)

```json
{"obs_step": 116, "intent": "approach",
 "intent_probabilities": {"approach": 0.99, "grasp": 0.01, "lift": 0, "carry": 0, "lower": 0, "release": 0, "withdraw": 0, "finish": 0},
 "motor": {"x": "hold", "y": "negative", "z": "negative", "gripper": "open"},
 "command": {"id": 7, "type": "move_delta", "dpos": [0, -0.004, -0.02], "tol": 0.002},
 "latency_ms": {"intent": 406, "motor": 342}}
```

y は目標まで 3.5 mm なので歩幅 4 mm、z は 198 mm なので 20 mm になった。

### コードが決めていること

- 掴む手先の位置: ボウルの中心から (0, +6, +3) cm (`GRASP_OFFSET`)。離す手先の位置: トレイの中心から (0, +6, +6) cm (`RELEASE_OFFSET`)。運ぶ高さ: 掴む高さの 15 cm 上
- `alignment` の真偽: 位置の差が 8 mm 以内なら合っているとする (`ALIGN_TOL`)。`held`: 指を閉じた後の開きが 3 mm より大きい
- 歩幅: 意図の目標までの距離が 12 mm 未満なら 4 mm、25 mm 未満なら 8 mm、それ以上なら 20 mm。目標は意図で変わる (approach と grasp は掴む位置、carry、lower、release は離す位置、lift と withdraw は運ぶ高さ)
- 指の命令は、答えが今の指と違うときだけ送り、その判断では動かない

### 結果

成功 10/10。

- どのエピソードも、掴み直さずに 1 回の grasp で掴み、finish を選んで終えた
- 1 エピソードの判断は 59〜85 回 (平均 65)、Jev の呼び出しは平均 129 回、1339 step (67 秒)。1 回の判断のレイテンシは平均 684 ms
- 行き先から 2 cm 以上ずれている軸で、遠ざかる向きを選んだ判断は 1 回も無かった
- 掴む位置の付近や運ぶ途中で、x が ±4 mm で行き来することがあった。位置合わせの許容幅 (8 mm) の境目で差の符号が変わるため。成功には影響しなかった
- 9 エピソードで、ボウルを離した直後にトレイが 2〜12 cm 浮いた。最後には元の高さに戻った。原因は確かめていない

### 結論と次へ

- 真値から作った目標、条件の真偽、条件と動きの対応を与えると、Jev は 10 回とも完遂した。先行事例の問いの構造は、LIBERO のこのタスクでも働いた
- Jev がしている判断は、文に書かれた差の符号と真偽の読み取りに近く、知覚は担っていない
- 次へ: 真値を外して画像を渡すと、まず動く向きを決められるかを確かめる (002)

---

## 002 画像だけを渡し、世界座標の軸の向きを問う

コード: `src/s1cap/jev_policy.py`。[README](../experiments/002-image-direction/README.md)

### 課題と仮説

- 課題: 001 で Jev が読んでいたのは、真値から作った文だった。真値を外して画像を渡したとき、まず、ボウルへ向かう向きを決められるか
- 仮説: 画像と座標系の説明を渡せば、Jev は世界座標の軸ごとに、ボウルへ近づく向きを答えられる
- 測るもの: 横の向きの答え (主)。成功も数えるが、002 では掴み方 (ボウルの縁を挟むこと) を伝えていないので、向きが正しくても成功しにくい

Jev に画像だけを渡し、何をどこへ動かすかをすべて任せたときの出発点である。001 との違いは入力 (真値の代わりに画像) だけではない。意図を選ぶ呼び出しが無く、条件付きの手順も無く、歩幅は 2 cm に固定で、座標系の説明も変えた。このため、001 との差は、入力を画像に替えた効果だけを表すものではない。

### 判断 1 回の流れ

1. state に、座標系の説明、手先の位置と指の開き、直前 5 回の命令と結果、画像 2 枚 (固定カメラ、180° 回した手首カメラ) を入れる
2. 1 回の呼び出しで、x、y、z の向き、指、終わったかを問う
3. コードが命令にする。`done` が 0.8 以上なら終わる。指の答えが今の指と違い、その確率が 0.7 以上なら `gripper`。そうでなければ 3 軸の符号 × 2 cm を `move_delta` にする (Jev に示す座標系は x と y を入れ替えてあるので、世界座標に戻す)

### state (例: 6 回目の判断、obs_step 99)

```text
Task: pick up the black bowl on the left and put it in the tray
Coordinate system, as seen by a viewer standing in front of the robot and facing it: +x points to the viewer's right (the robot's left), -x to the viewer's left. +y points toward the viewer (away from the robot base), -y away from the viewer (toward the robot base). +z points up, away from the table, -z down toward the table. x and y are parallel to the table.
Robot state (meters, in the coordinate system above): gripper position [-0.075, -0.094, 0.603], finger opening 0.001 m (0.08 fully open, 0 closed).
Previous steps (oldest first): close fingers -> reached; move -2cm x -2cm y -2cm z -> reached; move -2cm x +2cm y -2cm z -> reached; move -2cm x -2cm y -2cm z -> reached; move -2cm x -2cm y -2cm z -> reached
---
Fixed camera, looking down diagonally at the table from the viewer's right (the robot's front left). In this image, +x points to the lower right, +y points to the lower left, and +z points up:
---
[固定カメラの画像]
---
Wrist camera, looking straight down (-z) from the gripper. In this image, +x points right and +y points down:
---
[手首カメラの画像 (180° 回したもの)]
```

`---` は state のリストの要素の区切りで、Jev には別の要素として送る。

### 問い

**`x`** (Choice。`y`、`z` も同じ形)

```text
Task: pick up the black bowl on the left and put it in the tray. The robot moves its gripper 2.0 cm per step. Which way should the gripper move along the x axis in the next step?
```

- `plus`: +x: move to the viewer's right (the robot's left)
- `stay`: do not move along x
- `minus`: -x: move to the viewer's left (the robot's right)

`y` の選択肢は「+y: move toward the viewer, away from the robot base」など、`z` は「+z: move up, away from the table」などになる。

**`gripper`** (Choice)

```text
Task: pick up the black bowl on the left and put it in the tray. Should the fingers be open or closed after the next step?
```

- `open`: the fingers should be open (not holding anything, or releasing what is held)
- `closed`: the fingers should be closed (grasping an object between them)

**`done`** (Noul)

```text
Task: pick up the black bowl on the left and put it in the tray. Is the task complete?
```

- `true`: the goal of the task is achieved and the robot has let go
- `false`: the goal of the task is not achieved yet

### 記録の例 (6 回目の判断)

```json
{"obs_step": 99,
 "choices": {"x": "minus", "y": "plus", "z": "plus", "gripper": "closed"},
 "probabilities": {"x": {"plus": 0.35, "stay": 0.28, "minus": 0.37}, "y": {"plus": 0.39, "stay": 0.24, "minus": 0.37}, "z": {"plus": 0.53, "stay": 0.07, "minus": 0.4}, "gripper": {"open": 0.31, "closed": 0.69}},
 "done": 0.05,
 "command": {"id": 6, "type": "move_delta", "dpos": [0.02, -0.02, 0.02], "tol": 0.001, "timeout_steps": 40},
 "latency_ms": 384}
```

最初の判断で指を閉じている (履歴の 1 つ目)。向きの確率は 3 つの選択肢でほぼ同じになっている。

### コードが決めていること

- 歩幅 2 cm、指を切り替える確率 0.7、終わる確率 0.8
- 指の命令は、答えが今の指と違うときだけ送り、その判断では動かない (001 と同じ)
- 画像ごとの軸の向きの説明 (`CAMERA_CAPTIONS`)。手首カメラの画像は 180° 回して渡す

### 結果

成功 0/10。どのエピソードも判断の上限 (120 回) まで続き、ボウルを持ち上げたエピソードは無い。手先と掴む点の最短距離は 3.1〜18.3 cm。

10 エピソードとも同じ形で失敗した。

1. 最初の判断 (init 8 だけは 2 回目) で指を閉じた
2. z は 1200 回中 1177 回 minus を選び、242〜790 step でテーブルの高さまで下りた
3. 指を閉じたままテーブルに押し付けて横に引きずった。命令の 83〜92% が timeout で終わった
4. 横の向きはボウルの位置によらず偏った。左右はボウルが左にある 1001 回のうち 803 回で右 (−y) を選び、終わったときの手先はボウルから右へ 6〜44 cm 離れていた

x と y の答えで、選んだ選択肢の確率は中央値 0.48 で、2400 回中 1413 回 (59%) が 0.5 未満だった。3 つの選択肢の確率が近い答えが多い (記録の例を参照)。

エピソードの中では、指を閉じてテーブルに押し付けたことが、向きの答えに影響した可能性がある。そこで後から、指を開いた手先を決まった位置に置いた静止画で、同じ state と問いを試した ([008](../experiments/008-direction-probe/README.md))。静止画でも、y は手先の位置によらず 83〜90% が −y、x は 69〜95% が −x を選び、ずれていない軸で `stay` と答えたことは無かった。

### 結論と次へ

- 試した入力と問いでは、Jev は世界座標の軸の向きを、手先とボウルの位置に合わせて答えなかった。エピソードの中でも静止画でも同じだった
- 原因が、画像の中の向きを世界座標の向きに直す所にあるのか、入力 (座標系の説明、画像 2 枚、5 問) の多さにあるのかは、分けていない
- 次へ: 2026-10-26 の予備試行では、同じ手首の画像で「× をボウルに重ねるには画像のどちらへ動かすか」と画像の中の向きで問うと、左右 7〜8/9、上下 5〜8/9 が当たった。003 では画像の中の向きで問い、世界座標の向きへの変換はコードが受け持つ

---

## 003 画像に印を描き、画像の中の向きを問う

コード: `src/s1cap/jev_marked.py`、`src/s1cap/marks.py`。[README](../experiments/003-marked-image/README.md)

### 課題と仮説

- 課題: 002 では、世界座標の軸の向きを問うと外れた。画像の中の向きで問えば答えられるか
- 仮説: 画像に手先の印を描き、「印を行き先へ重ねるには、画像のどちらへ動かすか」と画像の中の向きで問えば、Jev はボウルへ近づく向きを答える。世界座標の向きへの変換はコードが受け持つ
- 測るもの: 向きを決めた画像ごとの、横の向きの答え (主)。成功も数える

003 で変えたのは向きの問い方だけで、下りる時機、指を閉じる時機、何を行き先とするかは、002 と同じく Jev に任せたままにした。このため、仮説は向きについてのものだが、エピソードの成功は向き以外の判断でも決まる。実際、エピソードは向きより先に、指を閉じる時機で失敗した。向きの仮説は、エピソードの中で数えた向きの表と、後から行った静止画の実験 (008) で確かめる。

### 判断 1 回の流れ

1. 画像に印を描く
   - 手首カメラの画像: 180° 回し、手先の真下の点に赤い × を描く (画像の (0.5, 0.40) の位置。`CROSS_UV`)。この位置は開始の高さで測った値で、手先が下りると、× は手先の真下の点から少しずれる
   - 固定カメラの画像: 手先に赤い丸、手先の真下の、高さ 0.44 m の水平面上の点 (`TABLE_Z`) に黄色い点を描く。位置は手先の位置とカメラの射影行列から計算する。0.44 m はテーブルの面ではなく、ボウルとトレイの中心がある高さに置いた基準の平面である
2. 1 回の呼び出しで、行き先が手首の画像に写っているか、手首の画像で × を行き先へ寄せる向き (左右、上下)、固定カメラの画像で黄色い点を行き先へ寄せる向き (左右、上下)、高さ、指、終わったかを問う。行き先は「the place where the gripper should go next to do the task」で、何が行き先かは Jev が決める
3. コードが命令にする
   - `done` が 0.8 以上なら終わる
   - 指の答えが今の指と違い、確率が 0.7 以上なら `gripper`
   - 横の向き: 行き先が手首の画像に写っている (0.5 以上) なら手首の画像の答え、写っていなければ固定カメラの画像の答えを世界座標の向きにする
   - 高さ: down、stay、up をそのまま z の符号にする
   - 横と高さに 2 cm を掛けて `move_delta`。下げる命令は 40 step (2 秒) で届かなければ timeout で止める

### state (例: 6 回目の判断、obs_step 65)

```text
Task: pick up the black bowl on the left and put it in the tray
Robot state: fingers open (opening 8.0 cm; 8 cm fully open), gripper 16 cm above the table.
Previous steps (oldest first): move_to -> done; move down -> done; move down -> done; move down -> done; move down -> done
---
Fixed camera, looking down diagonally at the table. The red circle marks the gripper. The yellow dot marks the point on the table directly below the gripper (the yellow line connects them):
---
[固定カメラの画像 (印つき)]
---
Wrist camera, looking straight down from the gripper. The red cross marks the point below the gripper, at the height of objects on the table:
---
[手首カメラの画像 (180° 回し、× つき)]
```

「above the table」の高さは `手先の z − 0.44 m` で計算する。

### 問い

文の `{target}` は「the place where the gripper should go next to do the task」。

**`target_in_wrist`** (Noul)

```text
Task: pick up the black bowl on the left and put it in the tray. Is {target} visible in the wrist camera image?
```

**`wrist_h`** (Choice。`wrist_v` は horizontally を vertically、選択肢を `up`、`none`、`down` にしたもの)

```text
Task: pick up the black bowl on the left and put it in the tray. In the wrist camera image, to move the red cross onto {target}, which way should it move horizontally?
```

- `left`
- `none`: the red cross is already horizontally at {target}
- `right`

**`fixed_h`、`fixed_v`** (Choice): `wrist_h`、`wrist_v` の「wrist camera」を「fixed camera」に、「red cross」を「yellow dot」にしたもの。

**`height`** (Choice)

```text
Task: pick up the black bowl on the left and put it in the tray. Should the gripper move down toward the table, stay at its height, or move up in the next step?
```

- `down` / `stay` / `up`

**`gripper`** (Choice)

```text
Task: pick up the black bowl on the left and put it in the tray. Should the fingers be open or closed after the next step?
```

- `open`: no object is between the fingers yet, or the held object has reached where it should be put
- `closed`: the object to pick up is between the fingers, or it is held and has not reached where it should be put

**`done`** (Noul): 002 と同じ。

### 記録の例 (6 回目の判断)

```json
{"obs_step": 65,
 "choices": {"wrist_h": "none", "wrist_v": "none", "fixed_h": "left", "fixed_v": "none", "height": "down", "gripper": "closed"},
 "nouls": {"target_in_wrist": 0.72, "done": 0.04},
 "gripper_probabilities": {"open": 0.14, "closed": 0.86},
 "command": {"id": 6, "type": "gripper", "closed": true},
 "latency_ms": {"move": 414}}
```

テーブルの 16 cm 上で、指を閉じると答えている。

### コードが決めていること

- 印の位置: × の画像の位置 `CROSS_UV` (開始の高さで、掴む高さの点が写る位置を測った値) と、黄色い点を描く高さ `TABLE_Z` (このタスクのボウルとトレイの中心の高さ)。どちらもこのタスクの場面で決めた値である ([計画の「タスクに固有の知識」](cap-libero-idea.md#タスクに固有の知識))
- 画像の向きから世界座標の向きへの変換
  - 手首の画像: 固定の対応 (右が +y、下が +x)
  - 固定カメラの画像: 黄色い点の位置で射影のヤコビアンを取り、その逆で世界座標の水平の向きに直す。成分が 0.4 未満の軸は動かさない
- 横の向きにどちらの画像の答えを使うか (`target_in_wrist` が 0.5 以上なら手首)
- 歩幅 2 cm、下げる命令の timeout 40 step、指を切り替える確率 0.7、終わる確率 0.8

### 結果

成功 0/10。どのエピソードも判断の上限 (120 回) まで続き、ボウルを持ち上げたエピソードは無い。手先と掴む点の最短距離は 0.4〜6.3 cm で、002 より近づいた。

10 エピソードとも、次の形で失敗した。

1. 初めは手首の画像の向きで、ボウルの上へ寄った
2. 9 エピソードで、ボウルを指の間に入れる前に指を閉じた。閉じたのはテーブルから 7〜25 cm の高さで、手先はボウルの中心から水平に 5〜16 cm 離れていた (init 8 は最後まで閉じなかった)
3. 高さはほぼ毎回 down を選び (1190 回中 1137 回)、ボウルを押して 34〜81° 傾けたり、横へずらしたりした
4. ボウルが手首の画像から外れると、固定カメラの画像の向きで動いた。以後はテーブルに手先を押し付けたまま動き、命令の 58〜90% が timeout で終わった

横の向きを決めた画像で分けると、答えの当たり方がはっきり違った (行き先から 2 cm 以上ずれている軸の判断)。

| 向きを決めた画像 | 判断 (x と y の合計) | 近づく | 動かさない | 遠ざかる |
| --- | --- | --- | --- | --- |
| 手首カメラ | 292 | 88 (30%) | 192 (66%) | 12 (4%) |
| 固定カメラ | 1466 | 533 (36%) | 386 (26%) | 547 (37%) |

この数には、手先が下りた後の判断も入る。下りた後は × が手先の真下の点からずれるので、答えの誤りには、Jev の誤りと印の位置の誤りが混ざる。固定カメラの画像では、画像の中の向きを世界座標に直すときの誤差 (弱い成分の軸まで動かす) も入る。

### 結論と次へ

- 手首の画像に × を描いて画像の中の向きを問うと、遠ざかる向きはほとんど選ばなかった (4%)。ただし 3 分の 2 は「動かさない」で、ずれていても止まる答えが多い。この傾向は、開始の高さの静止画でも同じだった (008: 遠ざかる 0%、2 cm のずれでは半分以上が「動かさない」)
- 固定カメラの画像で黄色い点を行き先へ寄せる向きは、ボウルへ近づく向きと遠ざかる向きが同じくらいで、当て推量に近かった
- エピソードは、向きではなく、ボウルの上に着く前に指を閉じたことと、下り続けたことで失敗した
- 次へ: 指を閉じる時機を合わせるため、001 と同じく、先に段階を選ばせる (004)

---

## 004 段階を先に選ばせる (2 回の呼び出し)

コード: `src/s1cap/jev_marked.py` (`two_call=True`)。[README](../experiments/004-marked-two-call/README.md)

### 課題と仮説

- 課題: 003 では、1 回の呼び出しで行き先、向き、高さ、指を同時に問い、ボウルの上に着く前に指を閉じた
- 仮説: 001 と同じく呼び出しを 2 回に分け、先に段階 (近づく、下りる、掴むなど) を選ばせ、その段階を伝えてから動きを問えば、指を閉じる時機が合う
- 測るもの: 段階の選び方、指を閉じた高さと位置、成功

001 と 004 は、どちらも 1 回の判断で Jev を 2 回呼び、1 回目で段階 (001 では意図と呼ぶ) を、2 回目で動きを問う。違いは、段階の選び方と動きの問いに渡すものである。

| | 001 | 004 |
| --- | --- | --- |
| 段階の選択肢の説明 | 選ぶ条件を書く (例: grasp は「grasp_pose_reached が真なら」) | 段階の説明だけ (例: grasp は「close the fingers on the rim of the bowl」) |
| 条件の真偽 | 真値からコードが計算して state に入れる | 無い。段階は画像と手先の状態から選ぶ |
| 動きの問い | 軸ごとに、目標との差 [mm] と、意図ごとにどの軸をどちらへ動かすかを文に書く | 003 と同じ画像の中の向き、高さ、指。段階は「Current phase: ...」の 1 行で伝える |

行き先は 003 と同じボウルとトレイで、段階に応じてどちらを問うかを変える。

### 判断 1 回の流れ

003 の前に、段階を選ぶ呼び出しを 1 回足す。

1. state は 003 と同じ
2. 1 回目の呼び出し: 段階を 8 つから選ばせる。選択肢の説明に、選ぶ条件は書かない。`finish` なら終わる
3. 2 回目の呼び出し: state の最後に「Current phase: ...」の 1 行を足し、003 と同じ問いを問う。行き先 `{target}` は段階で変える
   - approach、descend: 「the bowl to pick up」
   - carry、lower: 「the tray」
   - それ以外 (grasp、lift、release): 003 と同じ「the place where the gripper should go next to do the task」。横の向きの答えは使わない (横に動かさない)
4. 命令の作り方は 003 と同じ

### 1 回目の問い

**`intent`** (Choice)

```text
Task: pick up the black bowl on the left and put it in the tray. The robot does the task in phases. Looking at the images and the robot state, which phase should the robot do next?
```

- `approach`: move the open gripper horizontally until it is right above the bowl to pick up
- `descend`: move the open gripper down to the rim of the bowl to pick up
- `grasp`: close the fingers on the rim of the bowl
- `lift`: raise the held bowl up from the table
- `carry`: move the held bowl horizontally until it is right above the tray
- `lower`: move the held bowl down into the tray
- `release`: open the fingers to put the bowl in the tray
- `finish`: the bowl is in the tray and the fingers are open; the task is done

2 回目の呼び出しで state に足す行 (approach の例):

```text
Current phase: approach (move the open gripper horizontally until it is right above the bowl to pick up).
```

### 記録の例 (6 回目の判断、obs_step 121)

state のロボットの行は「fingers open (opening 8.0 cm; 8 cm fully open), gripper 18 cm above the table.」。

```json
{"obs_step": 121, "intent": "grasp",
 "intent_probabilities": {"approach": 0.04, "descend": 0.35, "grasp": 0.61, "lift": 0, "carry": 0, "lower": 0, "release": 0, "finish": 0},
 "choices": {"wrist_h": "none", "wrist_v": "none", "fixed_h": "none", "fixed_v": "none", "height": "down", "gripper": "closed"},
 "nouls": {"target_in_wrist": 0.78, "done": 0.03},
 "gripper_probabilities": {"open": 0.04, "closed": 0.96},
 "command": {"id": 6, "type": "gripper", "closed": true},
 "latency_ms": {"intent": 525, "move": 454}}
```

テーブルの 18 cm 上で grasp を選び、指を閉じている。

### コードが決めていること

003 と同じ。加えて、段階ごとの行き先の言い方 (`INTENT_TARGETS`)。

### 結果

成功 0/10。どのエピソードも判断の上限 (120 回) まで続き、ボウルを持ち上げたエピソードは無い。手先と掴む点の最短距離は 0.5〜5.5 cm。

- 選んだ段階の合計は grasp 453、descend 412、approach 317、lift 7、carry 1。lower、release、finish は一度も選ばなかった
- 最初に指を閉じたのは grasp の段階で、手先はテーブルから 15〜22 cm の高さ、ボウルの中心から水平に 5〜13 cm 離れていた。どのエピソードも、ボウルの上に着く前に掴む段階に進んだ (init 2 は最後まで指を閉じなかった)
- 段階は 1〜数回ごとに approach、descend、grasp の間を行き来した。init 3、4、5 は grasp と descend を交互に選び続け、grasp が 90〜108 回になった
- 2 回目の問いの答えは段階とずれた。approach を選んだ 317 回のうち 260 回で高さを down と答え、descend を選んだ 412 回のうち 137 回で指を closed と答えた
- その後は 003 と同じく、閉じた指でボウルを押し、テーブルに手先を押し付けたまま動いた (命令の 69〜88% が timeout)

### 結論と次へ

- 段階を先に選ばせ、その段階を文で動きの問いへ伝えるだけでは、指を閉じる時機は改善しなかった
- 失敗には 2 つの形が混ざっている。手先がボウルの上に着く前に grasp を選んだこと (段階の選択) と、選んだ段階に合わない動きを答えたこと (approach で down、descend で closed) である。コードが段階で制限したのは横の動きだけで、高さと指は Jev の答えのままだった
- 001 の成功が、条件の真偽、目標との差、意図ごとの動きの指示のどれに支えられていたかは、この結果だけでは特定できない
- 次へ: 002〜004 で、Jev が画像から決められなかったのは、下りる時機、指を閉じる時機、段階だった。答えられたのは、手首の画像の中の向き (遠ざかる向きをほとんど選ばない) だった。005 では、決められなかったことを人が手順として書き、Jev には画像の中の位置関係だけを問う

---

## 004-2 静止画で、ボウルの縁を行き先にして問う

[004-2 README](../experiments/004-2-rim-probe/README.md)。エピソードを回さない静止画の実験で、方策は無い。009 の後に行ったが、005 の掴み方の根拠にあたるので、ここに置く。

### 課題と仮説

- 課題: ボウルは指の開き (8 cm) より大きいので、縁を指で挟んで掴む。掴む縁そのものを手首の画像で行き先にできれば、決まった距離のずらしが要らない
- 仮説: 縁を行き先にして問っても (「the left edge of the bowl to pick up」など)、中心を問うたとき (008 の `wrist_center`) と同じ程度に、ずれに合った向きを答える

### 方法

008 と同じ `scripts/probe_directions.py` で、掴む縁の点 (中心から y に ±6 cm) の周り 21 か所に手先を置き、手首の画像 (× つき) で問う。行き先は +y と −y の縁、言い方は「edge」と「rim」の 4 通り。init 0〜9、各 3 回、計 2520 問。

### 結果

| 行き先 | x: 近づく / 動かさない / 遠ざかる | y: 近づく / 動かさない / 遠ざかる |
| --- | --- | --- |
| 中心 (008 の `wrist_center`) | 58% / 42% / 0% | 81% / 19% / 0% |
| +y の縁 (edge / rim) | 2% / 97% / 0%、2% / 98% / 0% | 69% / 31% / 0%、57% / 41% / 2% |
| −y の縁 (edge / rim) | 0% / 100% / 0%、3% / 97% / 0% | 84% / 16% / 0%、95% / 5% / 0% |

### 結論と次へ

- 縁を行き先にすると、x に 4 cm ずれていても 97〜100% が「動かさない」と答えた。縁だけで合わせると x が合わない。005 以降の「中心に合わせてから縁へずらす」形は、この結果に合う
- y の向きは答えた。もう 1 つのボウルから離れる側 (−y) の縁では、中心と同じか、より多く近づく向きを答えた
- 次へ: 中心に合わせた後、決まった距離ずらす代わりに −y の縁を行き先にして y だけ合わせ直せば、中心に合わせたときの +y のずれ (006 の init 9、009 の init 0、9 の失敗の原因) が直る見込みがある。これを 010 で確かめた

---

## 005、006 画像への問いと、段階を選ぶ条件を分ける

コード: `src/s1cap/jev_staged.py`。[005 README](../experiments/005-staged-guide/README.md)、[006 README](../experiments/006-fixed-carry/README.md)

### 課題と仮説

005:

- 課題: 002〜004 で、Jev が画像から決められなかったのは、下りる時機、指を閉じる時機、段階だった。答えられたのは、手首の画像に描いた × を行き先へ寄せる向きだった
- 仮説: 物を運ぶ手順 (ボウルの上へ寄る、下ろす、掴む、持ち上げる、トレイの上へ運ぶ、下ろす、離す) と、このボウルの掴み方を人がコードに書き、Jev には画像の中の位置関係 (向き、写っているか) だけを問えば、Jev の答えでタスクを終えられる
- 測るもの: 成功、段の進み方、横の向き

005 は、人が設計した手順と掴み方に、Jev の画像への答えを組み込んだものである。004 から変えたことは 1 つではない。

- 段の並びと、各段の動き (縁へずらす量、3 cm ずつ下ろす、下ろす命令が届かなければ当たって止まったとみなす、閉じる前に 1.5 cm 上げる、運ぶ高さ) をコードで決める
- 段を選ぶ問いに、選ぶ条件を書き、その真偽を Jev の画像への答えとロボットの状態から計算して渡す
- 問いの行き先を「the center of the bowl to pick up」「the center of the tray」と明示する (003、004 は「次に手先が行くべき所」や「the bowl to pick up」)
- 手首の画像と固定カメラの画像を別の呼び出しで問う
- ボウルの上に合わせるのを開始の高さで行う。× の位置 (`CROSS_UV`) を測った高さなので、印が手先の真下の点と合う

成功がどの変更によるものかは分けていない。

段を Jev に選ばせたのは、001 と同じ「意図を選び、意図に応じて動く」形を保つためである。Jev が目的から段階を理解するかを試すためではない。条件の真偽をすべてコードが計算して渡すので、段の呼び出しは、条件の表を読んで当てはまる段を選ぶ問いになる。実際の選び方は「005 の結果」に書く。

縁の位置 (+y 6 cm)、閉じる前に上げる量 (1.5 cm)、ボウルを持っているとする指の開き (3 mm) は、このボウルを掴むために人が決めた値で、掴み方をコードに書き込んだものである ([計画の「タスクに固有の知識」](cap-libero-idea.md#タスクに固有の知識))。縁を直接行き先にせず中心に合わせるのは、縁を問うと x の向きを答えないためである (004-2)。

006:

- 課題: 005 では、運ぶ段の向きを決める画像を「トレイが手首の画像に写っているか」の答えで切り替えた。トレイから遠い所でこの答えが揺れ、2 エピソードが運ぶ段から抜けられなかった
- 仮説: 005 の記録では、固定カメラの画像でトレイへ寄せる向きは、左右 (y) の 131 回すべてが近づく向きだった。運ぶ段の向きを固定カメラの画像の答えで決めれば、行き来が無くなる
- 測るもの: 運ぶ段から抜けられないエピソードの数、運ぶ段の判断の回数、成功

005 と 006 の違いは、運ぶ段 (carry) の横の向きをどちらの画像の答えで決めるか (`CARRY_VIEW`) だけである。006 は、手順を人が書いたときの到達点として、007 と比べる基準になる。

### 判断 1 回の流れ

1. 知覚: 2 つの呼び出しを並べて送る
   - 手首の画像 (180° 回し、× つき): × をボウルの中心、トレイの中心へ寄せる向き (それぞれ左右と上下)、トレイが写っているか
   - 固定カメラの画像 (印つき): トレイの中にボウルがあるか、黄色い点をトレイの中心へ寄せる向き (左右と上下)
2. コードが、知覚の答えとロボットの状態から条件 (真偽など) を計算する
3. 意図: 条件を文にして渡し、意図を 9 つから選ばせる。選択肢の説明に、選ぶ条件を書く
4. コードが、意図ごとに決めた命令を送る。1 つの意図で命令が 2 つ以上あるときは、残りを次の判断で続けて送る (Jev は呼ばない。記録には `"queued": true` の判断として残る)

### 知覚の state

手首の画像への呼び出し:

```text
Task: pick up the black bowl on the left and put it in the tray
---
Wrist camera, looking straight down from the gripper. The red cross marks the point directly below the gripper:
---
[手首カメラの画像 (180° 回し、× つき)]
```

固定カメラの画像への呼び出し:

```text
Task: pick up the black bowl on the left and put it in the tray
---
Fixed camera, looking down diagonally at the table. The red circle marks the gripper. The yellow dot marks the point on the table directly below the gripper (the yellow line connects them):
---
[固定カメラの画像 (印つき)]
```

### 知覚の問い

手首の画像への呼び出し (5 問):

**`bowl_h`** (Choice。`bowl_v` は vertically と `up`、`none`、`down`)

```text
Task: pick up the black bowl on the left and put it in the tray. In the wrist camera image, to move the red cross onto the center of the bowl to pick up, which way should it move horizontally?
```

- `left`
- `none`: the red cross is already horizontally at the center of the bowl to pick up
- `right`

**`tray_h`、`tray_v`** (Choice): `bowl_h`、`bowl_v` の「the center of the bowl to pick up」を「the center of the tray」にしたもの。

**`tray_in_wrist`** (Noul)

```text
Task: pick up the black bowl on the left and put it in the tray. Is the tray visible in the wrist camera image?
```

固定カメラの画像への呼び出し (3 問):

**`bowl_in_tray`** (Noul)

```text
Task: pick up the black bowl on the left and put it in the tray. In the fixed camera image, is there any bowl in the tray?
```

**`tray_fixed_h`** (Choice。`tray_fixed_v` は vertically と `up`、`none`、`down`)

```text
Task: pick up the black bowl on the left and put it in the tray. In the fixed camera image, to move the yellow dot onto the center of the tray, which way should it move horizontally?
```

- `left`
- `none`: the yellow dot is already horizontally at the center of the tray
- `right`

### 条件の計算

| 条件 | 計算 |
| --- | --- |
| `fingers_closed` | 最後に送った指の命令 |
| `at_carry_height` | 手先の高さが開始の高さから 1 cm 以内 |
| `cross_on_bowl` | `bowl_h` と `bowl_v` がどちらも none |
| `cross_on_tray` | トレイが手首の画像に写っていて (`tray_in_wrist` が 0.5 以上)、`tray_h` と `tray_v` がどちらも none |
| `bowl_held` | 指を閉じていて、指の開きが 3 mm より大きい |
| `bowl_in_tray` | `bowl_in_tray` の答えが 0.5 以上 |
| `previous_intent` | 前の判断で選んだ意図 |
| `last_move` | 最後の移動の結果。下げる命令なら `down reached` か `down blocked`、それ以外は `move reached` など |

### 意図の state (例: 006 の 93 step の判断)

```text
Task: pick up the black bowl on the left and put it in the tray
Conditions:
- fingers_closed: false
- at_carry_height: true
- cross_on_bowl: false
- cross_on_tray: false
- bowl_held: false
- bowl_in_tray: false
- previous_intent: 'approach'
- last_move: 'move reached'
```

意図の呼び出しには画像を渡さない。

### 意図の問い

**`intent`** (Choice)

```text
Task: pick up the black bowl on the left and put it in the tray. The robot does the task in phases. Using the conditions in the state, which phase should the robot do next?
```

- `approach`: move the gripper horizontally toward the bowl. Choose when fingers_closed is false, bowl_held is false, at_carry_height is true, and cross_on_bowl is false
- `descend`: move the open gripper down onto the rim of the bowl. Choose when fingers_closed is false and bowl_held is false, and either at_carry_height and cross_on_bowl are both true, or previous_intent is descend and last_move is 'down reached'
- `grasp`: close the fingers on the rim of the bowl. Choose when fingers_closed is false, previous_intent is descend, and last_move is 'down blocked'. Do not close early
- `lift`: raise the gripper to the carrying height. Choose when fingers_closed is true and previous_intent is grasp
- `retry`: open the fingers to try again. Choose when fingers_closed is true, at_carry_height is true, and bowl_held is false (the grasp missed)
- `carry`: move the held bowl horizontally toward the tray. Choose when fingers_closed is true, bowl_held is true, at_carry_height is true, and cross_on_tray is false
- `lower`: move the held bowl down into the tray. Choose when fingers_closed is true and bowl_held is true, and either at_carry_height and cross_on_tray are both true, or previous_intent is lower and last_move is 'down reached'
- `release`: open the fingers and move up. Choose when fingers_closed is true, previous_intent is lower, and last_move is 'down blocked'
- `finish`: the task is done. Choose when fingers_closed is false and bowl_in_tray is true

### 意図ごとの命令

| 意図 | 命令 |
| --- | --- |
| approach | 手首の画像の `bowl_h`、`bowl_v` の向き × 2 cm。どちらも none なら `hold` |
| descend | 前の意図が descend でなければ、+y に 6 cm (縁へずらす) → 3 cm 下げる。続けて descend なら 3 cm 下げるだけ。下げる命令は 40 step で届かなければ timeout (当たって止まった) |
| grasp | 1.5 cm 上げる → 指を閉じる |
| lift | 開始の高さへ上げる |
| retry | 指を開く → 開始の高さへ上げる |
| carry | 下の「運ぶ段の向き」 |
| lower | descend と同じ (+y 6 cm → 3 cm 下げる) |
| release | 指を開く → 開始の高さへ上げる |
| finish | 終わる |

運ぶ段の向き:

- 005 (`CARRY_VIEW: wrist`): トレイが手首の画像に写っていれば (`tray_in_wrist` が 0.5 以上) 手首の画像の `tray_h`、`tray_v`、写っていなければ固定カメラの画像の `tray_fixed_h`、`tray_fixed_v` で決める
- 006 (`CARRY_VIEW: fixed`): 固定カメラの画像の答えで決める。固定カメラの答えがどちらも none になったら、手首の画像の答えで決める

運ぶ段を終えて lower へ移る条件 `cross_on_tray` は、005、006 とも手首の画像の答えで決める (トレイが写っていて、× をトレイの中心へ寄せる向きがどちらも none)。

### 記録の例 (006 の 93 step の判断)

```json
{"obs_step": 78,
 "perception": {"bowl_h": "left", "bowl_v": "none", "tray_h": "right", "tray_v": "down", "tray_in_wrist": 0.63, "tray_fixed_h": "right", "tray_fixed_v": "down", "bowl_in_tray": 0.01},
 "conditions": {"fingers_closed": false, "at_carry_height": true, "cross_on_bowl": false, "cross_on_tray": false, "bowl_held": false, "bowl_in_tray": false, "previous_intent": "approach", "last_move": "move reached"},
 "intent": "approach",
 "intent_probabilities": {"approach": 0.88, "descend": 0.1, "grasp": 0.02, "lift": 0, "retry": 0, "carry": 0, "lower": 0, "release": 0, "finish": 0},
 "command": {"id": 5, "type": "move_delta", "dpos": [0, -0.02, 0]},
 "latency_ms": {"perception": 411, "intent": 368}}
```

`bowl_h` が left なので、世界座標の −y に 2 cm 動かしている。

続けて送る命令の判断は、次の形で記録される。

```json
{"step": 167, "obs_step": 167, "intent": "descend", "queued": true}
```

### コードが決めていること

- 手順そのもの: 意図の並びと、意図を選ぶ条件の文、条件の計算、意図ごとの命令
- このボウルの掴み方: 縁は中心から +y に 6 cm (`RIM_OFFSET`)、閉じる前に 1.5 cm 上げる (`GRASP_RISE`)、指の開きが 3 mm より大きければ持っている (`HELD_WIDTH`)
- 問いの行き先の言い方: 「the center of the bowl to pick up」「the center of the tray」
- 印の位置 (`CROSS_UV`、`TABLE_Z`) と画像の向きの変換は 003 と同じ
- 歩幅 2 cm、下げる幅 3 cm、timeout 40 step、Noul の閾値 0.5、運ぶ高さの幅 1 cm

### 005 の結果

成功 8/10。10 エピソードともボウルを掴んで運ぶ高さまで持ち上げた。成功したエピソードは、どれも approach → descend → grasp → lift → carry → lower → release → finish の順に進んだ。エピソードごとの差は、ほぼ carry の回数 (14〜49 回) で決まった。

| init | 結果 | 判断 | 起きたこと |
| --- | --- | --- | --- |
| 0 | 成功 | 44 | |
| 1 | 成功 | 80 | 運ぶ段が長い (下の行き来が起きた) |
| 2 | 成功 | 46 | 離して上げるとき、トレイが手先と一緒に 22 cm 持ち上がった |
| 3 | 成功 | 45 | |
| 4 | 失敗 | 120 | 運ぶ段から抜けられず、判断の上限に達した。最後の数回でトレイに近づいていた |
| 5 | 成功 | 68 | 運ぶ段が長い。トレイが 21 cm 持ち上がった |
| 6 | 成功 | 45 | |
| 7 | 失敗 | 120 | 運ぶ段から抜けられず、トレイの中心から 40〜60 cm の所で行ったり来たりした |
| 8 | 成功 | 100 | 持ち上げる途中でボウルが指から外れ、retry で掴み直した。運ぶ段も長い |
| 9 | 成功 | 62 | 運ぶ段が長い |

運ぶ段の行き来の原因:

- 運ぶ段では「トレイが手首の画像に写っているか」の答えで、向きを決める画像を切り替える。トレイから遠い所で、この答えが 0.2〜0.7 の間で揺れた
- 0.5 以上のときは手首の画像の答え (おもに left で、トレイから遠ざかる向き)、0.5 未満のときは固定カメラの画像の答え (近づく向き) で動き、2 つが交互に出て手先がほぼ同じ所に留まった
- 運ぶ段で、固定カメラの画像の答えで動いた判断は、左右 (y) の 131 回すべてが近づく向きだった。手首の画像の答えで動いた判断は、左右の 47% が遠ざかる向きだった
- 手首の画像の答えで動いた 281 回のうち 260 回は、手先がトレイの中心から 12 cm 以上離れていた。トレイが写っていないのに「写っている」と答え、その画像の向きで外れたと考えられる

段の選び方 (`uv run scripts/intent_rules.py experiments/005-staged-guide`):

- 判断 681 回のうち 668 回は、Jev が選んだ段が、問いに書いた条件の成り立つ段だった。条件の成り立つ段が 2 つ以上あったのは 8 回
- 残りの 13 回は、どの段の条件も成り立たなかった。運ぶ段の途中で手先が運ぶ高さから 1 cm 以上外れたときで、Jev は lift (10 回) か carry (3 回) を選んだ
- 段の呼び出しは、条件の表を読んで当てはまる段を選ぶ問いとして働いた。段が順序どおりに進んだのは、条件の真偽をコードが計算して渡したからで、Jev が目的から段階を判断したことを示すものではない

条件の値にも、コードの決めごとが入っている。

- `bowl_held` は「指を閉じていて、指の開きが 3 mm より大きい」ことで、ボウルを持っているかを直接見てはいない。何かを挟んでいれば真になる
- `last_move` の「down blocked」は、下げる命令が 40 step で届かなかったことである。これを「当たって止まった」とみなして lower から release へ進めるのは、コードの解釈である

終わり方の問題: init 2、5 は判定は成功だが、指を開いて手先を上げたとき、トレイがボウルごと 21〜22 cm 持ち上がった。「きれいに終えた」(掴むはずのボウルだけを持ち上げてトレイに入れ、指が開いていて、トレイが元の高さにある) のは 6/10 (init 0、1、3、6、8、9)。

### 005 の結論と次へ

- 手順と掴み方をコードに書き、Jev に画像の中の位置関係だけを問う形で、8/10 になった。002〜004 から変えたことが多く、どの変更が効いたかは分けていない
- 失敗した 2 エピソードは、運ぶ段で、向きを決める画像を「トレイが手首の画像に写っているか」の答えで切り替えたことによる。この答えが揺れ、手首の画像と固定カメラの画像の答えが交互に出た
- 次へ (006): 運ぶ段の向きを、遠ざかる向きを答えなかった固定カメラの画像の答えで決める

### 006 の結果

運ぶ段から抜けられないエピソードは 005 の 2 から 0 になった。これが 006 で変えたことの結果である。成功は 9/10。10 エピソードとも finish まで進んで終わり、判断の上限に達したエピソードは無い。成功した 9 エピソードは、判断 40〜51 回、Jev の呼び出し平均 127 回、1078 step (54 秒)。

| init | 結果 | 判断 | 起きたこと |
| --- | --- | --- | --- |
| 0 | 成功 | 45 | トレイが 22 cm 持ち上がった |
| 1 | 成功 | 50 | |
| 2 | 成功 | 46 | トレイが 22 cm 持ち上がった |
| 3 | 成功 | 46 | |
| 4 | 成功 | 50 | 005 で失敗した init。運ぶ段 18 回でトレイの上に着いた |
| 5 | 成功 | 40 | lower の 1 回目の後、指を閉じたまま finish を選んだ。ボウルは下ろす途中で指から外れ、トレイに落ちていた。指は閉じたまま終わった |
| 6 | 成功 | 48 | トレイが 22 cm 持ち上がった |
| 7 | 成功 | 48 | 005 で失敗した init。運ぶ段 18 回でトレイの上に着いた |
| 8 | 成功 | 51 | |
| 9 | 失敗 | 46 | 隣のもう 1 つのボウルを掴んでトレイに入れた |

- 運ぶ段の判断は、どのエピソードでも 15〜18 回になった (005 は 14〜100 回)。12〜15 回を固定カメラの画像の答えで動き、残りの 2〜6 回を手首の画像の答えでトレイの上に合わせた
- 持ち上げた後に、トレイから遠ざかる向きへ動いた判断は無かった
- 段の選び方: 判断 421 回のうち 420 回は、条件の成り立つ段を選んだ。残りの 1 回は init 5 の finish で、どの段の条件も成り立たなかった (指は閉じていて、`bowl_held` は偽)
- init 9: 手首の画像の答えが「× がボウルの上にある」になったとき、手先はボウルの中心から +y の側 (もう 1 つのボウルの側) に 2.3 cm ずれていた。縁へ +y に 6 cm ずらすと、2 つのボウル (y に 18 cm 離れている) の間に下り、閉じた指がもう 1 つのボウルの縁に掛かった。指の開きは 3 mm より大きかったので、`bowl_held` が真になり、コードは先へ進めた。どちらのボウルを掴んだかは、どの条件からも分からない

「きれいに終えた」のは 5/10 (init 1、3、4、7、8)。init 0、2、6 はトレイが持ち上がり、init 5 は指を閉じたまま終わった。

### 006 の結論と次へ

- 運ぶ段の向きを固定カメラの画像の答えで決めると、運ぶ段から抜けられないことは無くなった (2 → 0)。成功は 8/10 から 9/10
- 残った失敗 (init 9) は、ボウルの中心に合わせる精度 (2 cm 程度) と、縁へ 6 cm ずらす掴み方の組み合わせで、もう 1 つのボウルを掴んだことによる。何を掴んだかを確かめる手順は無い
- トレイが持ち上がる終わり方は 005 から変わっていない。離した後の手先の上げ方を変えることは試していない
- 次へ (007): 006 は手順を人が書いたときの基準になる。同じ関数と掴み方を渡して、手順を LLM に書かせる

---

## 007 手順を LLM に書かせる (Code-as-Policies)

コード: `src/s1cap/cap.py`。LLM へのプロンプト: [programs/prompt.md](../experiments/007-cap/programs/prompt.md)。生成したプログラム: `experiments/007-cap/programs/init{N}.py`。[README](../experiments/007-cap/README.md)

### 課題と仮説

- 課題: 005、006 では、手順 (どの段で何を問い、答えでどう動くか) を人が書いた。手順は場面ごとに書き直す必要がある
- 仮説: 006 と同じ画像の問いを関数として LLM に渡し、手順をプログラムとして書かせても、006 (9/10) に近い成功になる。System 2 (LLM) が手順を組み、System 1 (Jev) が知覚を担う分担になる
- 測るもの: 成功、プログラムの流れ、ボウルの上に合わせる精度

LLM には、005、006 で人が決めたこのボウルの掴み方 (縁の位置、下ろし方、閉じる前に上げる量) を渡した。007 は、タスクの文と汎用の関数だけから手順を見つける実験ではない。タスクに固有の掴み方を与えたうえで、手順の組み立て (探す、合わせる、確かめる、やり直す) を LLM に任せる実験である。渡したものの内訳は「LLM へのプロンプト」に書く。

### 判断 1 回の流れ

1. 回す前に、LLM (`deepseek/deepseek-v4.1-flash-1017`) に init ごとにプログラムを書かせる。プロンプトは init によらず同じで、例のコードは渡さない
2. policy ノードは、プログラムを別のスレッドで `exec` する。プログラムが動きの関数 (`move_by`、`move_to`、`open_gripper`、`close_gripper`) を呼ぶと、命令を 1 つ sim に送り、結果と次の観測が届くまで待つ
3. 画像の関数 (`wrist_direction`、`fixed_direction`、`in_wrist_view`、`check`) は、呼ばれるたびに、その時点の画像で Jev を 1 回呼ぶ
4. 判断 1 回は「動きの関数を 1 回呼ぶまで」になる。その間に呼んだ画像の関数は、同じ判断の記録 (`api`) に入る

### LLM へのプロンプト

全文は [programs/prompt.md](../experiments/007-cap/programs/prompt.md)。構成は次のとおり。

- タスクの文
- 座標系と始めの姿勢
- 関数の説明 (ロボットの状態、動き、画像)
- このロボットと場面の事実 (「Facts」の節)
- 画像の答えの確かさ (「Reliability」の節)
- 上限 (画像の問い 360 回、動き 120 回)

「Facts」と「Reliability」に書いたことは、性質の違う 3 種類に分けられる。

| 種類 | 内容 | 出どころ |
| --- | --- | --- |
| ロボットとカメラの仕様、校正 | 座標系、始めの姿勢 (テーブルの約 24 cm 上)、指は y の向きに閉じる、手首の画像の × は始めの高さに合わせて描いてある、指の開きが 3 mm より小さければ掴み損ね | ロボットとカメラの設定から決まる。003 で × の位置を測った |
| このボウルを運ぶ人の手順 | 縁は中心から +y に 6 cm、3 cm ずつ止まるまで下ろす、閉じる前に 1.5 cm 上げる、横に合わせるのは始めの高さで行う、運ぶのも始めの高さ、縁を掴んでいる間はボウルの中心が手先から −y に 6 cm | 005 で人が決めた値と手順 |
| 測った傾向 | 答えは向きだけなので 2 cm ずつ動いて問い直す、手首の画像の向きはおおむね正しい、固定カメラの画像はトレイから 12 cm 以上離れていればトレイへの向きがおおむね正しいが、ボウルへの向きはよく外れる、トレイが写っているかの答えは写っていないのに高くなることがある | 003〜006 の記録 |

2 つ目の種類は、このタスクの解き方の一部を人が書いて渡したものである。プログラムが変えられるのは、それ以外の組み立て (どこから探すか、何回問うか、何で掴めたとするか、どうやり直すか) と、関数に渡す行き先の言い方になる。

### 画像の関数が Jev に送るもの

state は 005、006 と同じ (`wrist_direction` と `in_wrist_view` は手首の画像、`fixed_direction` は固定カメラの画像、`check` は 2 枚とも)。

**`wrist_direction(target)`**: 2 問 (Choice)。`{target}` はプログラムが渡した文字列

```text
Task: pick up the black bowl on the left and put it in the tray. In the wrist camera image, to move the red cross onto {target}, which way should it move horizontally?
```

- `left`
- `none`: the red cross is already horizontally at {target}
- `right`

もう 1 問は vertically と `up`、`none`、`down`。答えを世界座標の向きにして、`(sx, sy)` (それぞれ −1、0、1) を返す。

**`fixed_direction(target)`**: 「wrist camera」を「fixed camera」に、「red cross」を「yellow dot」にした 2 問。答えは 003 と同じ方法で世界座標の向きにする。

**`in_wrist_view(target)`** (Noul): `Task: {タスクの文}. Is {target} visible in the wrist camera image?`

**`check(question)`** (Noul): `Task: {タスクの文}. {question}`

005、006 との違い:

- 行き先の言い方はプログラムが決める (例: 「the black bowl on the left」「the center of the black bowl on the left」)
- 1 回の呼び出しで問うのは 1 つの行き先への 2 問だけ (005、006 は手首の画像への 1 回の呼び出しで、ボウルとトレイへの 4 問と、トレイが写っているかを問う)

### 生成されたプログラムの例 (init 9 の一部)

```python
def attempt_grasp():
    align_wrist("the black bowl on the left", max_iters=10, step=0.02, need_zero=2)
    align_wrist("the black bowl on the left", max_iters=6, step=0.01, need_zero=1)
    move_by(0, 0.06, 0)
    for _ in range(10):
        if not move_by(0, 0, -0.03):
            break
    move_by(0, 0, 0.015)
    close_gripper()
    return gripper_opening() > 0.003
```

`align_wrist` は、`wrist_direction` の答えが 2 回続けて (0, 0) になるまで 2 cm ずつ動かし、答えの向きが反転したら歩幅を半分にする。

### 記録の例 (6 回目の判断)

```json
{"obs_step": 70,
 "api": [
  {"fn": "move_by", "args": [0, -0.02, 0.0], "result": true},
  {"fn": "wrist_direction", "args": ["the center of the black bowl on the left"], "result": [0, -1], "answers": {"h": "left", "v": "none"}}
 ],
 "command": {"id": 6, "type": "move_delta", "dpos": [0, -0.02, 0]},
 "latency_ms": {"wrist_direction_6": 436}}
```

`api` には、前の動きの関数の結果と、その後に呼んだ画像の関数が入る。最後の `wrist_direction` の答え (0, −1) から、プログラムが `move_by(0, -0.02, 0)` を呼び、それがこの判断の命令になった。

### コードが決めていること

- 関数の中身: 問いの文、印、画像の向きの変換 (005、006 と同じ)、下げる命令の timeout 40 step
- 上限: 画像の問い 360 回、動き 120 回。超えたらプログラムを止める
- プログラムが使える名前: 上の関数、`print`、`math`、`np`、一部の組み込み関数。`import` は使えない
- 手順、歩幅、行き先の言い方、やり直しの条件は、プログラム (LLM) が決める

### 結果

成功 2/10。10 本のプログラムとも、例外や上限で止まらずに最後まで動いた。1 エピソードの Jev の呼び出しは 19〜33 回 (006 の成功したエピソードは平均 127 回)、step は 485〜891。

10 本とも流れは同じだった。手首の画像でボウルの上に合わせる → +y に 6 cm ずらす → 止まるまで下ろす → 1.5 cm 上げて閉じる → 指の開きで掴めたかを見て、外れていればやり直す → 始めの高さへ上げる → 固定カメラの画像でトレイへ寄せる → 手首の画像で合わせる → 下ろして開く。`check` を使ったプログラムは無い。

`akita_black_bowl_1` が掴むはずのボウル、`akita_black_bowl_2` は y に 18 cm 離れたもう 1 つのボウル。

| init | 結果 | Jev 呼び出し | 起きたこと |
| --- | --- | --- | --- |
| 0 | 成功 | 28 | 2 つのボウルを一緒に持ち上げ、`akita_black_bowl_1` がトレイに入った |
| 1 | 失敗 | 28 | 先にトレイの位置を確かめてからボウルを探した。もう 1 つのボウルの上に合わせて掴み、トレイから 5.5 cm の所に置いた |
| 2 | 成功 | 22 | 正しく縁を掴んだ。合わせたときのずれは 0.6 cm |
| 3 | 失敗 | 33 | 2 つのボウルを一緒に持ち上げたが、`akita_black_bowl_1` はトレイに入らなかった |
| 4 | 失敗 | 19 | 閉じたときボウルが 0.6 cm ほど浮いたが、上げる途中で指から外れた |
| 5 | 失敗 | 25 | もう 1 つのボウルを掴んで運んだ。Jev に渡した行き先は「the black bowl」 |
| 6 | 失敗 | 21 | もう 1 つのボウルを掴んで運んだ |
| 7 | 失敗 | 22 | 2 つのボウルを一緒に持ち上げたが、`akita_black_bowl_1` はトレイに入らなかった |
| 8 | 失敗 | 31 | 2 回とも掴み損ね、何も持たずに運ぶ段を進めた |
| 9 | 失敗 | 25 | もう 1 つのボウルを掴んで運んだ |

もう 1 つのボウルを掴んだ init 5、6、9 では、指を閉じた所は `akita_black_bowl_1` の中心から 11〜14 cm だった。init 8 が掴み損ねた所も 12〜13 cm 離れていた。

- 失敗の多くは、ボウルの上に合わせる所で決まった。手首の画像の答えが (0, 0) になったときのずれは +y の側に 2.6〜5.1 cm で (init 2 だけ 0.6 cm、init 1 は別のボウル)、006 (0.5〜3.0 cm) より 2〜3 cm 大きい。そこから縁へ +y に 6 cm ずらすので、指は 2 つのボウルの間に下りた
- 多くのエピソードで、合わせる所の最後の答えは (0, −1)、(0, −1)、(0, 0) と続いた。手先は +y の側からボウルへ近づき、届く前に (0, 0) で止まった。006 より早く止まる理由は、008、009 で行き先の言い方によると分かった (下の「結論と次へ」)
- 手順の側にも原因がある。init 8 は掴み損ねた後も運ぶ段へ進んだ。どのプログラムも、縁へずらした後の位置や、何を掴んだかを確かめなかった
- 006 と 007 では、手順を書いたのが人か LLM かに加え、行き先の言い方と 1 回の呼び出しで問う数も違う。007 だけでは、成功率の差のうち知覚の問い方によるものと手順によるものを分けられない
- 運ぶ段は、固定カメラの画像の答えでトレイへ寄せる 006 の方法が、LLM のプログラムでも働いた
- init 1 のプログラムは、先に固定カメラの画像でトレイの上へ動き、そこで `gripper_position()` を `tray_x`、`tray_y` に残し、後でその位置へ `move_to` で戻った。物体の位置を返す関数は無いが、手先が着いた位置を覚えて使うことは許している。画像から物体の位置を推定する処理ではなく、ロボット自身の状態の記録である
- 10 エピソードは、init ごとに別のプログラムで動いている。2/10 は、1 つの方策を 10 の init で評価した値ではない

### 結論と次へ

- LLM に手順を書かせると 2/10 で、006 の 9/10 より大きく下がった。失敗の多くは、ボウルの上に合わせる所が +y にずれ、縁へずらすと 2 つのボウルの間に下りたことによる
- 原因の候補は、手順 (LLM のプログラム)、行き先の言い方、1 回の呼び出しで問う数の 3 つで、007 だけでは分けられない
- 次へ (008): エピソードを回さずに、手先を決まった位置に置いた静止画で、問い方ごとの向きの答えを比べる
- 次へ (009): 008 の結果を受け、007 のプログラムを変えずに、関数の中で Jev に渡す行き先の言い方だけを 006 にそろえる

---

## 008 静止画で、問い方ごとの向きの答えを比べる

コード: `scripts/probe_directions.py`。[README](../experiments/008-direction-probe/README.md)

### 課題と仮説

- 課題: 002〜007 の向きの評価は、どれもエピソードの中で数えたものだった。エピソードでは下りる時機や手順も同時に変わるので、向きの答えのよしあしを分けられない。007 のずれの原因 (手順、行き先の言い方、問う数) も分けられなかった
- 仮説: 世界座標の軸の問い (002) は、静止画でもずれに合った向きを答えない。画像に × を描いた問い (005、006) は遠ざかる向きを答えない。007 のずれは行き先の言い方による
- 測るもの: 手先とボウルの中心の差 (真値) ごとの、近づく、動かさない、遠ざかる答えの数

### 方法

reset した後の始めの高さで、手先を掴むボウルの中心から x に −4、0、+4 cm、y に −6〜+6 cm (2 cm おき) ずらした 21 か所に置き、指を開いた静止画で問う。init 0〜9、問い方 7 通り、各 3 回。問い方は、002 の state と問い、002 の state に行き先を書いた問い、006 の手首の画像への 5 問、手首の画像への 2 問を行き先の言い方 3 通り (「the center of the bowl to pick up」「the black bowl on the left」「the center of the black bowl on the left」) で、固定カメラの画像への 2 問。真値は採点にだけ使う。エピソードは回さないので、成功は無い。

### 結果と結論

- 世界座標の軸の問いは、手先がどこにあっても、多くが −x、−y を選び、ずれていない軸で動かさないと答えたことは一度も無かった。行き先を問いの文に書いても変わらなかった。002 の向きの失敗は、静止画でも起きる
- 手首の画像に × を描いて「the center of the bowl to pick up」で問うと、遠ざかる向きは 870 問のうち 0 だった。ずれが 4 cm 以上なら 74〜90/90 で近づく向き、2 cm では半分以上が動かさないと答えた。2 cm 程度ずれた所で止まることになり、006 のずれ (0.5〜3.0 cm) と合う
- 1 回の呼び出しで問う数 (5 問と 2 問) は、答えをほとんど変えなかった
- 「the black bowl on the left」で問うと、+y に 4 cm ずれていても 83/90 が動かさないと答えた。007 で手先が +y の側 2.6〜5.1 cm で止まったことは、この答えで説明できる
- 次へ (009): エピソードで、行き先の言い方だけを変えて確かめる

## 009 007 のプログラムのまま、行き先の言い方だけを 006 にそろえる

コード: `src/s1cap/cap.py` (`FIXED_TARGETS=1`)。[README](../experiments/009-cap-fixed-targets/README.md)

### 課題と仮説

- 課題: 007 と 006 の差のうち、手順によるものと行き先の言い方によるものを、エピソードで分ける
- 仮説: 007 のずれが行き先の言い方によるなら、プログラムを変えずに言い方を 006 にそろえれば、合わせる所のずれは 006 と同じ程度になり、成功が増える
- 測るもの: 成功、合わせる所のずれ、失敗の内訳

### 方法

007 と同じ 10 本のプログラムを、同じ init state で動かす。プログラムは書き直さない。`wrist_direction`、`fixed_direction` が Jev に渡す行き先を、プログラムが渡した文字列に「bowl」が含まれれば「the center of the bowl to pick up」、「tray」が含まれれば「the center of the tray」に置き換える。問う数 (1 つの行き先に 2 問)、`in_wrist_view` と `check` の問いは 007 と同じ。

### 結果

成功 7/10 (init 2〜8)。「きれいに終えた」のは 4/10 (init 2、6、7、8)。

- 合わせる所のずれは −0.5〜+3.1 cm で、006 (+0.5〜+3.0 cm) と同じ範囲に入った。init 3、5〜9 は 006 と同じ値になった
- init 0: ずれ +3.1 cm で、2 つのボウルを一緒に持ち上げ、掴むはずのボウルはトレイに入らなかった
- init 1: 007 と同じく、プログラムの探し方でもう 1 つのボウルを掴んだ
- init 9: ずれ +2.3 cm で、006 の init 9 と同じく、もう 1 つのボウルを掴んで運んだ
- init 3、4、5: 判定は成功だが、トレイが 20〜22 cm 持ち上がった

### 結論と次へ

- 言い方だけを 006 にそろえると、2/10 から 7/10 になった。007 と 006 の差の大部分は、LLM が Jev に渡した行き先の言い方による。手順を LLM が書いたことによる失敗は、init 1 の 1 つだった
- LLM に手順を書かせるときは、Jev に渡す行き先の言い方もプログラムの一部になる。言い方を関数の側で決めるか、測った傾向としてプロンプトに書く必要がある
- 7/10 も、007 と同じく init ごとに別のプログラムで動いた値である
- 残った失敗 (init 0、9) は 006 の init 9 と同じで、合わせる精度と、縁へ 6 cm ずらす掴み方の組み合わせによる。決まった距離ずらす代わりに、縁への問いで y を合わせ直す手順を 010 で確かめる

---

## 010 中心に合わせた後、決まった距離ずらす代わりに、縁へ寄せる向きを問う

コード: `src/s1cap/jev_staged.py` (`rim_target="left"`)。[README](../experiments/010-rim-target/README.md)

### 課題と仮説

- 課題: 006、009 の残った失敗は、中心に合わせた所の +y のずれ (0.5〜3.1 cm) に、決まった距離 (+y に 6 cm) を足して掴み、2 つのボウルの間に下りたことによる
- 仮説: 中心に合わせて x と y をそろえた後、手首の画像で −y の縁 (「the left edge of the bowl to pick up」) へ寄せる左右の向きを問い、none と答えるまで y に動かせば、中心に合わせたときのずれは直り、もう 1 つのボウルから離れた所を掴む (004-2 の静止画で、−y の縁への y の答えに遠ざかる向きは無かった)
- 測るもの: 成功、下ろし始めた所と指を閉じた所、終わり方

### 方法

006 と同じ手順のガイド、問い、条件を使う。変えたのは次の 2 つである。

- 下ろす段 (descend) の初め: +y に 6 cm ずらす代わりに、縁への左右の問い (1 問) を送り、none と答えるまで y に 2 cm ずつ動かす (最大 5 歩)。寄せる間は段を選ぶ呼び出しをしない
- 掴む縁が −y の側になったので、トレイに下ろす前のずらしを −y に 6 cm にした (値は 006 と同じく人が決めたもの)

### 結果

成功 10/10。「きれいに終えた」のも 10/10。

- 中心に合わせ終えた所の y のずれは +0.3〜+3.1 cm (006 と同じ範囲)。縁への答えは、どのエピソードも left が 2〜4 回続いた後に none だった。ずれが大きいエピソードほど left が多く、下ろし始めた所の y は −3.4〜−5.1 cm にそろった
- 指を閉じた所は、もう 1 つのボウルから 22〜29 cm 離れていた。もう 1 つのボウルはどのエピソードでも動かなかった
- トレイが持ち上がったまま終わったエピソードは無かった (005、006、009 では 2〜3 ずつ)。理由は確かめていない
- 段を選ぶ判断 462 回は、すべて条件どおりだった

### 結論と次へ

- 決まった距離ずらす代わりに、Jev の答えで縁へ寄せると、中心に合わせたときのずれによらず掴む点が決まり、9/10 から 10/10 になった
- 縁へ寄せるのは y だけで、x は中心に合わせたときのずれ (−2.3〜+2.4 cm) が残る。縁を問うと x の向きを答えないためである (004-2)
- 掴む縁の側 (−y)、トレイに下ろす前のずらし (6 cm) は人が決めた。どちらの縁がもう 1 つのボウルから離れているかを画像から決めることは試していない。010 の掴み方を CaP の LLM に渡すことは 011 で試した

---

## 011 010 までに分かったことを CaP のプロンプトに入れ、LLM に手順を書かせ直す

コード: `src/s1cap/cap.py` (`KNOWLEDGE["010"]`)。LLM へのプロンプト: [programs/prompt.md](../experiments/011-cap-rim-target/programs/prompt.md)。[README](../experiments/011-cap-rim-target/README.md)

### 課題と仮説

- 課題: 007 の LLM に渡したのは 006 までの知識だった。その後、行き先の言い方で答えが大きく変わること (008)、縁を行き先にすると y は答えるが x はほぼ答えないこと (004-2)、中心に合わせた後に −y の縁への問いで y を合わせ直せば 10/10 になること (010) が分かった。009 は言い方を関数の側で固定したが、これらをプロンプトとして LLM に渡したときに手順に取り入れるかは確かめていない
- 仮説: 掴む縁の側 (−y) と、言い方と縁への問いについて測った傾向をプロンプトに書けば、LLM は「中心に合わせてから、縁への問いで y を合わせ直す」手順を書き、009 に残った掴み方の失敗が無くなる
- 測るもの: プログラムの流れ、指を閉じた所、成功と終わり方

### 方法

007 と同じ関数とコードを書く LLM で、プロンプトの「Facts」と「Reliability」の節だけを替えて、init ごとに 1 本書かせ直した。手順 (どの問いをどの順に使うか) は書いていない。関数の側で言い方は固定しない。

| | 007 | 011 |
| --- | --- | --- |
| 掴む縁 | 中心から +y に 6 cm の縁 | −y の側の縁 (手首の画像では左の縁)。中心からの距離は書かない |
| 掴んでいる間のボウルの中心 | 手先から −y に 6 cm | 手先から +y に約 6 cm |
| 足した傾向 | | 遠ざかる向きはほぼ答えない、2 cm 以内の軸は 0 が多い (008)。「the center of the bowl to pick up」と「the black bowl on the left」の答えの違い (008)。中心に合わせると 0〜3 cm ずれて止まる (006、009、010)。縁を行き先にすると y は答え、x はほぼ 0 (004-2) |

運ぶ段と置く段についての知識 (固定カメラの画像の傾向、トレイが写っているかの答え、運ぶ高さ) は 007 と同じである。

### 結果

成功 6/10。「きれいに終えた」のは 5/10。

- プログラム: 10 本とも、「the center of the bowl to pick up」で中心に合わせた後、「the left edge of the bowl to pick up」で y だけを合わせ直して下ろす。4 本 (init 1、3、4、9) は、先に −y に 5〜6 cm 動いてから縁への問いで合わせる
- 掴むまで: 9/10 で掴むはずのボウルの −y の縁を掴んだ。指を閉じた所の y は中心から −4.1〜−6.6 cm で、もう 1 つのボウルからは 23〜30 cm 離れていた。もう 1 つのボウルが持ち上がったエピソードは無かった。縁への問いの答えに +y は無かった
- 掴み損ねた init 2: 中心への問いでもう 1 つのボウルの上に止まり、縁への問いで −y に約 24 cm 動いたが、x が +5.8 cm ずれたままで掴み損ねた (プログラムは縁への問いの x の答えを使わない)
- 掴んだ後の失敗: init 5 は、トレイが写っていない所で `in_wrist_view` が 0.46 と答え、そこをトレイの位置として覚えて置いた。init 7 は、固定カメラの画像でトレイへ寄せる繰り返しを 15 回で打ち切り、トレイの手前で離した。init 9 は、トレイの中心から y に −14 cm の所で離し、ボウルが傾いてトレイの外と判定された

### 結論と次へ

- 010 までの知見を、手順ではなく、掴む縁の側と測った傾向としてプロンプトに書くと、LLM は 10 本とも 010 と同じ形の手順を書き、掴み方の失敗は無くなった
- 成功は 6/10 で、009 (7/10) より増えなかった。失敗は、知識を変えていない運ぶ段と置く段に移った。006、010 の運ぶ段の手順を測った傾向として書けば減る見込みがあるが、試していない
- 007、009 と同じく、init ごとに別のプログラムで動いた値である
