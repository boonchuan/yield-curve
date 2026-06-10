#!/usr/bin/env python3
"""
FINR-D-26-00277 R1 revision analysis  (v2: robust fetching)
Episode Heterogeneity in the Yield Curve Inversion-Credit Spread Relationship

Addresses Reviewer #1 comments:
  C2/C3: Add Gilchrist-Zakrajsek (GZ) spread and excess bond premium (EBP)
         as parallel credit spread measures (Fed Board monthly CSV).
  C4:    Extended control set (equity volatility, 10Y level, industrial
         production growth) alongside DFF and CPI YoY.
  Minor: ADF/KPSS stationarity tests; differenced-specification robustness;
         Engle-Granger residual-based cointegration check.

v2 changes: retry with exponential backoff, browser User-Agent,
date-bounded FRED downloads (much smaller payloads), 120s timeout,
PeriodIndex-based monthly aggregation (no resample alias issues on
modern pandas), on-disk cache so a partial failure does not re-download
everything.

Requires: pandas, numpy, statsmodels, requests. Optional: yfinance.
"""

import io
import os
import time as _time
import warnings

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
CACHE = os.path.join(HERE, "cache")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

NW_LAGS = 6  # Newey-West lag length, matching the manuscript

START, END = "1984-06-01", "2025-01-31"  # padding for YoY/rolling calcs
SAMPLE_START, SAMPLE_END = "1986-01", "2024-12"

FRED_URL = ("https://fred.stlouisfed.org/graph/fredgraph.csv"
            "?id={sid}&cosd={start}&coed={end}")
FRED_API_URL = ("https://api.stlouisfed.org/fred/series/observations"
                "?series_id={sid}&api_key={key}&file_type=json"
                "&observation_start={start}&observation_end={end}")
FRED_API_KEY = os.getenv("FRED_API_KEY", "").strip()
EBP_URL = "https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv"

SESSION = requests.Session()
# NOTE: do not spoof a browser UA here. The St. Louis Fed / Federal Reserve
# endpoints sit behind a WAF that tarpits requests claiming to be Chrome
# without a matching TLS fingerprint (connection accepted, response never
# sent -> ReadTimeout). An honest client identifier goes straight through.
SESSION.headers.update({
    "User-Agent": "r1-analysis/1.0 (research replication script)",
    "Accept": "text/csv,application/json,*/*",
})


def _get_with_retry(url: str, tries: int = 5, timeout: int = 120) -> str:
    last = None
    for attempt in range(tries):
        try:
            r = SESSION.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            last = e
            wait = 3 * (2 ** attempt)
            print(f"  [retry {attempt + 1}/{tries}] {e.__class__.__name__}; "
                  f"sleeping {wait}s")
            _time.sleep(wait)
    raise RuntimeError(f"Failed after {tries} attempts: {url}") from last


# ----------------------------------------------------------------------
# Episode definitions (manuscript Table 2)
# ----------------------------------------------------------------------
EPISODES = {
    1: ("1989-01", "1989-09"),
    2: ("1990-03", "1990-03"),
    3: ("1998-06", "1998-06"),
    4: ("2000-02", "2000-12"),
    5: ("2006-02", "2007-05"),
    6: ("2022-07", "2024-08"),
}

# Per-episode predictive windows (manuscript Table 5)
PRED_WINDOWS = {
    1: ("1988-07", "1990-03"),
    4: ("1999-08", "2001-06"),
    5: ("2005-08", "2007-11"),
    6: ("2022-01", "2024-12"),
}


# ----------------------------------------------------------------------
# Data acquisition
# ----------------------------------------------------------------------
def _fred_via_api(sid: str) -> pd.Series:
    import json
    url = FRED_API_URL.format(sid=sid, key=FRED_API_KEY,
                              start=START, end=END)
    obs = json.loads(_get_with_retry(url))["observations"]
    df = pd.DataFrame(obs)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df.set_index("date")["value"].replace(".", np.nan),
                      errors="coerce")
    s.name = sid
    return s


def _fred_via_fredgraph(sid: str) -> pd.Series:
    text = _get_with_retry(FRED_URL.format(sid=sid, start=START, end=END))
    df = pd.read_csv(io.StringIO(text))
    date_col = "observation_date" if "observation_date" in df.columns else "DATE"
    df[date_col] = pd.to_datetime(df[date_col])
    val_col = sid.upper() if sid.upper() in df.columns else df.columns[-1]
    s = pd.to_numeric(df.set_index(date_col)[val_col], errors="coerce")
    s.name = sid
    return s


def fetch_fred(sid: str) -> pd.Series:
    """Prefer the official FRED API (set FRED_API_KEY env var); fall back to
    fredgraph CSV. Caches the parsed series to disk either way."""
    cache_file = os.path.join(CACHE, f"{sid}.parquet")
    if os.path.exists(cache_file):
        print(f"  {sid}: cache")
        return pd.read_parquet(cache_file)[sid]
    print(f"  {sid}: downloading "
          f"({'API' if FRED_API_KEY else 'fredgraph'})")
    if FRED_API_KEY:
        try:
            s = _fred_via_api(sid)
        except Exception as e:
            print(f"  [warn] API failed ({e}); trying fredgraph")
            s = _fred_via_fredgraph(sid)
    else:
        s = _fred_via_fredgraph(sid)
    s.to_frame().to_parquet(cache_file)
    return s


def fetch_ebp() -> pd.DataFrame:
    cache_file = os.path.join(CACHE, "ebp_csv.csv")
    if os.path.exists(cache_file):
        text = open(cache_file, encoding="utf-8").read()
        print("  ebp_csv: cache")
    else:
        print("  ebp_csv: downloading")
        text = _get_with_retry(EBP_URL)
        open(cache_file, "w", encoding="utf-8").write(text)
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df.index = pd.PeriodIndex(df["date"], freq="M")
    return df[["gz_spread", "ebp"]]


def monthly_mean(s: pd.Series) -> pd.Series:
    """Daily or monthly series -> monthly mean on a PeriodIndex.
    Avoids resample alias differences across pandas versions."""
    s = s.dropna().copy()
    s.index = pd.PeriodIndex(s.index, freq="M")
    return s.groupby(level=0).mean()


def realized_vol() -> pd.Series:
    """Monthly mean of 21-day annualized realized vol of S&P 500 log returns
    (yfinance ^GSPC, full coverage from 1985). Falls back to VIXCLS (1990+)."""
    try:
        import yfinance as yf
        px = yf.download("^GSPC", start=START, end=END,
                         progress=False, auto_adjust=True)["Close"].squeeze()
        ret = np.log(px).diff()
        rv = ret.rolling(21).std() * np.sqrt(252) * 100
        s = monthly_mean(rv)
        s.name = "rvol"
        print("  rvol: realized vol from ^GSPC (yfinance)")
        return s
    except Exception as e:
        print(f"  [warn] yfinance unavailable ({e}); falling back to VIXCLS "
              f"(coverage starts 1990; pre-1990 episodes lose this control)")
        s = monthly_mean(fetch_fred("VIXCLS"))
        s.name = "rvol"
        return s


def build_panel() -> pd.DataFrame:
    print("Fetching data ...")
    df = pd.DataFrame({
        "baa_aaa": monthly_mean(fetch_fred("BAA"))
                   - monthly_mean(fetch_fred("AAA")),
        "t10y2y": monthly_mean(fetch_fred("T10Y2Y")),
        "dff": monthly_mean(fetch_fred("DFF")),
        "cpi_yoy": monthly_mean(fetch_fred("CPIAUCSL")).pct_change(12) * 100,
        "indpro_yoy": monthly_mean(fetch_fred("INDPRO")).pct_change(12) * 100,
        "dgs10": monthly_mean(fetch_fred("DGS10")),
        "rvol": realized_vol(),
    })
    df = df.join(fetch_ebp(), how="left")

    df = df.loc[SAMPLE_START:SAMPLE_END].copy()
    df["inv"] = (df["t10y2y"] < 0).astype(int)

    df["episode"] = 0
    for k, (s, e) in EPISODES.items():
        df.loc[s:e, "episode"] = k
    for k in EPISODES:
        df[f"inv_E{k}"] = df["inv"] * (df["episode"] == k).astype(int)

    df.to_csv(os.path.join(OUT, "panel.csv"))
    print(f"Panel: {df.index[0]}..{df.index[-1]}, n={len(df)}; "
          f"GZ coverage {df['gz_spread'].notna().sum()}, "
          f"rvol coverage {df['rvol'].notna().sum()} months")
    return df


# ----------------------------------------------------------------------
# Estimation helpers
# ----------------------------------------------------------------------
def nw_ols(y: pd.Series, X: pd.DataFrame):
    dat = pd.concat([y, X], axis=1).dropna()
    Xc = dat.iloc[:, 1:]
    Xc = Xc.loc[:, Xc.std() > 1e-12]  # drop degenerate (all-zero) regressors
    res = sm.OLS(dat.iloc[:, 0], sm.add_constant(Xc)).fit(
        cov_type="HAC", cov_kwds={"maxlags": NW_LAGS})
    return res, len(dat)


def coef_row(res, var):
    return (res.params[var], res.bse[var], res.tvalues[var], res.pvalues[var])


def wald_equal_episodes(res, names):
    names = [v for v in names if v in res.params.index]
    hyp = ", ".join(f"{names[0]} - {v} = 0" for v in names[1:])
    w = res.wald_test(hyp, scalar=True)
    return float(w.statistic), float(w.pvalue), len(names) - 1


# ----------------------------------------------------------------------
# Analyses
# ----------------------------------------------------------------------
def stationarity_table(df):
    rows = []
    series = ["baa_aaa", "gz_spread", "ebp", "t10y2y", "dff",
              "cpi_yoy", "indpro_yoy", "dgs10", "rvol"]
    for v in series:
        s = df[v].dropna()
        if len(s) < 30:
            continue
        for label, x in [("level", s), ("diff", s.diff().dropna())]:
            try:
                adf_p = adfuller(x, autolag="AIC")[1]
            except Exception:
                adf_p = np.nan
            try:
                kpss_p = kpss(x, regression="c", nlags="auto")[1]
            except Exception:
                kpss_p = np.nan
            rows.append({"series": v, "form": label,
                         "ADF p": round(adf_p, 4) if pd.notna(adf_p) else "n/a",
                         "KPSS p": round(kpss_p, 4) if pd.notna(kpss_p) else "n/a"})
    out = pd.DataFrame(rows)
    out.to_markdown(os.path.join(OUT, "T_stationarity.md"), index=False)
    print("\n=== Stationarity tests written (T_stationarity.md) ===")
    return out


CONTROL_SETS = {
    "baseline": ["dff", "cpi_yoy"],
    "extended": ["dff", "cpi_yoy", "rvol", "dgs10", "indpro_yoy"],
}

DEPVARS = {"baa_aaa": "BAA-AAA", "gz_spread": "GZ spread", "ebp": "EBP"}


def pooled_and_interacted(df):
    lines = ["# Pooled and episode-interacted results (levels)\n"]
    enames = [f"inv_E{k}" for k in EPISODES]
    for dv, dvlab in DEPVARS.items():
        for cs, controls in CONTROL_SETS.items():
            res, n = nw_ols(df[dv], df[["inv"] + controls])
            b, se, t, p = coef_row(res, "inv")
            lines.append(f"## {dvlab} | {cs} controls (n={n})")
            lines.append(f"Pooled inversion coef: {b:+.3f} (t={t:.2f}, p={p:.3f})")
            res2, n2 = nw_ols(df[dv], df[enames + controls])
            lines.append("| Episode | Coef | t | p |")
            lines.append("|---|---|---|---|")
            for k in EPISODES:
                name = f"inv_E{k}"
                if name not in res2.params.index:
                    lines.append(f"| E{k} | dropped (no obs) | | |")
                    continue
                bb, ss, tt, pp = coef_row(res2, name)
                lines.append(f"| E{k} | {bb:+.3f} | {tt:.2f} | {pp:.3f} |")
            ws, wp, dof = wald_equal_episodes(res2, enames)
            lines.append(f"Wald chi2({dof}) = {ws:.1f}, p = {wp:.2e}\n")
    path = os.path.join(OUT, "T_pooled_interacted.md")
    open(path, "w").write("\n".join(lines))
    print(f"=== Pooled/interacted results written ({os.path.basename(path)}) ===")


def predictive(df, horizon=6, within_window=True):
    """Eq (3). within_window=True replicates the manuscript convention:
    the h-month-ahead change is computed inside the episode window, so the
    last h months of each window drop out (matches Table 5 n's).
    within_window=False lets forecast targets extend beyond the window."""
    tag = "withinwin" if within_window else "exttarget"
    lines = [f"# Per-episode predictive regressions "
             f"({horizon}m horizon, {tag})\n"]
    for dv, dvlab in DEPVARS.items():
        lines.append(f"## {dvlab}")
        lines.append("| Ep | Window | beta(T10Y2Y) | t | p | R2 | n |")
        lines.append("|---|---|---|---|---|---|---|")
        for k, (s, e) in PRED_WINDOWS.items():
            sub = df.loc[s:e]
            if within_window:
                ysub = sub[dv].shift(-horizon) - sub[dv]
            else:
                ysub = (df[dv].shift(-horizon) - df[dv]).loc[s:e]
            res, n = nw_ols(ysub, sub[["t10y2y", "dff", "cpi_yoy"]])
            if n < 10:
                lines.append(f"| E{k} | {s}..{e} | n/a (n={n}) | | | | |")
                continue
            b, se, t, p = coef_row(res, "t10y2y")
            lines.append(f"| E{k} | {s}..{e} | {b:+.3f} | {t:.2f} | "
                         f"{p:.3f} | {res.rsquared:.3f} | {n} |")
        lines.append("")
        lines.append("With extended controls (rvol, dgs10, indpro_yoy added):")
        lines.append("| Ep | beta(T10Y2Y) | t | p | n |")
        lines.append("|---|---|---|---|---|")
        for k, (s, e) in PRED_WINDOWS.items():
            sub = df.loc[s:e]
            if within_window:
                ysub = sub[dv].shift(-horizon) - sub[dv]
            else:
                ysub = (df[dv].shift(-horizon) - df[dv]).loc[s:e]
            res, n = nw_ols(ysub, sub[["t10y2y"] + CONTROL_SETS["extended"]])
            if n < 12:
                lines.append(f"| E{k} | insufficient n ({n}) | | | |")
                continue
            b, se, t, p = coef_row(res, "t10y2y")
            lines.append(f"| E{k} | {b:+.3f} | {t:.2f} | {p:.3f} | {n} |")
        lines.append("")
    path = os.path.join(OUT, f"T_predictive_{horizon}m_{tag}.md")
    open(path, "w").write("\n".join(lines))
    print(f"=== Predictive results written ({os.path.basename(path)}) ===")


def differenced_robustness(df):
    lines = ["# Differenced specification and cointegration check\n"]
    enames = [f"inv_E{k}" for k in EPISODES]
    for dv, dvlab in DEPVARS.items():
        d = pd.DataFrame({
            "dy": df[dv].diff(),
            "d_dff": df["dff"].diff(),
            "d_cpi": df["cpi_yoy"].diff(),
        }).join(df[enames])
        res, n = nw_ols(d["dy"], d[enames + ["d_dff", "d_cpi"]])
        lines.append(f"## {dvlab}: d(spread) on episode dummies + d(controls) (n={n})")
        lines.append("| Episode | Coef | t | p |")
        lines.append("|---|---|---|---|")
        for k in EPISODES:
            name = f"inv_E{k}"
            if name not in res.params.index:
                lines.append(f"| E{k} | dropped (no obs) | | |")
                continue
            b, se, t, p = coef_row(res, name)
            lines.append(f"| E{k} | {b:+.4f} | {t:.2f} | {p:.3f} |")
        ws, wp, dof = wald_equal_episodes(res, enames)
        lines.append(f"Wald chi2({dof}) = {ws:.1f}, p = {wp:.2e}")
        lev, _ = nw_ols(df[dv], df[enames + CONTROL_SETS["baseline"]])
        try:
            eg_p = adfuller(lev.resid, autolag="AIC")[1]
            lines.append(f"Engle-Granger residual ADF p-value (levels eq): {eg_p:.4f}\n")
        except Exception:
            lines.append("Engle-Granger residual ADF: failed\n")
    path = os.path.join(OUT, "T_differenced.md")
    open(path, "w").write("\n".join(lines))
    print(f"=== Differenced robustness written ({os.path.basename(path)}) ===")


def episode_descriptives_gz(df):
    rows = []
    for k, (s, e) in EPISODES.items():
        ep = df.loc[s:e]
        pre = df.loc[:s].iloc[-13:-1]
        row = {"Ep": k, "Start": s, "Months": len(ep)}
        for v in ["baa_aaa", "gz_spread", "ebp"]:
            row[f"d_{v}"] = round(ep[v].mean() - pre[v].mean(), 3) \
                if ep[v].notna().any() and pre[v].notna().any() else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_markdown(os.path.join(OUT, "T_episode_deltas.md"), index=False)
    print("=== Episode delta table written (T_episode_deltas.md) ===")
    return out


if __name__ == "__main__":
    df = build_panel()
    stationarity_table(df)
    episode_descriptives_gz(df)
    pooled_and_interacted(df)
    predictive(df, horizon=6, within_window=True)    # manuscript convention
    predictive(df, horizon=12, within_window=True)
    predictive(df, horizon=6, within_window=False)   # for the footnote
    differenced_robustness(df)
    print("\nDone. All outputs in ./results/")
