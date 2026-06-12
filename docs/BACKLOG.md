# バックログ（GitHub Issue 化候補）

本デモ・レポートで「今後やると良い」と判断した項目。`scripts/create_issues.sh` で GitHub Issue として一括登録できます。

| # | タイトル | ラベル | 概要 |
|---|---|---|---|
| 1 | CI で clone-and-run 再現テストを回す | `enhancement` `reproducibility` `ci` | `setup_env.sh`+`run_all.sh`(軽量設定)を GitHub Actions で定期実行し、再現性を継続的に担保 |
| 2 | INDEPENDENT 機構の重複クリーク修正を upstream へ PR | `upstream` | `patches/independent_dedup_cliques.patch` を google/dpsynth に提案（手元 fork 依存をなくす） |
| 3 | Apache Beam (Scalable Pipeline API) のデモを追加 | `enhancement` `out-of-scope` | 現在 In-Memory のみ。Beam バックエンドでの分散生成サンプルと小規模検証を追加 |
| 4 | 数値列の離散化を改善（分位/対数ビン・列別ビン数） | `enhancement` | ✅一部対応: 汎用ガイドライン(分位ビン+n·εに応じたビン数)を EXPERIMENTS に追記。残: `dp_auto_discretizer` の活用 |
| 5 | 経験的プライバシー評価（メンバーシップ推論攻撃） | `enhancement` `privacy` | ✅対応済: 実験D(MIA)を追加。非DPコピー0.89 vs DP合成≈0.51。残: シャドウモデル型など強い攻撃 |
| 6 | スクリプトを CLI 引数/設定ファイル化 | `enhancement` `refactor` | ε・列・サンプル数・機構をハードコードせず引数化（再利用性向上） |
| 7 | データ取得の固定化（チェックサム/ベンダリング） | `reproducibility` | jbrownlee ミラーの消失リスクに備え、SHA256 検証 or データ同梱を検討 |
| 8 | cross-attribute constraints のデモ | `enhancement` `docs` | 列間制約（例: education と educational-num の整合）を使った生成例を追加 |
| 9 | 複数シード平均を本体レポートにも反映 | `docs` `reproducibility` | 実験Bの mean±std を要約として §6 に取り込み、単一シード依存の注意を強化 |
| 10 | AIM の ε スイープ実測を取得（method-aim §7） | `enhancement` `reproducibility` | ✅対応済(Issue #13): memlock 制約のないローカル WSL2 で ε=0.5/1.0/2.0/10.0 を完走取得し §7 を確定（`experiments/aim_eps_sweep_local.json`・`scripts/12_aim_eps_sweep.py`・`figures/fig5_*`）。所見=単一シードでは分散支配で ε トレンド判定不能 → Issue #14 へ |
| 11 | AIM ε スイープを複数シードで再評価 | `enhancement` `reproducibility` | 単一シードの §7 スイープは run-to-run 分散（実験B: TSTR ±0.153）に支配され ε トレンドが判定不能。複数シードで mean±std を取り ε 依存と分散を分離。あわせて `max_rounds`/`max_model_size` の感度も評価（Issue #14・#13 残課題①②） |
| 12 | 環境間のベースライン再現性を担保（数値差の定量化/固定環境での全再生成） | `reproducibility` | ローカル WSL2 再実行で `outputs/metrics.json` がコミット済み値と乖離（例: aim_eps1 相関誤差 0.226→0.007・TSTR 0.768→0.649）。jaxlib/XLA の数値挙動差が原因。固定環境(コンテナ)での全再生成か、許容差の明記が必要（Issue #15・#13 残課題③・BACKLOG #1 と関連） |

> ラベルは `create_issues.sh` が存在しなければ自動作成します（既存なら無視）。
