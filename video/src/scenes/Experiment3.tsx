import React from "react";
import { Img, staticFile } from "remotion";
import { ClipData } from "../clip";
import { Card } from "../components/Card";
import { Bars, Row } from "../components/JevPanels";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS, MONO } from "../theme";
import clip from "../../resources/clips/023-init0.json";

export const experiment3Duration = (fps: number) => Math.round(12 * fps);

const IMAGE_W = 320;

type Answer = Record<"h" | "v", Record<string, number>>;

// 実験 4 の録画の 2 回目の判断。箱から離れた位置で固定カメラの画像に問うた回答
const far = (clip as ClipData).decisions[1].calls![0].answers.p as Answer;

// 残りは実験 016 で、グリッパーを箱から 4 cm ずらした静止画に問うた回答
// (experiments/016-target-wording/probe/ の init 0、dx 0、dy ±4 cm、the chocolate pudding box)
const CAMERAS: {
  name: string;
  color: string;
  role: string;
  cells: { src: string; label: string; ok: boolean; p: Answer }[];
}[] = [
  {
    name: "固定カメラ",
    color: COLORS.fixed,
    role: "近くでは none と答える → 粗く寄せるステップに使う",
    cells: [
      {
        src: "images/023-init0-d02-fixed.png",
        label: "箱から離れた位置",
        ok: true,
        p: far,
      },
      {
        src: "images/016-init0-dy4-fixed.png",
        label: "箱から 4 cm ずらした位置",
        ok: false,
        p: {
          h: { left: 0.04, none: 0.94, right: 0.02 },
          v: { up: 0.03, none: 0.96, down: 0.01 },
        },
      },
    ],
  },
  {
    name: "手首カメラ",
    color: COLORS.wrist,
    role: "4 cm のずれでも向きを答える → 細かい位置合わせに使う",
    cells: [
      {
        src: "images/016-init0-dy4-wrist.png",
        label: "箱から 4 cm ずらした位置",
        ok: true,
        p: {
          h: { left: 0.81, none: 0.18, right: 0.01 },
          v: { up: 0.09, none: 0.89, down: 0.02 },
        },
      },
      {
        src: "images/016-init0-dy-4-wrist.png",
        label: "反対側に 4 cm ずらした位置",
        ok: true,
        p: {
          h: { left: 0.01, none: 0.06, right: 0.93 },
          v: { up: 0.04, none: 0.93, down: 0.03 },
        },
      },
    ],
  },
];

const chosen = (p: Record<string, number>): string =>
  Object.entries(p).reduce((a, b) => (b[1] > a[1] ? b : a))[0];

export const Experiment3: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="マーカーを画像に追加し、移動すべき向きだけを回答させる">
      実験 3: 画像内の向きで問う
    </SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 172,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        gap: 56,
      }}
    >
      {CAMERAS.map((camera) => (
        <div key={camera.name}>
          <div style={{ textAlign: "center", fontSize: 32, fontWeight: 700 }}>
            <span style={{ color: camera.color }}>● </span>
            {camera.name}
          </div>
          <div
            style={{
              textAlign: "center",
              fontSize: 24,
              color: COLORS.muted,
              margin: "4px 0 12px",
            }}
          >
            {camera.role}
          </div>
          <div style={{ display: "flex", gap: 24 }}>
            {camera.cells.map((cell) => (
              <div key={cell.src} style={{ width: IMAGE_W }}>
                <div
                  style={{ fontSize: 20, textAlign: "center", marginBottom: 6 }}
                >
                  <span
                    style={{
                      color: cell.ok ? COLORS.accent1 : COLORS.accent2,
                      fontWeight: 700,
                    }}
                  >
                    {cell.ok ? "成功" : "失敗"}
                  </span>{" "}
                  {cell.label}
                </div>
                <Img
                  src={staticFile(cell.src)}
                  style={{
                    width: IMAGE_W,
                    height: IMAGE_W,
                    borderRadius: 6,
                    display: "block",
                  }}
                />
                <div style={{ marginTop: 12 }}>
                  {(["h", "v"] as const).map((k) => (
                    <Bars
                      key={k}
                      name={k}
                      p={cell.p[k]}
                      chosen={chosen(cell.p[k])}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <div style={{ width: 300, marginTop: 120 }}>
        <Card title="Jev への入力">
          <Row label="画像">印を描いた画像 1 枚</Row>
          <Row label="寄せる物">
            <span style={{ fontFamily: MONO, fontSize: 18 }}>
              yellow dot / red cross
            </span>
          </Row>
          <Row label="行き先">
            <span style={{ fontFamily: MONO, fontSize: 18 }}>
              the chocolate pudding box
            </span>
          </Row>
          <Row label="選択肢">
            <div style={{ fontFamily: MONO, fontSize: 18 }}>
              h: left / none / right
            </div>
            <div style={{ fontFamily: MONO, fontSize: 18 }}>
              v: up / none / down
            </div>
          </Row>
        </Card>
      </div>
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "そこで、グリッパーの真下を示す印を画像に描くことにしました",
        },
        {
          at: 4,
          text: "印を箱に重ねるには、画像の中で左右・上下どちらへ動かせばいいかを聞きます",
        },
        {
          at: 8,
          text: "固定カメラは近くだとずれを見分けられないので、細かい位置合わせは手首カメラに任せます",
        },
      ]}
    />
  </SceneFrame>
);
