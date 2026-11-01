import React from "react";
import { ClipData } from "../clip";
import { ClipFooter, ClipLayout } from "../components/ClipLayout";
import { ClipView, viewDuration } from "../components/ClipView";
import { JevInput, JevOutput, StageList } from "../components/JevPanels";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import { COLORS } from "../theme";
import bowlClip from "../../resources/clips/024-init0.json";
import stacked7 from "../../resources/clips/025-init7.json";
import stacked3 from "../../resources/clips/025-init3.json";
import missed4 from "../../resources/clips/025-init4.json";
import missed5 from "../../resources/clips/025-init5.json";

const bowl = bowlClip as ClipData;

// 書き出した録画は 4 倍速。他の実験に合わせて 6 倍速で流す
const BOWL_RATE = 1.5;

const TITLE = "実験 5: スケルトンを別のタスクへ転用する";

export const experiment5BowlDuration = (fps: number) =>
  Math.max(viewDuration(bowl, fps, BOWL_RATE), Math.round(10 * fps));

export const Experiment5Bowl: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="左の黒いボウルをトレイへ 8/10 成功">
      {TITLE}
    </SceneTitle>
    <ClipLayout
      name="024-init0"
      data={bowl}
      rate={BOWL_RATE}
      left={(decision) => (
        <>
          <StageList
            stages={bowl.stages ?? []}
            current={decision?.stage ?? 0}
          />
          <JevInput decision={decision} />
        </>
      )}
      right={(decision) => <JevOutput decision={decision} />}
      footer={<ClipFooter data={bowl} rate={BOWL_RATE} />}
    />
    <TimedCaption
      items={[
        { at: 0, text: "同じスケルトンを、ボウルを運ぶタスクに使ってみます" },
        {
          at: 3.5,
          text: "対象物や置き場所の名前を差し替え、ボウルは縁を掴むよう修正が必要でした",
        },
        {
          at: 7,
          text: "縁まで下りても閉じなかったため、下りきったら閉じるか開くかだけを選ばせました",
        },
      ]}
    />
  </SceneFrame>
);

// 上の段に重ねられた回、下の段に重ねられなかった回を並べる
const STACK_CELLS: {
  name: string;
  data: ClipData;
  label: string;
  ok: boolean;
}[] = [
  {
    name: "025-init7",
    data: stacked7 as ClipData,
    label: "左のボウルに重ねる",
    ok: true,
  },
  {
    name: "025-init3",
    data: stacked3 as ClipData,
    label: "左のボウルに重ねる",
    ok: true,
  },
  {
    name: "025-init4",
    data: missed4 as ClipData,
    label: "左のボウルが画角から外れ、離れた所に置く",
    ok: false,
  },
  {
    name: "025-init5",
    data: missed5 as ClipData,
    label: "左のボウルを越えて進み、上限まで置けない",
    ok: false,
  },
];

export const experiment5StackDuration = (fps: number) =>
  Math.max(...STACK_CELLS.map((c) => viewDuration(c.data, fps)));

export const Experiment5Stack: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="右のボウルを左のボウルに重ねる 4/10 成功">
      {TITLE}
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
      {STACK_CELLS.map((c) => (
        <ClipView
          key={c.name}
          name={c.name}
          data={c.data}
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
          text: "今度はスケルトンを変えずに、ボウルをボウルに重ねてみます",
        },
        {
          at: 4,
          text: "右のボウルを掴むところは、指示文だけで 10 回とも成功しています",
        },
        {
          at: 8,
          text: "ただ、置く先のボウルが画面から外れると位置を合わせられず、重ねられたのは 4/10 でした",
        },
      ]}
    />
  </SceneFrame>
);
