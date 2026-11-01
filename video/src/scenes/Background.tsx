import React from "react";
import { Img, staticFile } from "remotion";
import {
  Section,
  SceneFrame,
  SceneTitle,
  TimedCaption,
} from "../components/SceneText";
import { COLORS } from "../theme";

export const backgroundDuration = (fps: number) => Math.round(24.8 * fps);

const SECTIONS: { head: React.ReactNode; items: string[] }[] = [
  {
    head: "Jev (Decision モデル) が画像入力に対応",
    items: [
      "問いと選択肢を渡すと、回答と各選択肢の確率を返す",
      "jev-1.14 (preview、2026-10-14 公開) から",
    ],
  },
  {
    head: (
      <>
        先行事例はシミュレータの座標を参照
        <span style={{ fontSize: 26, fontWeight: 400, color: COLORS.muted }}>
          {" "}
          (と思われるものが多い)
        </span>
      </>
    ),
    items: [
      "対象物や目標の座標を入力している",
      "実環境でこのような値は得にくい",
    ],
  },
  {
    head: "課題設定",
    items: [
      "座標の代わりにカメラ画像とロボットの状態を入力する",
      "Jev がうまく判断できる入力を探る",
    ],
  },
];

export const Background: React.FC = () => (
  <SceneFrame>
    <SceneTitle fontSize={80}>背景と課題設定</SceneTitle>
    <div
      style={{
        position: "absolute",
        top: 200,
        left: 100,
        right: 100,
        display: "flex",
        gap: 96,
        alignItems: "center",
      }}
    >
      <div style={{ width: 600 }}>
        <Img
          src={staticFile("images/scene-quarterview.png")}
          style={{ width: 600, height: 600, borderRadius: 6 }}
        />
        <div
          style={{
            margin: "12px -60px 0",
            fontSize: 24,
            lineHeight: 1.6,
            textAlign: "center",
          }}
        >
          <div style={{ color: COLORS.muted }}>
            LIBERO の LIVING_ROOM_SCENE4 (固定カメラ)
          </div>
          <div>代表タスク: プリンの箱 (左下) を木製のトレイ (右下) へ運ぶ</div>
        </div>
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 64,
        }}
      >
        {SECTIONS.map((s) => (
          <Section key={s.items[0]} head={s.head} items={s.items} />
        ))}
      </div>
    </div>
    <TimedCaption
      items={[
        { at: 0, text: "こんにちは、まず課題設定について述べます" },
        {
          at: 2.5,
          text: "2026-09 に Jev というモデルが公開され話題になりました",
        },
        {
          at: 6.5,
          text: "流行し様々な領域で活用され、ロボットアームを動かす例も見られました",
        },
        {
          at: 10.5,
          text: "私が見た事例の多くでは、シミュレータから正解となる座標を渡していたようです",
        },
        {
          at: 15.5,
          text: "しかし実環境ではそうした座標を手に入れるのは難しいです",
        },
        {
          at: 19,
          text: "そこで画像入力に対応した Jev を利用し、正解座標を参照せず解けないかを探ってみました",
        },
      ]}
    />
  </SceneFrame>
);
