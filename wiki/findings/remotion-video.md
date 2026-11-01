---
type: Finding
title: Remotion で説明動画を作るときの構成と調整
description: 最終課題の説明動画を Remotion 4 で作ったときの、場面の分け方、録画と Jev の判断の同期、場面末の静止、フェード、BGM のループ、尺の詰め方
tags: [remotion]
---

# Remotion で説明動画を作るときの構成と調整

2026-10〜11 に、最終課題の説明動画 (1920×1080、30 fps、177 秒) を Remotion 4.0.539 で作ったときに分かったこと。手順と構成は [video/README.md](../../video/README.md)、場面ごとの内容は [video/outline.md](../../video/outline.md) にある。

## 場面の分け方

場面ごとに、画面のコンポーネントと、fps から長さを返す関数 (`openingDuration` など) を 1 つのファイルに置く。`src/Main.tsx` の `SCENES` がそれを `Series` に並べ、`src/Root.tsx` は各場面を単独の composition としても登録する。

- Studio で場面を 1 つだけ開いて直せる。`Main` を開くと前後の場面とのつながりを確かめられる
- 長さを関数にしておくと、録画の長さから場面の長さを決められる (`Math.max(clipDuration, 10 * fps) + fps` など)。全体の長さは `SCENES` の合計で出る

Studio (`npx remotion studio --no-open`) をバックグラウンドで起動したまま編集すると、保存のたびにプレビューが更新される。字幕の切り替え時刻や場面の長さを秒単位で詰めるには、これが一番速かった。

## 録画と Jev の判断の同期

`video/scripts/export_resources.py` が、各実験の録画を倍速を掛けた 30 fps の動画にして `resources/clips/` に書き出す。sim の 1 step を録画の 1 フレームにしているので、倍速を掛けた後は動画の 1 フレームが Remotion の 1 フレームに当たる。同時に書き出す JSON には、判断ごとの step、Jev への問いと回答、命令が入っている。`src/clip.ts` の `stepAt` がフレームから step を求め、`decisionAt` がその時点の判断を引くので、録画と回答の表示がずれない。

`remotion.config.ts` で `Config.setPublicDir("resources")` にしているので、`staticFile("clips/...")` で書き出した素材を読める。

## 場面の終わりで止める

録画が終わってすぐ次の場面に切り替わると唐突に見える。場面の長さに `fps` (1 秒) を足し、足した分は `<Freeze frame={duration - 1}>` で録画の最後のフレームを表示し続けた (`src/components/ClipLayout.tsx`、`ClipView.tsx`)。

## フェード

場面の切り替えにフェードを入れるときは、`Series.Sequence` の中を opacity を変える `AbsoluteFill` で包む (`src/Main.tsx` の `Fade`)。`useVideoConfig().durationInFrames` は Sequence の中では場面の長さを返すので、終わりのフェードの位置はそこから計算できる。

フェード中は場面が半透明になるので、下に何も無いと Studio では透明を示す市松模様が見えた。`Series` の外側を背景色の `AbsoluteFill` で包むと、背景色からのフェードになる。

フェードは Opening と Background の間の 0.4 秒だけにした。録画の場面どうしは、上の静止で区切ったほうが自然だった。

## BGM

`<Audio src={staticFile("bgm.m4a")} loop>` で動画の間ループさせ、音量は 0.08 にした。`volume` に関数を渡して最後の 2 秒で 0 に下げるときは、`loopVolumeCurveBehavior="extend"` を付ける。既定の `"repeat"` では関数に渡るフレームがループのたびに 0 に戻るので、動画全体の終わりを基準にしたフェードにならない[^loop]。

音源はリポジトリに含めず、`video/.gitignore` で `resources/bgm.m4a` を除いている。

## 尺の詰め方

提出の上限は 3 分なので、余裕を 3 秒取って 177 秒にした。詰めるときは録画の倍速を変えず、文字だけの場面 (Background など) の長さと字幕の切り替え時刻を削った。録画の下には `speedLabel` で倍速を表示しており、Opening は「等倍速 (シミュレータの時間)」と表示しているので、倍速を変えると表示と食い違う。

字幕は `TimedCaption` に開始秒を並べて切り替える。Codex にレビューさせたところ、1 秒あたり 10 文字を超える字幕は読み切れないおそれがあると指摘された。字幕を足すときは、文字数と表示時間の比を見て開始秒を決める。

[^loop]: https://www.remotion.dev/docs/html5-audio#loopvolumecurvebehavior 。`"repeat"` (既定) はループのたびにフレームを 0 に戻し、`"extend"` は増やし続けると書かれている
