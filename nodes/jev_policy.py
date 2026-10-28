"""Jev の policy ノード: Jev の答えから sim への命令を作って送る (計画の C2)。

POLICY で方策を選ぶ。
    direction  Jev に手先の移動方向と指の開閉を選ばせる (s1cap.jev_policy)
    staged     Jev に画像の中の位置関係を問い、その答えから意図を選ばせる (s1cap.jev_staged)。
               INPUT、CAMERAS、OVERLAY は使わず、固定カメラと手首カメラの画像を使う
    marked     画像に手先の印を描き、印を行き先へ寄せる画像の中の向きを 1 回の呼び出しで問う (s1cap.jev_marked)。
               INPUT、CAMERAS、OVERLAY は使わず、固定カメラと手首カメラの画像を使う
    marked2    marked の前に意図を選ばせ、意図の行き先を問いに入れる (2 回の呼び出し)
    cap        LLM が書いた手順のプログラム (PROGRAM) を動かし、プログラムの中で Jev に画像を問う (s1cap.cap)。
               INPUT、CAMERAS、OVERLAY、STEP_M は使わず、固定カメラと手首カメラの画像を使う
    text       物体の位置の真値を文で渡し、意図と軸ごとの向きを選ばせる (s1cap.jev_text)。
               INPUT、CAMERAS、OVERLAY、STEP_M は使わず、scene を配線する

命令を 1 つ送ったら結果を待ち、結果より後の step の観測が届いてから次の判断をする。

入力:
    task            sim のタスクの指示文と固定カメラの置き方。届くまで判断しない
    robot_state     手先の姿勢と指の開き
    image_agentview、image_wrist  カメラ画像 (image、image_json 条件)
    scene           sim の ground_truth (json、image_json 条件だけ配線する)
    command_result  sim の命令の結果
出力:
    command         sim への命令。Jev がタスクを終えたと答えたら {"type": "end"} を送る
    decision        判断ごとの記録 (選んだもの、確率、レイテンシ、使った観測の step)

設定は環境変数で渡す。
    POLICY (direction)      direction / staged / marked / marked2 / cap / text
    INPUT (image)           json / image / image_json
    OVERLAY ()              画像に描く印。axes (隅に軸の矢印)、below (手首の画像に手先の真下の十字) を , で並べる
    CAMERAS (agentview,wrist)  image 条件で Jev に渡すカメラ
    STEP_M (0.02)           1 歩の移動量 [m]
    MAX_DECISIONS (100)     判断の回数の上限。超えたら end を送る
    FIXED_MARK ()           staged で 1 にすると、固定カメラの画像に手先の印を描き、トレイが手首の画像に
                            写っていないときは固定カメラの画像の答えで運ぶ向きを決める
    CARRY_VIEW (wrist)      staged で FIXED_MARK=1 のときの、運ぶ段の向きの決め方 (wrist / fixed)。
                            fixed は、固定カメラの答えで運び、黄色い点がトレイの上に来たら手首の画像で合わせる
    RIM_TARGET ()           staged で left / right にすると、ボウルの中心に合わせた後、決まった距離ずらす代わりに
                            手首の画像でその側の縁へ y だけ寄せてから下ろす (s1cap.jev_staged)
    PROGRAM ()              cap で動かすプログラムのパス。scripts/run_experiment.py が PROGRAM_DIR と init state から書く
    JEV_BUDGET (360)        cap で Jev を呼ぶ回数の上限
    MAX_MOVES (120)         cap で移動と指の命令を送る回数の上限
    FIXED_TARGETS ()        cap で 1 にすると、向きの関数はプログラムが渡した行き先の言い方を使わず、
                            実験 006 の言い方で Jev に問う (s1cap.cap.CaPPolicy)
    JEV_MODEL (typesafe/jev-1.14)
"""

import os
from pathlib import Path

import numpy as np
from arrow_io import decode_image, decode_json, encode_json
from dora import Node

from s1cap import cap, jev
from s1cap.jev_marked import JevMarkedPolicy
from s1cap.jev_policy import JevDirectionPolicy, Observation
from s1cap.jev_staged import JevStagedPolicy
from s1cap.jev_text import JevTextPolicy

CAMERA_OF_INPUT = {"image_agentview": "agentview", "image_wrist": "robot0_eye_in_hand"}
INPUT_OF_NAME = {"agentview": "image_agentview", "wrist": "image_wrist"}


def main() -> None:
    policy_kind = os.environ.get("POLICY", "direction")
    input_mode = os.environ.get("INPUT", "image")
    camera_names = os.environ.get("CAMERAS", "agentview,wrist")
    if policy_kind in ("staged", "marked", "marked2", "cap"):
        input_mode, camera_names = "image", "agentview,wrist"
    if policy_kind == "text":
        input_mode = "json"
    cameras = [INPUT_OF_NAME[c] for c in camera_names.split(",")]
    step_m = float(os.environ.get("STEP_M", "0.02"))
    overlays = tuple(o for o in os.environ.get("OVERLAY", "").split(",") if o)
    max_decisions = int(os.environ.get("MAX_DECISIONS", "100"))
    client = jev.client(os.environ.get("JEV_MODEL", jev.DEFAULT_MODEL))

    # 判断に使う入力。条件に合わない入力は待たない
    needed = ["robot_state"]
    if input_mode in ("image", "image_json"):
        needed += cameras
    if input_mode in ("json", "image_json"):
        needed.append("scene")

    node = Node()
    policy: (
        JevDirectionPolicy
        | JevStagedPolicy
        | JevMarkedPolicy
        | JevTextPolicy
        | cap.CaPPolicy
        | None
    ) = None
    latest: dict[str, tuple[int, object]] = {}  # 入力 -> (step, 値)
    pending: dict | None = None  # 結果を待っている命令
    ready_after = 0  # この step 以降の観測で次の判断をする
    decisions = 0
    camera_of_input = dict(CAMERA_OF_INPUT)
    ended = False

    def end(reason: str) -> None:
        nonlocal ended
        node.log("info", f"end: {reason} after {decisions} decisions")
        node.send_output("command", encode_json({"type": "end"}))
        ended = True

    for event in node:
        if event["type"] == "INPUT_CLOSED" and event["id"] == "robot_state":
            break
        # end を送ったら、sim が end を受けて止まるまで待つ。先に止まると、sim は end を
        # 受け取る前に command の入力が閉じたとみなし、終わり方を policy_closed と記録する
        if event["type"] != "INPUT" or ended:
            continue
        eid, meta = event["id"], event["metadata"]
        if eid == "task":
            task = decode_json(event["value"])
            # 固定カメラの画像に添える説明は、カメラの置き方で変える
            camera_of_input["image_agentview"] = task.get("fixed_view", "agentview")
            node.log("info", f"task: {task['instruction']} ({policy_kind})")
            if policy_kind == "staged":
                policy = JevStagedPolicy(
                    client,
                    task["instruction"],
                    fixed_camera=camera_of_input["image_agentview"],
                    step_m=step_m,
                    camera_matrix=np.array(task["camera_matrix"])
                    if os.environ.get("FIXED_MARK") == "1"
                    else None,
                    carry_view=os.environ.get("CARRY_VIEW", "wrist"),
                    rim_target=os.environ.get("RIM_TARGET") or None,
                )
            elif policy_kind in ("marked", "marked2"):
                policy = JevMarkedPolicy(
                    client,
                    task["instruction"],
                    np.array(task["camera_matrix"]),
                    fixed_camera=camera_of_input["image_agentview"],
                    two_call=policy_kind == "marked2",
                    step_m=step_m,
                )
            elif policy_kind == "cap":
                program = os.environ["PROGRAM"]
                policy = cap.CaPPolicy(
                    client,
                    task["instruction"],
                    Path(program).read_text(),
                    np.array(task["camera_matrix"]),
                    program_name=program,
                    fixed_camera=camera_of_input["image_agentview"],
                    jev_budget=int(
                        os.environ.get("JEV_BUDGET", cap.DEFAULT_JEV_BUDGET)
                    ),
                    max_moves=int(os.environ.get("MAX_MOVES", cap.DEFAULT_MAX_MOVES)),
                    fixed_targets=os.environ.get("FIXED_TARGETS") == "1",
                )
            elif policy_kind == "text":
                policy = JevTextPolicy(client, task["instruction"])
            else:
                policy = JevDirectionPolicy(
                    client,
                    task["instruction"],
                    input_mode=input_mode,
                    overlays=overlays,
                    step_m=step_m,
                )
        elif eid == "command_result":
            result = decode_json(event["value"])
            if pending is not None and result["id"] == pending["id"]:
                assert policy is not None
                policy.on_result(result, pending)
                pending = None
                ready_after = meta["step"]
        elif eid in camera_of_input:
            latest[eid] = (meta["step"], decode_image(event["value"], meta))
        else:
            latest[eid] = (meta["step"], decode_json(event["value"]))

        if policy is None or pending is not None:
            continue
        if any(name not in latest or latest[name][0] < ready_after for name in needed):
            continue
        if decisions >= max_decisions:
            end("max_decisions")
            continue

        obs = Observation(
            step=min(latest[name][0] for name in needed),
            robot_state=latest["robot_state"][1],
            images={
                camera_of_input[name]: latest[name][1]
                for name in needed
                if name in camera_of_input
            },
            objects=latest["scene"][1]["objects"] if "scene" in latest else None,
        )
        decision = policy.decide(obs)
        decisions += 1
        node.send_output("decision", encode_json(decision.record))
        if decision.command is None:
            end(f"Jev answered done ({decision.record.get('done', 'finish')})")
            continue
        pending = decision.command
        node.send_output("command", encode_json(pending))


if __name__ == "__main__":
    main()
