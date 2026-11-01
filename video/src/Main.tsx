import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Series,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Background, backgroundDuration } from "./scenes/Background";
import { Experiment1, experiment1Duration } from "./scenes/Experiment1";
import { Experiment2, experiment2Duration } from "./scenes/Experiment2";
import { Experiment3, experiment3Duration } from "./scenes/Experiment3";
import { Experiment4, experiment4Duration } from "./scenes/Experiment4";
import {
  Experiment5Bowl,
  experiment5BowlDuration,
  Experiment5Stack,
  experiment5StackDuration,
} from "./scenes/Experiment5";
import { Experiment6, experiment6Duration } from "./scenes/Experiment6";
import { Opening, openingDuration } from "./scenes/Opening";
import { Overview, overviewDuration } from "./scenes/Overview";
import { Summary, summaryDuration } from "./scenes/Summary";
import { COLORS } from "./theme";

// 提出する動画の場面の順。Root.tsx では各場面を単独でも登録する
export const SCENES: {
  id: string;
  component: React.FC;
  duration: (fps: number) => number;
  fadeIn?: boolean;
  fadeOut?: boolean;
}[] = [
  {
    id: "Opening",
    component: Opening,
    duration: openingDuration,
    fadeOut: true,
  },
  {
    id: "Background",
    component: Background,
    duration: backgroundDuration,
    fadeIn: true,
  },
  { id: "Overview", component: Overview, duration: overviewDuration },
  { id: "Experiment1", component: Experiment1, duration: experiment1Duration },
  { id: "Experiment2", component: Experiment2, duration: experiment2Duration },
  { id: "Experiment3", component: Experiment3, duration: experiment3Duration },
  { id: "Experiment4", component: Experiment4, duration: experiment4Duration },
  {
    id: "Experiment5Bowl",
    component: Experiment5Bowl,
    duration: experiment5BowlDuration,
  },
  {
    id: "Experiment5Stack",
    component: Experiment5Stack,
    duration: experiment5StackDuration,
  },
  { id: "Experiment6", component: Experiment6, duration: experiment6Duration },
  { id: "Summary", component: Summary, duration: summaryDuration },
];

export const mainDuration = (fps: number) =>
  SCENES.reduce((sum, s) => sum + s.duration(fps), 0);

// 場面の始めや終わりを背景色から、または背景色へ短くフェードする
const FADE_SECONDS = 0.4;

const Fade: React.FC<{
  fadeIn?: boolean;
  fadeOut?: boolean;
  children: React.ReactNode;
}> = ({ fadeIn, fadeOut, children }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const len = Math.round(FADE_SECONDS * fps);
  const opacity = Math.min(
    fadeIn
      ? interpolate(frame, [0, len], [0, 1], { extrapolateRight: "clamp" })
      : 1,
    fadeOut
      ? interpolate(
          frame,
          [durationInFrames - len, durationInFrames - 1],
          [1, 0],
          {
            extrapolateLeft: "clamp",
          },
        )
      : 1,
  );
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

// BGM は小さめの音量でループし、最後の 2 秒で消す
const BGM_VOLUME = 0.08;

export const Main: React.FC<{ fps: number }> = ({ fps }) => {
  const total = mainDuration(fps);
  // フェード中に透けないよう、場面の下に背景色を敷く
  return (
    <AbsoluteFill style={{ background: COLORS.bg }}>
      <Audio
        src={staticFile("bgm.m4a")}
        loop
        loopVolumeCurveBehavior="extend"
        volume={(f) =>
          interpolate(f, [total - 2 * fps, total], [BGM_VOLUME, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          })
        }
      />
      <Series>
        {SCENES.map((s) => (
          <Series.Sequence key={s.id} durationInFrames={s.duration(fps)}>
            <Fade fadeIn={s.fadeIn} fadeOut={s.fadeOut}>
              <s.component />
            </Fade>
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
