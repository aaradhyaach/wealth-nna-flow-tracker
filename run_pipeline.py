"""Build the NNA tracker end to end: load -> model -> validate -> forecast -> export."""
import json
from pathlib import Path
import duckdb
from src.forecast import run as run_forecast

ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

con = duckdb.connect(str(OUT / "nna.duckdb"))
for f in ["sql/01_model.sql", "sql/02_validation.sql"]:
    con.execute((ROOT / f).read_text())

# Exports used by the dashboard and the brief (CSV = easy to open in Excel / Tableau)
con.sql("SELECT * FROM mart_nna ORDER BY firm, q_index").df().to_csv(OUT / "mart_nna.csv", index=False)
con.sql("SELECT * FROM mart_peer_share ORDER BY period, firm").df().to_csv(OUT / "peer_share.csv", index=False)
con.sql("SELECT * FROM dim_client_assets ORDER BY firm, q_index").df().to_csv(OUT / "client_assets.csv", index=False)
val = con.sql("SELECT * FROM validation_results ORDER BY check_name, subject").df()
val.to_csv(OUT / "validation_results.csv", index=False)

fc = run_forecast(con)
(OUT / "forecast.json").write_text(json.dumps(fc, indent=2))

summary = val.groupby("status").size().to_dict()
print("Validation:", summary)
print(f"Forecast ({fc['method']}): 4Q26 NNA ${fc['nna_point_bn']:.0f}B "
      f"(80% band ${fc['nna_lo_bn']:.0f}B-${fc['nna_hi_bn']:.0f}B), "
      f"rate {fc['rate_point']*100:.1f}% annualized")
for m, s in fc["scores"].items():
    print(f"  {m:13s} MAE {s['mae_pp']:.2f}pp  RMSE {s['rmse_pp']:.2f}pp  bias {s['bias_pp']:+.2f}pp")

# Report charts (PNG) and the Tableau-ready Excel extract
import runpy
runpy.run_path(str(ROOT / "src" / "make_charts.py"), run_name="__main__")
runpy.run_path(str(ROOT / "src" / "make_tableau_data.py"), run_name="__main__")
