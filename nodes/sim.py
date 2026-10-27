"""sim ノード: LIBERO を tick ごとに 1 step 進め、画像、ロボットの状態、真値を流す。

入力:
    tick            1 step 進める合図 (dora のタイマー)
    command         命令 (JSON)。形式は src/s1cap/driver.py。{"type": "end"} でエピソードを終える。
                    policy が止まって入力が閉じたときも終える
出力:
    task            タスクの名前と指示文、固定カメラの置き方と射影行列 (JSON)。最初に 1 回だけ送る。
                    射影行列 camera_matrix は世界座標 [m] を image_agentview の画素に移す 3x4 の行列
    image_agentview 斜め上の固定カメラの画像 (uint8、shape はメタデータ)。FIXED_VIEW で置き方を選ぶ
    image_wrist     手首カメラの画像
    robot_state     手先の姿勢、指の開き、腕の関節角 (JSON)
    ground_truth    物体と固定物の姿勢、固定物の関節値、成功判定 (JSON)
    command_result  命令の結果 (JSON)。reached / timeout / preempted / rejected
    episode_end     エピソードを終えた理由 (JSON)。policy_end / policy_closed / max_steps

どの出力もメタデータの step で同じ step のものを対応付けられる。設定は環境変数で渡す。
    SUITE (libero_goal)、TASK (8)、INIT (0)、SEED (0)、IMAGE_SIZE (256)、MAX_STEPS (200)、
    FIXED_VIEW (agentview。quarterview にすると斜め 45° 上から見る。src/s1cap/sim.py の FIXED_VIEWS)
"""

import os
import time

import numpy as np
from arrow_io import decode_json, encode_image, encode_json
from dora import Node

from s1cap.driver import CommandResult, RobotDriver
from s1cap.sim import LiberoEnv, Percept

OUTPUT_OF_CAMERA = {"agentview": "image_agentview", "robot0_eye_in_hand": "image_wrist"}


def publish(node: Node, driver: RobotDriver, percept: Percept) -> None:
    meta = {"step": driver.step_count}
    for camera, image in percept.images.items():
        value, shape = encode_image(image)
        node.send_output(OUTPUT_OF_CAMERA[camera], value, {**meta, **shape})
    node.send_output("robot_state", encode_json(percept.to_dict()), meta)
    node.send_output("ground_truth", encode_json(driver.ground_truth().to_dict()), meta)


def main() -> None:
    max_steps = int(os.environ.get("MAX_STEPS", "200"))
    env = LiberoEnv(
        os.environ.get("SUITE", "libero_goal"),
        int(os.environ.get("TASK", "8")),
        image_size=int(os.environ.get("IMAGE_SIZE", "256")),
        horizon=max_steps,
        fixed_view=os.environ.get("FIXED_VIEW", "agentview"),
    )
    driver = RobotDriver(env)
    # reset は数秒かかる。Node を作ると dataflow が始まり tick が届き出すので、先に済ませる
    percept = driver.reset(
        int(os.environ.get("INIT", "0")), seed=int(os.environ.get("SEED", "0"))
    )
    node = Node()
    node.log("info", f"{env.task_name}: {env.instruction}")

    # 結果を出してから次の命令が届くまでの step 数 (その間に sim が進んだ量) と時間 [ms]
    finished_at: tuple[int, float] | None = None
    gaps: list[tuple[int, float]] = []

    def send_results(results: list[CommandResult]) -> None:
        nonlocal finished_at
        for result in results:
            node.send_output(
                "command_result",
                encode_json(result.to_dict()),
                {"step": driver.step_count},
            )
            if result.status != "reached":
                node.log("info", f"command {result.to_dict()}")
            finished_at = (driver.step_count, time.perf_counter())

    task = {
        "suite": env.suite,
        "task_name": env.task_name,
        "instruction": env.instruction,
        "fixed_view": env.fixed_view,
        "camera_matrix": env.camera_matrix("agentview").tolist(),
    }
    node.send_output("task", encode_json(task), {"step": 0})
    publish(node, driver, percept)
    started = time.perf_counter()
    reason = "input_closed"
    for event in node:
        if event["type"] == "INPUT_CLOSED" and event["id"] == "command":
            reason = "policy_closed"  # policy が end を送らずに止まった (例外など)
            break
        if event["type"] != "INPUT":
            continue
        if event["id"] == "command":
            command = decode_json(event["value"])
            if finished_at is not None:
                step, t = finished_at
                gaps.append((driver.step_count - step, (time.perf_counter() - t) * 1e3))
                finished_at = None
            if command.get("type") == "end":
                reason = "policy_end"
                break
            send_results(driver.submit(command))
        elif event["id"] == "tick":
            percept, result = driver.step()
            publish(node, driver, percept)
            if result is not None:
                send_results([result])
            if driver.step_count >= max_steps:
                reason = "max_steps"
                break
    node.send_output(
        "episode_end",
        encode_json({"reason": reason, "step": driver.step_count}),
        {"step": driver.step_count},
    )
    elapsed = time.perf_counter() - started
    env.close()
    node.log(
        "info",
        f"ended by {reason}: {driver.step_count} steps in {elapsed:.1f} s"
        f" ({driver.step_count / elapsed:.1f} steps/s)",
    )
    if gaps:
        steps, ms = np.array(gaps).T
        node.log(
            "info",
            f"from a result to the next command ({len(gaps)} commands):"
            f" {steps.mean():.2f} steps (max {steps.max():.0f}),"
            f" {ms.mean():.1f} ms (max {ms.max():.1f})",
        )


if __name__ == "__main__":
    main()
