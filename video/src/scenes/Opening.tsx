import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ClipData, clipDuration, decisionAt, stepAt } from "../clip";
import {
  cameraOf,
  JevInput,
  JevOutput,
  StageList,
} from "../components/JevPanels";
import { SceneCaption, SceneTitle } from "../components/SceneText";
import { COLORS, FONT } from "../theme";
import clip from "../../resources/clips/023-init0.json";

const data = clip as ClipData;

// 録画の幅と高さ (左が固定カメラ、右が手首カメラ)
const VIDEO_W = 1208;
const VIDEO_H = 604;
const PANEL_W = 300;
// カメラ名の行の高さ。左右のパネルを動画の上端に揃える
const LABEL_H = 52;

export const openingDuration = (fps: number) => clipDuration(data, fps);

export const Opening: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const decision = decisionAt(data, stepAt(data, frame, fps));
  const camera = cameraOf(decision);
  const fixed = camera?.name === "固定カメラ";

  return (
    <AbsoluteFill
      style={{ background: COLORS.bg, fontFamily: FONT, color: COLORS.ink }}
    >
      <SceneTitle>
        Decision モデルへの画像入力を活用しロボットアームを操作する
      </SceneTitle>

      <div
        style={{
          position: "absolute",
          top: 168,
          left: 32,
          right: 32,
          display: "flex",
          gap: 24,
          alignItems: "flex-start",
        }}
      >
        <div
          style={{
            width: PANEL_W,
            marginTop: LABEL_H,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          <StageList
            stages={data.stages ?? []}
            current={decision?.stage ?? 0}
          />
          <JevInput decision={decision} />
        </div>

        <div style={{ width: VIDEO_W }}>
          <div
            style={{
              display: "flex",
              height: LABEL_H - 10,
              marginBottom: 10,
              fontSize: 32,
              fontWeight: 700,
            }}
          >
            <div style={{ flex: 1, textAlign: "center" }}>固定カメラ</div>
            <div style={{ flex: 1, textAlign: "center" }}>手首カメラ</div>
          </div>
          <div
            style={{ position: "relative", width: VIDEO_W, height: VIDEO_H }}
          >
            <OffthreadVideo
              src={staticFile("clips/023-init0.mp4")}
              muted
              style={{ width: VIDEO_W, height: VIDEO_H, borderRadius: 6 }}
            />
            {camera ? (
              <div
                style={{
                  position: "absolute",
                  top: -5,
                  left: fixed ? -5 : VIDEO_W / 2 - 5,
                  width: VIDEO_W / 2 + 10,
                  height: VIDEO_H + 10,
                  border: `5px solid ${camera.color}`,
                  borderRadius: 8,
                  boxSizing: "border-box",
                }}
              />
            ) : null}
          </div>
          <div style={{ marginTop: 16, fontSize: 21, lineHeight: 1.6 }}>
            <div>
              <span style={{ color: COLORS.fixed, fontWeight: 700 }}>
                yellow dot
              </span>
              {" / "}
              <span style={{ color: COLORS.wrist, fontWeight: 700 }}>
                red cross
              </span>
              {
                ": グリッパーの真下を示す印 / グリッパーとカメラの位置から計算して描いています"
              }
            </div>
            <div>
              <span style={{ color: COLORS.sub }}>指示文 </span>
              {data.instruction}
              <span style={{ color: COLORS.sub, marginLeft: 24 }}>
                {data.speed} 倍速
              </span>
            </div>
          </div>
        </div>

        <div style={{ width: PANEL_W, marginTop: LABEL_H }}>
          <JevOutput decision={decision} />
        </div>
      </div>

      <SceneCaption>
        <div>
          物を掴んで別の場所に置く (pick-and-place) タスクを、ステップ分けした手順と
          Jev 1.14 への画像入力で解いています
        </div>
        <div>
          {
            "実環境を想定し、シミュレータから得られる対象物の座標等は参照していません / 入力画像にアノテーション (印) の補助を追加しています"
          }
        </div>
      </SceneCaption>
    </AbsoluteFill>
  );
};
