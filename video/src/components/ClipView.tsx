import React from "react";
import {
  Freeze,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  ClipData,
  clipDuration,
  decisionAt,
  speedLabel,
  stepAt,
} from "../clip";
import { COLORS, MONO } from "../theme";

// 書き出した動画を rate 倍で再生したときの長さ (フレーム数)
export const viewDuration = (data: ClipData, fps: number, rate = 1): number =>
  Math.ceil(clipDuration(data, fps) / rate);

// 実験の場面で使う録画。上にカメラ名か見出し、下に Jev の回答と命令を 1 行ずつ出す。
// wrap のときは回答と命令を別の行にして折り返す。場面が録画より長いときは最後のフレームで止める
export const ClipView: React.FC<{
  name: string;
  data: ClipData;
  width: number;
  rate?: number;
  heading?: React.ReactNode;
  input?: React.ReactNode;
  note?: string;
  fontSize?: number;
  wrap?: boolean;
}> = ({
  name,
  data,
  width,
  rate = 1,
  heading,
  input,
  note,
  fontSize = 22,
  wrap = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const duration = viewDuration(data, fps, rate);
  const shown = Math.min(frame, duration - 1);
  const decision = decisionAt(data, stepAt(data, shown * rate, fps));
  const height = width / 2;

  // 入力の行がないときは、Jev の行の右端に出す
  const speed = (
    <span style={{ color: COLORS.muted, marginLeft: 16, whiteSpace: "nowrap" }}>
      {speedLabel(data.speed * rate)}
      {note ? ` (${note})` : ""}
    </span>
  );

  const video = (
    <OffthreadVideo
      src={staticFile(`clips/${name}.mp4`)}
      muted
      playbackRate={rate}
      style={{ width, height, borderRadius: 6, display: "block" }}
    />
  );

  return (
    <div style={{ width }}>
      <div
        style={{
          display: "flex",
          marginBottom: 8,
          fontSize: fontSize + 10,
          fontWeight: 700,
        }}
      >
        {heading ?? (
          <>
            <div style={{ flex: 1, textAlign: "center" }}>固定カメラ</div>
            <div style={{ flex: 1, textAlign: "center" }}>手首カメラ</div>
          </>
        )}
      </div>
      {frame >= duration ? (
        <Freeze frame={duration - 1}>{video}</Freeze>
      ) : (
        video
      )}
      <div
        style={{
          marginTop: 10,
          fontSize,
          lineHeight: 1.5,
          whiteSpace: wrap ? "normal" : "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {input ? (
          <div style={{ display: "flex" }}>
            <div
              style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}
            >
              <span style={{ color: COLORS.muted }}>入力 </span>
              {input}
            </div>
            {speed}
          </div>
        ) : null}
        <div style={{ display: "flex" }}>
          <div
            style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}
          >
            <span style={{ color: COLORS.muted }}>Jev </span>
            <span style={{ fontFamily: MONO, fontSize: fontSize - 2 }}>
              {decision?.text ?? ""}
            </span>
            {decision?.command && !wrap ? (
              <>
                <span style={{ color: COLORS.muted, marginLeft: 16 }}>
                  命令{" "}
                </span>
                {decision.command}
              </>
            ) : null}
          </div>
          {input ? null : speed}
        </div>
        {decision?.command && wrap ? (
          <div>
            <span style={{ color: COLORS.muted }}>命令 </span>
            {decision.command}
          </div>
        ) : null}
      </div>
    </div>
  );
};
