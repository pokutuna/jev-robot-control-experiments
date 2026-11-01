import React from "react";
import { Img, staticFile } from "remotion";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS, MONO } from "../theme";

export const experiment3Duration = (fps: number) => Math.round(10 * fps);

const IMAGE_W = 600;

const Still: React.FC<{
  src: string;
  camera: string;
  mark: string;
  color: string;
}> = ({ src, camera, mark, color }) => (
  <div style={{ width: IMAGE_W }}>
    <div
      style={{
        textAlign: "center",
        fontSize: 32,
        fontWeight: 700,
        marginBottom: 8,
      }}
    >
      {camera}
    </div>
    <Img
      src={staticFile(src)}
      style={{ width: IMAGE_W, height: IMAGE_W, borderRadius: 6 }}
    />
    <div style={{ marginTop: 10, fontSize: 24, textAlign: "center" }}>
      <span style={{ color, fontWeight: 700 }}>{mark}</span> を対象物へ寄せるには?
    </div>
  </div>
);

export const Experiment3: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="静止画で問い方を検証">
      実験 3: 画像内の向きで問う
    </SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 186,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: 48,
      }}
    >
      <Still
        src="images/023-init0-d02-fixed.png"
        camera="固定カメラ"
        mark="yellow dot"
        color={COLORS.fixed}
      />
      <Still
        src="images/023-init0-d02-wrist.png"
        camera="手首カメラ"
        mark="red cross"
        color={COLORS.wrist}
      />
      <div style={{ fontSize: 26, lineHeight: 1.6 }}>
        <div style={{ color: COLORS.sub, fontSize: 20 }}>選択肢</div>
        <div style={{ fontFamily: MONO }}>h: left / none / right</div>
        <div style={{ fontFamily: MONO }}>v: up / none / down</div>
      </div>
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "グリッパーの真下を示す印を描き、印を対象物へ寄せる向きを画像内の左右 (h) と上下 (v) で問います",
        },
        {
          at: 5,
          text: "固定カメラは粗く寄せるステップ / 手首カメラは細かい位置合わせに使います",
        },
      ]}
    />
  </SceneFrame>
);
