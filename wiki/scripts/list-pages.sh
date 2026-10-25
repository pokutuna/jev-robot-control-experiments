#!/usr/bin/env bash
set -euo pipefail

dir=wiki/
words=
tag=
with_deprecated=

for arg in "$@"; do
  case "$arg" in
    DIR=*) dir=${arg#DIR=} ;;
    WORDS=*) words=${arg#WORDS=} ;;
    TAG=*) tag=${arg#TAG=} ;;
    WITH_DEPRECATED=*) with_deprecated=${arg#WITH_DEPRECATED=} ;;
    -h|--help)
      echo "usage: $0 [DIR=<dir>] [WORDS=<regex>] [TAG=<tag>] [WITH_DEPRECATED=1]"
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      echo "usage: $0 [DIR=<dir>] [WORDS=<regex>] [TAG=<tag>] [WITH_DEPRECATED=1]" >&2
      exit 2
      ;;
  esac
done

# ページが 1 つも無いときの rg の終了コード 1 は正常とする
{ rg --files "$dir" -g '*.md' -g '!index.md' || [ $? -eq 1 ]; } | sort | while IFS= read -r file; do
  awk -v file="$file" -v words="$words" -v tag="$tag" -v with_deprecated="$with_deprecated" '
    FNR == 1 { in_frontmatter = ($0 == "---"); next }
    in_frontmatter && $0 == "---" {
      n = split(description, sentences, "。")
      summary = (n > 1 ? sentences[1] "。" : description)
      haystack = tolower(file " " title " " description " " tags)
      # deprecated のページは WITH_DEPRECATED=1 のときだけ、印を付けて出す
      if (status == "deprecated" && with_deprecated != "1") exit
      mark = (status != "" ? " [" status "]" : "")
      if (tag != "" && index("," tags ",", "," tag ",") == 0) exit
      if (words == "" || haystack ~ tolower(words))
        print file " | " title " | " summary mark
      exit
    }
    in_frontmatter && /^title:/ {
      title = $0
      sub(/^title:[[:space:]]*/, "", title)
    }
    in_frontmatter && /^description:/ {
      description = $0
      sub(/^description:[[:space:]]*/, "", description)
    }
    in_frontmatter && /^tags:/ {
      tags = $0
      sub(/^tags:[[:space:]]*/, "", tags)
      gsub(/[][[:space:]]/, "", tags)
    }
    in_frontmatter && /^status:/ {
      status = $0
      sub(/^status:[[:space:]]*/, "", status)
    }
  ' "$file"
done
