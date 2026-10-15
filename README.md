# Wealth NNA Flow Tracker

**How fast is Morgan Stanley Wealth Management gathering assets once one-off events are stripped out, and how does that compare with Schwab and LPL?**

*By Aaradhya (Aru) Acharya · linkedin.com/in/aaradhya-a-09631b161 · Built Oct 2026 with public filings*

A small, end-to-end Net New Assets (NNA) reporting pipeline built only from public filings: source-cited raw data → SQL model → automated validation → explainable forecast → dashboard and a one-page senior-management brief.

## Headline findings (data through 3Q26, built Oct 15, 2026)

| | Morgan Stanley WM | Schwab (core) | LPL (organic) |
|---|---|---|---|
| Latest quarter NNA | $232.4B (3Q26) | $190.4B (3Q26) | $23.1B (2Q26) |
| Ex-event NNA | ~$114B (≈half of 3Q26 was IPO-related) | $190.4B | $23.1B |
| Ex-event organic growth, 2026 avg (annualized) | ~6.6% | ~5.1% | ~3.7% |

- The 3Q26 record is real but episodic; the underlying run-rate is still up ~41% year on year.
- 4Q25 and 2Q26 are statistical outliers with no disclosed driver — flagged for review rather than assumed to be run-rate.
- **4Q26 base-case forecast: ~$140B** (80% band $126B–$190B), excluding new one-off events.

## How it works

```
data/raw/*.csv          every number with its source document and URL
   │
sql/01_model.sql        staging → dim_quarter → fct_nna_quarterly → dim_client_assets → mart_nna, mart_peer_share
   │                    (dedup rules, gap-filling from FY/H1 totals, event adjustment, organic growth)
sql/02_validation.sql   six automated checks → validation_results
   │
src/forecast.py         rolling-origin backtest of 3 methods → 4Q26 point + 80% band
   │
outputs/                DuckDB file + CSVs (open in Excel/Tableau) + forecast.json
```

Run it: `pip install duckdb pandas numpy && python run_pipeline.py`

## Validation layer (the part reporting teams live in)

| Check | What it catches | Result |
|---|---|---|
| V1 Cross-source agreement | A restated or mis-keyed quarter | **Caught** a data aggregator showing LPL 2Q26 at $23.6B vs $23.1B in the filing |
| V2 Quarters sum to full year | Missing or double-counted quarters | MS 2023–25 and Schwab 2025 tie to $0.0B |
| V3 Narrative totals | Release text vs tables ("$131B in 1H24") | All within rounding |
| V4 Our growth math vs reported | Wrong denominator or annualization | Within 0.1pp where both exist; Schwab 3Q26 off 0.3pp because its base is interpolated (flagged) |
| V5 Completeness | Quarters not yet reported | LPL 3Q26 (reports Oct 30) |
| V6 Outlier review | Unusual quarters shipped without a "why" | MS 4Q25, 2Q26 need an explanation; 3Q26 explained (IPO flows) |

76 checks: 61 pass, 1 explained, 5 informational, 8 warnings, 1 fail.

## Forecast

Models the **ex-event growth rate** (not dollars), so quarters stay comparable as the asset base grows. Three simple methods were backtested on 8 quarters, each using only data available at the time:

| Method | Mean abs. error | Bias |
|---|---|---|
| Last quarter | 1.55pp | −0.15pp |
| **Trailing 4Q mean (chosen)** | **1.22pp** | −0.88pp |
| Trailing mean + seasonal | 1.36pp | −0.61pp |

Event upside (IPO lock-up expiries, new workplace mandates) is reported separately because history can't forecast it.

## Caveats

- Firms define NNA differently (Schwab "core", LPL "organic"); compare rates, not dollars.
- Event sizes are estimated from release wording ("just over half" → 51%).
- MS beginning client assets are interpolated between disclosed anchors (4Q24 $6.19T, 4Q25 $7.38T, 3Q26 ~$8.4T); each row says whether its base is an anchor or interpolated.
- Public data only — not Morgan Stanley internal data.

## Mapping to the role (NNA Analytics & Insights)

- **NNA reporting and senior-management reports** → mart tables + one-page brief written for executives.
- **Data reconciliation, benchmarking and validation** → `sql/02_validation.sql`.
- **NNA forecasting** → `src/forecast.py` with a backtest, not a single fitted line.
- **Competitor flows** → Schwab and LPL on a like-for-like organic growth basis.
- **SQL, Python, Excel/Tableau** → DuckDB SQL (Snowflake-portable), pandas/numpy, CSV outputs.
