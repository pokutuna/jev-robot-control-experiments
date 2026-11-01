import React from "react";
import {
  Freeze,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ClipData, clipDuration, decisionAt, stepAt } from "../clip";
import { COLORS, MONO } from "../theme";

// 書き出した動画を rate 倍で再生したときの長さ (フレーム数)
export const viewDuration = (data: ClipData, fps: number, rate = 1): number =>
  Math.ceil(clipDuration(data, fps) / rate);

// 実験の場面で使う録画。上にカメラ名か見出し、下に Jev の回答と命令を 1 行ずつ出す。
// 場面が録画より長いときは最後のフレームで止める
export const ClipView: React.FC<{
  name: string;
  data: ClipData;
  width: number;
  rate?: number;
  heading?: React.ReactNode;
  input?: React.ReactNode;
  note?: string;
  fontSize?: number;
}> = ({ name, data, width, rate = 1, heading, input, note, fontSize = 22 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const duration = viewDuration(data, fps, rate);
  const shown = Math.min(frame, duration - 1);
  const decision = decisionAt(data, stepAt(data, shown * rate, fps));
  const height = width / 2;

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
          fontSize: fontSize + 6,
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
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        <div style={{ display: "flex" }}>
          <div
            style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}
          >
            {input ? (
              <>
                <span style={{ color: COLORS.sub }}>入力 </span>
                {input}
              </>
            ) : null}
          </div>
          <span style={{ color: COLORS.sub, marginLeft: 16 }}>
            {data.speed * rate} 倍速{note ? ` (${note})` : ""}
          </span>
        </div>
        <div style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          <span style={{ color: COLORS.sub }}>Jev </span>
          <span style={{ fontFamily: MONO, fontSize: fontSize - 2 }}>
            {decision?.text ?? ""}
          </span>
          {decision?.command ? (
            <>
              <span style={{ color: COLORS.sub, marginLeft: 16 }}>命令 </span>
              {decision.command}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
