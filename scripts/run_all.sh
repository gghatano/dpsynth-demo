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

echo "==> 10e 追加実験E（マルチシード ε スイープ: まず軽量プリラン → 本実行）"
echo "    軽量プリラン（ε=1,10・各2シード）で疎通確認"
EXP_E_FAST=1 "$PY" scripts/10_experiments.py e
echo "    本実行（ε=0.5/1/2/10・MST/IND 10シード, AIM 5シード）— 時間がかかります"
"$PY" scripts/10_experiments.py e

echo "==> 11 追加実験D（メンバーシップ推論攻撃 MIA）"
"$PY" scripts/11_mia.py

echo "==> 03 レポート HTML 生成（REPORT.html / EXPERIMENTS.html / _site/）"
"$PY" scripts/03_build_html.py

echo "完了: outputs/ と figures/ に結果、REPORT.html / EXPERIMENTS.html にレポートが生成されました。"
