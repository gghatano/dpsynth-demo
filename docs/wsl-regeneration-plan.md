# WSL 固定環境への統一: 再生成プラン（使い回し／やり直しの棚卸し）

関連 Issue: #13（AIM ε 実測）, #14（ε は複数シード必須）, #15（環境間で数値が非再現）

## 方針

DP 機構は `jax`/`jaxlib`/`mbi` のバージョン差で数値が変わる（#15）。**固定環境を WSL2 +
`requirements.txt` ピン留め依存**と定め、環境依存の数値・図はすべて WSL で一括再生成して
内部整合を取り直す。コミット済み metrics はすべて旧（リモート/初期）環境産のため、数値の
流用はしない。

## 使い回せる（環境非依存・そのまま）

| 区分 | 対象 |
|---|---|
| コード | `scripts/*.py`, `requirements.txt`, `patches/`, `setup_env.sh` |
| 文章・構成 | `content/*.md` の章立て・図配置・記述枠組み（**数値を含む文だけ差し替え**） |
| 定性的結論（構造由来） | INDEPENDENT が列間依存を壊す／MST の全域木制約／AIM のワークロード適応選択 |
| ビルド・規約 | `scripts/03_build_html.py`, `.claude/`, ドキュメント規約 |
| データ準備ロジック | `00_prepare_data.py`（`seed=42`, UCI Adult。決定的） |

## WSL でやり直す（環境依存の数値・図）

| 成果物 | 生成スクリプト | 内容 |
|---|---|---|
| `outputs/metrics.json` | `01`→`02` | §5 機構比較 + MST/AIM ε スイープ（単一シード簡易パス） |
| `outputs/run_meta.json` | `01` | 生成時間・行数 |
| `figures/fig1〜4`, `fig2_epsilon` | `02` | 機構比較・ε トレードオフ |
| `experiments/metrics_experiments.json`（exp_a/b/c/**e**） | `10` | ビン数／マルチシード／2-way／**マルチシード ε スイープ** |
| `figures/expA〜C`, **`expE_eps_multiseed`** | `10` | 同上 |
| `experiments/metrics_mia.json`, `figures/expD_mia` | `11` | MIA |

> マルチシード方針（本セッションでの決定）: §5 機構比較・MST/AIM の ε スイープは
> **exp_e（複数シードの mean±std）で確定**する。単一シードの `01`/図2 は疎通・例示用。

## やり直すと結論が変わりうる箇所（要再検証）

- **AIM の相関誤差**: 旧 0.226 → ローカル 0.007（#15）。「AIM は相関誤差が MST より悪い」という
  §6 考察が逆転しうる。再取得後に method-aim / §6 を要確認。
- **AIM の TSTR AUC**: 旧 0.768 → ローカル 0.649。fig4・選定ガイドの数値も連動。
- **単一シード ε トレンド**: 非単調・ε=1 が ε=0.5 より悪い逆転が出る（#14）。exp_e の mean±std で判断。

## WSL 実行順

```bash
# 固定環境の確立（upstream SHA を控えて以後ピン）
DPSYNTH_REF=<upstream-sha> bash scripts/setup_env.sh   # 初回は未指定可→src_commit.txt に記録される
bash scripts/run_all.sh                                # 00→01→02→10→10e(軽量→本)→11→03
```

個別・段階実行:

```bash
.venv/bin/python scripts/00_prepare_data.py
.venv/bin/python scripts/01_generate.py
.venv/bin/python scripts/02_evaluate.py
.venv/bin/python scripts/10_experiments.py            # exp_a/b/c
EXP_E_FAST=1 .venv/bin/python scripts/10_experiments.py e   # 軽量プリラン（疎通）
.venv/bin/python scripts/10_experiments.py e          # 本実行（重い: AIM 高 ε は数百秒/本）
.venv/bin/python scripts/11_mia.py
.venv/bin/python scripts/03_build_html.py
```

## 再生成後にやること

1. `content/*.md` の数値（§5/§6・method-aim §7・選定ガイド・EXPERIMENTS）を再生成値へ差し替え。
2. #15 で変わりうる定性的結論（AIM 相関誤差など）を再検証して考察を更新。
3. `htmls/` を `03_build_html.py` で再ビルドしてコミット。
4. `src_commit.txt`（upstream SHA）を記録・固定。
