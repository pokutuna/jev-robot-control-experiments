import React from "react";
import { ClipData } from "../clip";
import { ClipView, viewDuration } from "../components/ClipView";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS } from "../theme";
import pudding0 from "../../resources/clips/021-init0.json";
import pudding1 from "../../resources/clips/021-init1.json";
import bowl6 from "../../resources/clips/022-init6.json";
import bowl3 from "../../resources/clips/022-init3.json";

// 書き出した録画は 4 倍速。他の実験に合わせて 6 倍速で流す
const RATE = 1.5;

const CELLS: { name: string; data: ClipData; label: string; ok: boolean }[] = [
  {
    name: "021-init0",
    data: pudding0 as ClipData,
    label: "プリンの箱",
    ok: true,
  },
  {
    name: "022-init6",
    data: bowl6 as ClipData,
    label: "左の黒いボウル",
    ok: true,
  },
  {
    name: "021-init1",
    data: pudding1 as ClipData,
    label: "プリンの箱 (トレイの手前に置く)",
    ok: false,
  },
  {
    name: "022-init3",
    data: bowl3 as ClipData,
    label: "左の黒いボウル (トレイの縁に掛かる)",
    ok: false,
  },
];

// 字幕を読み終えた後、最後のフレームで 1 秒止めてから次の場面へ移る
export const experiment6Duration = (fps: number) =>
  Math.max(
    ...CELLS.map((c) => viewDuration(c.data, fps, RATE)),
    Math.round(13 * fps),
  ) + fps;

export const Experiment6: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="Code as Policies (生成: DeepSeek V4.1 Flash) / 4/10〜8/10 成功">
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
        rowGap: 12,
        padding: "0 280px",
      }}
    >
      {CELLS.map((c) => (
        <ClipView
          key={c.name}
          name={c.name}
          data={c.data}
          rate={RATE}
          width={620}
          fontSize={16}
          heading={
            <div style={{ flex: 1, textAlign: "center", fontSize: 24 }}>
              <span style={{ color: c.ok ? COLORS.accent1 : COLORS.accent2 }}>
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
          text: "最後に、スケルトンを人ではなく LLM に書かせてみました",
        },
        {
          at: 3.5,
          text: "成否を分けたのは、プログラムごとの細かな書き方の違いでした",
        },
        {
          at: 6.5,
          text: "左下は、トレイへ寄せるループの上限が足りず、手前で置いてしまった回です",
        },
        {
          at: 9.5,
          text: "右下は、掴むときにずらした 6 cm を置くときにもずらし、縁に掛けてしまった回です",
        },
      ]}
    />
  </SceneFrame>
);
