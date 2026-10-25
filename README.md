# template-llm-wiki

コーディングエージェントが、調べたこと、試した結果、ハマったこと、設計判断を `wiki/` に貯め、セッションを跨いで再利用するためのリポジトリのテンプレート。
`wiki/` は [OKF (Open Knowledge Format) v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) に適合する。

## 使い方

| やりたいこと | 頼み方の例 |
| --- | --- |
| 調べる | 「wiki に foo について何か書いてある?」 |
| 資料を取り込む | 「この URL を wiki に取り込んで」 |
| 結果を残す | 「今の調査結果を wiki に残して」 |
| 点検する | `/wiki-lint`、`/wiki-lint wiki/research` |

## 既存のリポジトリに導入する

1. `.claude/rules/`、`.claude/skills/`、`wiki/` をコピーする
2. `CLAUDE.md` の内容を、既存の `CLAUDE.md` に統合する
3. Claude Code 以外のエージェントも使うなら、`AGENTS.md` を `CLAUDE.md` への、`.agents/skills` を `../.claude/skills` への symlink にする
