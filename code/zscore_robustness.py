"""Section 5.4: Z-score robustness check.

Re-estimates the episode-interacted specification and per-episode predictive
regression using (a) full-sample and (b) rolling 10-year z-scored BAA-AAA
spreads to check that the Episode 6 finding is not an artifact of shifts in
spread-level volatility across decades.

Expected runtime: <5 seconds.
"""
import sqlite3
import numpy as np
import pandas as pd
import statsmodels.api as sm
import warnings
warnings.filterwarnings("ignore")

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

# Standardizations
monthly["Spread_z_full"] = (monthly["Spread"] - monthly["Spread"].mean()) / monthly["Spread"].std()
window = 120
rmean = monthly["Spread"].rolling(window=window, min_periods=60).mean()
rstd  = monthly["Spread"].rolling(window=window, min_periods=60).std()
monthly["Spread_z_roll"] = (monthly["Spread"] - rmean) / rstd

# Episode identification
inv = monthly["Inversion"].values
episodes = []
i = 0
while i < len(inv):
    if inv[i] == 1:
        j = i; gap = 0; last_inverted = i
        while j < len(inv):
            if inv[j] == 1:
                last_inverted = j; gap = 0
            else:
                gap += 1
                if gap > 2: break
            j += 1
        episodes.append((i, last_inverted))
        i = last_inverted + 1
    else:
        i += 1

monthly["episode_id"] = 0
for k, (s, e) in enumerate(episodes, 1):
    col = monthly.columns.get_loc("episode_id")
    monthly.iloc[s:min(e+1+12, len(monthly)), col] = k

# --- 1. Descriptive table ---
print("="*90)
print("EPISODE-LEVEL SPREAD CHANGES: RAW vs FULL-SAMPLE Z vs ROLLING 10Y Z")
print("="*90)
rows = []
for k, (s, e) in enumerate(episodes, 1):
    sub = monthly.iloc[s:e+1]
    pre = monthly.iloc[max(0, s-12):s]
    raw_d  = sub["Spread"].mean() - pre["Spread"].mean()
    zf_d   = sub["Spread_z_full"].mean() - pre["Spread_z_full"].mean()
    zr_sub = sub["Spread_z_roll"].dropna()
    zr_pre = pre["Spread_z_roll"].dropna()
    zr_d   = (zr_sub.mean() - zr_pre.mean()) if (len(zr_sub) and len(zr_pre)) else np.nan
    rows.append({"ep": k, "start": sub.index[0].strftime("%Y-%m"),
                 "months": len(sub),
                 "raw_delta": round(raw_d, 3),
                 "z_full_delta": round(zf_d, 3),
                 "z_roll_delta": round(zr_d, 3) if not np.isnan(zr_d) else None})
print(pd.DataFrame(rows).to_string(index=False))

def hac(y, X, lags=6):
    return sm.OLS(y, sm.add_constant(X)).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})

# --- 2. Episode-interacted regression, full-sample z ---
print("\n" + "="*90)
print("EPISODE-INTERACTED: full-sample z-scored spread")
print("="*90)
reg = monthly.copy()
for k in range(1, len(episodes)+1):
    reg[f"Inv_x_E{k}"] = reg["Inversion"] * (reg["episode_id"] == k).astype(int)
Xc = [f"Inv_x_E{k}" for k in range(1, len(episodes)+1)] + ["DFF", "CPI_YoY"]
m1 = hac(reg["Spread_z_full"], reg[Xc], lags=6)
print(m1.summary().tables[1])

n_ep = len(episodes)
R = np.zeros((n_ep-1, len(m1.params)))
names = list(m1.params.index)
base = names.index("Inv_x_E1")
for j in range(1, n_ep):
    R[j-1, base] = 1
    R[j-1, names.index(f"Inv_x_E{j+1}")] = -1
wald1 = m1.wald_test(R, scalar=True)
print(f"\nWald test (full-sample z): chi2({n_ep-1}) = {wald1.statistic:.3f}, p = {wald1.pvalue:.4f}")

# --- 3. Episode-interacted regression, rolling z ---
print("\n" + "="*90)
print("EPISODE-INTERACTED: rolling 10-year z-scored spread")
print("="*90)
reg_r = reg.dropna(subset=["Spread_z_roll"])
m2 = hac(reg_r["Spread_z_roll"], reg_r[Xc], lags=6)
print(m2.summary().tables[1])

R2 = np.zeros((n_ep-1, len(m2.params)))
names2 = list(m2.params.index)
base2 = names2.index("Inv_x_E1")
for j in range(1, n_ep):
    R2[j-1, base2] = 1
    R2[j-1, names2.index(f"Inv_x_E{j+1}")] = -1
wald2 = m2.wald_test(R2, scalar=True)
print(f"\nWald test (rolling z): chi2({n_ep-1}) = {wald2.statistic:.3f}, p = {wald2.pvalue:.4f}")

# --- 4. Per-episode predictive on z-scored spread change ---
print("\n" + "="*90)
print("PER-EPISODE PREDICTIVE: 6-month change in z-scored spread")
print("="*90)
zrows = []
for k, (s, e) in enumerate(episodes, 1):
    w = monthly.iloc[max(0, s-6):min(e+1+6, len(monthly))].copy()
    if len(w) < 12: continue
    w["dZ6"] = w["Spread_z_full"].shift(-6) - w["Spread_z_full"]
    d = w[["dZ6", "T10Y2Y", "DFF", "CPI_YoY"]].dropna()
    if len(d) < 10: continue
    m3 = hac(d["dZ6"], d[["T10Y2Y", "DFF", "CPI_YoY"]], lags=6)
    zrows.append({"ep": k, "n": len(d),
                  "beta_T10Y2Y": round(m3.params["T10Y2Y"], 3),
                  "t_T10Y2Y": round(m3.tvalues["T10Y2Y"], 2),
                  "p_T10Y2Y": round(m3.pvalues["T10Y2Y"], 4),
                  "R2": round(m3.rsquared, 3)})
print(pd.DataFrame(zrows).to_string(index=False))

print("\nDone.")
