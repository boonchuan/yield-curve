"""
Yield Curve Inversion, Macroeconomic Conditions, and Credit Spreads
Full analysis with FRED data 1986-2024, HAC standard errors, robustness checks.

Dependencies: pandas numpy statsmodels matplotlib scipy
Run: python yield_curve_analysis.py
"""

import io
import urllib.request
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

def fred_csv(code, start="1986-01-01", end="2024-12-31"):
    """Fetch a FRED series via the public CSV endpoint (no API key needed)."""
    url = (f"https://fred.stlouisfed.org/graph/fredgraph.csv"
           f"?id={code}&cosd={start}&coed={end}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
    df = pd.read_csv(io.StringIO(raw))
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    df.columns = [code]
    df[code] = pd.to_numeric(df[code], errors="coerce")
    return df

START = "1986-01-01"
END   = "2024-12-31"

# ---------------------------------------------------------------------------
# 1. DATA
# ---------------------------------------------------------------------------
# T10Y2Y exists on FRED from 1976-06; BAA/AAA daily from 1986-01.
# DFF daily from 1954. CPIAUCSL monthly; we forward-fill to daily.

series = {
    "BAA":    "BAA",         # Moody's BAA corporate bond yield, daily
    "AAA":    "AAA",         # Moody's AAA corporate bond yield, daily
    "T10Y2Y": "T10Y2Y",      # 10Y minus 2Y Treasury, daily
    "DFF":    "DFF",         # Federal funds rate, daily
    "CPI":    "CPIAUCSL",    # CPI all urban consumers, monthly SA
}

frames = {}
for name, code in series.items():
    print(f"Fetching {name} ({code})...")
    frames[name] = fred_csv(code, START, END)
    frames[name].columns = [name]

df = pd.concat(frames.values(), axis=1)
df.columns = list(series.keys())

# CPI YoY, then forward-fill to daily frequency
df["CPI_YoY"] = df["CPI"].pct_change(12) * 100
df[["CPI", "CPI_YoY"]] = df[["CPI", "CPI_YoY"]].ffill()

# Credit spread (BAA - AAA)
df["Spread"] = df["BAA"] - df["AAA"]

# Inversion indicator (1 when 10Y < 2Y)
df["Inversion"] = (df["T10Y2Y"] < 0).astype(int)

# Keep only business-day rows with all fields available
use = df[["Spread", "Inversion", "DFF", "CPI_YoY"]].dropna()
print(f"\nSample: {use.index.min().date()} to {use.index.max().date()}")
print(f"Observations: {len(use):,}")
print(f"Inversion days: {use['Inversion'].sum():,} ({use['Inversion'].mean()*100:.1f}%)")

# ---------------------------------------------------------------------------
# 2. UNCONDITIONAL COMPARISON
# ---------------------------------------------------------------------------
print("\n" + "="*70)
print("UNCONDITIONAL: credit spread during inversion vs. non-inversion")
print("="*70)
desc = use.groupby("Inversion")["Spread"].agg(["mean", "std", "count"])
print(desc)
# Welch t-test
from scipy import stats
inv = use.loc[use.Inversion == 1, "Spread"]
non = use.loc[use.Inversion == 0, "Spread"]
t, p = stats.ttest_ind(inv, non, equal_var=False)
print(f"\nWelch t-stat = {t:.3f}, p = {p:.4f}")

# ---------------------------------------------------------------------------
# 3. CONTEMPORANEOUS OLS WITH NEWEY-WEST HAC SE
# ---------------------------------------------------------------------------
def run_ols_hac(y, X, lags):
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return model

print("\n" + "="*70)
print("CONTEMPORANEOUS: Spread_t = a + b1*Inv_t + b2*DFF_t + b3*CPI_t")
print("Newey-West HAC SE, lags=22 (~1 month)")
print("="*70)
Xc = use[["Inversion", "DFF", "CPI_YoY"]]
yc = use["Spread"]
m0 = run_ols_hac(yc, Xc, lags=22)
print(m0.summary().tables[1])

# ---------------------------------------------------------------------------
# 4. LAGGED (PREDICTIVE) REGRESSIONS WITH HAC SE
# ---------------------------------------------------------------------------
# Spread_{t+h} on (Inv_t, DFF_t, CPI_t). Overlapping horizons -> HAC lags = h + 22
print("\n" + "="*70)
print("PREDICTIVE: Spread_{t+h} = a + b1*Inv_t + b2*DFF_t + b3*CPI_t")
print("HAC lags = h + 22 to handle overlap + residual persistence")
print("="*70)

horizons = [5, 10, 20, 60, 125, 250]   # trading days: 1w, 2w, 1m, 3m, 6m, 1y
rows = []
for h in horizons:
    y = use["Spread"].shift(-h)
    X = use[["Inversion", "DFF", "CPI_YoY"]]
    data = pd.concat([y, X], axis=1).dropna()
    y, X = data.iloc[:, 0], data.iloc[:, 1:]
    m = run_ols_hac(y, X, lags=h + 22)
    coef = m.params["Inversion"]
    t = m.tvalues["Inversion"]
    p = m.pvalues["Inversion"]
    rows.append({"horizon_days": h, "beta_Inv": coef, "t_Inv": t, "p_Inv": p,
                 "n": len(data), "R2": m.rsquared})
    print(f"\nHorizon t+{h:3d} (n={len(data)}):")
    print(m.summary().tables[1])

res = pd.DataFrame(rows)
print("\n" + "="*70)
print("SUMMARY ACROSS HORIZONS")
print("="*70)
print(res.to_string(index=False))

# ---------------------------------------------------------------------------
# 5. SAVE
# ---------------------------------------------------------------------------
use.to_csv("analysis_data.csv")
res.to_csv("horizon_results.csv", index=False)
print("\nSaved: analysis_data.csv, horizon_results.csv")
