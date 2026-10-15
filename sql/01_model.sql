-- =====================================================================
-- NNA Tracker: data model (DuckDB; ANSI-style SQL portable to Snowflake)
-- Grain of the core fact: one row per firm x quarter.
-- =====================================================================

-- ---------- Staging: load raw, source-cited files ----------
CREATE OR REPLACE TABLE stg_nna AS
SELECT * FROM read_csv_auto('data/raw/nna_reported.csv', header = true);

CREATE OR REPLACE TABLE stg_client_assets AS
SELECT * FROM read_csv_auto('data/raw/client_assets.csv', header = true);

CREATE OR REPLACE TABLE stg_growth AS
SELECT * FROM read_csv_auto('data/raw/reported_growth_rates.csv', header = true);

CREATE OR REPLACE TABLE stg_events AS
SELECT * FROM read_csv_auto('data/raw/events.csv', header = true);

-- ---------- Calendar dimension ----------
CREATE OR REPLACE TABLE dim_quarter AS
SELECT
    y || 'Q' || q                    AS period,
    y                                AS year,
    q                                AS quarter,
    (y - 2023) * 4 + q               AS q_index,
    make_date(y, q * 3, 1) + INTERVAL 1 MONTH - INTERVAL 1 DAY AS quarter_end
FROM range(2023, 2027) t(y), range(1, 5) s(q)
WHERE NOT (y = 2026 AND q = 4);

-- ---------- Quarterly NNA: pick one value per firm-quarter ----------
-- Rule: prefer the figure printed in the firm's own release for that quarter
-- ("current quarter"); otherwise the prior-year comparative column.
CREATE OR REPLACE TABLE int_nna_reported_q AS
SELECT firm, period, value_bn AS nna_bn, source_doc, source_url,
       'reported' AS nna_method
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY firm, period
               ORDER BY CASE WHEN report_context LIKE 'current quarter%' THEN 0
                             WHEN source_doc NOT LIKE '%TipRanks%'      THEN 1
                             ELSE 2 END
           ) AS rn
    FROM stg_nna
    WHERE period_type = 'Q'
)
WHERE rn = 1;

-- Gap-fill quarters that are only disclosed inside an annual or half-year total.
CREATE OR REPLACE TABLE int_nna_derived_q AS
-- Schwab 3Q25 = FY25 - (1Q25 + 2Q25 + 4Q25)
SELECT 'SCHW' AS firm, '2025Q3' AS period,
       fy.value_bn - SUM(q.nna_bn) AS nna_bn,
       'Derived: FY25 total less other three quarters' AS source_doc,
       fy.source_url, 'derived' AS nna_method
FROM stg_nna fy
JOIN int_nna_reported_q q
  ON q.firm = 'SCHW' AND q.period IN ('2025Q1', '2025Q2', '2025Q4')
WHERE fy.firm = 'SCHW' AND fy.period = '2025' AND fy.period_type = 'FY'
GROUP BY fy.value_bn, fy.source_url
UNION ALL
-- Schwab 1Q24 = 1H24 - 2Q24
SELECT 'SCHW', '2024Q1', h.value_bn - q.nna_bn,
       'Derived: 1H24 total less 2Q24', h.source_url, 'derived'
FROM stg_nna h
JOIN int_nna_reported_q q ON q.firm = 'SCHW' AND q.period = '2024Q2'
WHERE h.firm = 'SCHW' AND h.period = '2024H1';

CREATE OR REPLACE TABLE fct_nna_quarterly AS
SELECT n.*, d.year, d.quarter, d.q_index, d.quarter_end
FROM (SELECT * FROM int_nna_reported_q UNION ALL SELECT * FROM int_nna_derived_q) n
JOIN dim_quarter d USING (period);

-- ---------- Client assets: anchors + linear interpolation ----------
-- Schwab year-end 2024 is backed out from "up 18% on the year" in the 2025 10-K.
CREATE OR REPLACE TABLE int_assets_anchor AS
SELECT firm, period, client_assets_bn, precision, source_doc, source_url
FROM stg_client_assets
UNION ALL
SELECT 'SCHW', '2024Q4', ROUND(11900 / 1.18, 1),
       'derived (FY25 $11.90T / 1.18)', 'Schwab 2025 Form 10-K',
       'https://www.sec.gov/Archives/edgar/data/316709/000031670926000009/schw-20251231.htm';

CREATE OR REPLACE TABLE dim_client_assets AS
WITH grid AS (
    SELECT f.firm, d.period, d.q_index
    FROM (SELECT DISTINCT firm FROM int_assets_anchor) f CROSS JOIN dim_quarter d
),
anch AS (
    SELECT a.*, d.q_index FROM int_assets_anchor a JOIN dim_quarter d USING (period)
),
bounded AS (
    SELECT g.firm, g.period, g.q_index,
        (SELECT MAX(q_index) FROM anch a WHERE a.firm = g.firm AND a.q_index <= g.q_index) AS lo_q,
        (SELECT MIN(q_index) FROM anch a WHERE a.firm = g.firm AND a.q_index >= g.q_index) AS hi_q
    FROM grid g
)
SELECT b.firm, b.period, b.q_index,
       CASE WHEN b.lo_q = b.hi_q THEN lo.client_assets_bn
            ELSE lo.client_assets_bn
                 + (hi.client_assets_bn - lo.client_assets_bn)
                   * (b.q_index - b.lo_q) / (b.hi_q - b.lo_q)
       END AS client_assets_bn,
       CASE WHEN b.lo_q = b.hi_q THEN 'anchor: ' || lo.precision
            ELSE 'interpolated' END AS assets_method
FROM bounded b
JOIN anch lo ON lo.firm = b.firm AND lo.q_index = b.lo_q
JOIN anch hi ON hi.firm = b.firm AND hi.q_index = b.hi_q
WHERE b.lo_q IS NOT NULL AND b.hi_q IS NOT NULL;

-- ---------- Mart: organic growth, normalized flows, share of peer flows ----------
CREATE OR REPLACE TABLE mart_nna AS
WITH ev AS (
    SELECT firm, period, SUM(est_nna_impact_bn) AS event_bn, STRING_AGG(event, '; ') AS events
    FROM stg_events GROUP BY 1, 2
)
SELECT f.firm, f.period, f.year, f.quarter, f.q_index,
       f.nna_bn, f.nna_method,
       COALESCE(ev.event_bn, 0)                      AS event_bn,
       f.nna_bn - COALESCE(ev.event_bn, 0)           AS nna_ex_events_bn,
       ev.events,
       a.client_assets_bn                            AS begin_assets_bn,
       a.assets_method                               AS begin_assets_method,
       4 * f.nna_bn / a.client_assets_bn             AS organic_growth_ann,
       4 * (f.nna_bn - COALESCE(ev.event_bn, 0)) / a.client_assets_bn AS organic_growth_ex_events_ann,
       f.nna_bn / LAG(f.nna_bn, 4) OVER (PARTITION BY f.firm ORDER BY f.q_index) - 1 AS nna_yoy,
       SUM(f.nna_bn) OVER (PARTITION BY f.firm ORDER BY f.q_index
                           ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS nna_ttm_bn,
       COUNT(*) OVER (PARTITION BY f.firm ORDER BY f.q_index
                      ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ttm_quarters,
       f.source_doc, f.source_url
FROM fct_nna_quarterly f
LEFT JOIN ev ON ev.firm = f.firm AND ev.period = f.period
LEFT JOIN dim_client_assets a
       ON a.firm = f.firm AND a.q_index = f.q_index - 1;

-- Share of peer-set flows, only for quarters where all three firms have reported.
CREATE OR REPLACE TABLE mart_peer_share AS
WITH full_q AS (
    SELECT period FROM fct_nna_quarterly GROUP BY period HAVING COUNT(DISTINCT firm) = 3
)
SELECT m.period, m.firm, m.nna_bn,
       m.nna_bn / SUM(m.nna_bn) OVER (PARTITION BY m.period) AS share_of_peer_nna
FROM mart_nna m JOIN full_q USING (period);
