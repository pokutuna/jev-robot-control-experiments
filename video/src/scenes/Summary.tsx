import React from "react";
import {
  Section,
  SceneFrame,
  SceneTitle,
  TimedCaption,
} from "../components/SceneText";
import { COLORS } from "../theme";

export const summaryDuration = (fps: number) => Math.round(15 * fps);

export const Summary: React.FC = () => (
  <SceneFrame>
    <SceneTitle fontSize={80}>まとめ</SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 200,
        left: 80,
        right: 80,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 56 }}>
        <Section
          head="Jev が担えた判断"
          fontSize={44}
          items={[
            "印を行き先へ寄せる画像内の向き",
            "指示文に合う掴む対象の選択",
            "選択肢を絞った後の、閉じるか開くか",
          ]}
        />
        <Section
          head="Jev の回答だけでは難しかったこと"
          fontSize={44}
          items={[
            "下ろすのを止めて閉じるタイミング",
            "小さい置き先、画角から外れた置き先への位置合わせ",
          ]}
        />
      </div>
    </div>
    <div
      style={{
        position: "absolute",
        right: 32,
        bottom: 8,
        fontSize: 20,
        color: COLORS.muted,
      }}
    >
      ♫ 「龍の住む森」 モイモイ
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "対象物の座標を渡さずに、カメラ画像とロボットの状態だけで物を運べました",
        },
        {
          at: 4,
          text: "Jev に任せられたのは、印を動かす向きや掴む物の選択といった画像で答えられる判断です",
        },
        {
          at: 8,
          text: "閉じるタイミングや、見えなくなった置き先への位置合わせは Jev だけでは決まりませんでした",
        },
        {
          at: 11.5,
          text: "手順や座標の変換はコードが担い、Jev への問いを絞る分担が有効でした",
        },
      ]}
    />
  </SceneFrame>
);
