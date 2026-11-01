import React from "react";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS } from "../theme";

export const overviewDuration = (fps: number) => Math.round(8 * fps);

// 各実験の場面の見出しと同じ名前
const EXPERIMENTS = [
  "対象物の座標をテキストで渡す",
  "画像で世界座標の向きを問う",
  "画像内の向きで問う",
  "スケルトンを定義する",
  "スケルトンを別のタスクへ転用する",
  "LLM にスケルトンを書かせる",
];

export const Overview: React.FC = () => (
  <SceneFrame>
    <SceneTitle fontSize={80}>実験の全体像</SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 200,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
        {EXPERIMENTS.map((title, i) => (
          <div key={title} style={{ fontSize: 56, lineHeight: 1.3 }}>
            <span
              style={{
                display: "inline-block",
                width: 240,
                color: COLORS.accent1,
                fontWeight: 700,
              }}
            >
              実験 {i + 1}
            </span>
            {title}
          </div>
        ))}
      </div>
    </div>
    <TimedCaption
      items={[
        { at: 0, text: "このような実験と試行錯誤を順番に行いました" },
        {
          at: 3,
          text: "まずは既存のシミュレータの座標を参照する実装を参考に再現してみました",
        },
      ]}
    />
  </SceneFrame>
);
