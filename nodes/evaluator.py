"""evaluator ノード: sim の画像と真値を受け、動画と成功判定の記録を保存する。

入力:
    image_agentview、image_wrist  sim のカメラ画像
    ground_truth                  sim の真値
    robot_state                   sim のロボットの状態 (任意。つなぐと robot_state.jsonl に記録する)
    sim_state                     sim の MuJoCo の状態 (任意。つなぐと sim_states.npz に記録する)
    以下は任意。つなぐと events.jsonl に記録し、まとめに入れる
    task、episode_end             sim のタスクの情報と、エピソードを終えた理由
    command、command_result       policy の命令と、sim が返した結果
    decision                      policy の判断ごとの記録 (Jev の policy など)
保存先は環境変数 OUT_DIR (既定はリポジトリの outputs/runs/<日時>)。sim が止まると記録を閉じる。
環境変数 WRIST_CROSS_UV (例 "0.5,0.40") を与えると、手首の画像を Jev に渡すときと同じ向き (180° 回す) にし、
その位置 (画像の幅と高さに対する割合) に赤い × を描いて動画に書く。"height" にすると、× を手先の高さごとに
真下のテーブルの点が写る位置 (s1cap.marks.wrist_cross_uv) に描く。
環境変数 FIXED_MARK を 1 にすると、固定カメラの画像に 手先の印 (s1cap.marks)を描いて動画に書く。
印の位置は task の射影行列と robot_state の手先の位置から求めるので、task と robot_state をつなぐ。
"""

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from arrow_io import decode_image, decode_json
from dora import Node

from s1cap.jev_policy import wrist_view
from s1cap.marks import fixed_view, wrist_cross_uv
from s1cap.recorder import EpisodeRecorder

# dora はノードを dataflow の yaml の場所で起動するので、既定の保存先はこのファイルの位置から決める
RUNS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "runs"
CAMERA_OF_INPUT = {"image_agentview": "agentview", "image_wrist": "robot0_eye_in_hand"}


def main() -> None:
    out_dir = Path(
        os.environ.get("OUT_DIR") or RUNS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    ).resolve()
    recorder = EpisodeRecorder(out_dir, tuple(CAMERA_OF_INPUT.values()))
    cross = os.environ.get("WRIST_CROSS_UV")
    by_height = cross == "height"
    cross_uv = (
        tuple(float(v) for v in cross.split(",")) if cross and not by_height else None
    )
    fixed_mark = os.environ.get("FIXED_MARK") == "1"
    camera_matrix = None  # task で受ける
    eef = None  # 最後に受けた手先の位置
    node = Node()
    # sim の出力が閉じたら記録を閉じる。policy の命令は sim より後に閉じることがある
    open_inputs = {"image_agentview", "image_wrist", "ground_truth"}
    step = 0  # 最後に受けた sim の step。命令には step が無いので、これを付けて記録する

    for event in node:
        if event["type"] == "INPUT":
            eid = event["id"]
            step = event["metadata"].get("step", step)
            if eid == "ground_truth":
                recorder.add_ground_truth(step, decode_json(event["value"]))
            elif eid == "sim_state":
                recorder.add_sim_state(step, event["value"].to_numpy())
            elif eid == "robot_state":
                state = decode_json(event["value"])
                eef = np.asarray(state["eef"]["pos"])
                recorder.add_robot_state(step, state)
            elif eid in CAMERA_OF_INPUT:
                image = decode_image(event["value"], event["metadata"])
                if eid == "image_wrist" and by_height and eef is not None:
                    image = wrist_view(image, wrist_cross_uv(eef[2]))
                elif eid == "image_wrist" and cross_uv:
                    image = wrist_view(image, cross_uv)
                if (
                    eid == "image_agentview"
                    and fixed_mark
                    and camera_matrix is not None
                    and eef is not None
                ):
                    image = fixed_view(image, camera_matrix, eef)
                recorder.add_image(step, CAMERA_OF_INPUT[eid], image)
            else:
                value = decode_json(event["value"])
                if eid == "task" and "camera_matrix" in value:
                    camera_matrix = np.array(value["camera_matrix"])
                recorder.add_event(step, eid, value)
        elif event["type"] == "INPUT_CLOSED":
            open_inputs.discard(event["id"])
            if not open_inputs:
                break

    summary = recorder.close()
    node.log("info", f"{json.dumps(summary)} -> {out_dir}")


if __name__ == "__main__":
    main()
