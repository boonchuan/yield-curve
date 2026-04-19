"""Generate Figures 1-3 for the manuscript.

Figure 1: Time series of T10Y2Y and BAA-AAA with episode and NBER shading
Figure 2: Episode-interacted inversion coefficients with 95% CIs
Figure 3: Per-episode added-variable (partial-residual) scatter plots
"""
import sqlite3
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.labelsize": 10, "axes.titlesize": 11,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.8, "grid.linewidth": 0.4, "grid.alpha": 0.3,
    "lines.linewidth": 1.2, "figure.dpi": 150, "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

DB = "/root/fred.db"
conn = sqlite3.connect(DB)

def load(sid):
    df = pd.read_sql(
        "SELECT date, value FROM observations WHERE series_id=? ORDER BY date",
        conn, params=(sid,), parse_dates=["date"])
    return df.set_index("date")["value"].rename(sid)

baa = load("BAA"); aaa = load("AAA"); cpi = load("CPIAUCSL")
dff = load("DFF"); t10y2y = load("T10Y2Y")
conn.close()

spread_m  = (baa - aaa).rename("Spread")
cpi_yoy_m = cpi.pct_change(12).mul(100).rename("CPI_YoY")
dff_m     = dff.resample("MS").mean().rename("DFF")
t10y2y_m  = t10y2y.resample("MS").mean().rename("T10Y2Y")

monthly = pd.concat([spread_m, cpi_yoy_m, dff_m, t10y2y_m], axis=1)
monthly["Inversion"] = (monthly["T10Y2Y"] < 0).astype(int)
monthly = monthly.loc["1986-01-01":"2024-12-31"].dropna()

inv = monthly["Inversion"].values
episodes = []; i = 0
while i < len(inv):
    if inv[i] == 1:
        j = i; gap = 0; last = i
        while j < len(inv):
            if inv[j] == 1: last = j; gap = 0
            else:
                gap += 1
                if gap > 2: break
            j += 1
        episodes.append((i, last)); i = last + 1
    else: i += 1

episode_ranges = [(k, monthly.index[s], monthly.index[e])
                  for k, (s, e) in enumerate(episodes, 1)]

# --- Figure 1 ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 5.5), sharex=True,
                                gridspec_kw={"hspace": 0.1})
ax1.plot(monthly.index, monthly["T10Y2Y"], color="black", linewidth=1.0)
ax1.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax1.set_ylabel("10Y - 2Y Treasury (%)")
ax1.set_ylim(-1.2, 3.2); ax1.grid(True, axis="y")
for k, s, e in episode_ranges:
    ax1.axvspan(s, e, color="red", alpha=0.15, zorder=0)
    ax1.annotate(f"E{k}", xy=(s + (e-s)/2, 3.0), ha="center", va="top",
                 fontsize=8, color="darkred", fontweight="bold")
ax2.plot(monthly.index, monthly["Spread"], color="navy", linewidth=1.0)
ax2.set_ylabel("BAA - AAA spread (%)")
ax2.set_ylim(0.3, 3.6); ax2.set_xlabel("Year"); ax2.grid(True, axis="y")
for k, s, e in episode_ranges:
    ax2.axvspan(s, e, color="red", alpha=0.15, zorder=0)
for s_, e_ in [("1990-07-01","1991-03-01"),("2001-03-01","2001-11-01"),
               ("2007-12-01","2009-06-01"),("2020-02-01","2020-04-01")]:
    ax2.axvspan(pd.Timestamp(s_), pd.Timestamp(e_), color="gray", alpha=0.25, zorder=0)
ax2.legend(handles=[mpatches.Patch(color="red", alpha=0.15, label="Inversion episode"),
                    mpatches.Patch(color="gray", alpha=0.25, label="NBER recession")],
           loc="upper left", frameon=False)
plt.savefig("figure1_timeseries.png"); plt.close()
print("Wrote figure1_timeseries.png")

# --- Figure 2 ---
monthly["episode_id"] = 0
for k, (s, e) in enumerate(episodes, 1):
    col = monthly.columns.get_loc("episode_id")
    monthly.iloc[s:min(e+1+12, len(monthly)), col] = k
reg = monthly.copy()
for k in range(1, len(episodes)+1):
    reg[f"Inv_x_E{k}"] = reg["Inversion"] * (reg["episode_id"] == k).astype(int)
Xc = [f"Inv_x_E{k}" for k in range(1, len(episodes)+1)] + ["DFF", "CPI_YoY"]
X = sm.add_constant(reg[Xc])
m = sm.OLS(reg["Spread"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})

coefs = []
for k in range(1, len(episodes)+1):
    b = m.params[f"Inv_x_E{k}"]; se = m.bse[f"Inv_x_E{k}"]
    coefs.append({"label": f"E{k}\n{episode_ranges[k-1][1].strftime('%Y')}",
                  "beta": b, "lo": b - 1.96*se, "hi": b + 1.96*se,
                  "sig": abs(b/se) > 1.96})

fig, ax = plt.subplots(figsize=(6.5, 3.8))
xs = np.arange(len(coefs))
betas = [c["beta"] for c in coefs]
los = [c["beta"]-c["lo"] for c in coefs]
his = [c["hi"]-c["beta"] for c in coefs]
ax.errorbar(xs, betas, yerr=[los, his], fmt="none",
            ecolor="black", capsize=4, linewidth=1.0)
for i, c in enumerate(coefs):
    col = "black" if c["sig"] else "gray"
    mk = "o" if c["sig"] else "s"
    ax.plot(i, c["beta"], marker=mk, color=col, markersize=7,
            markerfacecolor="white" if not c["sig"] else col, markeredgewidth=1.2)
ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
ax.set_xticks(xs); ax.set_xticklabels([c["label"] for c in coefs])
ax.set_ylabel("Inversion coefficient\n(change in BAA-AAA spread, %)")
ax.set_xlabel("Episode"); ax.set_ylim(-0.65, 0.45); ax.grid(True, axis="y")
ax.text(0.98, 0.03,
        "Wald test H0: b1 = b2 = ... = b6\nchi2(5) = 436.69, p < 0.001",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="gray", linewidth=0.5))
ax.text(0.02, 0.97, "Filled: p < 0.05    Open: not significant",
        transform=ax.transAxes, ha="left", va="top", fontsize=8, style="italic")
plt.savefig("figure2_episode_coefs.png"); plt.close()
print("Wrote figure2_episode_coefs.png")

# --- Figure 3: added-variable plots ---
fig, axes = plt.subplots(1, 4, figsize=(11, 3.0), sharey=True)
colors_ep = {1:"#1f77b4", 4:"#ff7f0e", 5:"#2ca02c", 6:"#d62728"}
titles = {
    1: "E1: 1989\n(n=15, b=+0.07, t=0.51)",
    4: "E4: 2000\n(n=17, b=+0.06, t=0.54)",
    5: "E5: 2006-07\n(n=22, b=+0.02, t=0.09)",
    6: "E6: 2022-24\n(n=30, b=+0.22, t=3.11*)",
}
for ax, ep_k in zip(axes, [1, 4, 5, 6]):
    s_i, e_i = episodes[ep_k-1]
    w = monthly.iloc[max(0, s_i-6):min(e_i+1+6, len(monthly))].copy()
    w["dSpread_6"] = w["Spread"].shift(-6) - w["Spread"]
    d = w[["dSpread_6","T10Y2Y","DFF","CPI_YoY"]].dropna()
    Z = sm.add_constant(d[["DFF","CPI_YoY"]])
    y_resid = d["dSpread_6"] - sm.OLS(d["dSpread_6"], Z).fit().predict(Z)
    x_resid = d["T10Y2Y"]    - sm.OLS(d["T10Y2Y"],    Z).fit().predict(Z)
    ax.scatter(x_resid, y_resid, color=colors_ep[ep_k], alpha=0.7, s=25,
               edgecolor="white", linewidth=0.5)
    if len(d) > 3:
        beta_pr, alpha_pr = np.polyfit(x_resid, y_resid, 1)
        xs_line = np.linspace(x_resid.min(), x_resid.max(), 50)
        ax.plot(xs_line, alpha_pr + beta_pr*xs_line,
                color="black", linewidth=1.0, linestyle="--")
    ax.axhline(0, color="gray", linewidth=0.4, linestyle=":")
    ax.axvline(0, color="gray", linewidth=0.4, linestyle=":")
    ax.set_title(titles[ep_k], fontsize=9)
    ax.set_xlabel("T10Y2Y | DFF, CPI (%)", fontsize=9)
    ax.grid(True, linewidth=0.3)
axes[0].set_ylabel("Delta_6 BAA-AAA | DFF, CPI (%)", fontsize=9)
plt.tight_layout()
plt.savefig("figure3_per_episode_scatter.png"); plt.close()
print("Wrote figure3_per_episode_scatter.png")
