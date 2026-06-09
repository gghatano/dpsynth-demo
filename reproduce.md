# 再現手順ノート: 実験の再現

本ページは [実証評価レポート](index.html) の付随資料であり、レポート本体の実験結果を再現するための手順をまとめる。
環境構築は [環境構築ノート](setup.html)、API の利用方法は [API・CLI 利用ノート](usage.html) を参照のこと。

---

## 1. 一括再現

> **前提**: google/dpsynth は Windows ホイールの無い `python-dp` に依存し、Python は `>=3.12,<3.14`。
> **Linux もしくは WSL2 (Ubuntu) + Python 3.12** で実行する(Windows ネイティブ不可。詳細は [環境構築ノート](setup.html))。

```bash
# 1. リポジトリを取得
git clone https://github.com/gghatano/dpsynth-demo.git
cd dpsynth-demo

# 2. 環境構築（uv 導入・dpsynth クローン&パッチ・venv 作成・依存インストールまで一括）
bash scripts/setup_env.sh

# 3. 一括実行（データ取得 → DP 合成生成 → 評価 → レポート HTML 生成）
bash scripts/run_all.sh
```

実行後、`outputs/`(合成 CSV・`metrics.json`)、`figures/`(評価図)、`htmls/`(レポート HTML) が再生成される。

---

## 2. 個別実行

各段階を個別に動かす場合は以下のとおり。

```bash
.venv/bin/python scripts/00_prepare_data.py   # Adult データ取得・整形（data/adult.csv）
.venv/bin/python scripts/01_generate.py       # 合成データ生成（MST/AIM/INDEPENDENT + ε スイープ）
.venv/bin/python scripts/02_evaluate.py       # 1-way TVD / 相関誤差 / TSTR と図
.venv/bin/python scripts/10_experiments.py    # 追加実験 A/B/C
.venv/bin/python scripts/11_mia.py            # 追加実験D（MIA）
.venv/bin/python scripts/03_build_html.py     # htmls/ 配下の各 HTML を生成
```

---

## 3. 再現に必要な主要情報

| 項目 | 値 |
|---|---|
| Python | 3.12.3（WSL2 / Ubuntu 24.04） |
| 依存固定 | [`requirements.txt`](requirements.txt)（`mbi` はコミットハッシュまで固定） |
| 乱数シード | `seed=42`（合成元サンプリング・生成。主表） |
| 合成元サンプル | UCI Adult Income 48,842 行から 20,000 行を抽出 |
| 対象列(9 列) | 数値 `age`, `hours-per-week` ／ カテゴリ `workclass, education, marital-status, occupation, race, gender, income` |
| プライバシー予算 | 機構比較 `ε=1.0`、MST スイープ `ε=0.5/1.0/2.0/10.0`、`δ=1e-5` |
| 数値ビン数 | `numerical_bins=16` |

### 入力・出力ファイルの場所

- **入力データ**: `data/adult.csv`（`00_prepare_data.py` が取得・整形。git 管理外）
- **合成データ・指標**: `outputs/`（`synthetic_*.csv`, `metrics.json`, `run_meta.json`）
- **追加実験の指標**: `experiments/`（`metrics_experiments.json`, `metrics_mia.json`）
- **評価図**: `figures/`（`fig1_*.png` 〜 `fig4_*.png`, `expA_*.png` 〜 `expD_*.png`）
- **レポート HTML**: `htmls/`（`index.html` ほか）

---

## 4. 再現性に関する注意

レポート本体の主表は**単一シード(`seed=42`)・特定の依存バージョンでの代表的な 1 実行**である。
新規インストールでは `jax` / `mbi` 等のバージョン差で乱数列が変わり、**個々の数値は多少前後する**
(実測でも別環境で MST の平均 TVD が 0.098→0.109、INDEPENDENT の TSTR AUC が 0.433→0.546 などの変動を確認)。
ただし**定性的傾向(機構の優劣・トレードオフの向き)は再現される**。
厳密な数値比較を行う場合は依存バージョンを固定し、複数シードで平均を取ることを推奨する
（複数シードの mean±std は [追加実験](experiments.html) 実験Bを参照）。

---

## 5. GitHub Pages 公開

`REPORT.md` ほかの Markdown と `figures/` から、`scripts/03_build_html.py` が自己完結型 HTML を生成し、
GitHub Actions で Pages に公開する。DP 合成データの再生成は不要で、`markdown` だけでビルドされる。

- ワークフロー: [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)
- ローカル確認: `python -m http.server 8099 --directory htmls` → http://localhost:8099/

---

← [実証評価レポートに戻る](index.html)
