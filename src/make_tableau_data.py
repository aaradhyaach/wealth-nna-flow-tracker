"""Tidy, Tableau-ready Excel extract (one sheet per data source) from pipeline outputs."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT, TAB = ROOT / "outputs", ROOT / "tableau"
TAB.mkdir(exist_ok=True)
FIRM = {"MS": "Morgan Stanley WM", "SCHW": "Schwab (core)", "LPLA": "LPL (organic)"}


def qend(p):
    y, q = int(p[:4]), int(p[5])
    return pd.Timestamp(year=y, month=q * 3, day=1) + pd.offsets.MonthEnd(0)


m = pd.read_csv(OUT / "mart_nna.csv")
fc = json.loads((OUT / "forecast.json").read_text())

nna = pd.DataFrame({
    "Firm": m.firm.map(FIRM),
    "Quarter": m.period.map(lambda p: f"{p[5]}Q{p[2:4]}"),
    "Quarter End": m.period.map(qend),
    "NNA ($B)": m.nna_bn.round(1),
    "Event NNA ($B)": m.event_bn.round(1),
    "Underlying NNA ($B)": m.nna_ex_events_bn.round(1),
    "Event": m.events.fillna(""),
    "Beginning Client Assets ($B)": m.begin_assets_bn.round(0),
    "Assets Basis": m.begin_assets_method.fillna(""),
    "Organic Growth (annualized)": m.organic_growth_ann.round(4),
    "Organic Growth ex-Events (annualized)": m.organic_growth_ex_events_ann.round(4),
    "NNA YoY": m.nna_yoy.round(4),
    "NNA Method": m.nna_method,
    "Source": m.source_doc,
    "Source URL": m.source_url,
}).sort_values(["Firm", "Quarter End"])

# Long format for a stacked bar: one row per quarter x component, forecast included
ms = m[m.firm == "MS"]
comp = pd.concat([
    pd.DataFrame({"Quarter End": ms.period.map(qend), "Component": "Underlying", "Value ($B)": ms.nna_ex_events_bn.round(1)}),
    pd.DataFrame({"Quarter End": ms.period.map(qend), "Component": "One-off event", "Value ($B)": ms.event_bn.round(1)}),
    pd.DataFrame({"Quarter End": [qend("2026Q4")], "Component": ["Forecast (base case)"], "Value ($B)": [round(fc["nna_point_bn"], 1)]}),
])
comp["Quarter"] = comp["Quarter End"].map(lambda d: f"{(d.month - 1) // 3 + 1}Q{str(d.year)[2:]}")
comp["Forecast Low ($B)"] = comp.Component.eq("Forecast (base case)").map({True: round(fc["nna_lo_bn"], 1), False: None})
comp["Forecast High ($B)"] = comp.Component.eq("Forecast (base case)").map({True: round(fc["nna_hi_bn"], 1), False: None})
comp = comp[comp["Value ($B)"] != 0].sort_values(["Quarter End", "Component"])

bt = pd.DataFrame(fc["backtest"])
back = pd.concat([
    pd.DataFrame({"Quarter End": bt.period.map(qend), "Series": "Actual", "Growth": bt.actual.round(4)}),
    pd.DataFrame({"Quarter End": bt.period.map(qend), "Series": "Forecast at the time", "Growth": bt.ttm_mean.round(4)}),
    pd.DataFrame({"Quarter End": [qend("2026Q4")], "Series": ["Forecast at the time"], "Growth": [round(fc["rate_point"], 4)]}),
])
back["Quarter"] = back["Quarter End"].map(lambda d: f"{(d.month - 1) // 3 + 1}Q{str(d.year)[2:]}")

kpi = pd.DataFrame([
    ("MS 3Q26 NNA ($B)", 232.4), ("MS 3Q26 underlying NNA ($B)", float(ms[ms.period == "2026Q3"].nna_ex_events_bn.iloc[0].round(1))),
    ("MS 3Q26 organic growth ex-events", float(ms[ms.period == "2026Q3"].organic_growth_ex_events_ann.iloc[0].round(4))),
    ("4Q26 forecast ($B)", round(fc["nna_point_bn"], 1)), ("4Q26 forecast low ($B)", round(fc["nna_lo_bn"], 1)),
    ("4Q26 forecast high ($B)", round(fc["nna_hi_bn"], 1)),
], columns=["KPI", "Value"])
kpi["Display"] = [f"{v:.1%}" if "growth" in k else f"${v:,.0f}B" for k, v in zip(kpi.KPI, kpi.Value)]

val = pd.read_csv(OUT / "validation_results.csv").rename(columns=str.title)

with pd.ExcelWriter(TAB / "nna_tableau_data.xlsx", engine="openpyxl") as xw:
    nna.to_excel(xw, sheet_name="NNA", index=False)
    comp.to_excel(xw, sheet_name="MS_Components", index=False)
    back.to_excel(xw, sheet_name="Backtest", index=False)
    kpi.to_excel(xw, sheet_name="KPIs", index=False)
    val.to_excel(xw, sheet_name="Validation", index=False)
    for ws in xw.book.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(48, max(10, max(len(str(c.value or "")) for c in col) + 2))
        ws.freeze_panes = "A2"
print("Wrote", TAB / "nna_tableau_data.xlsx")
