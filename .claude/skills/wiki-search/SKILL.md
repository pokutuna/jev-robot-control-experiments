---
name: wiki-search
description: 作業や質問に wiki/ の知識を使うとき、wiki/ に書く前に既存ページを探すときに使う
---

# wiki の探し方

`wiki/index.md` を読み、次のコマンドで関連するページを探して、必要なページだけを開く。
語で探すときは、言い換えや略称も含める。

```sh
rg -l 'foo|bar' wiki/                          # 本文を語で探す
wiki/scripts/list-pages.sh                    # 全ページの title と description
wiki/scripts/list-pages.sh WORDS='foo|bar'    # title、description、tags を語で絞る
wiki/scripts/list-pages.sh TAG=cache          # タグで絞る
wiki/scripts/list-pages.sh DIR=wiki/research  # ディレクトリで絞る
wiki/scripts/list-pages.sh WITH_DEPRECATED=1  # 現行でないページも含める
wiki/scripts/list-tags.sh                     # 使われているタグと使用数
```

## 読み方

- `status: deprecated` のページは現行ではない。冒頭のリンクから後継ページを読む
- `sources/` のページは、取り込んだ時点の資料の内容である。正確な値や最新の内容が要るときは、`resource` にある元の資料を開いて確かめる

## 答えるとき

- wiki に書かれていることと、それ以外 (一般的な知識や推測) を分け、参照したページのパスを示す
