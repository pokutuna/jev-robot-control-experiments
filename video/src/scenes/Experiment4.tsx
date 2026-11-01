import React from "react";
import { ClipData } from "../clip";
import { ClipFooter, ClipLayout } from "../components/ClipLayout";
import { viewDuration } from "../components/ClipView";
import { JevInput, JevOutput, StageList } from "../components/JevPanels";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import clip from "../../resources/clips/023-init0.json";

const data = clip as ClipData;
// Opening と同じ録画を、ここでは速めて流す
const RATE = 4;

// 字幕を読み終えた後、最後のフレームで 1 秒止めてから次の場面へ移る
export const experiment4Duration = (fps: number) =>
  Math.max(viewDuration(data, fps, RATE), Math.round(10 * fps)) + fps;

export const Experiment4: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="プリンの箱をトレイへ 10/10 成功">
      実験 4: スケルトンを定義する
    </SceneTitle>
    <ClipLayout
      name="023-init0"
      data={data}
      rate={RATE}
      left={(decision) => (
        <>
          <StageList
            stages={data.stages ?? []}
            current={decision?.stage ?? 0}
          />
          <JevInput decision={decision} />
        </>
      )}
      right={(decision) => <JevOutput decision={decision} />}
      footer={<ClipFooter data={data} rate={RATE} />}
    />
    <TimedCaption
      items={[
        {
          at: 0,
          text: "この問い方を使って、寄せる・掴む・置くといったステップを人が決めました",
        },
        { at: 3.5, text: "Jev が選ぶのは、動かす向きと次の動作だけです" },
        {
          at: 6.5,
          text: "ステップを進めたり世界座標に直したりするのはコードの役目で、10 回とも成功しました",
        },
      ]}
    />
  </SceneFrame>
);
