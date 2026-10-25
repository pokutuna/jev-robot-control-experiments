#!/usr/bin/env bash
set -euo pipefail

dir=wiki/

for arg in "$@"; do
  case "$arg" in
    DIR=*) dir=${arg#DIR=} ;;
    -h|--help)
      echo "usage: $0 [DIR=<dir>]"
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      echo "usage: $0 [DIR=<dir>]" >&2
      exit 2
      ;;
  esac
done

# frontmatter の tags を集計し、使用数の多い順に出す
# ページが 1 つも無いときの rg の終了コード 1 は正常とする
{ rg --files "$dir" -g '*.md' -g '!index.md' || [ $? -eq 1 ]; } | sort | tr '\n' '\0' | xargs -0 awk '
  FNR == 1 { in_frontmatter = ($0 == "---"); next }
  in_frontmatter && $0 == "---" { in_frontmatter = 0 }
  in_frontmatter && /^tags:/ {
    tags = $0
    sub(/^tags:[[:space:]]*/, "", tags)
    gsub(/[][[:space:]]/, "", tags)
    n = split(tags, list, ",")
    for (i = 1; i <= n; i++) if (list[i] != "") count[list[i]]++
  }
  END { for (t in count) printf "%4d %s\n", count[t], t }
' | sort -k1,1nr -k2
