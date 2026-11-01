import React from "react";
import { ClipData } from "../clip";
import { ClipView, viewDuration } from "../components/ClipView";
import { SceneFrame, SceneTitle, TimedCaption } from "../components/SceneText";
import clip from "../../resources/clips/014-init0.json";

const data = clip as ClipData;

export const experiment2Duration = (fps: number) => viewDuration(data, fps);

export const Experiment2: React.FC = () => (
  <SceneFrame>
    <SceneTitle subtitle="プリンの箱をトレイへ 0/10 成功">
      実験 2: 画像で世界座標の向きを問う
    </SceneTitle>
    <div style={{ position: "absolute", top: 196, left: 310 }}>
      <ClipView
        name="014-init0"
        data={data}
        width={1300}
        input="固定カメラと手首カメラの画像、座標系の説明"
        note="最初の 60 秒"
      />
    </div>
    <TimedCaption
      items={[
        {
          at: 0,
          text: "座標を外し、画像から x, y, z の向きとグリッパーの開閉を 1 回の問いで選ばせます",
        },
        {
          at: 5,
          text: "最初にグリッパーを閉じ、箱から離れる向きへ動き続けました / 10 回とも失敗",
        },
      ]}
    />
  </SceneFrame>
);
