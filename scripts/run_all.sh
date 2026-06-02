#!/usr/bin/env bash
# データ整形 → DP 合成生成 → 評価 → HTML ビルドを一括実行する。
# 事前に  bash scripts/setup_env.sh  を実行しておくこと。
#
# 使い方:  bash scripts/run_all.sh
set -euo pipefail

cd "$(dirname "$0")/.."
PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "ERROR: .venv が見つかりません。先に  bash scripts/setup_env.sh  を実行してください。" >&2
  exit 1
fi

echo "==> 00 データ整形（必要なら自動ダウンロード）"
"$PY" scripts/00_prepare_data.py

echo "==> 01 DP 合成データ生成（MST / AIM / INDEPENDENT + ε スイープ）"
"$PY" scripts/01_generate.py

echo "==> 02 品質評価（1-way TVD / 相関誤差 / TSTR）と図生成"
"$PY" scripts/02_evaluate.py

echo "==> 10 追加実験（numerical_bins / マルチシード / 2-way）"
"$PY" scripts/10_experiments.py

echo "==> 03 レポート HTML 生成（REPORT.html / EXPERIMENTS.html / _site/）"
"$PY" scripts/03_build_html.py

echo "完了: outputs/ と figures/ に結果、REPORT.html / EXPERIMENTS.html にレポートが生成されました。"
