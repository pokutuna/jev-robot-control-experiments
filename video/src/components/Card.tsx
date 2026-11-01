import React from "react";
import { COLORS } from "../theme";

export const Card: React.FC<{
  title: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ title, children, style }) => {
  return (
    <div
      style={{
        background: COLORS.card,
        border: `1px solid ${COLORS.line}`,
        borderRadius: 14,
        padding: "16px 20px",
        ...style,
      }}
    >
      <div
        style={{
          fontSize: 16,
          letterSpacing: "0.12em",
          color: COLORS.sub,
          fontWeight: 700,
          marginBottom: 10,
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
};
