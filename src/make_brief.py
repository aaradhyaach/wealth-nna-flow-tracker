"""Builds reports/NNA_Weekly_Brief_3Q26.pdf: a two-page research-note style brief.

Charts come from reports/figures (src/make_charts.py), so the brief, README and the
Tableau dashboard share one palette: Tableau 10 blue/orange/green, gray for one-offs.
"""
import json
from pathlib import Path
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, KeepTogether, PageBreak)

ROOT = Path(__file__).resolve().parents[1]
FIG, OUT = ROOT / "reports" / "figures", ROOT / "outputs"
PDF = ROOT / "reports" / "NNA_Weekly_Brief_3Q26.pdf"

DASHBOARD = "https://public.tableau.com/app/profile/aaradhya.acharya/viz/WealthNNAFlowTracker/WealthNNAFlowTracker"
REPO = "https://github.com/aaradhyaach/wealth-nna-flow-tracker"

INK, MUTED, RULE, BLUE = HexColor("#222222"), HexColor("#666666"), HexColor("#BFBFBF"), HexColor("#4E79A7")


def register_fonts():
    """Arial-metric font if available (Liberation Sans on Linux), else built-in Helvetica."""
    for reg, bold in [("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                       "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
                      ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
                      ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")]:
        if Path(reg).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont("Body", reg))
            pdfmetrics.registerFont(TTFont("Body-Bold", bold))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")
            return "Body", "Body-Bold"
    return "Helvetica", "Helvetica-Bold"


F, FB = register_fonts()
S = {
    "kicker": ParagraphStyle("kicker", fontName=FB, fontSize=8, textColor=BLUE, leading=10),
    "title": ParagraphStyle("title", fontName=FB, fontSize=17, textColor=INK, leading=21, spaceAfter=4),
    "byline": ParagraphStyle("byline", fontName=F, fontSize=8, textColor=MUTED, leading=10, spaceAfter=10),
    "h": ParagraphStyle("h", fontName=FB, fontSize=10.5, textColor=INK, leading=13, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", fontName=F, fontSize=9, textColor=INK, leading=12.5, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName=F, fontSize=9, textColor=INK, leading=12.5, leftIndent=11,
                             bulletIndent=0, spaceAfter=3),
    "exhibit": ParagraphStyle("exhibit", fontName=FB, fontSize=8.5, textColor=INK, leading=11, spaceBefore=8, spaceAfter=2),
    "source": ParagraphStyle("source", fontName=F, fontSize=7, textColor=MUTED, leading=9, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName=F, fontSize=8, textColor=INK, leading=10),
    "cellr": ParagraphStyle("cellr", fontName=F, fontSize=8, textColor=INK, leading=10, alignment=TA_RIGHT),
    "head": ParagraphStyle("head", fontName=FB, fontSize=7.5, textColor=MUTED, leading=9),
    "headr": ParagraphStyle("headr", fontName=FB, fontSize=7.5, textColor=MUTED, leading=9, alignment=TA_RIGHT),
}
W = letter[0] - 1.5 * inch


def bullet(text):
    return Paragraph(text, S["bullet"], bulletText="•")


def exhibit(n, title, png, height_in, source):
    img = Image(str(FIG / png), width=W, height=height_in * inch)
    return KeepTogether([Paragraph(f"Exhibit {n}: {title}", S["exhibit"]), img, Paragraph(source, S["source"])])


def key_table():
    head = ["Firm (NNA definition)", "Latest qtr", "NNA ($B)", "YoY", "Ex-events ($B)", "Organic growth (ann.)", "2026 YTD ($B)"]
    rows = [
        ["Morgan Stanley WM (net new assets)", "3Q26", "232.4", "+187%", "~114", "11.5% headline / ~5.7% ex-IPO", "498.9"],
        ["Schwab (core NNA)", "3Q26", "190.4", "+38%", "190.4", "5.8% reported", "450.2"],
        ["LPL Financial (organic NNA)", "2Q26*", "23.1", "+13%", "23.1", "4.0% reported", "44.5 (1H)"],
    ]
    right = {2, 3, 4, 6}
    data = [[Paragraph(h, S["headr"] if i in right else S["head"]) for i, h in enumerate(head)]]
    data += [[Paragraph(c, S["cellr"] if i in right else S["cell"]) for i, c in enumerate(r)] for r in rows]
    t = Table(data, colWidths=[w * inch for w in [1.75, 0.6, 0.62, 0.55, 0.8, 1.6, 0.78]], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, INK),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, RULE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, RULE),
        ("LINEBELOW", (0, -1), (-1, -1), 1, INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def on_page(c, doc):
    c.saveState()
    c.setStrokeColor(BLUE); c.setLineWidth(2)
    c.line(0.75 * inch, letter[1] - 0.5 * inch, letter[0] - 0.75 * inch, letter[1] - 0.5 * inch)
    c.setFont(F, 7); c.setFillColor(MUTED)
    c.drawString(0.75 * inch, 0.5 * inch, "Aaradhya Acharya  |  Independent analysis using public filings only; "
                                          "not affiliated with or reviewed by Morgan Stanley.")
    c.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
    c.restoreState()


def link(text, url):
    return f'<a href="{url}" color="#4E79A7">{text}</a>'


def build():
    fc = json.loads((OUT / "forecast.json").read_text())
    sc = fc["scores"]
    story = [
        Paragraph("WEALTH MANAGEMENT FLOW MONITOR  |  3Q26", S["kicker"]),
        Paragraph("Record quarter at Morgan Stanley WM, but underlying growth is in the normal range", S["title"]),
        Paragraph(f"Aaradhya Acharya  ·  October 15, 2026  ·  Data through 3Q26 (LPL through 2Q26)  ·  "
                  f"{link('Interactive dashboard', DASHBOARD)}  ·  {link('Code and data', REPO)}", S["byline"]),

        Paragraph("Key takeaways", S["h"]),
        bullet("<b>The record is real but episodic.</b> Morgan Stanley WM gathered $232B of net new assets (NNA) in 3Q26. "
               "About half (~$118B, estimated) was IPO-related; the underlying ~$114B is still up ~41% on 3Q25 ($81B)."),
        bullet("<b>Underlying growth sits mid-target.</b> Ex-event organic growth was ~5.7% annualized, at the midpoint of the "
               "firm's 5–7% target; in 3Q26 alone it was level with Schwab (5.8% reported)."),
        bullet("<b>MS leads peers on a like-for-like basis in 2026.</b> Ex-event growth averaged ~6.6% annualized vs ~5.1% for "
               "Schwab and ~3.7% for LPL."),
        bullet("<b>Two strong quarters lack a public explanation.</b> 4Q25 ($122B) and 2Q26 ($148B) sit more than two standard "
               "deviations above trend with no disclosed driver; confirm before treating them as run-rate."),
        bullet(f"<b>Recommendation:</b> report NNA as <i>underlying + attributed events</i> in the senior-management pack. "
               f"Base case for 4Q26 is ~${fc['nna_point_bn']:.0f}B (80% band ${fc['nna_lo_bn']:.0f}–{fc['nna_hi_bn']:.0f}B) "
               f"before any new events."),

        Paragraph("Exhibit 1: Key figures, latest reported quarter", S["exhibit"]),
        key_table(),
        Paragraph("*LPL reports 3Q26 on Oct 30. Firms define NNA differently, so growth rates compare better than dollars. "
                  "MS ex-IPO estimated from release wording (\"just over half\"); MS growth uses beginning client assets "
                  "interpolated between disclosed anchors. Source: company earnings releases and SEC filings; author analysis.",
                  S["source"]),

        exhibit(2, "Morgan Stanley WM quarterly net new assets: underlying vs one-off events ($B)", "ms_quarterly_nna.png", 2.63,
                "Gray = flows the firm attributed to a specific event (1Q24 family office; 3Q26 IPO-related). "
                f"Teal = 4Q26 base-case forecast (80% band ${fc['nna_lo_bn']:.0f}–{fc['nna_hi_bn']:.0f}B). "
                "Source: Morgan Stanley earnings releases; author analysis."),
        PageBreak(),

        exhibit(3, "Organic growth excluding one-off events, annualized", "organic_growth_peers.png", 2.55,
                "Annualized NNA ÷ beginning-period client assets, after removing attributed one-offs. Shaded band = MS 5–7% "
                "target. Schwab's 3Q26 computes at 6.1% vs its reported 5.8% because its beginning asset base is interpolated. "
                "Source: company filings; author analysis."),

        Paragraph("What to watch in 4Q26", S["h"]),
        bullet("<b>IPO lock-ups and fund distributions:</b> management flagged further asset-retention opportunities; "
               "the main upside to the base case."),
        bullet("<b>Workplace-to-advisor funnel:</b> ~$99B moved from Workplace and E*TRADE into advisor-led accounts in 2025; "
               "equity-compensation events convert directly into NNA."),
        bullet("<b>No seasonal uplift assumed:</b> 4Q was the strongest quarter in 2025 ($122B) but weaker than 3Q in 2024 "
               "($57B vs $64B)."),
        bullet("<b>Competitor pressure:</b> Schwab core NNA hit a record $190B (+38%); it remains the largest gatherer in dollars "
               "once MS one-offs are removed."),

        exhibit(4, "Forecast backtest: MS ex-event organic growth, actual vs forecast at the time", "forecast_backtest.png", 2.15,
                f"Last point = 4Q26 forecast ({fc['rate_point']:.1%} annualized ≈ ${fc['nna_point_bn']:.0f}B). "
                "Source: author analysis."),

        Paragraph("Method and data quality", S["h"]),
        bullet(f"<b>Forecast:</b> trailing-four-quarter mean of ex-event growth, chosen over last-quarter and seasonal methods in an "
               f"{fc['n_backtest']}-quarter rolling backtest (mean absolute error {sc['ttm_mean']['mae_pp']:.2f}pp vs "
               f"{sc['last_q']['mae_pp']:.2f}pp and {sc['ttm_seasonal']['mae_pp']:.2f}pp). It has run "
               f"~{abs(sc['ttm_mean']['bias_pp']):.1f}pp low as growth accelerated, so the band leans upward."),
        bullet("<b>Validation:</b> 76 automated checks, 61 pass. Quarters tie exactly to full-year totals (MS 2023–25, "
               "Schwab 2025); computed growth matches firms' own disclosed rates within 0.1pp."),
        bullet("<b>Caught:</b> a third-party data site lists LPL 2Q26 organic NNA as $23.6B vs $23.1B in LPL's release; "
               "the filing is used."),
        bullet("<b>Open questions:</b> drivers of MS 4Q25 and 2Q26; retention of 3Q26 IPO assets through lock-up expiry."),
        Spacer(1, 6),
        Paragraph("Sources: " + " · ".join([
            link("MS 3Q26 release", "https://www.sec.gov/Archives/edgar/data/0000895421/000089542126000288/a3q26msearningsrelease.htm"),
            link("MS 2025 10-K", "https://www.sec.gov/Archives/edgar/data/895421/000089542126000086/ms-20251231.htm"),
            link("MS 3Q26 call", "https://www.fool.com/earnings/call-transcripts/2026/10/14/morgan-stanley-ms-q3-2026-earnings-call-transcript/"),
            link("Schwab 3Q26 release", "https://content.schwab.com/web/retail/public/about-schwab/schwab_q3_2026_earnings_release.pdf"),
            link("Schwab 2025 10-K", "https://www.sec.gov/Archives/edgar/data/316709/000031670926000009/schw-20251231.htm"),
            link("LPL 2Q26 results", "https://investor.lpl.com/news-releases/news-release-details/lpl-financial-announces-second-quarter-2026-results"),
        ]), S["source"]),
    ]
    doc = BaseDocTemplate(str(PDF), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                          topMargin=0.7 * inch, bottomMargin=0.75 * inch,
                          title="NNA Weekly Brief: 3Q26 Wealth Flow Review", author="Aaradhya Acharya")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])
    doc.build(story)
    print("Wrote", PDF)


if __name__ == "__main__":
    build()
