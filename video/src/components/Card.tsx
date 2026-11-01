import React from "react";
import { BORDER_W, COLORS, RADIUS } from "../theme";

// 枠の上辺に teal の見出しを載せた白い面 (docgen の .dg-note[data-label])
export const Card: React.FC<{
  title: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ title, children, style }) => {
  return (
    <div
      style={{
        position: "relative",
        background: COLORS.surface,
        border: `${BORDER_W}px solid ${COLORS.border}`,
        borderRadius: RADIUS,
        padding: "24px 20px 16px",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -14,
          left: 16,
          padding: "2px 12px",
          borderRadius: 4,
          background: COLORS.accent1,
          color: COLORS.bg,
          fontSize: 16,
          fontWeight: 700,
          letterSpacing: "0.04em",
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
};
