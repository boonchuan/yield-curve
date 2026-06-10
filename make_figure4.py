#!/usr/bin/env python3
"""Figure 4 for FINR-D-26-00277 R1: episode-specific inversion coefficients
for the GZ spread and the excess bond premium, with 95% CIs (NW HAC, 6 lags).
Style mirrors the manuscript's Figure 2 (filled = p<0.05, open = n.s.,
Wald box lower-right). Reads panel.csv produced by r1_analysis.py."""
import pandas as pd, numpy as np, statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("panel.csv", index_col=0)
ENAMES = [f"inv_E{k}" for k in range(1, 7)]
LABELS = ["E1\n1989", "E2\n1990", "E3\n1998", "E4\n2000", "E5\n2006", "E6\n2022"]

def fit(dv):
    dat = df[[dv] + ENAMES + ["dff", "cpi_yoy"]].dropna()
    X = sm.add_constant(dat[ENAMES + ["dff", "cpi_yoy"]])
    res = sm.OLS(dat[dv], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    hyp = ", ".join(f"{ENAMES[0]} - {v} = 0" for v in ENAMES[1:])
    w = res.wald_test(hyp, scalar=True)
    return res, float(w.statistic), float(w.pvalue)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharex=True)
for ax, (dv, title, ylab) in zip(axes, [
        ("gz_spread", "GZ spread", "Inversion coefficient\n(change in GZ spread, %)"),
        ("ebp", "Excess bond premium", "Inversion coefficient\n(change in EBP, %)")]):
    res, wstat, wp = fit(dv)
    b = res.params[ENAMES].values
    se = res.bse[ENAMES].values
    p = res.pvalues[ENAMES].values
    x = np.arange(6)
    ax.axhline(0, color="gray", lw=0.8, ls="--")
    ax.errorbar(x, b, yerr=1.96 * se, fmt="none", ecolor="black",
                elinewidth=1.1, capsize=3)
    sig = p < 0.05
    ax.scatter(x[sig], b[sig], marker="o", s=42, facecolor="black",
               edgecolor="black", zorder=3)
    ax.scatter(x[~sig], b[~sig], marker="s", s=42, facecolor="white",
               edgecolor="black", zorder=3)
    ax.set_xticks(x); ax.set_xticklabels(LABELS, fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(ylab, fontsize=8)
    ax.tick_params(labelsize=8)
    ptxt = "p < 0.001" if wp < 0.001 else f"p = {wp:.3f}"
    ax.text(0.97, 0.04,
            "Wald test H\u2080: \u03b2\u2081 = \u2026 = \u03b2\u2086\n"
            f"\u03c7\u00b2(5) = {wstat:.1f}, {ptxt}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="black", lw=0.7))
axes[0].text(0.03, 0.96, "Filled: p < 0.05    Open: not significant",
             transform=axes[0].transAxes, ha="left", va="top", fontsize=7.5,
             style="italic")
fig.tight_layout()
fig.savefig("figure4_gz_ebp_coefficients.png", dpi=300, bbox_inches="tight")
fig.savefig("figure4_gz_ebp_coefficients.pdf", bbox_inches="tight")
print("wrote figure4_gz_ebp_coefficients.{png,pdf}")
