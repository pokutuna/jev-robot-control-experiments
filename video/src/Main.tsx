import React from "react";
import { Series } from "remotion";
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
import { Summary, summaryDuration } from "./scenes/Summary";

// 提出する動画の場面の順。Root.tsx では各場面を単独でも登録する
export const SCENES: {
  id: string;
  component: React.FC;
  duration: (fps: number) => number;
}[] = [
  { id: "Opening", component: Opening, duration: openingDuration },
  { id: "Background", component: Background, duration: backgroundDuration },
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

export const Main: React.FC<{ fps: number }> = ({ fps }) => (
  <Series>
    {SCENES.map((s) => (
      <Series.Sequence key={s.id} durationInFrames={s.duration(fps)}>
        <s.component />
      </Series.Sequence>
    ))}
  </Series>
);
