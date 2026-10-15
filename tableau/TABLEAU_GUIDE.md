# Build the NNA dashboard in Tableau Public (about 60–90 minutes)

Tableau Public is free, runs on Mac and Windows, and gives you a public link for your resume. Everything you need is in `nna_tableau_data.xlsx` (one sheet per data source).

| Excel sheet | Used for |
|---|---|
| `KPIs` | Headline numbers across the top |
| `MS_Components` | Morgan Stanley quarterly NNA, stacked: underlying vs one-off, plus 4Q26 forecast |
| `NNA` | Organic growth vs Schwab and LPL |
| `Backtest` | Forecast accuracy chart |
| `Validation` | Data-checks table |

Colors used in the static charts, for consistency: Morgan Stanley `#2A78D6` (blue), Schwab `#EB6834` (orange), LPL `#1BAF7A` (green), one-off events `#B9B7B0` (gray).

---

## 0. Install and connect

1. Go to **public.tableau.com** → sign up (free) → download **Tableau Public** (the desktop app) and install it.
2. Open Tableau Public. Under **Connect → To a File**, click **Microsoft Excel** and choose `tableau/nna_tableau_data.xlsx`.
3. You'll see the five sheets on the left. Drag **MS_Components** onto the canvas.
4. Add the others as separate data sources: **Data → New Data Source → Microsoft Excel →** same file, then drag in **NNA**. Repeat for **Backtest**, **KPIs** and **Validation**. (Keep them separate; don't join them.)

**The date trick you'll use on every chart:** drag **Quarter End** to Columns. Click the pill's dropdown arrow and pick **Quarter** from the *second* group of options (the one whose example reads like "Q2 2015"). Then right-click the pill → **Discrete**. You now get one column per quarter, in date order.

---

## 1. Sheet "Headline" (KPI row)

1. Click the **Sheet 1** tab at the bottom, rename it **Headline**. Select the **KPIs** data source (top left).
2. Drag **KPI** to Columns. Drag **Display** to **Text** on the Marks card.
3. Click **Text** → **…** → set the font size to 20, bold. Right-click the KPI header → **Format** → make header text 9pt gray.
4. Right-click the column headers row → **Hide Field Labels for Columns**.

## 2. Sheet "MS quarterly NNA" (stacked bars)

1. New sheet (icon at the bottom), rename it. Data source: **MS_Components**.
2. Quarter End to Columns (date trick). **Value ($B)** to Rows.
3. Marks card: change **Automatic** to **Bar**. Drag **Component** to **Color**.
4. Click **Color → Edit Colors**: Underlying `#2A78D6`, One-off event `#B9B7B0`, Forecast (base case) `#A8C8F0`. (Click a value, then the color box → enter the hex code.)
5. Drag **Forecast Low ($B)** and **Forecast High ($B)** onto **Tooltip**, so hovering on 4Q26 shows the 80% band.
6. Right-click the y-axis → **Format** → Numbers → **Currency (Custom)**, 0 decimals, suffix `B`. Title: double-click the title → "Morgan Stanley WM: quarterly net new assets ($B)".

## 3. Sheet "Organic growth vs peers" (lines)

1. New sheet. Data source: **NNA**.
2. Quarter End to Columns (date trick). **Organic Growth ex-Events (annualized)** to Rows. Drag **Firm** to **Color**. Marks: **Line**.
3. Edit Colors: Morgan Stanley WM `#2A78D6`, Schwab (core) `#EB6834`, LPL (organic) `#1BAF7A`.
4. Right-click y-axis → **Format** → Numbers → **Percentage**, 0 decimals.
5. Target band: open the **Analytics** tab (top left, next to Data) → drag **Reference Band** onto the chart → **Table**. Set Band From: **Constant 0.05**, Band To: **Constant 0.07**, label "MS 5–7% target", fill light blue.
6. Optional: Marks → **Label** → check *Show mark labels* → **Line Ends** to label each line's latest value.
7. If a small "nulls" indicator appears at the bottom right, right-click it → **Hide Indicator** (some quarters have no starting-asset data, by design).

## 4. Sheet "Forecast backtest" (lines)

1. New sheet. Data source: **Backtest**.
2. Quarter End to Columns (date trick). **Growth** to Rows. **Series** to Color. Marks: **Line**.
3. Colors: Actual `#2A78D6`, Forecast at the time `#52514E`. Click **Size** and make the lines a bit thinner if you like.
4. Y-axis format: **Percentage**, 0 decimals. Title: "Forecast backtest: actual vs forecast (annualized growth)".

## 5. Sheet "Data checks" (table)

1. New sheet. Data source: **Validation**.
2. Drag **Status**, **Check_Name**, **Subject**, **Detail** to Rows (in that order). Drag **Validation (Count)** to **Text** on the Marks card. (On some versions it is named **Number of Records** or **Validation (Count)** at the bottom of the field list.)
3. Drag **Status** to **Filters** → uncheck **PASS** → OK. Now it shows only checks that need attention (the LPL mismatch FAIL is the one to talk about).
4. Optional: drag **Status** to **Color** and set FAIL red, WARN amber, EXPLAINED green, INFO gray.

## 6. Build the dashboard

1. Click the **New Dashboard** icon (bottom). On the left, **Size → Fixed size → 1200 × 1000**.
2. Drag a **Text** object (left panel, Objects) to the top. Type:
   - Title: **Wealth NNA Flow Tracker: 3Q26**
   - Line 2 (smaller): *Record $232B at Morgan Stanley WM, but ~half was IPO-related; underlying growth ~5.7%, at the midpoint of the 5–7% target.*
3. Drag **Headline** under the title, then **MS quarterly NNA** full width below it.
4. Drag **Organic growth vs peers** and **Forecast backtest** side by side below that.
5. Drag **Data checks** to the bottom.
6. Add a final **Text** object as a footer: *Source: company earnings releases, 10-K/10-Q filings and earnings calls (Morgan Stanley, Schwab, LPL), through 3Q26. Public data only. Code: github.com/aaradhyaach/wealth-nna-flow-tracker*
7. Tidy: select any chart → its dropdown arrow → uncheck **Title** if the dashboard looks crowded; hide legends you don't need.

## 7. Publish and get your link

1. **File → Save to Tableau Public As…** → sign in → name it **Wealth NNA Flow Tracker**.
2. It opens in your browser on your Tableau Public profile. Click the **settings/edit details** option to add a description (paste the README's opening sentence).
3. Copy the URL from the browser (or use **Share → Copy Link**). That's your resume link.
4. Take a screenshot of the dashboard (Cmd+Shift+4), save it as `tableau_dashboard.png`, and add it to the repo's `reports/figures/` folder.

Note: everything saved to Tableau Public is public. That's fine here, because the data is all public filings.

## Interview tip

Be ready to explain *why* each chart exists: the stacked bar separates repeatable growth from one-offs; the growth chart compares firms of different sizes fairly; the backtest shows the forecast was tested, not just fitted; the checks table shows the numbers were reconciled before anyone saw them.
