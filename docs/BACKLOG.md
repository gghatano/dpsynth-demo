# バックログ（GitHub Issue 化候補）

本デモ・レポートで「今後やると良い」と判断した項目。`scripts/create_issues.sh` で GitHub Issue として一括登録できます。

| # | タイトル | ラベル | 概要 |
|---|---|---|---|
| 1 | CI で clone-and-run 再現テストを回す | `enhancement` `reproducibility` `ci` | `setup_env.sh`+`run_all.sh`(軽量設定)を GitHub Actions で定期実行し、再現性を継続的に担保 |
| 2 | INDEPENDENT 機構の重複クリーク修正を upstream へ PR | `upstream` | `patches/independent_dedup_cliques.patch` を google/dpsynth に提案（手元 fork 依存をなくす） |
| 3 | Apache Beam (Scalable Pipeline API) のデモを追加 | `enhancement` `out-of-scope` | 現在 In-Memory のみ。Beam バックエンドでの分散生成サンプルと小規模検証を追加 |
| 4 | 数値列の離散化を改善（分位/対数ビン・列別ビン数） | `enhancement` | `hours-per-week` 等の一点集中分布で TVD が高い。列ごとのビン戦略を検証（実験Aの発展） |
| 5 | 経験的プライバシー評価（メンバーシップ推論攻撃） | `enhancement` `privacy` | DP 保証を経験的に裏付ける MIA を追加し、ε とリスクの関係を可視化 |
| 6 | スクリプトを CLI 引数/設定ファイル化 | `enhancement` `refactor` | ε・列・サンプル数・機構をハードコードせず引数化（再利用性向上） |
| 7 | データ取得の固定化（チェックサム/ベンダリング） | `reproducibility` | jbrownlee ミラーの消失リスクに備え、SHA256 検証 or データ同梱を検討 |
| 8 | cross-attribute constraints のデモ | `enhancement` `docs` | 列間制約（例: education と educational-num の整合）を使った生成例を追加 |
| 9 | 複数シード平均を本体レポートにも反映 | `docs` `reproducibility` | 実験Bの mean±std を要約として §6 に取り込み、単一シード依存の注意を強化 |

> ラベルは `create_issues.sh` が存在しなければ自動作成します（既存なら無視）。
