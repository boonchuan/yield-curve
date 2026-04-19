"""
Episode-level analysis of yield curve inversion and credit spreads
Builds on monthly_panel.csv produced by yc_analysis.py.
"""
import sqlite3
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

DB = "/root/fred.db"
conn = sqlite3.connect(DB)

def load(sid):
    df = pd.read_sql(
        "SELECT date, value FROM observations WHERE series_id=? ORDER BY date",
        conn, params=(sid,), parse_dates=["date"])
    return df.set_index("date")["value"].rename(sid)

baa    = load("BAA")
aaa    = load("AAA")
cpi    = load("CPIAUCSL")
dff    = load("DFF")
t10y2y = load("T10Y2Y")
conn.close()

spread_m   = (baa - aaa).rename("Spread")
cpi_yoy_m  = cpi.pct_change(12).mul(100).rename("CPI_YoY")
dff_m      = dff.resample("MS").mean().rename("DFF")
t10y2y_m   = t10y2y.resample("MS").mean().rename("T10Y2Y")

monthly = pd.concat([spread_m, cpi_yoy_m, dff_m, t10y2y_m], axis=1)
monthly["Inversion"] = (monthly["T10Y2Y"] < 0).astype(int)
monthly = monthly.loc["1986-01-01":"2024-12-31"].dropna()

# ============================================================
# 1. IDENTIFY EPISODES
# ============================================================
# An episode = a contiguous run of inversion months.
# Allow short gaps (< 3 months) of non-inversion to be treated as part
# of the same episode, since brief un-inversions happen.

inv = monthly["Inversion"].values
episodes = []
i = 0
while i < len(inv):
    if inv[i] == 1:
        # find end of this episode allowing up to 2 months of non-inversion gap
        j = i
        gap = 0
        last_inverted = i
        while j < len(inv):
            if inv[j] == 1:
                last_inverted = j
                gap = 0
            else:
                gap += 1
                if gap > 2:
                    break
            j += 1
        episodes.append((i, last_inverted))
        i = last_inverted + 1
    else:
        i += 1

print("="*80)
print("INVERSION EPISODES (1986-2024, monthly T10Y2Y)")
print("="*80)
print(f"{'#':>3} {'Start':>10} {'End':>10} {'Months':>7} "
      f"{'MaxInv':>8} {'AvgSpd':>8} {'PreSpd':>8} {'ΔSpd':>8} "
      f"{'AvgCPI':>8} {'AvgDFF':>8}")
print("-"*80)

ep_info = []
for k, (s, e) in enumerate(episodes, 1):
    sub = monthly.iloc[s:e+1]
    pre_window = monthly.iloc[max(0, s-12):s]   # 12 months pre-inversion
    max_inv = sub["T10Y2Y"].min()
    avg_spd = sub["Spread"].mean()
    pre_spd = pre_window["Spread"].mean() if len(pre_window) else np.nan
    d_spd   = avg_spd - pre_spd
    avg_cpi = sub["CPI_YoY"].mean()
    avg_dff = sub["DFF"].mean()
    start_d = sub.index[0].date()
    end_d   = sub.index[-1].date()
    months  = len(sub)
    print(f"{k:>3} {str(start_d):>10} {str(end_d):>10} {months:>7} "
          f"{max_inv:>8.3f} {avg_spd:>8.3f} {pre_spd:>8.3f} {d_spd:>+8.3f} "
          f"{avg_cpi:>8.2f} {avg_dff:>8.2f}")
    ep_info.append({
        "episode": k,
        "start": start_d, "end": end_d, "months": months,
        "max_inversion": max_inv,
        "avg_spread": avg_spd, "pre_spread": pre_spd, "delta_spread": d_spd,
        "avg_cpi": avg_cpi, "avg_dff": avg_dff,
    })

ep_df = pd.DataFrame(ep_info)

# ============================================================
# 2. EPISODE DUMMIES
# ============================================================
# Create a per-month column identifying which episode (if any) the month
# belongs to, extended to include the 12 months FOLLOWING each episode
# (the predictive window where the effect should show up).

monthly["episode_id"] = 0
for k, (s, e) in enumerate(episodes, 1):
    monthly.iloc[s:min(e+1+12, len(monthly)),
                 monthly.columns.get_loc("episode_id")] = k

# Interacted regression: Spread_t on Inv_t * episode dummies
# Only include months that are in-inversion
print("\n" + "="*80)
print("EPISODE-INTERACTED REGRESSION")
print("Spread_t = a + sum_k [beta_k * Inv_t * 1{episode=k}] + DFF + CPI")
print("="*80)

reg = monthly.copy()
for k in range(1, len(episodes)+1):
    reg[f"Inv_x_E{k}"] = reg["Inversion"] * (reg["episode_id"] == k).astype(int)

X_cols = [f"Inv_x_E{k}" for k in range(1, len(episodes)+1)] + ["DFF", "CPI_YoY"]
X = sm.add_constant(reg[X_cols])
y = reg["Spread"]
m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
print(m.summary().tables[1])

# Wald test: are the episode coefficients equal?
n_ep = len(episodes)
R = np.zeros((n_ep-1, len(X.columns)))
names = list(X.columns)
base_idx = names.index("Inv_x_E1")
for j in range(1, n_ep):
    other_idx = names.index(f"Inv_x_E{j+1}")
    R[j-1, base_idx] = 1
    R[j-1, other_idx] = -1
wald = m.wald_test(R, scalar=True)
print(f"\nWald test H0: all episode coefs equal")
print(f"  chi2({n_ep-1}) = {wald.statistic:.3f}, p = {wald.pvalue:.4f}")

# ============================================================
# 3. PER-EPISODE REGRESSION (6-month ahead)
# ============================================================
print("\n" + "="*80)
print("PER-EPISODE 6-MONTH-AHEAD SPREAD CHANGE")
print("For each inversion episode, regress Spread_{t+6} - Spread_t on")
print("inversion depth + macro controls, restricted to episode window")
print("="*80)

rows = []
for k, (s, e) in enumerate(episodes, 1):
    window = monthly.iloc[max(0, s-6):min(e+1+6, len(monthly))].copy()
    if len(window) < 12:
        continue
    window["dSpread_6"] = window["Spread"].shift(-6) - window["Spread"]
    d = window[["dSpread_6", "T10Y2Y", "DFF", "CPI_YoY"]].dropna()
    if len(d) < 10:
        continue
    try:
        m2 = sm.OLS(d["dSpread_6"],
                    sm.add_constant(d[["T10Y2Y","DFF","CPI_YoY"]])).fit(
                        cov_type="HAC", cov_kwds={"maxlags": 6})
        rows.append({
            "episode": k,
            "start": window.index[0].date(),
            "n": len(d),
            "beta_T10Y2Y": round(m2.params["T10Y2Y"], 3),
            "t_T10Y2Y":    round(m2.tvalues["T10Y2Y"], 2),
            "p_T10Y2Y":    round(m2.pvalues["T10Y2Y"], 4),
            "R2":          round(m2.rsquared, 3),
        })
    except Exception as exc:
        print(f"Episode {k} failed: {exc}")

print(pd.DataFrame(rows).to_string(index=False))

ep_df.to_csv("episodes.csv", index=False)
print("\nSaved: episodes.csv")
