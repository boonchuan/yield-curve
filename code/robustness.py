"""Sections 5.1 - 5.3: Robustness checks.

Section 5.1: T10Y3M as alternative inversion measure
Section 5.2: BAA - 10Y Treasury as alternative credit spread
Section 5.3: Continuous inversion-depth specification
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

baa=load("BAA"); aaa=load("AAA"); cpi=load("CPIAUCSL")
dff=load("DFF"); dgs10=load("DGS10")
t10y2y=load("T10Y2Y"); t10y3m=load("T10Y3M")
conn.close()

spread_m   = (baa - aaa).rename("BAA_AAA")
dgs10_m    = dgs10.resample("MS").mean()
spread_t_m = (baa - dgs10_m).dropna().rename("BAA_T10")
cpi_yoy_m  = cpi.pct_change(12).mul(100).rename("CPI_YoY")
dff_m      = dff.resample("MS").mean().rename("DFF")
t10y2y_m   = t10y2y.resample("MS").mean().rename("T10Y2Y")
t10y3m_m   = t10y3m.resample("MS").mean().rename("T10Y3M")

monthly = pd.concat([spread_m, spread_t_m, cpi_yoy_m, dff_m, t10y2y_m, t10y3m_m], axis=1)
monthly["Inv_2Y"] = (monthly["T10Y2Y"] < 0).astype(int)
monthly["Inv_3M"] = (monthly["T10Y3M"] < 0).astype(int)
monthly["Depth_2Y"] = np.minimum(monthly["T10Y2Y"], 0)
monthly = monthly.loc["1986-01-01":"2024-12-31"].dropna(
    subset=["BAA_AAA","CPI_YoY","DFF","T10Y2Y","T10Y3M"])

# Episodes (from T10Y2Y)
inv = monthly["Inv_2Y"].values
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

monthly["episode_id"] = 0
for k, (s, e) in enumerate(episodes, 1):
    col = monthly.columns.get_loc("episode_id")
    monthly.iloc[s:min(e+1+12, len(monthly)), col] = k

def hac(y, X, lags=6):
    return sm.OLS(y, sm.add_constant(X)).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})

def wald_eq(m, prefix):
    names = list(m.params.index)
    idx = [i for i, n in enumerate(names) if n.startswith(prefix)]
    n_ep = len(idx)
    if n_ep < 2: return None
    R = np.zeros((n_ep-1, len(names)))
    for j in range(1, n_ep):
        R[j-1, idx[0]] = 1
        R[j-1, idx[j]] = -1
    return m.wald_test(R, scalar=True)

# --- Section 5.1: T10Y3M ---
print("="*90)
print("5.1: T10Y3M as inversion measure")
print("="*90)
reg = monthly.copy()
for k in range(1, len(episodes)+1):
    reg[f"Inv3M_x_E{k}"] = reg["Inv_3M"] * (reg["episode_id"] == k).astype(int)
Xc = [f"Inv3M_x_E{k}" for k in range(1, len(episodes)+1)] + ["DFF", "CPI_YoY"]
m = hac(reg["BAA_AAA"], reg[Xc])
print(m.summary().tables[1])
w = wald_eq(m, "Inv3M_x_E")
print(f"\nWald (T10Y3M, coef equality): chi2 = {w.statistic:.3f}, p = {w.pvalue:.4f}")

# --- Section 5.2: BAA - 10Y Treasury ---
print("\n" + "="*90)
print("5.2: BAA - 10Y Treasury spread")
print("="*90)
reg = monthly.copy()
for k in range(1, len(episodes)+1):
    reg[f"Inv_x_E{k}"] = reg["Inv_2Y"] * (reg["episode_id"] == k).astype(int)
Xc = [f"Inv_x_E{k}" for k in range(1, len(episodes)+1)] + ["DFF", "CPI_YoY"]
m = hac(reg["BAA_T10"], reg[Xc])
print(m.summary().tables[1])
w = wald_eq(m, "Inv_x_E")
print(f"\nWald (BAA-10Y, coef equality): chi2 = {w.statistic:.3f}, p = {w.pvalue:.4f}")

# --- Section 5.3: Inversion depth ---
print("\n" + "="*90)
print("5.3: Continuous inversion depth")
print("="*90)
reg = monthly.copy()
for k in range(1, len(episodes)+1):
    reg[f"Depth_x_E{k}"] = reg["Depth_2Y"] * (reg["episode_id"] == k).astype(int)
Xc = [f"Depth_x_E{k}" for k in range(1, len(episodes)+1)] + ["DFF", "CPI_YoY"]
m = hac(reg["BAA_AAA"], reg[Xc])
print(m.summary().tables[1])

# --- Pooled vs pre-2022 vs Ep6-only (Table 3) ---
print("\n" + "="*90)
print("Pooled vs Pre-2022 vs Episode-6 window only")
print("="*90)
for label, df in [
    ("Full 1986-2024", monthly),
    ("Pre-2022",       monthly.loc[:"2022-06-01"]),
    ("Ep6 window",     monthly.iloc[max(0, episodes[-1][0]-12):min(episodes[-1][1]+1+12, len(monthly))]),
]:
    mp = hac(df["BAA_AAA"], df[["Inv_2Y","DFF","CPI_YoY"]])
    print(f"{label:18s}  n={int(mp.nobs):4d}  beta_Inv={mp.params['Inv_2Y']:+.4f}  "
          f"t={mp.tvalues['Inv_2Y']:+.2f}  p={mp.pvalues['Inv_2Y']:.3f}")

print("\nDone.")
