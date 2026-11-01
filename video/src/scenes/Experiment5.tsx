import React from "react";
import { ClipData } from "../clip";
import { ClipView, viewDuration } from "../components/ClipView";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import bowlClip from "../../resources/clips/024-init0.json";
import stackedClip from "../../resources/clips/025-init7.json";
import missedClip from "../../resources/clips/025-init4.json";

const bowl = bowlClip as ClipData;
const stacked = stackedClip as ClipData;
const missed = missedClip as ClipData;

const TITLE = "実験 5: スケルトンを別のタスクへ転用する";

export const experiment5BowlDuration = (fps: number) =>
  Math.max(viewDuration(bowl, fps), Math.round(10 * fps));

export const Experiment5Bowl: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="左の黒いボウルをトレイへ 8/10 成功">{TITLE}</SceneTitle>
    <div style={{ position: "absolute", top: 196, left: 310 }}>
      <ClipView
        name="024-init0"
        data={bowl}
        width={1300}
        input="印を描いた画像、寄せる物と行き先の名前"
      />
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "対象物や置き場所の名前だけを差し替えて転用しました / ボウルは縁を挟んで掴みます",
        },
        {
          at: 5,
          text: "下ろして当たった後は選択肢を close と open に絞るなど、失敗した点を修正しています",
        },
      ]}
    />
  </SceneFrame>
);

export const experiment5StackDuration = (fps: number) =>
  Math.max(viewDuration(stacked, fps), viewDuration(missed, fps));

const Heading: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ flex: 1, textAlign: "center" }}>{children}</div>
);

export const Experiment5Stack: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="右のボウルを左のボウルに重ねる 4/10 成功">
      {TITLE}
    </SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 280,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        gap: 40,
      }}
    >
      <ClipView
        name="025-init7"
        data={stacked}
        width={880}
        fontSize={20}
        heading={<Heading>重ねられた回</Heading>}
      />
      <ClipView
        name="025-init4"
        data={missed}
        width={880}
        fontSize={20}
        heading={<Heading>左のボウルが画角から外れた回</Heading>}
      />
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "スケルトンを変えずに適用しました / 指示文だけで右のボウルを掴み分けます (10 回中 10 回)",
        },
        {
          at: 6.5,
          text: "置き場所が画角から外れると位置を合わせられず、重ねられたのは 10 回中 4 回でした",
        },
      ]}
    />
  </SceneFrame>
);
