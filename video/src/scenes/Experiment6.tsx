import React from "react";
import { ClipData } from "../clip";
import { ClipView, viewDuration } from "../components/ClipView";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS } from "../theme";
import pudding0 from "../../resources/clips/021-init0.json";
import pudding1 from "../../resources/clips/021-init1.json";
import bowl6 from "../../resources/clips/022-init6.json";
import bowl3 from "../../resources/clips/022-init3.json";

const CELLS: { name: string; data: ClipData; label: string; ok: boolean }[] = [
  { name: "021-init0", data: pudding0 as ClipData, label: "プリンの箱", ok: true },
  { name: "022-init6", data: bowl6 as ClipData, label: "左の黒いボウル", ok: true },
  {
    name: "021-init1",
    data: pudding1 as ClipData,
    label: "プリンの箱 (ループの上限でトレイの手前に置く)",
    ok: false,
  },
  {
    name: "022-init3",
    data: bowl3 as ClipData,
    label: "左の黒いボウル (トレイの縁に掛かる)",
    ok: false,
  },
];

export const experiment6Duration = (fps: number) =>
  Math.max(
    ...CELLS.map((c) => viewDuration(c.data, fps)),
    Math.round(10 * fps),
  );

export const Experiment6: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="Code as Policies / 4/10〜8/10 成功">
      実験 6: LLM にスケルトンを書かせる
    </SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 172,
        left: 0,
        right: 0,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        columnGap: 48,
        rowGap: 4,
        padding: "0 300px",
      }}
    >
      {CELLS.map((c) => (
        <ClipView
          key={c.name}
          name={c.name}
          data={c.data}
          width={600}
          fontSize={16}
          heading={
            <div style={{ flex: 1, textAlign: "center" }}>
              <span style={{ color: c.ok ? COLORS.barOn : COLORS.wrist }}>
                {c.ok ? "成功" : "失敗"}
              </span>{" "}
              {c.label}
            </div>
          }
        />
      ))}
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "人が書く代わりに、LLM にスケルトン (制御プログラム) を生成させました",
        },
        {
          at: 5,
          text: "成否はループの上限など、生成されたプログラムごとの実装の違いで分かれました",
        },
      ]}
    />
  </SceneFrame>
);
