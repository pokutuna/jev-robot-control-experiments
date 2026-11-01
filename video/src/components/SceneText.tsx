import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, FONT } from "../theme";

// 画面上部の見出し。各場面で中央寄せにそろえ、subtitle は見出しの下に小さく出す
export const SceneTitle: React.FC<{
  children: React.ReactNode;
  subtitle?: React.ReactNode;
  fontSize?: number;
}> = ({ children, subtitle, fontSize = 60 }) => (
  <div
    style={{
      position: "absolute",
      top: 36,
      left: 32,
      right: 32,
      textAlign: "center",
    }}
  >
    <div
      style={{
        display: "inline-block",
        fontSize,
        fontWeight: 700,
        lineHeight: 1.2,
      }}
    >
      {children}
    </div>
    {subtitle ? (
      <div style={{ fontSize: 28, color: COLORS.muted, marginTop: 6 }}>
        {subtitle}
      </div>
    ) : null}
  </div>
);

// 画面下部の字幕。ほかの文字と見分けられるよう、暗い帯に白い文字で出す
export const SceneCaption: React.FC<{
  children: React.ReactNode;
  fontSize?: number;
  opacity?: number;
}> = ({ children, fontSize = 40, opacity = 1 }) => (
  <div
    style={{
      position: "absolute",
      bottom: 40,
      left: 32,
      right: 32,
      textAlign: "center",
    }}
  >
    <div
      style={{
        display: "inline-block",
        padding: "8px 28px",
        borderRadius: 8,
        background: COLORS.ink,
        color: COLORS.surface,
        fontSize,
        lineHeight: 1.5,
        opacity,
      }}
    >
      {children}
    </div>
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
  return <SceneCaption opacity={opacity}>{current.text}</SceneCaption>;
};

// 各場面の背景と文字の既定
export const SceneFrame: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <AbsoluteFill
    style={{
      background: COLORS.bg,
      fontFamily: FONT,
      color: COLORS.ink,
      fontFeatureSettings: '"palt"',
    }}
  >
    {children}
  </AbsoluteFill>
);

// 左に teal の縦線を引いた小見出しと、その下の箇条書き。項目内の \n は改行する
// 見出しは箇条書きの文字より 8px 大きくする
export const Section: React.FC<{
  head: React.ReactNode;
  items: string[];
  fontSize?: number;
}> = ({ head, items, fontSize = 30 }) => (
  <div>
    <div
      style={{
        fontSize: fontSize + 8,
        fontWeight: 700,
        lineHeight: 1.4,
        paddingLeft: 16,
        borderLeft: `8px solid ${COLORS.accent1}`,
        marginBottom: 16,
      }}
    >
      {head}
    </div>
    <ul style={{ margin: 0, paddingLeft: 56, fontSize, lineHeight: 1.7 }}>
      {items.map((item) => (
        <li key={item} style={{ whiteSpace: "pre-line" }}>
          {item}
        </li>
      ))}
    </ul>
  </div>
);

// 実験の結果。成功は accent1、失敗は accent2 の太字で示す
export const Outcome: React.FC<{ ok: boolean; children: React.ReactNode }> = ({
  ok,
  children,
}) => (
  <span
    style={{ color: ok ? COLORS.accent1 : COLORS.accent2, fontWeight: 700 }}
  >
    {children}
  </span>
);
