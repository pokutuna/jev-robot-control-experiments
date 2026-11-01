import React from "react";
import { ClipData } from "../clip";
import { ClipFooter, ClipLayout } from "../components/ClipLayout";
import { viewDuration } from "../components/ClipView";
import { JevInput, JevOutput, StageList } from "../components/JevPanels";
import { SceneFrame, SceneTitle } from "../components/SceneText";
import { COLORS } from "../theme";
import clip from "../../resources/clips/023-init0.json";

const data = clip as ClipData;
// 書き出した録画は 1.5 倍速。Opening では等倍に戻して流す
const RATE = 1 / data.speed;

export const openingDuration = (fps: number) => viewDuration(data, fps, RATE);

export const Opening: React.FC = () => (
  <SceneFrame>
    <SceneTitle>
      Decision モデルへの画像入力でロボットアームを操作する
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
      footer={
        <>
          <div>
            <span style={{ color: COLORS.fixed, fontWeight: 700 }}>
              yellow dot
            </span>
            {" / "}
            <span style={{ color: COLORS.wrist, fontWeight: 700 }}>
              red cross
            </span>
            {
              ": グリッパーの真下を示す印 / グリッパーとカメラの位置から計算して描いています"
            }
          </div>
          <ClipFooter data={data} rate={RATE} />
        </>
      }
    />

    <div
      style={{
        position: "absolute",
        bottom: 40,
        left: 32,
        right: 32,
        textAlign: "center",
        fontSize: 30,
        lineHeight: 1.6,
      }}
    >
      <div>
        物を掴んで別の場所に置く (pick-and-place)
        タスクを、ステップ分けした手順と Jev 1.14 への画像入力で解いています
      </div>
      <div>
        {
          "実環境を想定し、シミュレータから得られる対象物の座標等は参照していません / 入力画像に印の補助を追加しています"
        }
      </div>
    </div>
  </SceneFrame>
);
