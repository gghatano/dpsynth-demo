# .claude/ — ドキュメント整理・レビュー・対応の知見とスキル集

このディレクトリは、本リポジトリ（実験デモ + 実証評価レポート + 公開サイト）の
構成・ドキュメンテーション・公開の知見を汎用化し、Claude Code のスキルとして
順次呼び出せる形に整理したもの。同型のリポジトリへそのまま転用できる。

## 構成

| パス | 役割 |
|---|---|
| `docs/documentation-conventions.md` | 規約の本体（構成・記述の分離原則・実験の計画/実行・公開/再現性/課題管理の原則） |
| **作成系（骨子 → 計画 → 実行）** | |
| `skills/report-skeleton/` | レポート骨子の設計。章立て・主張・必要な実験の抽出（実験より先に書く） |
| `skills/experiment-plan/` | 実験計画。既存研究準拠の指標・公平な比較条件・業務シナリオ → `docs/plans/` |
| `skills/experiment-run/` | 実験実行。uv 固定環境・シード規約・結果のレポート反映・問題の即時記録 |
| **整理系（レビュー → 公開）** | |
| `skills/doc-cycle/` | オーケストレーター。下記 4 スキルを順次実行し統合レポートを出す |
| `skills/report-review/` | 前提・結果・考察・課題の分離と数値整合のレビュー |
| `skills/repro-engineering-review/` | 再現手順・依存固定・パッチ・エンジニアリングノートのレビュー |
| `skills/related-info-review/` | 参考文献・出典タグ・上流情報・バックログの整理 |
| `skills/publish-check/` | content↔ビルダー↔htmls↔README の整合確認とビルド検証 |

## 使い方

標準ライフサイクル（新しい評価対象・大きな実験追加のとき）:

```
/report-skeleton → /experiment-plan → /experiment-run（実験ごとに繰り返し）→ /doc-cycle
```

- 全体点検のみ: `/doc-cycle`（公開前・実験追記後・定期点検）
- 個別: `/report-review`・`/repro-engineering-review`・`/related-info-review`・`/publish-check`
- 各スキルは「軽微な問題は修正、主張・挙動に関わる指摘は報告」の方針で動く。

## 他リポジトリへの転用

1. `docs/documentation-conventions.md` の「このリポジトリでは〜」の具体例
   （ファイル名・スクリプト番号）を対象リポジトリに合わせて差し替える。
2. 各 SKILL.md の対象パス（`content/` 等）を読み替える。チェックリスト自体は汎用。
