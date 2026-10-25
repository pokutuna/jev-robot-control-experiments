---
name: wiki-lint
description: wiki/ を点検し、ページ間の矛盾、古い記述、足りないページやリンクと、その直し方の案を報告する
disable-model-invocation: true
argument-hint: "[対象のディレクトリまたはファイル]"
---

# wiki の点検

対象: $ARGUMENTS (指定が無ければ `wiki/` 全体)

ファイルは書き換えない。

## 1. 機械的な点検

次のコマンドの出力を候補とし、開いて確かめる。

```sh
t='$ARGUMENTS'; t=${t:-wiki/}
# type、title、description のどれかが無いページ
for k in type title description; do rg --files-without-match "^$k: *\S" "$t" -g '*.md' -g '!index.md'; done | sort -u
# リンク先が存在しない相対リンク
rg -o --no-heading --no-line-number '\]\(([^)#: ]+)(#[^)]*)?\)' -r '$1' "$t" -g '*.md' |
  while IFS=: read -r file link; do [ -e "$(dirname "$file")/$link" ] || echo "$file -> $link"; done
# タグと使用数 (表記ゆれや意味の重なるタグ、1 ページにしか付いていないタグを探す)
wiki/scripts/list-tags.sh
```

## 2. 内容の点検

wiki 全体を一度に読まず、関連するページの組ごとに読んで比べる。組は、同じタグ (`wiki/scripts/list-pages.sh TAG=`)、
title や description に共通する語 (`wiki/scripts/list-pages.sh WORDS=`)、ページ間のリンクで作る。
ページの新しさは、`notes/` はファイル名の日付、それ以外は `git log -1 --format=%cs -- <file>` で比べる。

組ごとに次を確かめる。

- 同じ事柄を扱う別々のページ
- 同じ事柄について食い違う記述。出典や条件の違いが書かれていて説明がつくものは除く
- 組の中のより新しいページ (取り込んだ資料、作業の結果) と比べて、古くなった記述
- 関連するのに、互いにリンクしていないページ
- 組のページを読んでも答えられない、調べるべき問い。Web 検索などで埋められそうなら、探すべき資料も挙げる
- 複数のページに出てくるのに、専用のページが無い概念。`wiki/scripts/list-pages.sh WORDS=` で専用のページが無いことを確かめる

## 3. 報告

確かめた結果だけを、ファイルパス、問題、直し方の案と共に報告する。
