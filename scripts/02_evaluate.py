"""DPSynth デモの品質評価。

評価指標:
  1) 1-way TVD     : 各列の分布差 (Total Variation Distance, 小さいほど良い)
  2) 2-way 相関誤差: 数値ペアの相関係数の絶対誤差
  3) TSTR          : 合成データで学習し実データで評価する下流ユーティリティ
                     (Train on Synthetic, Test on Real) — income 二値分類

出力: outputs/metrics.json, figures/*.png
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
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "adult.csv"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# 日本語フォントは環境依存なので図ラベルは英語に統一（文字化け回避）
plt.rcParams["axes.unicode_minus"] = False

meta = json.loads((OUT / "run_meta.json").read_text(encoding="utf-8"))
CAT_COLS = meta["cat_cols"]
NUM_COLS = meta["num_cols"]
COLS = NUM_COLS + CAT_COLS
SEED = meta["seed"]
SAMPLE_N = meta["sample_n"]


# ---------- データ ----------
def load_real_split():
    full = pd.read_csv(DATA)[COLS].copy()
    train = full.sample(n=SAMPLE_N, random_state=SEED)          # 合成に使った 20k と同一
    test_pool = full.drop(train.index)
    test = test_pool.sample(n=min(8000, len(test_pool)), random_state=7)
    return train.reset_index(drop=True), test.reset_index(drop=True)


# ---------- 指標 ----------
def tvd_categorical(a: pd.Series, b: pd.Series) -> float:
    cats = sorted(set(a.dropna().astype(str)) | set(b.dropna().astype(str)))
    pa = a.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0)
    pb = b.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0)
    return 0.5 * float(np.abs(pa - pb).sum())


def tvd_numeric(a: pd.Series, b: pd.Series, bins: np.ndarray) -> float:
    pa, _ = np.histogram(a, bins=bins)
    pb, _ = np.histogram(b, bins=bins)
    pa = pa / max(pa.sum(), 1)
    pb = pb / max(pb.sum(), 1)
    return 0.5 * float(np.abs(pa - pb).sum())


def one_way_tvd(real: pd.DataFrame, syn: pd.DataFrame) -> dict:
    res = {}
    for c in CAT_COLS:
        res[c] = tvd_categorical(real[c], syn[c])
    for c in NUM_COLS:
        bins = np.histogram_bin_edges(real[c].dropna(), bins=20)
        res[c] = tvd_numeric(real[c], syn[c], bins)
    res["__mean__"] = float(np.mean(list(res.values())))
    return res


def corr_error(real: pd.DataFrame, syn: pd.DataFrame) -> float:
    # 数値列ペアの Pearson 相関の絶対誤差の平均
    rc = real[NUM_COLS].corr().to_numpy()
    sc = syn[NUM_COLS].corr().to_numpy()
    iu = np.triu_indices_from(rc, k=1)
    return float(np.mean(np.abs(rc[iu] - sc[iu])))


# ---------- TSTR ----------
def encode_xy(df: pd.DataFrame, categories: dict):
    y = (df["income"].astype(str).str.contains(">50K")).astype(int).to_numpy()
    feats = [c for c in COLS if c != "income"]
    parts = []
    for c in feats:
        if c in NUM_COLS:
            parts.append(pd.to_numeric(df[c], errors="coerce").fillna(0).to_numpy().reshape(-1, 1))
        else:
            cat = pd.Categorical(df[c].astype(str), categories=categories[c])
            oh = pd.get_dummies(cat).to_numpy().astype(float)
            parts.append(oh)
    X = np.hstack(parts)
    return X, y


def tstr(train_df, real_test, categories):
    Xtr, ytr = encode_xy(train_df, categories)
    Xte, yte = encode_xy(real_test, categories)
    if len(np.unique(ytr)) < 2:
        return {"accuracy": float("nan"), "f1": float("nan"), "auc": float("nan")}
    clf = GradientBoostingClassifier(random_state=SEED)
    clf.fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {"accuracy": round(accuracy_score(yte, pred), 4),
            "f1": round(f1_score(yte, pred), 4),
            "auc": round(roc_auc_score(yte, proba), 4)}


# ---------- メイン ----------
def main() -> None:
    real_train, real_test = load_real_split()
    # one-hot のカテゴリ集合は実+全合成の和集合で固定
    syn_files = {r["tag"]: OUT / r["file"] for r in meta["runs"] if "file" in r}
    syns = {tag: pd.read_csv(p)[COLS] for tag, p in syn_files.items()}

    categories = {}
    for c in CAT_COLS:
        vals = set(real_train[c].astype(str)) | set(real_test[c].astype(str))
        for s in syns.values():
            vals |= set(s[c].astype(str))
        categories[c] = sorted(vals)

    metrics = {"one_way_tvd": {}, "corr_error": {}, "tstr": {}}

    # 実データ自身の TRTR ベースライン（上限の目安）
    metrics["tstr"]["real_train (TRTR baseline)"] = tstr(real_train, real_test, categories)

    for tag, syn in syns.items():
        metrics["one_way_tvd"][tag] = one_way_tvd(real_train, syn)
        metrics["corr_error"][tag] = round(corr_error(real_train, syn), 4)
        metrics["tstr"][tag] = tstr(syn, real_test, categories)
        print(f"[{tag}] meanTVD={metrics['one_way_tvd'][tag]['__mean__']:.3f} "
              f"corrErr={metrics['corr_error'][tag]:.3f} "
              f"TSTR_auc={metrics['tstr'][tag]['auc']}")

    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    make_figures(real_train, syns, metrics)
    print("\nmetrics.json + figures written. done.")


# ---------- 図 ----------
def make_figures(real, syns, metrics):
    # Fig1: 機構別の列ごとTVD (eps=1.0)
    mechs = [m for m in ["mst_eps1", "aim_eps1", "independent_eps1"]
             if m in metrics["one_way_tvd"]]
    cols_plot = ["education", "marital-status", "occupation", "income", "age", "hours-per-week"]
    x = np.arange(len(cols_plot))
    w = 0.8 / max(len(mechs), 1)
    plt.figure(figsize=(10, 5))
    for i, m in enumerate(mechs):
        vals = [metrics["one_way_tvd"][m][c] for c in cols_plot]
        plt.bar(x + (i - (len(mechs) - 1) / 2) * w, vals, w, label=m.replace("_eps1", ""))
    plt.xticks(x, cols_plot, rotation=30, ha="right")
    plt.ylabel("1-way TVD (lower = better)")
    plt.title("Per-column distribution error by mechanism (epsilon=1.0)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "fig1_tvd_by_mechanism.png", dpi=130)
    plt.close()

    # Fig2: epsilon スイープの平均TVD（MST と AIM を meta から動的収集して重ねる）
    def collect_eps(prefix):
        tags = []
        for r in meta["runs"]:
            if r["tag"].startswith(prefix) and r["tag"] in metrics["one_way_tvd"]:
                tags.append((r["tag"], r["epsilon"]))
        tags.sort(key=lambda te: te[1])
        return tags

    plt.figure(figsize=(6.4, 4.5))
    series_eps = [("mst_eps", "MST", "#c0392b", "o-"),
                  ("aim_eps", "AIM", "#2980b9", "s--")]
    for prefix, label, color, style in series_eps:
        eps_tags = collect_eps(prefix)
        if not eps_tags:
            continue
        xs = [e for _, e in eps_tags]
        ys = [metrics["one_way_tvd"][t]["__mean__"] for t, _ in eps_tags]
        plt.plot(xs, ys, style, color=color, label=label)
        for xx, yy in zip(xs, ys):
            plt.annotate(f"{yy:.3f}", (xx, yy), textcoords="offset points",
                         xytext=(0, 8), fontsize=8, color=color)
    plt.xscale("log")
    plt.xlabel("privacy budget epsilon (log scale)")
    plt.ylabel("mean 1-way TVD")
    plt.title("Privacy-utility tradeoff (MST vs AIM)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIG / "fig2_epsilon_tradeoff.png", dpi=130)
    plt.close()

    # Fig3: 分布比較 (education) real vs 利用可能な各機構 (eps=1.0)
    col = "education"
    cats = real[col].value_counts().index.tolist()
    series = [("real", real[col])]
    for tag, label in [("mst_eps1", "MST"), ("aim_eps1", "AIM"),
                       ("independent_eps1", "INDEPENDENT")]:
        if tag in syns:
            series.append((label, syns[tag][col]))
    n = len(series)
    w = 0.8 / n
    xx = np.arange(len(cats))
    plt.figure(figsize=(11, 5))
    for i, (label, s) in enumerate(series):
        p = s.value_counts(normalize=True).reindex(cats, fill_value=0)
        plt.bar(xx + (i - (n - 1) / 2) * w, p.values, w, label=label)
    plt.xticks(xx, cats, rotation=45, ha="right", fontsize=8)
    plt.ylabel("proportion")
    plt.title("Distribution fidelity: education (epsilon=1.0)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "fig3_education_distribution.png", dpi=130)
    plt.close()

    # Fig4: TSTR AUC 比較
    plt.figure(figsize=(9, 4.8))
    order = ["real_train (TRTR baseline)", "aim_eps1", "mst_eps1",
             "mst_eps10.0", "mst_eps2.0", "mst_eps0.5", "independent_eps1"]
    order = [o for o in order if o in metrics["tstr"]]
    aucs = [metrics["tstr"][o]["auc"] for o in order]
    colors = []
    for o in order:
        if o.startswith("real_train"):
            colors.append("#2c3e50")
        elif o.startswith("independent"):
            colors.append("#c0392b")  # 破綻するベースラインを赤で強調
        else:
            colors.append("#2980b9")
    plt.bar(range(len(order)), aucs, color=colors)
    plt.axhline(0.5, color="gray", ls="--", lw=1)
    plt.annotate("random (AUC=0.5)", (len(order) - 0.5, 0.505), ha="right",
                 fontsize=8, color="gray")
    plt.xticks(range(len(order)), order, rotation=30, ha="right", fontsize=8)
    plt.ylabel("ROC-AUC on real test (TSTR)")
    plt.ylim(0.4, 1.0)
    plt.title("Downstream utility: predict income>50K (train on synthetic, test on real)")
    for i, a in enumerate(aucs):
        plt.annotate(f"{a:.3f}", (i, a), textcoords="offset points", xytext=(0, 5),
                     ha="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "fig4_tstr_auc.png", dpi=130)
    plt.close()


if __name__ == "__main__":
    main()
