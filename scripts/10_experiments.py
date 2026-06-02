"""追加実験（本体レポートを簡潔に保つため別ページ EXPERIMENTS.md 用）。

実験A: numerical_bins スイープ — 数値列の忠実度がビン数でどう変わるか（MST, eps=1.0）
実験B: マルチシード頑健性 — seed を変えたときの平均TVD / TSTR AUC の mean±std
実験C: 2-way 周辺分布の忠実度 — ペア分布の TVD（相関保持を定量化、既存の合成CSVを再利用）

出力: experiments/metrics_experiments.json, figures/exp*.png
実行: .venv/bin/python scripts/10_experiments.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score

import dpsynth
from dpsynth import discrete_mechanisms as dm
from dpsynth import domain

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "adult.csv"
OUT = ROOT / "outputs"
EXP = ROOT / "experiments"
FIG = ROOT / "figures"
EXP.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

SEED = 42
SAMPLE_N = 20000
DELTA = 1e-5
CAT_COLS = ["workclass", "education", "marital-status",
            "occupation", "race", "gender", "income"]
NUM_COLS = ["age", "hours-per-week"]
COLS = NUM_COLS + CAT_COLS


# ---------- 共通 ----------
def load_real() -> pd.DataFrame:
    df = pd.read_csv(DATA)[COLS].copy()
    return df.sample(n=min(SAMPLE_N, len(df)), random_state=SEED).reset_index(drop=True)


def real_split():
    full = pd.read_csv(DATA)[COLS].copy()
    train = full.sample(n=SAMPLE_N, random_state=SEED)
    test = full.drop(train.index).sample(n=8000, random_state=7)
    return train.reset_index(drop=True), test.reset_index(drop=True)


def build_domains(df) -> dict:
    d = {"age": domain.NumericalAttribute(min_value=17.0, max_value=90.0,
                                          dtype="int", clip_to_range=True),
         "hours-per-week": domain.NumericalAttribute(min_value=1.0, max_value=99.0,
                                                     dtype="int", clip_to_range=True)}
    for c in CAT_COLS:
        d[c] = domain.CategoricalAttribute(possible_values=sorted(df[c].dropna().unique().tolist()))
    return d


def tvd_cat(a, b) -> float:
    cats = sorted(set(a.astype(str)) | set(b.astype(str)))
    pa = a.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0)
    pb = b.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0)
    return 0.5 * float(np.abs(pa - pb).sum())


def tvd_num(a, b, bins) -> float:
    pa, _ = np.histogram(a, bins=bins); pb, _ = np.histogram(b, bins=bins)
    pa = pa / max(pa.sum(), 1); pb = pb / max(pb.sum(), 1)
    return 0.5 * float(np.abs(pa - pb).sum())


def mean_tvd(real, syn) -> float:
    vals = [tvd_cat(real[c], syn[c]) for c in CAT_COLS]
    for c in NUM_COLS:
        bins = np.histogram_bin_edges(real[c].dropna(), bins=20)
        vals.append(tvd_num(real[c], syn[c], bins))
    return float(np.mean(vals))


def encode_xy(df, categories):
    y = df["income"].astype(str).str.contains(">50K").astype(int).to_numpy()
    parts = []
    for c in [c for c in COLS if c != "income"]:
        if c in NUM_COLS:
            parts.append(pd.to_numeric(df[c], errors="coerce").fillna(0).to_numpy().reshape(-1, 1))
        else:
            cat = pd.Categorical(df[c].astype(str), categories=categories[c])
            parts.append(pd.get_dummies(cat).to_numpy().astype(float))
    return np.hstack(parts), y


def tstr_auc(train_df, test_df, categories) -> float:
    Xtr, ytr = encode_xy(train_df, categories)
    Xte, yte = encode_xy(test_df, categories)
    if len(np.unique(ytr)) < 2:
        return float("nan")
    clf = GradientBoostingClassifier(random_state=SEED).fit(Xtr, ytr)
    return float(roc_auc_score(yte, clf.predict_proba(Xte)[:, 1]))


# ---------- 実験A: numerical_bins スイープ ----------
def exp_a(real, domains):
    print("\n== 実験A: numerical_bins スイープ (MST, eps=1.0) ==")
    bins_list = [8, 16, 32, 64]
    res = {c: [] for c in NUM_COLS}
    for nb in bins_list:
        syn = dpsynth.generate(data=real, domains=domains, epsilon=1.0, delta=DELTA,
                               discrete_config=dm.MSTConfig(seed=SEED), numerical_bins=nb)
        for c in NUM_COLS:
            edges = np.histogram_bin_edges(real[c].dropna(), bins=20)
            t = tvd_num(real[c], syn[c], edges)
            res[c].append(t)
        print(f"  bins={nb:3d}  " + "  ".join(f"{c}={res[c][-1]:.3f}" for c in NUM_COLS))

    plt.figure(figsize=(7, 4.6))
    for c in NUM_COLS:
        plt.plot(bins_list, res[c], "o-", label=c)
    plt.xscale("log", base=2)
    plt.xticks(bins_list, [str(b) for b in bins_list])
    plt.xlabel("numerical_bins (log2 scale)")
    plt.ylabel("1-way TVD (numeric columns)")
    plt.title("Exp A: numerical fidelity vs numerical_bins (MST, eps=1.0)")
    plt.legend(); plt.grid(True, alpha=.3); plt.tight_layout()
    plt.savefig(FIG / "expA_numerical_bins.png", dpi=130); plt.close()
    return {"bins": bins_list, "tvd": res}


# ---------- 実験B: マルチシード頑健性 ----------
def exp_b(real, domains, train, test, categories):
    print("\n== 実験B: マルチシード頑健性 (eps=1.0) ==")
    plans = [
        ("MST", lambda s: dm.MSTConfig(seed=s), [0, 1, 2, 3, 4]),
        ("INDEPENDENT", lambda s: dm.IndependentConfig(seed=s), [0, 1, 2, 3, 4]),
        ("AIM", lambda s: dm.AIMConfig(seed=s, max_rounds=16, pgm_iters=1000,
                                       max_model_size=100), [0, 1, 2]),
    ]
    summary = {}
    for name, cfg, seeds in plans:
        tvds, aucs = [], []
        for s in seeds:
            syn = dpsynth.generate(data=real, domains=domains, epsilon=1.0, delta=DELTA,
                                   discrete_config=cfg(s), numerical_bins=16)
            tvds.append(mean_tvd(train, syn))
            aucs.append(tstr_auc(syn, test, categories))
        summary[name] = {"n": len(seeds), "seeds": seeds,
                         "tvd_mean": float(np.mean(tvds)), "tvd_std": float(np.std(tvds)),
                         "auc_mean": float(np.nanmean(aucs)), "auc_std": float(np.nanstd(aucs)),
                         "tvd": tvds, "auc": aucs}
        print(f"  {name:12} n={len(seeds)}  meanTVD={np.mean(tvds):.3f}±{np.std(tvds):.3f}  "
              f"TSTR_AUC={np.nanmean(aucs):.3f}±{np.nanstd(aucs):.3f}")

    names = list(summary)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].bar(names, [summary[n]["tvd_mean"] for n in names],
                yerr=[summary[n]["tvd_std"] for n in names], capsize=6,
                color=["#2980b9", "#c0392b", "#27ae60"])
    axes[0].set_ylabel("mean 1-way TVD"); axes[0].set_title("Exp B: TVD (mean±std over seeds)")
    axes[1].bar(names, [summary[n]["auc_mean"] for n in names],
                yerr=[summary[n]["auc_std"] for n in names], capsize=6,
                color=["#2980b9", "#c0392b", "#27ae60"])
    axes[1].axhline(0.5, color="gray", ls="--", lw=1)
    axes[1].set_ylabel("TSTR ROC-AUC"); axes[1].set_ylim(0.4, 0.85)
    axes[1].set_title("Exp B: downstream AUC (mean±std over seeds)")
    for ax in axes:
        ax.tick_params(axis="x", rotation=15)
    plt.tight_layout(); plt.savefig(FIG / "expB_multiseed.png", dpi=130); plt.close()
    return summary


# ---------- 実験C: 2-way 周辺分布の忠実度 ----------
def exp_c(real):
    print("\n== 実験C: 2-way 周辺分布の忠実度 (eps=1.0, 既存合成CSVを再利用) ==")
    tags = {"MST": "synthetic_mst_eps1.csv", "AIM": "synthetic_aim_eps1.csv",
            "INDEPENDENT": "synthetic_independent_eps1.csv"}
    syns = {k: pd.read_csv(OUT / v)[COLS] for k, v in tags.items() if (OUT / v).exists()}
    pairs = [("education", "income"), ("marital-status", "income"),
             ("occupation", "income"), ("relationship_proxy", None)]
    # relationship_proxy は無いので数値ペアに差し替え
    pairs = [("education", "income"), ("marital-status", "income"),
             ("occupation", "income"), ("age", "income")]

    # 数値列は実データから共有ビン境界を決め、実/合成に同じ境界を適用する
    num_edges = {c: np.histogram_bin_edges(real[c].dropna(), bins=10)
                 for c in NUM_COLS}

    def two_way_tvd(a: pd.DataFrame, b: pd.DataFrame, c1, c2) -> float:
        def col(df, c):
            if c in CAT_COLS:
                return df[c].astype(str)
            return pd.cut(pd.to_numeric(df[c], errors="coerce"),
                          bins=num_edges[c], include_lowest=True).astype(str)

        def disc(df):
            return col(df, c1) + " | " + col(df, c2)
        ja = disc(a).value_counts(normalize=True)
        jb = disc(b).value_counts(normalize=True)
        keys = sorted(set(ja.index) | set(jb.index))
        pa = ja.reindex(keys, fill_value=0); pb = jb.reindex(keys, fill_value=0)
        return 0.5 * float(np.abs(pa - pb).sum())

    res = {k: [] for k in syns}
    labels = [f"{a}×{b}" for a, b in pairs]
    for name, syn in syns.items():
        for a, b in pairs:
            res[name].append(two_way_tvd(real, syn, a, b))
        print(f"  {name:12} " + "  ".join(f"{l}={v:.3f}" for l, v in zip(labels, res[name])))

    x = np.arange(len(pairs)); w = 0.8 / max(len(syns), 1)
    plt.figure(figsize=(9, 4.8))
    colors = {"MST": "#2980b9", "AIM": "#27ae60", "INDEPENDENT": "#c0392b"}
    for i, (name, vals) in enumerate(res.items()):
        plt.bar(x + (i - (len(syns) - 1) / 2) * w, vals, w, label=name,
                color=colors.get(name))
    plt.xticks(x, labels, rotation=15)
    plt.ylabel("2-way TVD (lower = better)")
    plt.title("Exp C: pairwise (2-way) marginal fidelity (eps=1.0)")
    plt.legend(); plt.tight_layout()
    plt.savefig(FIG / "expC_two_way.png", dpi=130); plt.close()
    return {"pairs": labels, "tvd": res}


def main(only: str | None = None):
    real = load_real()
    mfile = EXP / "metrics_experiments.json"
    metrics = json.loads(mfile.read_text(encoding="utf-8")) if mfile.exists() else {}

    if only in (None, "a"):
        metrics["exp_a"] = exp_a(real, build_domains(real))
    if only in (None, "b"):
        train, test = real_split()
        categories = {c: sorted(set(train[c].astype(str)) | set(test[c].astype(str)))
                      for c in CAT_COLS}
        metrics["exp_b"] = exp_b(real, build_domains(real), train, test, categories)
    if only in (None, "c"):
        metrics["exp_c"] = exp_c(real)

    mfile.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print("\nexperiments/metrics_experiments.json + figures written. done.")


if __name__ == "__main__":
    import sys
    main(only=sys.argv[1] if len(sys.argv) > 1 else None)
