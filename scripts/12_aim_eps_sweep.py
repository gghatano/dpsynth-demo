"""AIM の ε スイープ（ローカル実測）を可視化する。Issue #13。

`experiments/aim_eps_sweep_local.json`（00→01→02 をローカル WSL で実行して
得た AIM / MST の ε スイープ抽出）を読み、figures/fig5_aim_eps_sweep_local.png を生成する。

このスイープは memlock 制約のないローカル環境での **別実行** であり、
リモートで作られたコミット済み metrics.json（REPORT/index を裏付ける）とは
jaxlib/XLA の数値差で乖離する。混同を避けるため独立した図として出力し、
メインレポートの図2（fig2_epsilon_tradeoff.png）は上書きしない。

使い方:  .venv/bin/python scripts/12_aim_eps_sweep.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "experiments" / "aim_eps_sweep_local.json"
OUT = ROOT / "figures" / "fig5_aim_eps_sweep_local.png"


def series(d: dict, key: str):
    """ε 昇順に (epsilon, 値) を返す。"""
    rows = sorted(d.values(), key=lambda r: r["epsilon"])
    return [r["epsilon"] for r in rows], [r[key] for r in rows]


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    aim, mst = data["aim"], data["mst"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    panels = [("mean_one_way_tvd", "Mean 1-way TVD (lower = better)"),
              ("tstr_auc", "TSTR AUC (higher = better)")]
    for ax, (key, title) in zip(axes, panels):
        ex, ey = series(mst, key)
        ax.plot(ex, ey, "o-", color="#c0392b", label="MST")
        ax.plot(*series(aim, key), "s--", color="#2980b9", label="AIM")
        ax.set_xscale("log")
        ax.set_xticks(ex)
        ax.set_xticklabels([str(e) for e in ex])
        ax.set_xlabel("epsilon (log scale)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()

    fig.suptitle("AIM / MST epsilon sweep — local re-run (Issue #13, single seed=42)",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
