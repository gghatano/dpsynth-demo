# DPSynth デモ & レポート

[google/dpsynth](https://github.com/google/dpsynth)(差分プライバシーを満たす合成テーブルデータ生成ライブラリ)を
日本語で解説し、UCI Adult Income データで実際に動かした**デモ**と**レポート**をまとめたリポジトリです。

> **⚠️ スコープ**: 本デモ・実験は **In-Memory DataFrame API(`dpsynth.generate`、単一マシン・Pandas)のみ**を対象とします。
> **Apache Beam を用いた Scalable Pipeline API(分散処理)は対象外**です(機能紹介はしますが実行・評価はしていません)。

- 解説・利用例・メリデメ・デモ結果の本体 → **[REPORT.md](REPORT.md)** / 公開サイト **https://gghatano.github.io/dpsynth-demo/**

## クイックスタート（clone してコマンド実行で再現）

> **前提**: DPSynth は Windows ホイールの無い `python-dp` に依存し、Python は `>=3.12,<3.14` が必要です。
> **Linux もしくは WSL2 (Ubuntu) + Python 3.12** で実行してください（Windows ネイティブ不可）。
> Windows の方は WSL を起動し、その中で以下を実行します。

```bash
git clone https://github.com/gghatano/dpsynth-demo.git
cd dpsynth-demo

bash scripts/setup_env.sh   # uv 導入・dpsynth クローン&パッチ・venv 作成・依存インストール
bash scripts/run_all.sh     # データ取得 → DP 合成生成 → 評価 → レポート HTML 生成
```

実行後、`outputs/`(合成 CSV・`metrics.json`)、`figures/`(評価図)、`REPORT.html` が再生成されます。
所要時間の目安は合計 5〜10 分程度(初回は依存インストール分が加算)。

### 個別実行

```bash
.venv/bin/python scripts/00_prepare_data.py   # Adult データ取得・整形（data/adult.csv、無ければ自動DL）
.venv/bin/python scripts/01_generate.py       # 合成データ生成（MST/AIM/INDEPENDENT + ε スイープ）
.venv/bin/python scripts/02_evaluate.py       # 1-way TVD / 相関誤差 / TSTR と図生成
.venv/bin/python scripts/03_build_html.py     # REPORT.html / _site/index.html を生成
```

## 構成

```
dpsynth-demo/
├── README.md              … 本ファイル（再現手順）
├── REPORT.md / .html      … 解説・利用例・メリデメ・デモ結果レポート
├── scripts/
│   ├── setup_env.sh       … 環境構築（uv・dpsynth クローン&パッチ・venv・依存）一括
│   ├── run_all.sh         … 00→03 を一括実行
│   ├── 00_prepare_data.py … Adult データ取得・ヘッダー付与・整形
│   ├── 01_generate.py     … DPSynth で DP 合成データを生成（MST/AIM/INDEPENDENT + ε スイープ）
│   ├── 02_evaluate.py     … 1-way TVD / 相関誤差 / TSTR で品質評価し図を出力
│   └── 03_build_html.py   … REPORT.md → 自己完結 HTML / Pages 用 _site を生成
├── patches/               … dpsynth への最小修正パッチ（INDEPENDENT 機構の重複クリーク対策）
├── data/                  … 入力データ（自動取得、git 管理外）
├── outputs/               … 合成 CSV・metrics.json・run_meta.json
├── figures/               … 評価図 PNG
└── src/                   … dpsynth のクローン（setup_env.sh が取得・パッチ。git 管理外）
```

## 動作環境（重要）

DPSynth は `pipeline-dp` → `python-dp`(Google C++ 差分プライバシーライブラリ)に依存します。
**`python-dp` には Windows 用ホイールが存在せず**(Linux / macOS のみ)、Python は `>=3.12,<3.14` が必要です。
そのため本デモは **WSL2 (Ubuntu 24.04) + Python 3.12 + uv** で実行しています。

`scripts/setup_env.sh` が以下の上流対処を自動で行います（手動で行う場合の内訳）:

- `pyproject.toml` から `tensorflow` を除外（In-Memory デモには不要）
- サブパッケージ(`pipeline_transformations` 等)へ `__init__.py` を補完（パッケージング漏れ対策）
- INDEPENDENT 機構の重複クリーク・バグを [`patches/independent_dedup_cliques.patch`](patches/independent_dedup_cliques.patch) で 1 行修正

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
