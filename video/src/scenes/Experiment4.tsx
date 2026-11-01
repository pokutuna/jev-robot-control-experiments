import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ClipData, decisionAt, stepAt } from "../clip";
import { ClipView, viewDuration } from "../components/ClipView";
import { StageList } from "../components/JevPanels";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import clip from "../../resources/clips/023-init0.json";

const data = clip as ClipData;
// Opening と同じ録画を、ここでは速めて流す
const RATE = 4;

export const experiment4Duration = (fps: number) =>
  Math.max(viewDuration(data, fps, RATE), Math.round(10 * fps));

export const Experiment4: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shown = Math.min(frame, viewDuration(data, fps, RATE) - 1);
  const decision = decisionAt(data, stepAt(data, shown * RATE, fps));
  return (
    <SceneFrame>
      <SceneTitle subtitle="プリンの箱をトレイへ 10/10 成功">
        実験 4: スケルトンを定義する
      </SceneTitle>
      <div
        style={{
          position: "absolute",
          top: 196,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 32,
        }}
      >
        <div style={{ width: 300, marginTop: 50 }}>
          <StageList
            stages={data.stages ?? []}
            current={decision?.stage ?? 0}
          />
        </div>
        <ClipView
          name="023-init0"
          data={data}
          width={1300}
          rate={RATE}
          input="印を描いた画像、寄せる物と行き先の名前"
        />
      </div>
      <TimedCaption
        items={[
          {
            at: 0,
            text: "対象物へ寄せる、掴む、置くといったステップと、各ステップで Jev に問う内容を人が定義しました",
          },
          {
            at: 5,
            text: "Jev は向きと次の動作を選びます / ステップの進行と世界座標への変換はコードが担います",
          },
        ]}
      />
    </SceneFrame>
  );
};
