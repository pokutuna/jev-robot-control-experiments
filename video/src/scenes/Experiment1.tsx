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
import clip from "../../resources/clips/013-init0.json";

const data = clip as ClipData;

// 録画が終わった後、最後のフレームで 1 秒止めてから次の場面へ移る
export const experiment1Duration = (fps: number) =>
  viewDuration(data, fps) + fps;

const mono: React.CSSProperties = { fontFamily: MONO, fontSize: 18 };

export const Experiment1: React.FC = () => (
  <SceneFrame>
    <SceneTitle
      subtitle={
        <>
          先行事例の再現 / プリンの箱をトレイへ <Outcome ok>10/10 成功</Outcome>
        </>
      }
    >
      実験 1: 対象物の座標をテキストで渡す
    </SceneTitle>
    <ClipLayout
      name="013-init0"
      data={data}
      left={() => (
        <Card title="Jev への入力">
          <Row label="画像">使わない</Row>
          <Row label="テキスト">
            箱とトレイの座標、グリッパーとの差 (シミュレータから取得)
          </Row>
          <Row label="選択肢">
            <div style={mono}>意図: approach / grasp / …</div>
            <div style={mono}>x, y, z:</div>
            <div style={mono}>&nbsp;&nbsp;negative / hold / positive</div>
            <div style={mono}>gripper: hold / close / open</div>
          </Row>
        </Card>
      )}
      right={(decision) => <JevTextOutput decision={decision} />}
      footer={<ClipFooter data={data} />}
    />
    <TimedCaption
      items={[
        {
          at: 0,
          text: "まずは先行事例と同じように、箱とトレイの座標をテキストで渡してみました",
        },
        {
          at: 4,
          text: "Jev には x, y, z をそれぞれどちらに動かすかを選んでもらいます",
        },
        {
          at: 7.5,
          text: "10 回とも成功しましたが、数値の符号を見れば答えられるので画像は使っていません",
        },
      ]}
    />
  </SceneFrame>
);
