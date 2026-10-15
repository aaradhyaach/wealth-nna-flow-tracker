"""Static report charts (PNG) for the brief and README, styled to match the Tableau dashboard."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Colors sampled from the published Tableau dashboard (Tableau 10 palette)
BLUE, ORANGE, GREEN = "#4E79A7", "#F28E2B", "#59A14F"
EVENT, FORECAST, BAND, FC_LINE = "#BAB0AC", "#A1D5D2", "#DDEBF0", "#5F5654"
INK, INK2, GRID = "#333333", "#666666", "#E6E6E6"
FIRM = {"MS": ("Morgan Stanley WM", BLUE), "SCHW": ("Schwab (core)", ORANGE), "LPLA": ("LPL (organic)", GREEN)}

_have = {f.name for f in font_manager.fontManager.ttflist}
FONT = next(f for f in ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"] if f in _have)
plt.rcParams.update({
    "font.family": FONT, "font.size": 9,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": "#BBBBBB", "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 220,
})


def qlabel(p):  # "2025Q3" -> "3Q25", the same labels as the dashboard
    return f"{p[5]}Q{p[2:4]}"


def finish(ax, ylabel):
    ax.tick_params(length=0, labelsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.margins(x=0.01)


def save(fig, name):
    """Save as flat RGB (no alpha) so the chart background stays pure white in PDFs."""
    fig.savefig(FIG / name, pil_kwargs={"optimize": True})
    from PIL import Image
    Image.open(FIG / name).convert("RGB").save(FIG / name, optimize=True)


def ms_quarterly(m, fc):
    """Exhibit 1: quarterly NNA, underlying vs one-off events, plus the 4Q26 forecast bar."""
    ms = m[m.firm == "MS"].sort_values("q_index")
    labels = [qlabel(p) for p in ms.period] + ["4Q26"]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    ax.bar(x[:-1], ms.nna_ex_events_bn, width=0.75, color=BLUE, label="Underlying")
    ax.bar(x[:-1], ms.event_bn, bottom=ms.nna_ex_events_bn, width=0.75, color=EVENT, label="One-off event")
    ax.bar(x[-1], fc["nna_point_bn"], width=0.75, color=FORECAST, label="Forecast (base case)")
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 250)
    ax.set_yticks([0, 100, 200])
    finish(ax, "$ billions")
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=3, handlelength=1, handleheight=1)
    fig.tight_layout()
    save(fig, "ms_quarterly_nna.png")
    plt.close(fig)


def growth_peers(m):
    """Exhibit 2: organic growth ex-events by firm, MS 5-7% target band, labels at line ends."""
    d = m.dropna(subset=["organic_growth_ex_events_ann"])
    periods = sorted(d.period.unique(), key=lambda p: (p[:4], p[5]))
    pos = {p: i for i, p in enumerate(periods)}
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    ax.axhspan(0.05, 0.07, color=BAND, lw=0, zorder=0)
    ax.text(-0.2, 0.0705, "7%", fontsize=7, color=INK2, va="bottom")
    ax.text(-0.2, 0.0495, "5%", fontsize=7, color=INK2, va="top")
    ends = []
    for f in ["MS", "SCHW", "LPLA"]:
        name, col = FIRM[f]
        s = d[d.firm == f].sort_values("q_index")
        xs = [pos[p] for p in s.period]
        ax.plot(xs, s.organic_growth_ex_events_ann, color=col, lw=2, solid_capstyle="round", solid_joinstyle="round", zorder=3)
        ends.append([xs[-1], s.organic_growth_ex_events_ann.iloc[-1], f"{name}\n{s.organic_growth_ex_events_ann.iloc[-1]:.1%}", col])
    ends.sort(key=lambda e: e[1])  # spread end labels so they never overlap
    placed = []
    for xe, ye, txt, col in ends:
        ylab = max(ye, placed[-1] + 0.011) if placed else ye
        placed.append(ylab)
        ax.text(len(periods) - 1 + 0.25, ylab, txt, fontsize=7.5, color=INK, va="center", linespacing=1.1)
    ax.set_xticks(range(len(periods)), [qlabel(p) for p in periods])
    ax.set_xlim(-0.4, len(periods) + 1.6)
    ax.set_ylim(0, 0.09)
    ax.set_yticks([0, 0.02, 0.04, 0.06, 0.08])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    finish(ax, "Annualized growth")
    fig.tight_layout()
    save(fig, "organic_growth_peers.png")
    plt.close(fig)


def backtest(fc):
    """Exhibit 3: actual ex-event growth vs what the model forecast at the time, through 4Q26."""
    bt = pd.DataFrame(fc["backtest"])
    labels = [qlabel(p) for p in bt.period] + ["4Q26"]
    x = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    ax.plot(x[:-1], bt.actual, color=BLUE, lw=2, solid_capstyle="round", solid_joinstyle="round", label="Actual")
    ax.plot(x, list(bt.ttm_mean) + [fc["rate_point"]], color=FC_LINE, lw=2, solid_capstyle="round",
            solid_joinstyle="round", label="Forecast at the time")
    ax.text(x[-1] + 0.15, fc["rate_point"], f"{fc['rate_point']:.1%}", fontsize=7.5, va="center", color=INK)
    ax.set_xticks(x, labels)
    ax.set_xlim(-0.3, len(x) - 0.4)
    ax.set_ylim(0, 0.09)
    ax.set_yticks([0, 0.02, 0.04, 0.06, 0.08])
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    finish(ax, "Growth")
    ax.legend(frameon=False, fontsize=8, loc="lower right", ncol=2, handlelength=1.5)
    fig.tight_layout()
    save(fig, "forecast_backtest.png")
    plt.close(fig)


if __name__ == "__main__":
    m = pd.read_csv(OUT / "mart_nna.csv")
    fc = json.loads((OUT / "forecast.json").read_text())
    ms_quarterly(m, fc)
    growth_peers(m)
    backtest(fc)
    print("Charts written to", FIG)
