<!-- bunch:task skill. The main session fills the {{INIT}} parts; the worker updates the rest while working. -->
# policy を差し替えて Jev や CaP を載せられるか確かめる

ID: 09-policy-swap-check
Bunch: ../20261026-dora-nodes.md

## Goal

04 の構成 (sim / policy / evaluator、命令の形式) のまま policy ノードを差し替えれば、Jev による直接操作 (C) と CaP (A、B) を載せられるかを、Jev や LLM を呼ばないモックの policy で確かめる。足りないものを見つけ、直せるものは直す。

## Done When

- Jev 型のモック: 真値を配線せず、画像とロボットの状態だけを購読し、1 回の判断に数百 ms かけて相対移動を選ぶ policy が dora で動く。判断に使った画像が、命令が届いた時点で何 step 古いかを測る。画像は Jev の下限 (一辺 280 px) 以上
- CaP 型のモック: 上から順に実行するコード (`move_to(...)`、`check(...)` で分岐とリトライ) を policy ノードの中で動かし、task 8 が成功する。知覚 API は最新の真値、`check` は最新の画像と真値を参照できる
- 足りなかったもの (配線、記録、エラー時の振る舞いなど) の一覧と、直したか残したかを Result に書く

## Context

- 04 の成果: 命令の形式と結果は `wiki/guides/dora-nodes.md`。手書き policy は `nodes/scripted_policy.py`、`dataflows/scripted_json.yml`。policy は命令を 1 つ送り、`command_result` を受けてから次を送る
- 計画 (`docs/cap-libero-idea.md`): C は Jev が毎回の判断で次の動作を選ぶ (C1 は primitive、C2 は 1〜2 cm の移動方向)。入力は JSON、画像、画像 + JSON の 3 通り。A と B は LLM が書いたコードを実行し、述語 `check(question) -> bool` を A は真値の幾何判定、B は Jev の画像判定で実装する。Jev のレイテンシは 70〜500 ms、画像は一辺 280〜1568 px
- 確かめたい懸念: policy の画像の入力の待ち行列 (既定 10) で古い画像を読まないか / CaP の逐次実行のコードと dora のイベントループの組み合わせ (dora の `Node` を別スレッドから使えるか) / 04 の policy は真値を最初の 1 つしか読まない / evaluator が命令と結果を記録していない / policy が例外で止まったときの sim と evaluator の振る舞い
- モックは確認用なのでスクラッチに置く。結果として repo のコードを直す場合は `src/s1cap/` と `nodes/` を直す

## Result

04 の構成のまま policy ノードを差し替えれば、Jev による直接操作 (C) も CaP (A、B) も載せられる。Jev や LLM を呼ばないモックの policy 2 つで、どちらも task 8 が成功した。差し替えるときの注意は [wiki/guides/dora-nodes.md](../../../wiki/guides/dora-nodes.md) の「policy を差し替えるとき」にある。

| 確かめたこと | 結果 |
| --- | --- |
| Jev 型: 画像 (320 px) と robot_state だけで判断、1 回 300 ms | 成功。`queue_size: 1` で最新の画像を受けられる。判断に使った画像は、命令が届く時点で 6 step 古い |
| CaP 型: 逐次実行のコード、`check` で分岐とリトライ | 成功 (step 384)。コードは別スレッドで実行し、dora の呼び出しはメインスレッドに限る。結果から次の命令まで 12 ms |
| policy が例外で止まったとき | 直す前は sim が MAX_STEPS まで進み続けた |

足りなかったものと対応:

| 足りなかったもの | 対応 |
| --- | --- |
| policy が止まっても sim が止まらない | 直した。sim は `command` の入力が閉じたら止まる (`policy_closed`) |
| policy に指示文が届かない | 直した。sim が最初に `task` を出す |
| evaluator が命令と結果を記録しない、終わった理由が分からない | 直した。`events.jsonl` に記録し、`summary.json` に `end_reason` と `command_status` を入れる |
| 小さな `move_delta` を続けると、毎回 `tol` 分だけ足りなくなる | 測って wiki に書いた (`tol` 1 mm を使う)。コードは変えない |
| CaP の知覚 API と `check` は最新の観測が要る | wiki に書いた。07 で `queue_size: 1` で購読し続ける |
| 非同期なので、推論時間の揺れで実行ごとに結果が少し変わる | wiki に書いた。05 で同じ条件を何度か回して揺れを見る |

後続タスク向け:

- 06: policy は `task`、`image_agentview`、`image_wrist`、`robot_state` を `queue_size: 1` で購読する。画像は Jev の下限 (一辺 280 px) 以上にするため、sim の `IMAGE_SIZE` を 320 などにする
- 07: スクラッチで試した Bridge (コードのスレッドと dora のメインスレッドをキューでつなぐ部分) は dora に依存しない形にできるので、`src/s1cap/` に置く

## Work Log

<!-- 以下の形式で追記していく
- {{yyyy-mm-dd hh:mm}} {{したこと・おきたこと}}
-->
- 2026-10-26 11:46 Jev 型のモック (画像と robot_state だけを queue_size 1 で購読、320 px、1 回の判断に 300 ms、2 cm の move_delta) で task 8 が成功した。判断に使った画像は、命令が届いた時点で 6 step 古かった
  - 既定の tol 5 mm では 2 cm の move_delta が 1.6 cm 程度しか進まず、続けて送ると足りない分が積もった
- 2026-10-26 11:46 CaP 型のモック (生成コードを別スレッドで exec し、dora の呼び出しはメインスレッドに限る Bridge でつなぐ) で task 8 が成功した (step 384)。check() の失敗からリトライの分岐も通った。結果から次の命令まで 12 ms
  - 最初はコードがボウルの姿勢をループの外で 1 回だけ読んで失敗した。ループの中で読み直すと成功した。知覚 API は最新の観測を返す必要がある
- 2026-10-26 11:46 policy を例外で止めると、sim は MAX_STEPS まで進み続けた。evaluator は正常に閉じ、dora run は終了コード 1 で traceback を出した
- 2026-10-26 11:46 足りなかったものを直した: sim は command の入力が閉じたら止まる / sim が task (指示文) と episode_end (終えた理由) を出す / evaluator が task、command、command_result、episode_end を events.jsonl に記録し、summary.json に end_reason と命令の status ごとの数を入れる
  - scripted_json.yml (policy_end、129 step、成功)、sim_eval.yml (max_steps)、crash のモック (policy_closed で 35 step で止まる) で確かめた
- 2026-10-26 11:46 move_delta の tol を 5 / 3 / 2 / 1 / 0.5 mm で測った。reached の時点の誤差はほぼ tol どおりで、1 mm なら step は 2〜5 増えるだけ。20 step 後にはどの tol でも 0.1〜0.3 mm に収まる。コードは変えず、小さな移動を続ける方策は tol 1 mm を使うと wiki に書いた
  - move_delta の基準を「今の手先」から「制御器の目標」に変える案もあるが、timeout や preempted の後の振る舞いが分かりにくくなるので、今は採らない
