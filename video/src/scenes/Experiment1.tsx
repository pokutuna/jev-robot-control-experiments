import React from "react";
import { ClipData } from "../clip";
import { ClipView, viewDuration } from "../components/ClipView";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import clip from "../../resources/clips/013-init0.json";

const data = clip as ClipData;

export const experiment1Duration = (fps: number) => viewDuration(data, fps);

export const Experiment1: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="先行事例の再現 / プリンの箱をトレイへ 10/10 成功">
      実験 1: 対象物の座標をテキストで渡す
    </SceneTitle>
    <div style={{ position: "absolute", top: 196, left: 310 }}>
      <ClipView
        name="013-init0"
        data={data}
        width={1300}
        input="箱とトレイの座標、グリッパーとの差 (シミュレータから取得したテキスト)"
      />
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "シミュレータから得た座標と目標までの差をテキストで渡し、x, y, z の向きを問います",
        },
        {
          at: 5.5,
          text: "10 回中 10 回成功します / ただし Jev は数値の符号を読めば答えられ、画像は使っていません",
        },
      ]}
    />
  </SceneFrame>
);
