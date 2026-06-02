# DPSynth デモ & レポート

[google/dpsynth](https://github.com/google/dpsynth)(差分プライバシーを満たす合成テーブルデータ生成ライブラリ)を
日本語で解説し、UCI Adult Income データで実際に動かした**デモ**と**レポート**をまとめたリポジトリです。

- 解説・利用例・メリデメ・デモ結果の本体 → **[REPORT.md](REPORT.md)** / **[REPORT.html](REPORT.html)**

## 構成

```
dpsynth-demo/
├── README.md              … 本ファイル（再現手順）
├── REPORT.md / .html      … 解説・利用例・メリデメ・デモ結果レポート
├── scripts/
│   ├── 00_prepare_data.py … Adult データにヘッダー付与・整形
│   ├── 01_generate.py     … DPSynth で DP 合成データを生成（MST/AIM/INDEPENDENT + ε スイープ）
│   └── 02_evaluate.py     … 1-way TVD / 相関誤差 / TSTR で品質評価し図を出力
├── data/                  … 入力データ（adult.csv ほか）
├── outputs/               … 合成 CSV・metrics.json・run_meta.json
├── figures/               … 評価図 PNG
└── src/                   … dpsynth のクローン（インストール時に最小パッチ済み）
```

## 動作環境（重要）

DPSynth は `pipeline-dp` → `python-dp`(Google C++ 差分プライバシーライブラリ)に依存します。
**`python-dp` には Windows 用ホイールが存在せず**(Linux / macOS のみ)、Python は `>=3.12,<3.14` が必要です。
そのため本デモは **WSL2 (Ubuntu 24.04) + Python 3.12 + uv** で実行しています。

### セットアップ（WSL 内）

```bash
# 1. uv 導入
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. リポジトリ取得 & 軽量化（In-Memory デモには tensorflow 不要なので除外）
git clone --depth 1 https://github.com/google/dpsynth.git src
sed -i '/"tensorflow",/d' src/pyproject.toml
# サブパッケージに __init__.py が無いため補う（パッケージング漏れ対策）
touch src/dpsynth/{pipeline_transformations,dataset_descriptors,eval,local_mode,bin}/__init__.py

# 3. venv 作成 & インストール
uv venv --python 3.12 .venv
uv pip install --python .venv ./src matplotlib scikit-learn tqdm scipy networkx
```

> 補足: 本デモでは INDEPENDENT 機構の `expand` に重複クリークが渡る上流バグを 1 行修正しています
> （詳細は REPORT.md、差分は [`patches/independent_dedup_cliques.patch`](patches/independent_dedup_cliques.patch)）。
> 適用例: `git -C src apply ../patches/independent_dedup_cliques.patch`

### 実行

```bash
.venv/bin/python scripts/00_prepare_data.py   # データ整形
.venv/bin/python scripts/01_generate.py       # 合成データ生成
.venv/bin/python scripts/02_evaluate.py       # 評価 & 図生成
.venv/bin/python scripts/03_build_html.py     # REPORT.html / _site/index.html を生成
```

## GitHub Pages 公開

`REPORT.md` と `figures/` から自己完結型 HTML を生成し、GitHub Actions で Pages に公開します。
DP 合成データの再生成は不要で、`markdown` だけで数十秒でビルドされます。

- ワークフロー: [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)
- 公開物: `scripts/03_build_html.py` が生成する `_site/index.html`（目次サイドバー + 図埋め込み）

### 有効化手順（初回のみ）

1. GitHub で本リポジトリの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** に設定。
2. `main` ブランチに push（または Actions タブから **Deploy report to GitHub Pages** を手動実行）。
3. 完了後、`https://gghatano.github.io/dpsynth-demo/` で公開されます。

ローカル確認: `python -m http.server 8099 --directory _site` → http://localhost:8099/

## データ出典

UCI Adult / "Census Income" データセット（48,842 行）。
本デモは [jbrownlee/Datasets](https://raw.githubusercontent.com/jbrownlee/Datasets/master/adult-all.csv) のミラーを利用。
