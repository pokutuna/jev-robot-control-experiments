import React from "react";
import { ClipData } from "../clip";
import { ClipFooter, ClipLayout } from "../components/ClipLayout";
import { viewDuration } from "../components/ClipView";
import { Card } from "../components/Card";
import { JevTextOutput, Row } from "../components/JevPanels";
import {
  Outcome,
  SceneFrame,
  SceneTitle,
  TimedCaption,
} from "../components/SceneText";
import { MONO } from "../theme";
import clip from "../../resources/clips/014-init0.json";

const data = clip as ClipData;

// 録画が終わった後、最後のフレームで 1 秒止めてから次の場面へ移る
export const experiment2Duration = (fps: number) =>
  viewDuration(data, fps) + fps;

const mono: React.CSSProperties = { fontFamily: MONO, fontSize: 18 };

export const Experiment2: React.FC = () => (
  <SceneFrame>
    <SceneTitle
      subtitle={
        <>
          プリンの箱をトレイへ <Outcome ok={false}>10 回とも失敗</Outcome>
        </>
      }
    >
      実験 2: 画像で世界座標の向きを問う
    </SceneTitle>
    <ClipLayout
      name="014-init0"
      data={data}
      left={() => (
        <Card title="Jev への入力">
          <Row label="画像">固定カメラ、手首カメラ</Row>
          <Row label="テキスト">座標系の説明</Row>
          <Row label="選択肢">
            <div style={mono}>x, y, z: plus / stay / minus</div>
            <div style={mono}>gripper: open / closed</div>
            <div style={mono}>完了したか</div>
          </Row>
        </Card>
      )}
      right={(decision) => <JevTextOutput decision={decision} />}
      footer={<ClipFooter data={data} note="最初の 60 秒" />}
    />
    <TimedCaption
      items={[
        {
          at: 0,
          text: "次は座標を渡すのをやめて、カメラ画像から同じように選んでもらいました",
        },
        { at: 3.5, text: "すると、いきなりグリッパーを閉じてしまいました" },
        {
          at: 6.5,
          text: "そのまま箱から離れる方へ進み続けて、10 回とも失敗です",
        },
      ]}
    />
  </SceneFrame>
);
