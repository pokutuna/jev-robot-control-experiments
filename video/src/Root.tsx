import React from "react";
import { Composition } from "remotion";
import { Main, mainDuration, SCENES } from "./Main";

const FPS = 30;
const SIZE = { fps: FPS, width: 1920, height: 1080 };

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Main"
        component={Main}
        durationInFrames={mainDuration(FPS)}
        defaultProps={{ fps: FPS }}
        {...SIZE}
      />
      {SCENES.map((s) => (
        <Composition
          key={s.id}
          id={s.id}
          component={s.component}
          durationInFrames={s.duration(FPS)}
          {...SIZE}
        />
      ))}
    </>
  );
};
