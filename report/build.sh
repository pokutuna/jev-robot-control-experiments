#!/usr/bin/env bash
# report.md -> PDF。どこからでも実行できる:
#   bash report/build.sh
#
# 依存: pandoc、Google Chrome、Node.js (npx)。
# mermaid の図は mermaid-cli (npx で取得) で SVG にする。描画には上記の Chrome を使い、puppeteer の Chrome はダウンロードしない。
# 出力は report/build/ (gitignore 済み) に置く。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${HERE}/report.md"
BUILD="${HERE}/build"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
MERMAID_CLI="@mermaid-js/mermaid-cli@12.0.0"

command -v pandoc >/dev/null || { echo "error: pandoc がない"; exit 1; }
command -v npx >/dev/null || { echo "error: npx がない"; exit 1; }
test -x "$CHROME" || { echo "error: Chrome が見つからない: $CHROME (環境変数 CHROME で指定できる)"; exit 1; }

# 0. 本文に手元の環境が漏れていないか検査する
if grep -nE '/Users/|physicalai' "$SRC"; then
  echo "error: 手元のパスなど、本文に入れてはならない語がある"; exit 1
fi

mkdir -p "$BUILD"

# 1. mermaid のコードブロックを SVG の画像に置き換えた Markdown を作る
printf '{"executablePath": "%s", "args": ["--no-sandbox"]}\n' "$CHROME" > "${BUILD}/puppeteer.json"
PUPPETEER_SKIP_DOWNLOAD=1 npx -y -p "$MERMAID_CLI" mmdc \
  --input "$SRC" \
  --output "${BUILD}/report.md" \
  --outputFormat svg \
  --configFile "${HERE}/mermaid.json" \
  --puppeteerConfigFile "${BUILD}/puppeteer.json" \
  --backgroundColor white \
  --quiet

# 2. Markdown -> HTML (画像と CSS を埋め込んで 1 ファイルにする)
pandoc "${BUILD}/report.md" \
  --from=gfm \
  --to=html5 \
  --standalone \
  --metadata pagetitle="$(sed -n 's/^# //p' "$SRC" | head -1)" \
  --css="${HERE}/report.css" \
  --lua-filter="${HERE}/caption.lua" \
  --resource-path="${BUILD}:${HERE}" \
  --embed-resources \
  --output="${BUILD}/report.html"

# 3. HTML -> PDF
#    --headless=new は macOS の Chrome で PDF 出力が空になることがあるため旧 headless を使う
"$CHROME" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="${BUILD}/report.pdf" \
  --virtual-time-budget=10000 \
  "file://${BUILD}/report.html" 2>/dev/null

test -f "${BUILD}/report.pdf" || { echo "error: PDF が生成されなかった"; exit 1; }
echo "生成: ${BUILD}/report.pdf"
