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
#    再現性（Issue #15）: upstream を特定コミットに固定できるよう DPSYNTH_REF を用意する。
#    例)  DPSYNTH_REF=<commit-sha> bash scripts/setup_env.sh
#    未指定なら main の最新を取得し、解決された SHA を src_commit.txt に記録する
#    （固定環境＝WSL を確立する際は、この SHA を控えて以後 DPSYNTH_REF に渡すこと）。
DPSYNTH_REF="${DPSYNTH_REF:-}"
if [ ! -d src ]; then
  if [ -n "$DPSYNTH_REF" ]; then
    echo "[setup] cloning google/dpsynth@$DPSYNTH_REF -> src/"
    git clone https://github.com/google/dpsynth.git src
    git -C src checkout "$DPSYNTH_REF"
  else
    echo "[setup] cloning google/dpsynth (latest main) -> src/  ※再現性のため DPSYNTH_REF の指定を推奨"
    git clone --depth 1 https://github.com/google/dpsynth.git src
  fi
else
  echo "[setup] src/ already exists, skipping clone"
  if [ -n "$DPSYNTH_REF" ]; then
    # 既存 src/ でも DPSYNTH_REF が指定されたら必ずその版へ合わせる（B3: 固定の取りこぼし防止）
    cur="$(git -C src rev-parse HEAD 2>/dev/null || echo unknown)"
    if [ "$cur" != "$DPSYNTH_REF" ]; then
      echo "[setup] re-pinning existing src/ to DPSYNTH_REF=$DPSYNTH_REF (was $cur)"
      # 既存 src/ は sed/パッチで作業ツリーが汚れているため、checkout 前にクリーン化する。
      # tensorflow 除去・INDEPENDENT パッチは後続ステップ(3-5)が冪等に再適用する。
      git -C src reset --hard
      git -C src fetch --depth 1 origin "$DPSYNTH_REF" 2>/dev/null \
        || git -C src fetch origin
      git -C src checkout "$DPSYNTH_REF"
    fi
  fi
fi
# 実際に取得した upstream コミットを記録（プロビナンス）
git -C src rev-parse HEAD > src_commit.txt 2>/dev/null \
  && echo "[setup] upstream dpsynth commit = $(cat src_commit.txt) (recorded in src_commit.txt)"

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
