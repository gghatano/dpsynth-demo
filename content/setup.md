# 環境構築ノート: 依存関係とセットアップ

本ページは [実証評価レポート](index.html) の付随資料であり、DPSynth デモを再現するための環境構築手順をまとめる。
研究上の知見そのものはレポート本体を参照のこと。本ページはエンジニアリング上の手順に限定する。

---

## 1. 動作環境の前提

DPSynth は `pipeline-dp` → `python-dp`(Google C++ 差分プライバシーライブラリ)に依存する。
**`python-dp` には Windows 用ホイールが存在せず**(Linux / macOS のみ)、Python は `>=3.12,<3.14` が必要である。
そのため本デモは **WSL2 (Ubuntu 24.04) + Python 3.12 + uv** で実行している。

> Windows ホストの場合は WSL を起動し、その中で以下を実行する。Windows ネイティブでは動作しない。

| 項目 | 値 |
|---|---|
| OS | Linux もしくは WSL2 (Ubuntu 24.04) |
| Python | 3.12（`>=3.12,<3.14`） |
| パッケージ管理 | [uv](https://github.com/astral-sh/uv) |
| 再現性の要 | [`requirements.txt`](requirements.txt)（全推移的依存をバージョン固定） |

---

## 2. 一括セットアップ

リポジトリ直下で次を実行すると、uv の導入・dpsynth のクローンとパッチ・venv 作成・依存インストールまでを一括で行う。

```bash
git clone https://github.com/gghatano/dpsynth-demo.git
cd dpsynth-demo
bash scripts/setup_env.sh
```

`scripts/setup_env.sh` の処理内容は以下のとおり。

1. **uv を導入**（未インストールの場合）。
2. **dpsynth を `src/` にクローン**（`git clone --depth 1 https://github.com/google/dpsynth.git src`）。
3. **`tensorflow` を除外**（`pyproject.toml` から削除。In-Memory デモには不要で重い）。
4. **サブパッケージへ `__init__.py` を補完**（`pipeline_transformations` 等。無いと import 不能）。
5. **INDEPENDENT 機構の上流バグを修正**（`patches/independent_dedup_cliques.patch` を適用。詳細は [実装ノート](engineering-notes.html)）。
6. **Python 3.12 の venv を作成し、固定依存と dpsynth 本体をインストール**。

---

## 3. 再現性のための依存固定

`setup_env.sh` は [`requirements.txt`](requirements.txt) で全推移的依存をバージョン固定してインストールする。
`jax` / `mbi` / `numpy` 等のバージョン差は乱数列の揺れを生むため、再現性の観点から固定が重要である。`mbi` はコミットハッシュまで固定している。生成元は Python 3.12.3 / WSL2 である。

```bash
uv pip install -r requirements.txt        # 固定依存
uv pip install --no-deps ./src            # dpsynth 本体（patches 適用済み）
```

---

## 4. 上流ライブラリへの対処（手動で行う場合の内訳）

`setup_env.sh` が自動で行う上流対処を、手動で行う場合のために明記する。背景・原因の詳細は [実装ノート](engineering-notes.html) を参照。

- `pyproject.toml` から `tensorflow` を除外（In-Memory デモには不要）。
- サブパッケージ(`pipeline_transformations` 等)へ `__init__.py` を補完（パッケージング漏れ対策）。
- INDEPENDENT 機構の重複クリーク・バグを [`patches/independent_dedup_cliques.patch`](patches/independent_dedup_cliques.patch) で 1 行修正。

---

## 5. 次のステップ

環境構築が完了したら、[再現手順ノート](reproduce.html) に従って実験を実行する。
API の利用方法は [API・CLI 利用ノート](usage.html) を参照のこと。

← [実証評価レポートに戻る](index.html)
