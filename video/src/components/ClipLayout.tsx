import React from "react";
import {
  Freeze,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ClipData, Decision, decisionAt, speedLabel, stepAt } from "../clip";
import { viewDuration } from "./ClipView";
import { cameraOf } from "./JevPanels";
import { COLORS } from "../theme";

// 録画の幅と高さ (左が固定カメラ、右が手首カメラ)
const VIDEO_W = 1208;
const VIDEO_H = 604;
const PANEL_W = 300;
// カメラ名の行の高さ。左右のパネルを動画の上端に揃える
const LABEL_H = 52;

// 録画を中央に、その時点の判断を表すパネルを左右に置く。Opening と実験の場面で共通の配置。
// 場面が録画より長いときは最後のフレームで止める
export const ClipLayout: React.FC<{
  name: string;
  data: ClipData;
  rate?: number;
  left?: (decision: Decision | null) => React.ReactNode;
  right?: (decision: Decision | null) => React.ReactNode;
  footer?: React.ReactNode;
}> = ({ name, data, rate = 1, left, right, footer }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const duration = viewDuration(data, fps, rate);
  const shown = Math.min(frame, duration - 1);
  const decision = decisionAt(data, stepAt(data, shown * rate, fps));
  const camera = cameraOf(decision);
  const fixed = camera?.name === "固定カメラ";

  const video = (
    <OffthreadVideo
      src={staticFile(`clips/${name}.mp4`)}
      muted
      playbackRate={rate}
      style={{ width: VIDEO_W, height: VIDEO_H, borderRadius: 6 }}
    />
  );

  const panel = (content: React.ReactNode) => (
    <div
      style={{
        width: PANEL_W,
        marginTop: LABEL_H,
        display: "flex",
        flexDirection: "column",
        gap: 30,
      }}
    >
      {content}
    </div>
  );

  return (
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
      {panel(left?.(decision))}

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
        <div style={{ position: "relative", width: VIDEO_W, height: VIDEO_H }}>
          {frame >= duration ? (
            <Freeze frame={duration - 1}>{video}</Freeze>
          ) : (
            video
          )}
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
          {footer}
        </div>
      </div>

      {panel(right?.(decision))}
    </div>
  );
};

// 動画の下に出す指示文と倍速
export const ClipFooter: React.FC<{
  data: ClipData;
  rate?: number;
  note?: string;
}> = ({ data, rate = 1, note }) => (
  <div>
    <span style={{ color: COLORS.muted }}>指示文 </span>
    {data.instruction}
    <span style={{ color: COLORS.muted, marginLeft: 24 }}>
      {speedLabel(data.speed * rate)}
      {note ? ` (${note})` : ""}
    </span>
  </div>
);
