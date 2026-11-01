// 色は docgen のデザインシステム (ライトテーマ) に合わせる。
// 有彩色は accent1 (teal: 見出しの線、ラベル、選んだ選択肢) と accent2 (amber: 強調) の 2 つに絞る。
// fixed と wrist は録画に描いた印の色で、印を指すときだけ使う
export const COLORS = {
  bg: "#FAFAF8",
  surface: "#FFFFFF",
  surfaceAlt: "#F2F3F5",
  ink: "#111827",
  muted: "#6B7280",
  border: "#1F2937",
  rule: "#E3E5E8",
  accent1: "#008080",
  accent2: "#B45309",
  barOff: "#C4C9D0",
  fixed: "#d9a400",
  wrist: "#c8322a",
};

export const BORDER_W = 1.5;
export const RADIUS = 10;

// Noto Sans CJK JP をインストールした環境で書き出す (README.md)
export const FONT = '"Noto Sans CJK JP", sans-serif';
export const MONO = '"Noto Sans Mono CJK JP", monospace';

// 録画は 20 fps で、1 フレームが sim の 1 step
export const SOURCE_FPS = 20;
