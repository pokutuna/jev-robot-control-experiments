"""エピソードの動画と、step ごとの真値の記録を保存する。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np

# LIBERO の制御周期 (1 step = 1/20 秒) に合わせ、動画も 20 fps で書く
FPS = 20


class EpisodeRecorder:
    """カメラ画像を横に並べた動画 (episode.mp4)、真値の記録 (ground_truth.jsonl)、
    ロボットの状態の記録 (robot_state.jsonl)、命令などの出来事の記録 (events.jsonl) を書く。
    sim の状態を受けたときは、step ごとの状態を sim_states.npz (steps、states) に書く。

    画像と真値は step 番号で対応付ける。同じ step の画像がカメラの数だけ揃ったら 1 フレームにする。
    """

    def __init__(self, out_dir: Path, cameras: tuple[str, ...]) -> None:
        self.out_dir = out_dir
        self.cameras = cameras
        out_dir.mkdir(parents=True, exist_ok=True)
        self._video = imageio.get_writer(
            out_dir / "episode.mp4", fps=FPS, macro_block_size=1
        )
        self._gt_log = (out_dir / "ground_truth.jsonl").open("w")
        self._robot_log = (out_dir / "robot_state.jsonl").open("w")
        self._event_log = (out_dir / "events.jsonl").open("w")
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._sim_states: dict[int, np.ndarray] = {}
        self._pending: dict[int, dict[str, np.ndarray]] = {}
        self.frames = 0
        self.steps = 0
        self.first_success_step: int | None = None
        self.last: dict[str, Any] | None = None

    def add_image(self, step: int, camera: str, image: np.ndarray) -> None:
        images = self._pending.setdefault(step, {})
        images[camera] = image
        if len(images) == len(self.cameras):
            del self._pending[step]
            self._video.append_data(
                np.concatenate([images[c] for c in self.cameras], axis=1)
            )
            self.frames += 1

    def add_ground_truth(self, step: int, ground_truth: dict[str, Any]) -> None:
        self._gt_log.write(json.dumps({"step": step, **ground_truth}) + "\n")
        self.steps += 1
        self.last = ground_truth
        if ground_truth["success"] and self.first_success_step is None:
            self.first_success_step = step

    def add_robot_state(self, step: int, robot_state: dict[str, Any]) -> None:
        """手先の姿勢、指の開き、腕の関節角 (Percept.to_dict) を記録する。"""
        self._robot_log.write(json.dumps({"step": step, **robot_state}) + "\n")

    def add_sim_state(self, step: int, state: np.ndarray) -> None:
        """MuJoCo の状態 (LiberoEnv.sim_state) を記録する。動画を後から描き直すのに使う。"""
        self._sim_states[step] = state.copy()

    def add_event(self, step: int, kind: str, data: dict[str, Any]) -> None:
        """命令、命令の結果、タスクの情報、エピソードの終わりなどを記録する。"""
        self._event_log.write(json.dumps({"step": step, "kind": kind, **data}) + "\n")
        self._event_log.flush()
        self._events.setdefault(kind, []).append(data)

    def close(self, **info: Any) -> dict[str, Any]:
        """ファイルを閉じ、エピソードのまとめ (summary.json) を書いて返す。"""
        self._video.close()
        self._gt_log.close()
        self._robot_log.close()
        self._event_log.close()
        if self._sim_states:
            steps = sorted(self._sim_states)
            np.savez_compressed(
                self.out_dir / "sim_states.npz",
                steps=np.array(steps),
                states=np.stack([self._sim_states[s] for s in steps]),
            )
        results = self._events.get("command_result", [])
        decisions = self._events.get("decision", [])
        summary = {
            **(self._events["task"][-1] if "task" in self._events else {}),
            **info,
            "steps": self.steps,
            "frames": self.frames,
            # 画像が揃わずに捨てた step の数。sim が途中で止まると最後の step が欠ける
            "dropped_frames": len(self._pending),
            "success": bool(self.last and self.last["success"]),
            "first_success_step": self.first_success_step,
            "end_reason": self._events.get("episode_end", [{}])[-1].get("reason"),
            "commands": len(results),
            "command_status": {
                s: sum(r["status"] == s for r in results)
                for s in sorted({r["status"] for r in results})
            },
        }
        if decisions:  # 方策が判断ごとの記録を出すとき
            summary["decisions"] = len(decisions)
            # Jev を呼ばずに出した命令 (続けて送る命令など) の記録には latency_ms が無い。
            # 何段かに分けて呼ぶ方策は、段ごとの値の合計を 1 回の判断のレイテンシとする
            latencies = [
                sum(lat.values()) if isinstance(lat, dict) else lat
                for d in decisions
                if (lat := d.get("latency_ms")) is not None
            ]
            if latencies:
                summary["mean_latency_ms"] = round(float(np.mean(latencies)))
            # Jev の呼び出しごとの記録 (s1cap.jev.call_record) を、名前を付けて calls に入れる
            calls = [c for d in decisions for c in d.get("calls", {}).values()]
            if calls:
                summary["jev_calls"] = len(calls)
                for key in ("input_tokens", "output_tokens"):
                    summary[key] = sum(c[key] or 0 for c in calls)
        (self.out_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
        )
        return summary
