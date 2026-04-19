# Episode Heterogeneity in the Yield Curve Inversion–Credit Spread Relationship

Replication code and manuscript for:

**LIM Boon Chuan (2026).** "Episode Heterogeneity in the Yield Curve Inversion–Credit Spread Relationship: Evidence from Six U.S. Inversion Episodes, 1986–2024." Independent Researcher, Singapore.

Submitted to *Finance Research Open* (Elsevier).

## Finding

Using monthly U.S. data from 1986–2024 and six identifiable yield curve inversion episodes defined by the 10-year minus 2-year Treasury spread, the relationship between inversion and investment-grade credit spreads is strongly heterogeneous across episodes. An episode-interacted regression decisively rejects the null of coefficient homogeneity (Wald χ²(5) = 436.7, p < 0.001). Only the 2022–2024 episode shows a statistically significant relationship between inversion depth and six-month-ahead spread changes (β = +0.22, t = 3.11, R² = 0.74). The apparent pooled "inversion predicts wider spreads" pattern visible in recent data is driven entirely by this single episode.

## Repository structure

```
manuscript/     Final Word + PDF for submission, cover letter, highlights
code/           Analysis and manuscript-generation scripts
figures/        Generated PNG figures used in the manuscript
data-snapshot/  (Optional) Frozen copies of FRED series used for replication
```

## Data sources

All data are publicly available from the Federal Reserve Economic Data (FRED) database at the Federal Reserve Bank of St. Louis (https://fred.stlouisfed.org). Series used:

- `BAA`, `AAA` — Moody's BAA and AAA corporate bond yields (monthly)
- `T10Y2Y` — 10-year minus 2-year Treasury spread (daily, aggregated to monthly mean)
- `T10Y3M` — 10-year minus 3-month Treasury spread (daily, aggregated to monthly mean, used in robustness)
- `DGS10` — 10-year Treasury constant maturity yield (for BAA–10Y robustness)
- `DFF` — Federal funds effective rate (daily, aggregated to monthly mean)
- `CPIAUCSL` — Consumer Price Index, all urban consumers (monthly), converted to year-over-year percent change

Sample period: January 1986 – December 2024 (468 monthly observations).

## Replication

The analysis scripts expect a SQLite database `/root/fred.db` with a standard schema:

```sql
CREATE TABLE observations (
    series_id TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (series_id, date)
);
```

If you do not have a FRED cache, the first script in `code/` (`yield_curve_analysis.py`) contains an alternative `fred_csv()` function that fetches directly from FRED's public CSV endpoint. To use it, comment out the SQLite section and uncomment the CSV section.

### Environment

```bash
python3 -m venv yc-env
source yc-env/bin/activate
pip install pandas numpy statsmodels scipy matplotlib
```

### Order of execution

```bash
python code/yield_curve_analysis.py      # main monthly regressions
python code/episode_analysis.py          # episode-interacted + per-episode
python code/zscore_robustness.py         # Section 5.4 z-score check
python code/robustness.py                # T10Y3M, BAA-10Y, depth (Sections 5.1–5.3)
python code/make_figures.py              # Figures 1-3
```

### Manuscript generation

Requires Node.js and the `docx` package (`npm install -g docx`).

```bash
node code/build_manuscript.js      # produces manuscript/yield_curve_manuscript.docx
node code/build_cover_letter.js    # produces manuscript/cover_letter.docx
node code/build_highlights.js      # produces manuscript/highlights.docx
```

## AI disclosure

During preparation of this work the author used Claude (Anthropic) to assist with drafting prose, reviewing analysis code, and improving readability. The author reviewed and edited the content as needed and takes full responsibility for the content of the publication.

## License

Code is released under the MIT License. The manuscript (PDF and DOCX) is copyright of the author and will be subject to the publisher's license terms upon acceptance.
