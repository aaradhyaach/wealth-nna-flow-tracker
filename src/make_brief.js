// Builds reports/NNA_Weekly_Brief_3Q26.docx (convert to PDF with LibreOffice or Word).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, LevelFormat, ExternalHyperlink, Footer, PageNumber,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "reports", "figures");
const NAVY = "0B2A4A", INK = "1A1A1A", MUTED = "5A5A5A", RULE = "C9CED6", BAND = "EEF2F7";
const FONT = "Calibri";

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 19, bold: o.bold, italics: o.italics, color: o.color || INK });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs)], spacing: { after: o.after ?? 80, before: o.before ?? 0, line: 264 }, alignment: o.align, border: o.border, keepNext: o.keepNext });
const h = (text, before = 160) => new Paragraph({
  children: [t(text.toUpperCase(), { bold: true, size: 18, color: NAVY })],
  spacing: { before, after: 70 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 2 } },
  keepNext: true,
});
const bullet = (runs, ref = "bul") => new Paragraph({ children: runs, numbering: { reference: ref, level: 0 }, spacing: { after: 50, line: 252 } });
const link = (text, url) => new ExternalHyperlink({ link: url, children: [new TextRun({ text, font: FONT, size: 16, color: "1F5FAD", underline: {} })] });
const img = (file, w, hgt) => new Paragraph({
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: w, height: hgt },
    altText: { title: file, description: file, name: file } })],
  spacing: { before: 60, after: 40 }, alignment: AlignmentType.CENTER,
});
const caption = (text) => p([t(text, { size: 15, italics: true, color: MUTED })], { after: 100 });

// ---- Key figures table ----
const W = 10800; // 7.5in content width
const cols = [2350, 1250, 1050, 1100, 1250, 2350, 1450];
const head = ["Firm (NNA definition)", "Latest quarter", "NNA ($B)", "vs year ago", "Ex-events ($B)", "Organic growth, annualized", "2026 YTD ($B)"];
const rows = [
  ["Morgan Stanley WM (net new assets)", "3Q26", "232.4", "+187%", "~114", "11.5% headline; ~5.7% ex-IPO", "498.9"],
  ["Schwab (core NNA)", "3Q26", "190.4", "+38%", "190.4", "5.8% (reported)", "450.2"],
  ["LPL Financial (organic NNA)", "2Q26*", "23.1", "+13%", "23.1", "4.0% (reported)", "44.5 (1H)"],
];
const border = { style: BorderStyle.SINGLE, size: 4, color: RULE };
const cell = (text, i, isHead) => new TableCell({
  width: { size: cols[i], type: WidthType.DXA },
  shading: isHead ? { type: ShadingType.CLEAR, fill: NAVY, color: "auto" } : undefined,
  margins: { top: 50, bottom: 50, left: 80, right: 80 },
  borders: { top: border, bottom: border, left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" } },
  children: [new Paragraph({ alignment: i >= 2 && i !== 5 ? AlignmentType.RIGHT : AlignmentType.LEFT,
    children: [t(text, { size: 16, bold: isHead || i === 0, color: isHead ? "FFFFFF" : INK })] })],
});
const table = new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: cols,
  rows: [new TableRow({ tableHeader: true, children: head.map((x, i) => cell(x, i, true)) }),
         ...rows.map(r => new TableRow({ children: r.map((x, i) => cell(x, i, false)) }))],
});

// ---- Callout box (bottom line) ----
const callout = new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: [W],
  rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: BAND, color: "auto" },
    margins: { top: 120, bottom: 120, left: 180, right: 180 },
    borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
               right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, left: { style: BorderStyle.SINGLE, size: 24, color: NAVY } },
    children: [
      p([t("Bottom line. ", { bold: true, color: NAVY, size: 20 }),
         t("Morgan Stanley Wealth Management posted a record $232B of net new assets (NNA) in 3Q26, but about half was IPO-related. The underlying run-rate is ~$114B, or ~5.7% annualized organic growth, at the midpoint of the firm's 5–7% target.", { size: 20 })], { after: 60 }),
      p([t("Recommendation. ", { bold: true, color: NAVY, size: 20 }),
         t("Report NNA as underlying + attributed events in the senior-management pack, so repeatable growth is not confused with one-offs. 4Q26 base case: ~$140B (80% band $126B–$190B), before any new events.", { size: 20 })], { after: 0 }),
    ],
  })] })],
});

const doc = new Document({
  creator: "Aaradhya Acharya",
  title: "NNA Weekly Brief — 3Q26 Flow Review",
  styles: { default: { document: { run: { font: FONT, size: 19 } } } },
  numbering: { config: [
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 300, hanging: 260 } } } }] },
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 300, hanging: 220 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 720, bottom: 720, left: 720, right: 720 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      t("Portfolio project using public filings only; not Morgan Stanley internal data.   Page ", { size: 14, color: MUTED }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 14, color: MUTED }) ] })] }) },
    children: [
      p([t("NNA WEEKLY BRIEF", { bold: true, size: 16, color: MUTED })], { after: 0 }),
      p([t("3Q26 Wealth Flow Review: record quarter, normal underlying growth", { bold: true, size: 32, color: NAVY })], { after: 40 }),
      p([t("Prepared by Aaradhya Acharya  ·  October 15, 2026  ·  Data through 3Q26 (LPL through 2Q26)", { size: 16, color: MUTED })], { after: 160 }),
      callout,
      h("Key findings"),
      new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 50, line: 252 }, children: [t("The record is real, but episodic. ", { bold: true }), t("Excluding ~$118B of estimated IPO-related flows, 3Q26 NNA was still up ~41% on 3Q25 ($81B).")] }),
      new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 50, line: 252 }, children: [t("MS leads peers on a like-for-like basis in 2026. ", { bold: true }), t("Ex-event organic growth averaged ~6.6% annualized vs ~5.1% for Schwab and ~3.7% for LPL; in 3Q26 alone MS (5.7%) and Schwab (~5.8–6.1%) were level.")] }),
      new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 50, line: 252 }, children: [t("Two strong quarters lack a public explanation. ", { bold: true }), t("4Q25 ($122B) and 2Q26 ($148B) sit >2 standard deviations above trend with no event disclosed; confirm drivers before treating them as run-rate.")] }),
      h("Key figures, latest quarter"),
      table,
      caption("*LPL reports 3Q26 on Oct 30. Firms define NNA differently, so growth rates compare better than dollars. MS ex-IPO estimated from release wording (\"just over half\"); MS growth uses beginning client assets interpolated between disclosed anchors."),
      img("ms_quarterly_nna.png", 640, 276),
      caption("Gray = flows the firm attributed to a specific event (1Q24 family office; 3Q26 IPO-related). Dashed bar = 4Q26 base case with 80% band."),

      h("Peer comparison", 120),
      img("organic_growth_peers.png", 640, 276),
      caption("Annualized NNA ÷ beginning-period client assets, after removing attributed one-offs. Schwab's 3Q26 computes at 6.1% vs its reported 5.8% because its beginning asset base is interpolated."),
      h("What to watch in 4Q26"),
      bullet([t("IPO lock-ups and fund distributions: ", { bold: true }), t("management flagged further asset-retention opportunities; the main upside to the base case.")]),
      bullet([t("Workplace-to-advisor funnel: ", { bold: true }), t("~$99B moved from Workplace and E*TRADE into advisor-led accounts in 2025; equity-compensation events convert directly into NNA.")]),
      bullet([t("No seasonal uplift assumed: ", { bold: true }), t("4Q was the strongest quarter in 2025 ($122B) but weaker than 3Q in 2024 ($57B vs $64B).")]),
      bullet([t("Competitor pressure: ", { bold: true }), t("Schwab core NNA hit a record $190B (+38%); it remains the largest gatherer in dollars once MS one-offs are removed.")]),
      h("Forecast and data quality"),
      img("forecast_backtest.png", 600, 233),
      bullet([t("Method: ", { bold: true }), t("trailing-four-quarter mean of ex-event growth, chosen over last-quarter and seasonal methods in an 8-quarter rolling backtest (mean absolute error 1.22pp vs 1.55pp and 1.36pp). It has run ~0.9pp low as growth accelerated, so the band leans upward.")]),
      bullet([t("Validation: ", { bold: true }), t("76 automated checks, 61 pass. Quarters tie exactly to full-year totals (MS 2023–25, Schwab 2025); computed growth matches firms' own disclosed rates within 0.1pp.")]),
      bullet([t("Caught: ", { bold: true }), t("a third-party data site lists LPL 2Q26 organic NNA as $23.6B vs $23.1B in LPL's release; the filing is used.")]),
      bullet([t("Open questions: ", { bold: true }), t("drivers of MS 4Q25 and 2Q26; retention of 3Q26 IPO assets through lock-up expiry.")]),
      p([t("Sources: ", { bold: true, size: 16, color: MUTED }),
         link("MS 3Q26 release", "https://www.sec.gov/Archives/edgar/data/0000895421/000089542126000288/a3q26msearningsrelease.htm"), t(" · ", { size: 16, color: MUTED }),
         link("MS 2025 10-K", "https://www.sec.gov/Archives/edgar/data/895421/000089542126000086/ms-20251231.htm"), t(" · ", { size: 16, color: MUTED }),
         link("MS 3Q26 call", "https://www.fool.com/earnings/call-transcripts/2026/10/14/morgan-stanley-ms-q3-2026-earnings-call-transcript/"), t(" · ", { size: 16, color: MUTED }),
         link("Schwab 3Q26 release", "https://content.schwab.com/web/retail/public/about-schwab/schwab_q3_2026_earnings_release.pdf"), t(" · ", { size: 16, color: MUTED }),
         link("Schwab 2025 10-K", "https://www.sec.gov/Archives/edgar/data/316709/000031670926000009/schw-20251231.htm"), t(" · ", { size: 16, color: MUTED }),
         link("LPL 2Q26 results", "https://investor.lpl.com/news-releases/news-release-details/lpl-financial-announces-second-quarter-2026-results"), t(" · ", { size: 16, color: MUTED }),
         link("Code & data", "https://github.com/aaradhyaach/wealth-nna-flow-tracker")], { before: 120 }),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(ROOT, "reports", "NNA_Weekly_Brief_3Q26.docx");
  fs.writeFileSync(out, buf);
  console.log("Wrote", out);
});
