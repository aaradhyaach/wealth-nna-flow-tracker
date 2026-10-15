-- =====================================================================
-- Validation layer: every check returns one row per test with a status.
-- PASS = within tolerance, WARN = explainable gap, FAIL = needs a human.
-- =====================================================================
CREATE OR REPLACE TABLE validation_results AS

-- V1. Same firm-quarter printed in two places must agree (restatement check)
SELECT 'V1 cross-source agreement' AS check_name,
       firm || ' ' || period AS subject,
       MIN(value_bn) AS expected, MAX(value_bn) AS actual,
       MAX(value_bn) - MIN(value_bn) AS diff,
       CASE WHEN MAX(value_bn) - MIN(value_bn) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
       STRING_AGG(source_doc || ' = ' || value_bn, ' | ') AS detail
FROM stg_nna WHERE period_type = 'Q'
GROUP BY firm, period HAVING COUNT(*) > 1

UNION ALL
-- V2. Four quarters must sum to the reported full year (rounding tolerance $0.15B)
SELECT 'V2 quarters sum to full year', fy.firm || ' ' || fy.period,
       fy.value_bn, SUM(q.nna_bn), SUM(q.nna_bn) - fy.value_bn,
       CASE WHEN COUNT(*) < 4 THEN 'WARN'
            WHEN ABS(SUM(q.nna_bn) - fy.value_bn) <= 0.15 THEN 'PASS' ELSE 'FAIL' END,
       COUNT(*) || ' quarters found; methods: ' || STRING_AGG(DISTINCT q.nna_method, ',' ORDER BY q.nna_method)
FROM (SELECT DISTINCT firm, period, value_bn FROM stg_nna WHERE period_type = 'FY') fy
JOIN fct_nna_quarterly q ON q.firm = fy.firm AND q.year = CAST(fy.period AS INT)
GROUP BY fy.firm, fy.period, fy.value_bn

UNION ALL
-- V3. Half-year and YTD narrative totals vs sum of quarters (narrative figures are rounded)
SELECT 'V3 narrative totals vs quarters', s.firm || ' ' || s.period,
       s.value_bn, SUM(q.nna_bn), SUM(q.nna_bn) - s.value_bn,
       CASE WHEN ABS(SUM(q.nna_bn) - s.value_bn) / s.value_bn <= 0.02 THEN 'PASS' ELSE 'FAIL' END,
       s.report_context
FROM stg_nna s
JOIN fct_nna_quarterly q
  ON q.firm = s.firm AND q.year = CAST(LEFT(s.period, 4) AS INT)
 AND q.quarter <= CASE s.period_type WHEN 'H1' THEN 2 ELSE CAST(RIGHT(s.period, 1) AS INT) END
 AND q.nna_method = 'reported'
WHERE s.period_type IN ('H1', 'YTD')
  AND NOT (s.firm = 'SCHW' AND s.period = '2024H1')   -- used to derive 1Q24, so not an independent test
GROUP BY s.firm, s.period, s.value_bn, s.report_context

UNION ALL
-- V4. Our computed organic growth vs the firm's own reported rate (tolerance 0.25pp)
SELECT 'V4 computed vs reported growth', g.firm || ' ' || g.period,
       g.reported_annualized_growth, c.computed, c.computed - g.reported_annualized_growth,
       CASE WHEN c.computed IS NULL THEN 'INFO'
            WHEN ABS(c.computed - g.reported_annualized_growth) <= 0.0025 THEN 'PASS'
            ELSE 'WARN' END,
       CASE WHEN c.computed IS NULL THEN 'not testable: no sourced beginning-period assets'
            ELSE 'begin assets: ' || c.method END
FROM stg_growth g
LEFT JOIN (
    SELECT firm, period, organic_growth_ann AS computed, begin_assets_method AS method
    FROM mart_nna
    UNION ALL
    SELECT m.firm, CAST(m.year AS VARCHAR), SUM(m.nna_bn) / MAX(a.client_assets_bn), MAX(a.assets_method)
    FROM mart_nna m
    JOIN dim_client_assets a ON a.firm = m.firm AND a.period = (m.year - 1) || 'Q4'
    GROUP BY m.firm, m.year HAVING COUNT(*) = 4
) c ON c.firm = g.firm AND c.period = g.period

UNION ALL
-- V5. Completeness: every firm-quarter in scope is present (gaps are flagged, not filled silently)
SELECT 'V5 completeness', f.firm || ' ' || d.period, NULL, NULL, NULL,
       CASE WHEN n.nna_bn IS NULL THEN 'WARN' ELSE 'PASS' END,
       CASE WHEN n.nna_bn IS NULL THEN 'not yet reported / not sourced' ELSE n.nna_method END
FROM (VALUES ('MS', 1), ('SCHW', 9), ('LPLA', 8)) f(firm, first_q)
JOIN dim_quarter d ON d.q_index >= f.first_q
LEFT JOIN fct_nna_quarterly n ON n.firm = f.firm AND n.period = d.period

UNION ALL
-- V6. Outlier flag: quarter > 2 std dev from the firm's trailing mean (forces a "why" before it ships)
SELECT 'V6 outlier review', firm || ' ' || period, ROUND(mu, 1), nna_bn, ROUND(nna_bn - mu, 1),
       CASE WHEN ABS(nna_bn - mu) <= 2 * sd THEN 'PASS'
            WHEN events IS NOT NULL THEN 'EXPLAINED' ELSE 'WARN' END,
       COALESCE('known driver: ' || events, 'no tagged event')
FROM (
    SELECT *, AVG(nna_bn) OVER w AS mu, STDDEV_SAMP(nna_bn) OVER w AS sd
    FROM mart_nna
    WINDOW w AS (PARTITION BY firm ORDER BY q_index ROWS BETWEEN 8 PRECEDING AND 1 PRECEDING)
) WHERE sd IS NOT NULL;
