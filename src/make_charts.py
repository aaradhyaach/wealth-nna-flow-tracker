"""Static report charts (PNG) for the brief and README, built from pipeline outputs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Palette: categorical slots in fixed order (validated reference palette), muted gray for events
C = {"MS": "#2a78d6", "SCHW": "#eb6834", "LPLA": "#1baf7a"}
MUTED, INK, INK2, GRID, SURF = "#b9b7b0", "#0b0b0b", "#52514e", "#e6e4df", "#ffffff"
NAME = {"MS": "Morgan Stanley WM", "SCHW": "Schwab (core)", "LPLA": "LPL (organic)"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "axes.grid.axis": "y", "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.dpi": 200,
})


def qlabel(p):  # "2025Q3" -> "3Q25"
    return f"{p[5]}Q{p[2:4]}"


def ms_quarterly(m, fc):
    ms = m[m.firm == "MS"].sort_values("q_index")
    x = list(range(len(ms))) + [len(ms)]
    labels = [qlabel(p) for p in ms.period] + ["4Q26F"]
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    ax.bar(x[:-1], ms.nna_ex_events_bn, width=0.62, color=C["MS"], label="Underlying NNA", zorder=2)
    ax.bar(x[:-1], ms.event_bn, bottom=ms.nna_ex_events_bn, width=0.62, color=MUTED,
           label="Attributed one-off event", zorder=2, edgecolor=SURF, linewidth=1)
    ax.bar(x[-1], fc["nna_point_bn"], width=0.62, facecolor="none", edgecolor=C["MS"],
           linestyle=(0, (3, 2)), linewidth=1.4, label="4Q26 forecast (80% band)", zorder=2)
    ax.errorbar(x[-1], fc["nna_point_bn"], yerr=[[fc["nna_point_bn"] - fc["nna_lo_bn"]], [fc["nna_hi_bn"] - fc["nna_point_bn"]]],
                fmt="none", ecolor=INK, elinewidth=1.2, capsize=4, zorder=3)
    for xi, (_, r) in zip(x, ms.iterrows()):
        if r.period in ("2024Q1", "2026Q3", "2025Q4", "2026Q2"):
            ax.text(xi, r.nna_bn + 4, f"${r.nna_bn:.0f}B", ha="center", va="bottom", fontsize=7.5, color=INK2)
    ax.set_xticks(x, labels, fontsize=7.5)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:.0f}B")
    ax.tick_params(length=0)
    ax.set_ylim(0, 260)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=3)
    ax.set_title("Morgan Stanley Wealth Management: quarterly net new assets", loc="left", fontsize=10.5, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(FIG / "ms_quarterly_nna.png")
    plt.close(fig)


def growth_peers(m):
    d = m.dropna(subset=["organic_growth_ex_events_ann"]).copy()
    periods = sorted(d.period.unique(), key=lambda p: (p[:4], p[5]))
    pos = {p: i for i, p in enumerate(periods)}
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    ax.axhspan(0.05, 0.07, color=C["MS"], alpha=0.07, lw=0, zorder=0)
    ax.text(0.05, 0.0705, "MS 5–7% organic growth target", fontsize=7, color=INK2, va="bottom")
    ends = []
    for f in ["MS", "SCHW", "LPLA"]:
        s = d[d.firm == f].sort_values("q_index")
        xs = [pos[p] for p in s.period]
        ax.plot(xs, s.organic_growth_ex_events_ann, color=C[f], lw=2, solid_capstyle="round", marker="o", ms=3.5,
                markeredgecolor=SURF, markeredgewidth=0.8, zorder=3)
        ends.append([xs[-1], s.organic_growth_ex_events_ann.iloc[-1], f])
    ends.sort(key=lambda e: e[1])
    for i in range(1, len(ends)):
        if ends[i][1] - ends[i - 1][1] < 0.004:
            ends[i][1] = ends[i - 1][1] + 0.004
    for xe, ye, f in ends:
        ax.text(len(periods) - 1 + 0.3, ye, f"{NAME[f]}  {d[(d.firm == f)].sort_values('q_index').organic_growth_ex_events_ann.iloc[-1]:.1%}",
                color=INK, fontsize=7.5, va="center")
        ax.plot([len(periods) - 1 + 0.08, len(periods) - 1 + 0.25], [ye, ye], color=C[f], lw=2)
    ax.set_xticks(range(len(periods)), [qlabel(p) for p in periods], fontsize=7.5)
    ax.set_xlim(-0.3, len(periods) + 2.6)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_ylim(0, 0.09)
    ax.tick_params(length=0)
    ax.set_title("Organic growth excluding one-off events (annualized)", loc="left", fontsize=10.5, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(FIG / "organic_growth_peers.png")
    plt.close(fig)


def backtest(fc):
    bt = pd.DataFrame(fc["backtest"])
    labels = [qlabel(p) for p in bt.period] + ["4Q26F"]
    x = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.plot(x[:-1], bt.actual, color=C["MS"], lw=2, marker="o", ms=4, markeredgecolor=SURF, label="Actual (ex-events)", zorder=3)
    ax.plot(x, list(bt.ttm_mean) + [fc["rate_point"]], color=INK2, lw=1.6, ls=(0, (4, 3)), label="Forecast at the time (trailing 4Q mean)", zorder=2)
    ax.errorbar(x[-1], fc["rate_point"], yerr=[[fc["rate_point"] - fc["rate_lo"]], [fc["rate_hi"] - fc["rate_point"]]],
                fmt="o", color=INK, ms=5, mfc=SURF, capsize=4, elinewidth=1.2, zorder=4)
    ax.text(x[-1] + 0.15, fc["rate_point"], f" {fc['rate_point']:.1%}\n ≈ ${fc['nna_point_bn']:.0f}B", fontsize=7.5, va="center", color=INK)
    ax.set_xticks(x, labels, fontsize=7.5)
    ax.set_xlim(-0.4, len(x) + 0.4)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_ylim(0, 0.10)
    ax.tick_params(length=0)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2)
    ax.set_title("Forecast backtest: MS organic growth, actual vs forecast", loc="left", fontsize=10.5, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(FIG / "forecast_backtest.png")
    plt.close(fig)


if __name__ == "__main__":
    m = pd.read_csv(OUT / "mart_nna.csv")
    fc = json.loads((OUT / "forecast.json").read_text())
    ms_quarterly(m, fc)
    growth_peers(m)
    backtest(fc)
    print("Charts written to", FIG)
