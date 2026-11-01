import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, FONT } from "../theme";

// 画面上部の見出し。各場面で中央寄せにそろえる。subtitle は見出しの下に小さく出す
export const SceneTitle: React.FC<{
  children: React.ReactNode;
  subtitle?: React.ReactNode;
}> = ({ children, subtitle }) => (
  <div
    style={{
      position: "absolute",
      top: 44,
      left: 32,
      right: 32,
      textAlign: "center",
    }}
  >
    <div style={{ fontSize: 60, fontWeight: 700, lineHeight: 1.2 }}>{children}</div>
    {subtitle ? (
      <div style={{ fontSize: 28, color: COLORS.sub, marginTop: 8 }}>
        {subtitle}
      </div>
    ) : null}
  </div>
);

// 画面下部の説明
export const SceneCaption: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <div
    style={{
      position: "absolute",
      bottom: 40,
      left: 32,
      right: 32,
      textAlign: "center",
      fontSize: 28,
      lineHeight: 1.6,
      color: COLORS.ink,
    }}
  >
    {children}
  </div>
);

// 下部の説明を時間で切り替える。at は場面の始めからの秒数
export const TimedCaption: React.FC<{
  items: { at: number; text: React.ReactNode }[];
}> = ({ items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const current = [...items].reverse().find((item) => frame >= item.at * fps);
  if (!current) return null;
  const opacity = interpolate(frame - current.at * fps, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  return (
    <SceneCaption>
      <div style={{ opacity }}>{current.text}</div>
    </SceneCaption>
  );
};

// 各場面の背景と文字の既定
export const SceneFrame: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <AbsoluteFill
    style={{ background: COLORS.bg, fontFamily: FONT, color: COLORS.ink }}
  >
    {children}
  </AbsoluteFill>
);
