#!/usr/bin/env bash
# DPSynth デモの実行環境を構築する（Linux / WSL2 用）。
#
# google/dpsynth は Windows ホイールの無い python-dp に依存し、Python >=3.12,<3.14 が必要。
# このスクリプトは Linux/WSL 上で:
#   1. uv を導入（無ければ）
#   2. dpsynth を src/ にクローン
#   3. In-Memory デモに不要な tensorflow を除外
#   4. パッケージング漏れ（サブパッケージの __init__.py 欠落）を補完
#   5. INDEPENDENT 機構の上流バグを patches/ の差分で修正
#   6. Python 3.12 の venv を作成し、dpsynth と評価用ライブラリをインストール
#
# 使い方:  bash scripts/setup_env.sh
set -euo pipefail

cd "$(dirname "$0")/.."          # リポジトリ直下へ
ROOT="$(pwd)"
echo "[setup] repo root: $ROOT"

# 1. uv
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] installing uv ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"
uv --version

# 2. clone dpsynth
if [ ! -d src ]; then
  echo "[setup] cloning google/dpsynth -> src/"
  git clone --depth 1 https://github.com/google/dpsynth.git src
else
  echo "[setup] src/ already exists, skipping clone"
fi

# 3. tensorflow を除外（In-Memory デモには不要・重い）
sed -i '/"tensorflow",/d' src/pyproject.toml

# 4. サブパッケージに __init__.py を補完（無いと import 不能）
#    上流の構成変化で一部ディレクトリが存在しないことがあるため、存在するものだけ補完する。
for d in pipeline_transformations dataset_descriptors eval local_mode bin; do
  if [ -d "src/dpsynth/$d" ]; then
    touch "src/dpsynth/$d/__init__.py"
  fi
done

# 5. INDEPENDENT 機構の重複クリーク修正（未適用のときだけ当てる：冪等）
if grep -q 'expand(\[m.clique for m in measurements\])' \
     src/dpsynth/discrete_mechanisms/independent.py; then
  echo "[setup] applying patches/independent_dedup_cliques.patch"
  git -C src apply ../patches/independent_dedup_cliques.patch
else
  echo "[setup] independent.py already patched, skipping"
fi

# 6. venv + install
echo "[setup] creating venv (.venv) with Python 3.12"
uv venv --python 3.12 .venv

if [ -f requirements.txt ]; then
  # 再現性重視: ロックファイルで全依存をバージョン固定 → dpsynth 本体は --no-deps で追加
  echo "[setup] installing pinned deps from requirements.txt (reproducible)"
  uv pip install --python .venv -r requirements.txt
  echo "[setup] installing dpsynth (patched src, --no-deps)"
  uv pip install --python .venv --no-deps ./src
else
  # フォールバック: ロックファイルが無い場合は最新解決（バージョンは固定されない）
  echo "[setup] requirements.txt not found; installing latest (NOT pinned)"
  uv pip install --python .venv ./src \
    matplotlib scikit-learn tqdm scipy networkx markdown pygments
fi

echo "[setup] done. next:  bash scripts/run_all.sh"
