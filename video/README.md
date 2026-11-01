# 説明動画

課題の説明動画を [Remotion](https://www.remotion.dev/) で作る。1920×1080、30 fps、約 2 分で、音声は入れない。場面の構成は [outline.md](outline.md) にある。

## 素材の書き出し

録画と Jev の判断の記録を、`experiments/` の各実験から `resources/` へ書き出す。書き出した素材はリポジトリに含めているので、録画を変えたときだけ実行すればよい。ffmpeg が要る。

```sh
# リポジトリのルートで
uv run python video/scripts/export_resources.py
```

- `resources/clips/<名前>.mp4`: 録画を倍速にして 30 fps にした動画。動画の 1 フレームが Remotion の 1 フレームに当たる
- `resources/clips/<名前>.json`: 判断ごとの Jev の問いと回答、命令、スケルトンのステップ
- `resources/images/`: レポートの図から使う静止画

使う録画と倍速は `scripts/export_resources.py` の `CLIPS` で決める。

## プレビューと書き出し

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
