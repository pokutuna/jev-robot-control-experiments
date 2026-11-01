import React from "react";
import { Img, staticFile } from "remotion";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS } from "../theme";

export const backgroundDuration = (fps: number) => Math.round(12 * fps);

const POINTS: { head: string; body: string }[] = [
  {
    head: "Jev",
    body: "状態と型付きの問いを受け取り、選択肢とその確率を返す Decision モデルです / 1.14 (preview) で画像を入力できるようになりました",
  },
  {
    head: "先行事例",
    body: "Jev でロボットアームを操作する事例の多くは、シミュレータから得た物体の座標をテキストで渡しています",
  },
  {
    head: "この課題",
    body: "対象物の座標を使わず、カメラ画像とロボットの状態 (グリッパーの高さ、開き幅) だけを Jev に渡します",
  },
];

export const Background: React.FC = () => (
  <SceneFrame>
    <SceneTitle>背景と方針</SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 200,
        left: 120,
        right: 120,
        display: "flex",
        gap: 64,
        alignItems: "center",
      }}
    >
      <div style={{ width: 640 }}>
        <Img
          src={staticFile("images/scene-quarterview.png")}
          style={{ width: 640, height: 640, borderRadius: 6 }}
        />
        <div
          style={{
            marginTop: 8,
            fontSize: 22,
            color: COLORS.sub,
            textAlign: "center",
          }}
        >
          LIBERO のシーン (固定カメラ)
        </div>
      </div>
      <div style={{ flex: 1 }}>
        {POINTS.map((p) => (
          <div key={p.head} style={{ marginBottom: 40 }}>
            <div style={{ fontSize: 26, color: COLORS.sub, fontWeight: 700 }}>
              {p.head}
            </div>
            <div style={{ fontSize: 34, lineHeight: 1.5 }}>{p.body}</div>
          </div>
        ))}
      </div>
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "LIBERO の物を掴んで別の場所に置くタスクを、シミュレータ上のロボットアームで解きます",
        },
      ]}
    />
  </SceneFrame>
);
