"""DPSynth In-Memory API デモ: Adult Income データから DP 合成データを生成する。

- 機構比較      : MST / AIM / INDEPENDENT を epsilon=1.0 で比較
- 予算スイープ  : MST / AIM を epsilon=0.5 / 1.0 / 2.0 / 10.0 で比較
- 出力          : outputs/synthetic_<tag>.csv と outputs/run_meta.json

実行 (WSL の venv 経由):
  ~/dpsynth-demo/.venv/bin/python scripts/01_generate.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

import dpsynth
from dpsynth import discrete_mechanisms as dm
from dpsynth import domain

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "adult.csv"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

SEED = 42
# デモを高速・再現的にするためのサンプル件数（差分プライバシーの効果が見える規模）
SAMPLE_N = 20000

# 合成対象カラム（カテゴリカル + 数値の混在で両方の扱いを示す）
CAT_COLS = ["workclass", "education", "marital-status",
            "occupation", "race", "gender", "income"]
NUM_COLS = ["age", "hours-per-week"]
COLS = NUM_COLS + CAT_COLS


def load_real() -> pd.DataFrame:
    df = pd.read_csv(DATA)[COLS].copy()
    # 欠損 '?' は明示カテゴリとして残す（DPSynth は out_of_domain_index で吸収可能）
    df = df.sample(n=min(SAMPLE_N, len(df)), random_state=SEED).reset_index(drop=True)
    return df


def build_domains(df: pd.DataFrame) -> dict:
    domains: dict[str, domain.AttributeType] = {}
    # 数値属性: 実データ範囲を「公開メタデータ」として与える（範囲はDP前提では公知情報とする）
    domains["age"] = domain.NumericalAttribute(
        min_value=17.0, max_value=90.0, dtype="int", clip_to_range=True)
    domains["hours-per-week"] = domain.NumericalAttribute(
        min_value=1.0, max_value=99.0, dtype="int", clip_to_range=True)
    # カテゴリカル属性: 取りうる値の集合をスキーマとして与える
    for col in CAT_COLS:
        values = sorted(df[col].dropna().unique().tolist())
        domains[col] = domain.CategoricalAttribute(possible_values=values)
    return domains


def run(df, domains, *, tag, epsilon, delta, config, numerical_bins=16):
    """1 機構を実行。失敗してもデモ全体を止めず、結果に error を記録する。"""
    t0 = time.time()
    try:
        syn = dpsynth.generate(
            data=df,
            domains=domains,
            epsilon=epsilon,
            delta=delta,
            discrete_config=config,
            numerical_bins=numerical_bins,
        )
    except Exception as exc:  # noqa: BLE001  研究段階ライブラリのため機構により失敗しうる
        elapsed = time.time() - t0
        print(f"[{tag}] eps={epsilon} FAILED in {elapsed:.1f}s: {type(exc).__name__}: {exc}")
        return {"tag": tag, "epsilon": epsilon, "delta": delta,
                "error": f"{type(exc).__name__}: {exc}", "seconds": round(elapsed, 2)}
    elapsed = time.time() - t0
    path = OUT / f"synthetic_{tag}.csv"
    syn.to_csv(path, index=False)
    print(f"[{tag}] eps={epsilon} rows={len(syn)} time={elapsed:.1f}s -> {path.name}")
    return {"tag": tag, "epsilon": epsilon, "delta": delta,
            "rows": len(syn), "seconds": round(elapsed, 2),
            "file": path.name}


def main() -> None:
    df = load_real()
    domains = build_domains(df)
    df.to_csv(OUT / "real_sample.csv", index=False)
    print(f"real sample: rows={len(df)} cols={list(df.columns)}")

    delta = 1e-5
    runs = []

    # 1) 機構比較 (epsilon = 1.0)
    runs.append(run(df, domains, tag="mst_eps1", epsilon=1.0, delta=delta,
                    config=dm.MSTConfig(seed=SEED)))
    runs.append(run(df, domains, tag="aim_eps1", epsilon=1.0, delta=delta,
                    config=dm.AIMConfig(seed=SEED, max_rounds=16, pgm_iters=1000,
                                        max_model_size=100)))
    runs.append(run(df, domains, tag="independent_eps1", epsilon=1.0, delta=delta,
                    config=dm.IndependentConfig(seed=SEED)))

    # 2) プライバシー予算スイープ (MST) — eps=1.0 は上で生成済み
    for eps in (0.5, 2.0, 10.0):
        runs.append(run(df, domains, tag=f"mst_eps{eps}", epsilon=eps, delta=delta,
                        config=dm.MSTConfig(seed=SEED)))

    # 3) プライバシー予算スイープ (AIM) — eps=1.0 は上で生成済み
    #    MST スイープと同形式で AIM の ε–有用性の変化を実測する。
    #    AIM は 1 実行あたり重い（~90s/run）ため 3 本追加で数分かかる。
    for eps in (0.5, 2.0, 10.0):
        runs.append(run(df, domains, tag=f"aim_eps{eps}", epsilon=eps, delta=delta,
                        config=dm.AIMConfig(seed=SEED, max_rounds=16, pgm_iters=1000,
                                            max_model_size=100)))

    meta = {"seed": SEED, "sample_n": len(df), "columns": list(df.columns),
            "cat_cols": CAT_COLS, "num_cols": NUM_COLS,
            "delta": delta, "runs": runs}
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print("\nrun_meta.json written. done.")


if __name__ == "__main__":
    main()
