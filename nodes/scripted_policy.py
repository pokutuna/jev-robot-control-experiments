"""手書きの policy ノード: 決めた順に命令を出し、sim から結果を受けたら次の命令を出す。

物体の位置を画像から推定しないので、「JSON 入力」条件として物体の姿勢 (scene) を受け取る。

入力:
    task            タスクの名前と指示文。手書きの方策は指示文を使わず、ログに出すだけ
    scene           sim の ground_truth。最初の 1 つから物体の姿勢を読む (JSON 入力条件)
    command_result  sim の命令の結果
出力:
    command         sim への命令。命令列を出し終えたら {"type": "end"} を送る

環境変数 POLICY_DELAY_MS (既定 0) を与えると、結果を受けてから次の命令を出すまでその時間だけ待つ。
推論に時間のかかる方策 (LLM など) を真似て、待つ間に sim がどう振る舞うかを確かめるために使う。
"""

import os
import time

from arrow_io import decode_json, encode_json
from dora import Node

from s1cap.scripted import ScriptedPolicy, bowl_on_plate_commands


def main() -> None:
    delay = float(os.environ.get("POLICY_DELAY_MS", "0")) / 1e3
    node = Node()
    policy: ScriptedPolicy | None = None

    def send(command: dict | None) -> None:
        if command is None:
            command = {"type": "end"}
        node.send_output("command", encode_json(command))

    for event in node:
        if event["type"] != "INPUT":
            continue
        if event["id"] == "task":
            node.log("info", f"task: {decode_json(event['value'])['instruction']}")
        elif event["id"] == "scene" and policy is None:
            scene = decode_json(event["value"])
            policy = ScriptedPolicy(bowl_on_plate_commands(scene["objects"]))
            send(policy.start())
        elif event["id"] == "command_result" and policy is not None:
            result = decode_json(event["value"])
            if result["status"] != "reached":
                node.log("info", f"command {result['id']} {result['status']}")
            time.sleep(delay)
            send(policy.on_result(result))
            if policy.done:
                break


if __name__ == "__main__":
    main()
