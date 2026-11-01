// scripts/export_resources.py が書き出す判断の記録の型と、step から判断を引く関数

export type Probabilities = Record<string, Record<string, number>>;

export type JevCall = {
  fn: string;
  args: (string | number)[];
  answers: Record<string, string> & { p?: Probabilities };
};

export type Decision = {
  obs: number;
  step: number;
  text: string;
  command?: string;
  calls?: JevCall[];
  stage?: number | null;
};

export type ClipData = {
  experiment: string;
  init: number;
  instruction: string;
  fps: number;
  steps: number;
  speed: number;
  clip_steps: number;
  success: boolean;
  stages?: string[];
  decisions: Decision[];
};

// step の時点で最後に Jev へ画像を渡した判断
export const decisionAt = (data: ClipData, step: number): Decision | null => {
  let found: Decision | null = null;
  for (const d of data.decisions) {
    if (d.obs > step) break;
    found = d;
  }
  return found;
};

// 書き出した動画は倍速を掛けた 30 fps なので、フレームから step を求める
export const stepAt = (data: ClipData, frame: number, fps: number): number =>
  Math.floor((frame / fps) * data.speed * data.fps);

export const clipDuration = (data: ClipData, fps: number): number =>
  Math.ceil((data.clip_steps / data.fps / data.speed) * fps);
