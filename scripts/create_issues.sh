#!/usr/bin/env bash
# docs/BACKLOG.md の項目を GitHub Issue として一括作成する。
#
# 前提: gh が github.com に認証済みであること
#   gh auth login --hostname github.com
# 実行: bash scripts/create_issues.sh [owner/repo]
#   引数省略時は origin リモートのリポジトリに作成。
set -euo pipefail

REPO="${1:-}"
if [ -z "$REPO" ]; then
  REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
fi
if [ -z "$REPO" ]; then
  echo "ERROR: 対象リポジトリを特定できません。引数で owner/repo を指定してください。" >&2
  exit 1
fi
echo "target repo: $REPO"

# ラベルを用意（既存ならスキップ）
ensure_label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" 2>/dev/null || true; }
ensure_label enhancement     "a2eeef" "新機能・改善"
ensure_label reproducibility "0e8a16" "再現性"
ensure_label ci              "fbca04" "CI/自動化"
ensure_label upstream        "5319e7" "upstream への貢献"
ensure_label out-of-scope    "cccccc" "本デモのスコープ外"
ensure_label privacy         "d93f0b" "プライバシー評価"
ensure_label refactor        "c5def5" "リファクタリング"
ensure_label docs            "0075ca" "ドキュメント"

mk() {  # mk "title" "label,label" "body"
  echo "creating: $1"
  gh issue create --repo "$REPO" --title "$1" --label "$2" --body "$3"
}

mk "CI で clone-and-run 再現テストを回す" "enhancement,reproducibility,ci" \
"\`scripts/setup_env.sh\` + \`scripts/run_all.sh\`（軽量設定: 小サンプル・AIM省略など）を GitHub Actions で実行し、
clone してコマンド一発で再現できる状態を継続的に担保する。
- ubuntu-latest / Python 3.12 / requirements.txt 固定
- 生成→評価が exit 0 で完走することをスモークテスト"

mk "INDEPENDENT 機構の重複クリーク修正を upstream へ PR" "upstream" \
"\`patches/independent_dedup_cliques.patch\`（\`expand\` に渡すクリークの重複排除）を google/dpsynth に提案する。
新しい mbi では \`CliqueVector.expand\` が重複クリークで例外になるため、本デモではローカルパッチで回避している。
fork/パッチ依存をなくすため upstream 化したい。"

mk "Apache Beam (Scalable Pipeline API) のデモを追加" "enhancement,out-of-scope" \
"現状のデモは In-Memory DataFrame API のみ。\`dpsynth.data_generation.generate\` + \`pipeline_dp.BeamBackend\` を用いた
分散生成の最小サンプルと、小規模データでの妥当性確認を追加する。"

mk "数値列の離散化を改善（分位/対数ビン・列別ビン数）" "enhancement" \
"実験Aで確認した通り、\`hours-per-week\` 等の一点集中分布は TVD が高い。
列ごとに \`numerical_bins\` を変える・対数/分位ビンを使う等の戦略を検証し、数値忠実度を改善する。"

mk "経験的プライバシー評価（メンバーシップ推論攻撃）" "enhancement,privacy" \
"DP 保証を経験的に裏付けるため、合成データに対するメンバーシップ推論攻撃(MIA)を実装し、
ε を変えたときの攻撃成功率の変化を可視化する。"

mk "スクリプトを CLI 引数/設定ファイル化" "enhancement,refactor" \
"ε・対象列・サンプル数・機構などをハードコードせず、argparse もしくは設定ファイルで指定できるようにし、
他データセットへの再利用性を高める。"

mk "データ取得の固定化（チェックサム/ベンダリング）" "reproducibility" \
"\`00_prepare_data.py\` が参照する jbrownlee ミラーの消失リスクに備え、
SHA256 検証を入れる or データを同梱（ライセンス確認の上）するなどで取得を安定化する。"

mk "cross-attribute constraints のデモ" "enhancement,docs" \
"\`dpsynth.generate(cross_attribute_constraints=...)\` を用い、列間の整合（例: education と educational-num）を
保つ生成例を追加する。"

mk "複数シード平均を本体レポートにも反映" "docs,reproducibility" \
"実験Bの mean±std を要約として §6 に取り込み、単一シード依存への注意を本体側でも明確にする。"

echo "done."
