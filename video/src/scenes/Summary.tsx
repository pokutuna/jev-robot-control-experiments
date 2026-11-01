import React from "react";
import { SceneFrame, SceneTitle } from "../components/SceneText";
import { COLORS } from "../theme";

export const summaryDuration = (fps: number) => Math.round(12 * fps);

const ROWS = [
  ["1", "対象物の座標 (テキスト)", "10/10"],
  ["2", "画像、世界座標の向きで問う", "0/10"],
  ["4", "印を描いた画像、人が定義したスケルトン", "プリンの箱 10/10"],
  ["5", "同じスケルトンを転用", "左の黒いボウル 8/10、重ねる 4/10"],
  ["6", "LLM が生成したスケルトン", "4/10〜8/10"],
];

const cell: React.CSSProperties = {
  padding: "12px 24px",
  borderBottom: `1px solid ${COLORS.line}`,
  textAlign: "left",
};

export const Summary: React.FC = () => (
  <SceneFrame>
    <SceneTitle>まとめ</SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 240,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 56,
      }}
    >
      <table style={{ borderCollapse: "collapse", fontSize: 32 }}>
        <thead>
          <tr style={{ color: COLORS.sub, fontSize: 24 }}>
            <th style={cell}>実験</th>
            <th style={cell}>方策への入力</th>
            <th style={cell}>成功</th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map(([n, input, result]) => (
            <tr key={n}>
              <td style={{ ...cell, textAlign: "center" }}>{n}</td>
              <td style={cell}>{input}</td>
              <td style={cell}>{result}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: 34, lineHeight: 1.7, textAlign: "center" }}>
        <div>
          <span style={{ color: COLORS.sub }}>Jev </span>
          画像から判断できる問い (画像内の向き、閉じるか開くか)
        </div>
        <div>
          <span style={{ color: COLORS.sub }}>スケルトンのコード </span>
          ステップの順序、世界座標への変換、選択肢の絞り込み
        </div>
        <div style={{ marginTop: 16 }}>
          この役割分担で、対象物の座標を渡さずに物を運べました
        </div>
      </div>
    </div>
  </SceneFrame>
);
