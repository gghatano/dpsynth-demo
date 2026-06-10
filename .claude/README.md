# .claude/ — ドキュメント整理・レビュー・対応の知見とスキル集

このディレクトリは、本リポジトリ（実験デモ + 実証評価レポート + 公開サイト）の
構成・ドキュメンテーション・公開の知見を汎用化し、Claude Code のスキルとして
順次呼び出せる形に整理したもの。同型のリポジトリへそのまま転用できる。

## 構成

| パス | 役割 |
|---|---|
| `docs/documentation-conventions.md` | 構成規約の本体（ディレクトリ構成・記述の分離原則・公開/再現性/課題管理の原則） |
| `skills/doc-cycle/` | オーケストレーター。下記 4 スキルを順次実行し統合レポートを出す |
| `skills/report-review/` | 前提・結果・考察・課題の分離と数値整合のレビュー |
| `skills/repro-engineering-review/` | 再現手順・依存固定・パッチ・エンジニアリングノートのレビュー |
| `skills/related-info-review/` | 参考文献・出典タグ・上流情報・バックログの整理 |
| `skills/publish-check/` | content↔ビルダー↔htmls↔README の整合確認とビルド検証 |

## 使い方

- 全体点検: `/doc-cycle`（公開前・実験追記後・定期点検）
- 個別: `/report-review`・`/repro-engineering-review`・`/related-info-review`・`/publish-check`
- 各スキルは「軽微な問題は修正、主張・挙動に関わる指摘は報告」の方針で動く。

## 他リポジトリへの転用

1. `docs/documentation-conventions.md` の「このリポジトリでは〜」の具体例
   （ファイル名・スクリプト番号）を対象リポジトリに合わせて差し替える。
2. 各 SKILL.md の対象パス（`content/` 等）を読み替える。チェックリスト自体は汎用。
