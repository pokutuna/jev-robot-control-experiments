import React from "react";
import { Decision, JevCall } from "../clip";
import { COLORS, MONO } from "../theme";
import { Card } from "./Card";

const CAMERA: Record<string, { name: string; mark: string; color: string }> = {
  fixed_direction: {
    name: "固定カメラ",
    mark: "yellow dot",
    color: COLORS.fixed,
  },
  wrist_direction: { name: "手首カメラ", mark: "red cross", color: COLORS.wrist },
  wrist_step: { name: "手首カメラ", mark: "red cross", color: COLORS.wrist },
};

// 置く段の wrist_step は、赤い × の代わりに持っている物を行き先へ寄せる
const markOf = (call: JevCall, fallback: string): string => {
  const mark = call.args[1];
  return typeof mark === "string" && mark !== "red cross" ? mark : fallback;
};

const GROUP_NAMES: Record<string, string> = {
  h: "h (horizontal)",
  v: "v (vertical)",
};

const OPTIONS: Record<string, string[]> = {
  h: ["left", "none", "right"],
  v: ["up", "none", "down"],
  action: ["move", "lower", "close", "open"],
};

// Jev の関数を使わない判断 (コードが行う動作) の説明
const codeAction = (d: Decision): string => {
  if (d.text.startsWith("close_gripper")) return "閉じた後、コードが持ち上げる";
  if (d.text.startsWith("open_gripper")) return "開いた後、コードが持ち上げる";
  return "";
};

export const cameraOf = (d: Decision | null) => {
  const fn = d?.calls?.[0]?.fn;
  return fn ? CAMERA[fn] : null;
};

const Row: React.FC<{ label: string; children: React.ReactNode }> = ({
  label,
  children,
}) => (
  <div style={{ marginBottom: 10, fontSize: 20 }}>
    <div style={{ fontSize: 16, color: COLORS.sub }}>{label}</div>
    <div>{children}</div>
  </div>
);

export const StageList: React.FC<{
  stages: string[];
  current: number | null;
}> = ({ stages, current }) => (
  <Card title="スケルトンのステップ">
    {stages.map((s, i) => {
      const active = i === current;
      const done = current !== null && i < current;
      return (
        <div
          key={s}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "4px 10px",
            borderRadius: 8,
            fontSize: 20,
            background: active ? COLORS.barOn : "transparent",
            color: active ? "white" : done ? COLORS.sub : COLORS.ink,
            fontWeight: active ? 700 : 400,
          }}
        >
          <span style={{ width: 22, fontFamily: MONO, fontSize: 18 }}>
            {done ? "✓" : i + 1}
          </span>
          {s}
        </div>
      );
    })}
  </Card>
);

export const JevInput: React.FC<{ decision: Decision | null }> = ({
  decision,
}) => {
  const call: JevCall | undefined = decision?.calls?.[0];
  const camera = cameraOf(decision);
  return (
    <Card title="Jev への入力">
      {call && camera ? (
        <>
          <Row label="画像">
            <span style={{ color: camera.color, fontWeight: 700 }}>● </span>
            {camera.name}
          </Row>
          <Row label="寄せる物">
            <span style={{ fontFamily: MONO, fontSize: 18 }}>
              {markOf(call, camera.mark)}
            </span>
          </Row>
          <Row label="行き先">
            <span style={{ fontFamily: MONO, fontSize: 18 }}>
              {call.args[0]}
            </span>
          </Row>
          <Row label="選択肢">
            {Object.keys(call.answers.p ?? {}).map((k) => (
              <div key={k} style={{ fontFamily: MONO, fontSize: 18 }}>
                {k}: {OPTIONS[k]?.join(" / ")}
              </div>
            ))}
          </Row>
        </>
      ) : (
        <div style={{ fontSize: 21, color: COLORS.sub }}>
          {decision?.text.startsWith("check")
            ? "両方の画像と、完了したかを問う文"
            : decision
              ? `Jev に問わない (${codeAction(decision)})`
              : ""}
        </div>
      )}
    </Card>
  );
};

const Bars: React.FC<{
  name: string;
  p: Record<string, number>;
  chosen: string;
}> = ({ name, p, chosen }) => (
  <div style={{ marginBottom: 20 }}>
    <div
      style={{
        fontFamily: MONO,
        fontSize: 18,
        color: COLORS.sub,
        marginBottom: 4,
      }}
    >
      {GROUP_NAMES[name] ?? name}
    </div>
    {(OPTIONS[name] ?? Object.keys(p)).map((option) => {
      const value = p[option] ?? 0;
      const on = option === chosen;
      return (
        <div
          key={option}
          style={{ display: "flex", alignItems: "center", gap: 10, height: 26 }}
        >
          <div
            style={{
              width: 64,
              fontFamily: MONO,
              fontSize: 18,
              fontWeight: on ? 700 : 400,
              color: on ? COLORS.ink : COLORS.sub,
            }}
          >
            {option}
          </div>
          <div
            style={{
              flex: 1,
              height: 14,
              background: COLORS.bar,
              borderRadius: 7,
            }}
          >
            <div
              style={{
                width: `${value * 100}%`,
                height: "100%",
                borderRadius: 7,
                background: on ? COLORS.barOn : COLORS.barOff,
              }}
            />
          </div>
          <div
            style={{
              width: 52,
              textAlign: "right",
              fontFamily: MONO,
              fontSize: 18,
            }}
          >
            {value.toFixed(2)}
          </div>
        </div>
      );
    })}
  </div>
);

export const JevOutput: React.FC<{ decision: Decision | null }> = ({
  decision,
}) => {
  const call = decision?.calls?.[0];
  const checked = decision?.text.match(/^check\(.*\) → ([\d.]+)/);
  return (
    <Card title="Jev の出力">
      {call?.answers.p ? (
        Object.entries(call.answers.p).map(([k, p]) => (
          <Bars key={k} name={k} p={p} chosen={call.answers[k]} />
        ))
      ) : checked ? (
        <Bars name="完了したか" p={{ yes: Number(checked[1]) }} chosen="yes" />
      ) : (
        <div style={{ fontSize: 21, color: COLORS.sub }}>なし</div>
      )}
      {decision?.command ? (
        <div
          style={{
            paddingTop: 12,
            borderTop: `1px solid ${COLORS.line}`,
            fontSize: 21,
          }}
        >
          <span style={{ color: COLORS.sub }}>命令 </span>
          {decision.command}
        </div>
      ) : null}
    </Card>
  );
};
