# .claude/ — ドキュメント整理・レビュー・対応の知見とスキル集

このディレクトリは、本リポジトリ（実験デモ + 実証評価レポート + 公開サイト）の
構成・ドキュメンテーション・公開の知見を汎用化し、Claude Code のスキルとして
順次呼び出せる形に整理したもの。同型のリポジトリへそのまま転用できる。

## 構成

構成は「**プロセスごとのスキル + それらを順に呼び出すオーケストレーター**」の二層。
プロセススキルが手順とチェックリストの実体を持ち、オーケストレーターは順序・現在地判定・統合報告だけを担う。

| パス | 役割 |
|---|---|
| `docs/documentation-conventions.md` | 規約の本体（構成・記述の分離原則・実験の計画/実行・公開/再現性/課題管理の原則） |
| **サブエージェント（モデルティア制: 計画=上位 / レビュー=中位 / 実行=下位）** | |
| `agents/planner.md` | 計画・調査・issue 起案担当（**上位ティア**）。編集は Markdown に限る |
| `agents/reviewer.md` | レビュー担当（**中位ティア**）。チェックリスト実行・指摘洗い出し・軽微修正 |
| `agents/implementer.md` | 実行・実装担当（**下位ティア**）。1 worktree = 1 issue 単位、実装は TDD |
| **オーケストレーター** | |
| `skills/research-cycle/` | 全体統括。①骨子→②計画→③実行（反復）→④整理 の現在地を判定して順に進める |
| `skills/doc-cycle/` | 整理系の統括。④〜⑦ を順次実行し統合レポートを出す（research-cycle の最終段） |
| **プロセス: 作成系（骨子 → 計画 → 実行）** | |
| `skills/report-skeleton/` | ① レポート骨子の設計。章立て・主張・必要な実験の抽出（実験より先に書く） |
| `skills/experiment-plan/` | ② 実験計画。既存研究準拠の指標・公平な比較条件・業務シナリオ → `docs/plans/` |
| `skills/experiment-run/` | ③ 実験実行。uv 固定環境・シード規約・結果のレポート反映・問題の即時記録 |
| **プロセス: 整理系（レビュー → 公開）** | |
| `skills/report-review/` | ④ 前提・結果・考察・課題の分離と数値整合のレビュー |
| `skills/repro-engineering-review/` | ⑤ 再現手順・依存固定・パッチ・エンジニアリングノートのレビュー |
| `skills/related-info-review/` | ⑥ 参考文献・出典タグ・上流情報・バックログの整理 |
| `skills/publish-check/` | ⑦ content↔ビルダー↔htmls↔README の整合確認とビルド検証 |

## 使い方

- 全体を進める / 現在地を確認する: `/research-cycle`（①→②→③→④ を判定して順次実行）
- 整理・点検のみ: `/doc-cycle`（公開前・実験追記後・定期点検）
- 個別プロセスの実行: `/report-skeleton`・`/experiment-plan`・`/experiment-run`・
  `/report-review`・`/repro-engineering-review`・`/related-info-review`・`/publish-check`
- 各スキルは「軽微な問題は修正、主張・挙動に関わる指摘は報告」の方針で動く。

## 他リポジトリへの転用

1. `docs/documentation-conventions.md` の「このリポジトリでは〜」の具体例
   （ファイル名・スクリプト番号）を対象リポジトリに合わせて差し替える。
2. 各 SKILL.md の対象パス（`content/` 等）を読み替える。チェックリスト自体は汎用。
