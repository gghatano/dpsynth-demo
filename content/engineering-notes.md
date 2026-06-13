# 実装ノート: 実行時に遭遇した問題と対応

本ページは [実証評価レポート](index.html) の付随資料であり、本デモを「再現可能に動作する」状態にするまでに遭遇した
実装・運用上の問題と、その対応を記録する。これらはライブラリの成熟度を示す一次情報であり、
研究上の知見そのものではなくエンジニアリング上の記録として整理する。

> 🔎 本ページは全体が本デモの実行で得た一次情報である。該当コード位置は示すが、ドキュメントに記載された仕様ではない。
> 出典タグ **[n]** はレポート本体の第10章「参考文献」に対応する。

---

## 1. 遭遇した問題と対応

| # | 問題 | 原因 | 対応 |
|---|---|---|---|
| 1 | Windows で `python-dp` が導入できない | `pipeline-dp` の依存 `python-dp`(Google C++ DP ライブラリ)が Linux/macOS ホイールのみ | **WSL2 (Ubuntu) + Python 3.12** に切り替えて解決 |
| 2 | `pip install` 後に import できない | ルート以外のサブパッケージに `__init__.py` が無く、`dpsynth.pipeline_transformations` 等が同梱されない | 各ディレクトリに `__init__.py` を補って解決 |
| 3 | 未宣言の依存 | `tqdm` が `dependencies` に無く ImportError | 追加インストールで解決 |
| 4 | INDEPENDENT 機構のクラッシュ | `generate()` が常に渡す 1-way 測定値 [\[11\]](index.html#ref11) の上に、INDEPENDENT が同じ 1-way を再測定する [\[12\]](index.html#ref12) ため、`mbi` 新版の `CliqueVector.expand` が「Cliques must be unique」で例外 | `expand` へ渡すクリーク列を重複排除する **1 行修正**で解決（予算消費は不変） |
| 5 | 小さい ε での会計破綻 | ε=0.1 でノイズ較正の区間探索が失敗(`NoBracketIntervalFoundError`) | スイープを ε≥0.5 に調整 |
| 6 | AIM の ε スイープが JIT で失敗 | 一部リモート環境の `RLIMIT_MEMLOCK`(`ulimit -l` 8192KB・引き上げ不可)上限で、AIM（ε≥0.5 で大きい MRF カーネル）の XLA/LLVM JIT がセクションメモリ確保に失敗（`Cannot allocate memory`）。ε ごとのプロセス分離・`XLA_FLAGS` 緩和でも再現 | **memlock 制約のないローカル(WSL2・`ulimit -l`=65536KB)で 4 本を完走**して取得（ε=0.5/1.0/2.0/10.0、生成 242/73/350/458s）。[Issue #13](https://github.com/gghatano/dpsynth-demo/issues/13) |

---

## 2. 各問題の詳細

### 問題1: プラットフォーム制約

`pipeline-dp` → `python-dp` の依存連鎖により、Windows ネイティブ環境では動作しない。
Python のバージョン制約も `>=3.12,<3.14` と狭い。対処として WSL2 上に Python 3.12 環境を構築した（[環境構築ノート](setup.html)）。

### 問題2: パッケージング漏れ

`src/dpsynth/` 配下の一部サブパッケージ（`pipeline_transformations`, `dataset_descriptors`, `eval`, `local_mode`, `bin`）に
`__init__.py` が存在せず、インストール後に import できない。`setup_env.sh` が各ディレクトリへ `__init__.py` を補完する。

### 問題3: 未宣言依存

`tqdm` が `pyproject.toml` の依存に含まれていないため、実行時に ImportError となる。固定依存（[`requirements.txt`](requirements.txt)）側で補っている。

### 問題4: INDEPENDENT 機構の重複クリーク

これは本デモで最も典型的な「研究コードと依存ライブラリの版ずれ」事例である。
`generate()` は常に 1-way 測定値を機構へ渡す [\[11\]](index.html#ref11) が、INDEPENDENT は内部で同じ 1-way を再測定する [\[12\]](index.html#ref12)。
結果として `mbi` 新版の `CliqueVector.expand` が重複クリークを検出して例外（「Cliques must be unique」）を投げる。
対処は [`patches/independent_dedup_cliques.patch`](patches/independent_dedup_cliques.patch) による 1 行修正で、
`expand` へ渡すクリーク列を重複排除する。測定自体は変えないため、DP 予算消費は不変である。

### 問題5: 小さい ε での数値的破綻

`ε=0.1` のような極端に強いプライバシー設定では、ノイズ較正の区間探索が失敗し `NoBracketIntervalFoundError` となる。
本デモでは ε を変える比較の範囲を `ε≥0.5` に調整して回避した。

### 問題6: AIM ε スイープの JIT メモリ確保失敗（環境依存）

AIM は ε≥0.5 で MST より大きいグラフィカルモデル（MRF）の推論カーネルを JIT する。
`RLIMIT_MEMLOCK`（`ulimit -l`）が低く固定された一部のサンドボックス環境では、この JIT 時に
LLVM のセクションメモリ確保が memlock 上限に頭打ちし、`Cannot allocate memory` /
`Unable to allocate section memory` で完走しなかった（ε=0.5/2.0/10.0、各 ~230–300s 走った末に失敗）。
ε ごとにプロセスを分離しても、`XLA_FLAGS` を緩めても再現する**環境固有**の制約である
（小さいカーネルで早く収束する ε=1.0 のみ通っていた）。
対処として、**memlock 制約のない WSL2（Ubuntu 24.04・`ulimit -l`=65536KB）を唯一の固定環境と定め**、
`scripts/run_all.sh` で全パイプライン（生成→評価→追加実験→ビルド）を一括再生成した（Issue #17）。
高 ε ほど生成時間が伸び（ε=1 の約 70 秒に対し ε=10 で約 420 秒）、これは「高 ε ほど測定マージナルが大きくなる」AIM の
計算資源依存性そのものであり、上記の JIT 失敗が高 ε で起きやすかったことと符合する。
ε スイープは当初 `scripts/12_aim_eps_sweep.py`（単一シード・`aim_eps_sweep_local.json`）で取得していたが、
単一シードでは run-to-run 分散が ε トレンドを覆ったため（Issue #14）、現在は **`scripts/10_experiments.py` の
実験E（マルチシード ε スイープ・mean±std）を正**とし、レポートの数値・図はすべてこの WSL 固定環境の
単一の実行系列で統一している（詳細は [AIM 解説 §7](method-aim.html#7)・[追加実験E](experiments.html)）。

---

## 3. 位置づけ

これらの問題は、DPSynth が「公式サポート対象外の研究段階プロダクト」[\[13\]](index.html#ref13) であることと整合する。
PoC・研究用途には十分機能するが、本番採用にあたってはフォーク／パッチ管理と検証体制を前提とする必要がある。
この観点はレポート本体の [残課題（実装・運用上の残課題）](index.html#72) に対応する。

---

← [実証評価レポートに戻る](index.html)
