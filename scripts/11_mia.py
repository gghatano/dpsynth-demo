"""実験D: メンバーシップ推論攻撃 (MIA) による経験的プライバシー評価。

考え方（デモ用の標準的な距離ベース MIA）:
  - メンバー    = 合成元の訓練データ(20k)に含まれる実レコード
  - 非メンバー  = 合成に使っていない holdout 実レコード（同一分布）
  - スコア      = 各レコードの「合成データへの最近傍距離」の符号反転（近いほどメンバーらしい）
  - 指標        = メンバー/非メンバーを当てる ROC-AUC
                  AUC ≈ 0.5 なら個人の有無は漏れていない（= DP として安全）

対照（攻撃が機能することの担保）:
  - "copy"(非DP) = 合成データ＝訓練データそのもの。メンバーは距離0になり AUC ≈ 1.0 になる。
    → 攻撃は漏洩を検出できる。その攻撃でも DP 合成が ≈0.5 なら「漏れていない」と言える。

出力: experiments/metrics_mia.json, figures/expD_mia.png
実行: .venv/bin/python scripts/11_mia.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "adult.csv"
OUT = ROOT / "outputs"
EXP = ROOT / "experiments"
FIG = ROOT / "figures"
EXP.mkdir(exist_ok=True)

SEED = 42
SAMPLE_N = 20000
N_ATTACK = 2000  # メンバー/非メンバー各件数
CAT_COLS = ["workclass", "education", "marital-status",
            "occupation", "race", "gender", "income"]
NUM_COLS = ["age", "hours-per-week"]
COLS = NUM_COLS + CAT_COLS


def load_splits():
    full = pd.read_csv(DATA)[COLS].copy()
    train = full.sample(n=SAMPLE_N, random_state=SEED)            # 合成元(=メンバー母集団)
    holdout = full.drop(train.index)                             # 非メンバー母集団
    members = train.sample(n=N_ATTACK, random_state=1).reset_index(drop=True)
    nonmembers = holdout.sample(n=N_ATTACK, random_state=2).reset_index(drop=True)
    return train.reset_index(drop=True), members, nonmembers


class Encoder:
    """カテゴリは one-hot、数値は min-max でスケールし、ユークリッド距離を可能にする。

    カテゴリの one-hot 同士のユークリッド距離^2 は「不一致カテゴリ数 × 2」に対応するため、
    数値(0..1)とおおよそ同じスケールで素朴な混合距離になる。
    """

    def __init__(self, ref: pd.DataFrame):
        self.cats = {c: sorted(ref[c].astype(str).unique()) for c in CAT_COLS}
        self.num_min = {c: float(pd.to_numeric(ref[c]).min()) for c in NUM_COLS}
        self.num_rng = {c: max(float(pd.to_numeric(ref[c]).max()) - self.num_min[c], 1e-9)
                        for c in NUM_COLS}

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        parts = []
        for c in NUM_COLS:
            v = (pd.to_numeric(df[c], errors="coerce").fillna(self.num_min[c]) - self.num_min[c]) / self.num_rng[c]
            parts.append(v.to_numpy().reshape(-1, 1))
        for c in CAT_COLS:
            cat = pd.Categorical(df[c].astype(str), categories=self.cats[c])
            parts.append(pd.get_dummies(cat).to_numpy().astype(float))
        return np.hstack(parts)


def mia_auc(synthetic: pd.DataFrame, members, nonmembers, enc: Encoder) -> float:
    syn = enc.transform(synthetic)
    nn = NearestNeighbors(n_neighbors=1, algorithm="auto").fit(syn)
    dm, _ = nn.kneighbors(enc.transform(members))
    dn, _ = nn.kneighbors(enc.transform(nonmembers))
    scores = np.concatenate([-dm.ravel(), -dn.ravel()])          # 近い(距離小)ほどメンバー予測
    labels = np.concatenate([np.ones(len(dm)), np.zeros(len(dn))])
    return float(roc_auc_score(labels, scores))


def main():
    train, members, nonmembers = load_splits()
    enc = Encoder(train)

    targets = {
        "copy (non-DP)": train,                                  # 対照: 訓練データそのもの
        "MST ε=1": OUT / "synthetic_mst_eps1.csv",
        "AIM ε=1": OUT / "synthetic_aim_eps1.csv",
        "INDEPENDENT ε=1": OUT / "synthetic_independent_eps1.csv",
        "MST ε=0.5": OUT / "synthetic_mst_eps0.5.csv",
        "MST ε=2": OUT / "synthetic_mst_eps2.0.csv",
        "MST ε=10": OUT / "synthetic_mst_eps10.0.csv",
    }
    results = {}
    for name, src in targets.items():
        if isinstance(src, pd.DataFrame):
            syn = src
        elif src.exists():
            syn = pd.read_csv(src)[COLS]
        else:
            # 01_generate.py で当該機構が失敗し CSV が無い場合はスキップ（run_all を止めない）
            print(f"  {name:18} SKIP（{src.name} が無い: 生成が失敗した可能性）")
            continue
        auc = mia_auc(syn, members, nonmembers, enc)
        results[name] = round(auc, 4)
        print(f"  {name:18} MIA AUC = {auc:.3f}")

    (EXP / "metrics_mia.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))

    names = list(results)
    aucs = [results[n] for n in names]
    colors = ["#c0392b"] + ["#2980b9"] * (len(names) - 1)
    plt.figure(figsize=(9, 4.8))
    plt.bar(range(len(names)), aucs, color=colors)
    plt.axhline(0.5, color="gray", ls="--", lw=1)
    plt.annotate("0.5 = no leakage (safe)", (len(names) - 0.5, 0.515), ha="right",
                 fontsize=8, color="gray")
    plt.xticks(range(len(names)), names, rotation=25, ha="right", fontsize=8)
    plt.ylabel("Membership Inference AUC (lower = safer)")
    plt.ylim(0.4, 1.05)
    plt.title("Exp D: Membership Inference Attack (0.5 ≒ no leakage)")
    for i, a in enumerate(aucs):
        plt.annotate(f"{a:.3f}", (i, a), textcoords="offset points", xytext=(0, 4),
                     ha="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "expD_mia.png", dpi=130)
    plt.close()
    print("\nexperiments/metrics_mia.json + figures/expD_mia.png written. done.")


if __name__ == "__main__":
    main()
