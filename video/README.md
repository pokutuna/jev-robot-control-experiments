# 説明動画

課題の説明動画を [Remotion](https://www.remotion.dev/) で作る。1920×1080、30 fps、約 3 分で、ナレーションは入れず BGM だけを流す。場面の構成は [outline.md](outline.md) にある。

## 素材の書き出し

録画と Jev の判断の記録を、`experiments/` の各実験から `resources/` へ書き出す。書き出した素材はリポジトリに含めているので、録画を変えたときだけ実行すればよい。ffmpeg が要る。

```sh
# リポジトリのルートで
uv run python video/scripts/export_resources.py
```

- `resources/clips/<名前>.mp4`: 録画を倍速にして 30 fps にした動画。動画の 1 フレームが Remotion の 1 フレームに当たる
- `resources/clips/<名前>.json`: 判断ごとの Jev の問いと回答、命令、スケルトンのステップ
- `resources/images/`: レポートの図から使う静止画と、実験 016 で Jev に問うた静止画 (`016-*.png`)。後者は `outputs/probe_targets/` から写すので、先に [experiments/016-target-wording](../experiments/016-target-wording/README.md) の `probe_targets.py run` を実行しておく

使う録画と倍速は `scripts/export_resources.py` の `CLIPS` で決める。

BGM は `resources/bgm.m4a` に置く。音源はリポジトリに含めないので、プレビューや書き出しの前に用意する。`Main` が小さめの音量で動画の間ループさせる。

## プレビューと書き出し

文字は Noto Sans CJK JP と Noto Sans Mono CJK JP で描く。フォントは読み込まず、OS にインストールしたものを使う。

```sh
cd video
npm install
npx remotion studio            # http://localhost:3000/Main でプレビュー
npx remotion render Main out/video.mp4
```

`Main` は全場面をつないだもので、各場面も `Opening`、`Experiment1` などの名前で単独に開ける。

## ソースの構成

- `src/Main.tsx`: 場面の順と長さ
- `src/scenes/`: 場面ごとの画面
- `src/components/`: Jev の入出力の欄 (`JevPanels.tsx`)、録画と判断の表示 (`ClipView.tsx`)、見出しと説明 (`SceneText.tsx`)
- `src/clip.ts`: 判断の記録の型と、フレームから判断を引く関数
