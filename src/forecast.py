"""
NNA forecast for Morgan Stanley Wealth Management, next quarter (4Q26).

Approach (deliberately explainable, sized to 15 quarters of public data):
  1. Model the *rate*, not the dollars: annualized organic growth on beginning-period
     client assets, after stripping tagged one-off events (family-office, IPO flows).
     Rates are comparable across years even as the asset base grows ~15-20%/yr.
  2. Backtest three candidate methods with a rolling origin (each forecast only
     sees data available at the time) and keep the one with the lowest error.
  3. Convert the chosen rate back to dollars on the latest asset base and wrap it
     in an 80% band built from that method's own backtest errors.
  4. Report event-driven upside separately - it is real but not forecastable from
     history, so mixing it into the base case would hide what the model knows.
"""
import json
import numpy as np
import pandas as pd


def backtest(rates: pd.Series, quarters: pd.Series, min_train: int = 4) -> pd.DataFrame:
    rows = []
    for i in range(min_train, len(rates)):
        hist, q = rates.iloc[:i], quarters.iloc[i]
        last = hist.iloc[-1]
        ttm = hist.iloc[-4:].mean()
        # Seasonal: same-quarter deviation from its trailing-4 mean, averaged over prior years
        devs = []
        for j in range(4, i):
            if quarters.iloc[j] == q:
                devs.append(rates.iloc[j] - rates.iloc[j - 4:j].mean())
        seas = ttm + (np.mean(devs) if devs else 0.0)
        rows.append(dict(idx=i, actual=rates.iloc[i], last_q=last, ttm_mean=ttm, ttm_seasonal=seas))
    return pd.DataFrame(rows)


def run(con) -> dict:
    df = con.sql("""
        SELECT period, quarter, nna_bn, event_bn, nna_ex_events_bn, begin_assets_bn,
               organic_growth_ex_events_ann AS g
        FROM mart_nna WHERE firm = 'MS' AND g IS NOT NULL ORDER BY q_index
    """).df()

    bt = backtest(df["g"], df["quarter"])
    methods = ["last_q", "ttm_mean", "ttm_seasonal"]
    scores = {}
    for m in methods:
        err = bt[m] - bt["actual"]
        scores[m] = dict(mae_pp=float(err.abs().mean() * 100), rmse_pp=float(np.sqrt((err ** 2).mean()) * 100),
                         bias_pp=float(err.mean() * 100))
    best = min(scores, key=lambda m: scores[m]["mae_pp"])

    # Forecast 4Q26 with the winning method, using all data through 3Q26
    g, q = df["g"], df["quarter"]
    nxt = backtest(pd.concat([g, pd.Series([np.nan])], ignore_index=True),
                   pd.concat([q, pd.Series([4])], ignore_index=True)).iloc[-1]
    rate = float(nxt[best])
    resid = (bt[best] - bt["actual"]).values
    lo_r, hi_r = rate + np.quantile(resid * -1, 0.10), rate + np.quantile(resid * -1, 0.90)

    begin_assets = float(con.sql(
        "SELECT client_assets_bn FROM dim_client_assets WHERE firm='MS' AND period='2026Q3'").fetchone()[0])
    to_bn = lambda r: r * begin_assets / 4

    out = dict(
        target="MS Wealth Management NNA, 4Q26",
        begin_assets_bn=begin_assets,
        method=best,
        scores=scores,
        rate_point=rate, rate_lo=float(lo_r), rate_hi=float(hi_r),
        nna_point_bn=to_bn(rate), nna_lo_bn=to_bn(lo_r), nna_hi_bn=to_bn(hi_r),
        n_backtest=int(len(bt)),
        q4_history={p: float(v) for p, v in zip(df["period"], df["nna_bn"]) if p.endswith("Q4")},
        backtest=[dict(period=df["period"].iloc[int(r["idx"])], actual=float(r["actual"]),
                       **{m: float(r[m]) for m in methods})
                  for _, r in bt.iterrows()],
    )
    return out
