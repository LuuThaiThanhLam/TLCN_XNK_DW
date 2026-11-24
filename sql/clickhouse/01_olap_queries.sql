SELECT
    dd.calendar_year,
    dp.region,
    df.name_vi AS flow_name,
    round(sum(f.primary_value_usd) / 1e6, 2) AS total_million_usd
FROM olap_xnk.fact_trade AS f
INNER JOIN olap_xnk.dim_date AS dd    ON dd.date_key = f.date_key
INNER JOIN olap_xnk.dim_partner AS dp ON dp.partner_key = f.partner_key
INNER JOIN olap_xnk.dim_flow AS df    ON df.flow_key = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
  AND dd.granularity = 'MONTH'
GROUP BY dd.calendar_year, dp.region, df.name_vi WITH ROLLUP
ORDER BY dd.calendar_year, dp.region, df.name_vi;

SELECT
    dd.calendar_year,
    dc.commodity_group,
    dp.has_fta_with_vn,
    df.name_vi AS flow_name,
    round(sum(f.primary_value_usd) / 1e6, 2) AS total_million_usd
FROM olap_xnk.fact_trade AS f
INNER JOIN olap_xnk.dim_date AS dd      ON dd.date_key = f.date_key
INNER JOIN olap_xnk.dim_partner AS dp   ON dp.partner_key = f.partner_key
INNER JOIN olap_xnk.dim_commodity AS dc ON dc.commodity_key = f.commodity_key
INNER JOIN olap_xnk.dim_flow AS df      ON df.flow_key = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
  AND dd.granularity = 'MONTH'
GROUP BY GROUPING SETS (
    (dd.calendar_year, dc.commodity_group, df.name_vi),
    (dd.calendar_year, dp.has_fta_with_vn, df.name_vi),
    (df.name_vi)
);

SELECT
    calendar_year,
    partner_name,
    round(export_usd / 1e6, 2) AS export_mil_usd,
    round(
        100.0 * (export_usd - lagInFrame(export_usd, 1, 0) OVER (PARTITION BY partner_name ORDER BY calendar_year))
        / nullIf(lagInFrame(export_usd, 1, 0) OVER (PARTITION BY partner_name ORDER BY calendar_year), 0),
        2
    ) AS yoy_growth_pct
FROM (
    SELECT
        dd.calendar_year AS calendar_year,
        dp.partner_name AS partner_name,
        sum(f.primary_value_usd) AS export_usd
    FROM olap_xnk.fact_trade AS f
    INNER JOIN olap_xnk.dim_date AS dd    ON dd.date_key = f.date_key
    INNER JOIN olap_xnk.dim_partner AS dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND f.flow_key = 1
      AND dp.is_aggregate = 0
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, dp.partner_name
)
WHERE partner_name IN ('USA', 'China', 'Rep. of Korea', 'Japan', 'Germany')
ORDER BY partner_name, calendar_year;

WITH yearly_partner AS (
    SELECT
        dd.calendar_year AS calendar_year,
        f.flow_key AS flow_key,
        dp.partner_key AS partner_key,
        sum(f.primary_value_usd) AS partner_value
    FROM olap_xnk.fact_trade AS f
    INNER JOIN olap_xnk.dim_date AS dd    ON dd.date_key = f.date_key
    INNER JOIN olap_xnk.dim_partner AS dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, f.flow_key, dp.partner_key
),
shares AS (
    SELECT
        calendar_year,
        flow_key,
        100.0 * partner_value / nullIf(sum(partner_value) OVER (PARTITION BY calendar_year, flow_key), 0) AS share_pct,
        rank() OVER (PARTITION BY calendar_year, flow_key ORDER BY partner_value DESC) AS rk
    FROM yearly_partner
)
SELECT
    s.calendar_year,
    df.name_vi AS flow_name,
    round(sum(pow(s.share_pct, 2)), 0) AS hhi_index,
    round(sumIf(s.share_pct, s.rk <= 4), 2) AS cr4_pct
FROM shares AS s
INNER JOIN olap_xnk.dim_flow AS df ON df.flow_key = s.flow_key
GROUP BY s.calendar_year, df.name_vi
ORDER BY df.name_vi, s.calendar_year;

SELECT
    ft.calendar_year,
    dtt.code AS tariff_type_code,
    round(
        sum(toFloat64(ft.ad_valorem_pct) * ft.total_lines) / nullIf(sum(ft.total_lines), 0),
        4
    ) AS weighted_avg_tariff_pct,
    sum(ft.total_lines) AS total_lines
FROM olap_xnk.fact_tariff_rate AS ft
INNER JOIN olap_xnk.dim_tariff_type AS dtt ON dtt.tariff_type_key = ft.tariff_type_key
WHERE ft.ad_valorem_pct IS NOT NULL
GROUP BY ft.calendar_year, dtt.code
ORDER BY ft.calendar_year, dtt.code;

SELECT
    calendar_year,
    data_source_flag,
    count() AS cell_count,
    round(sum(best_estimate_usd) / 1e6, 2) AS best_estimate_mil_usd
FROM olap_xnk.mart_trade_reconciliation
GROUP BY calendar_year, data_source_flag
ORDER BY calendar_year, data_source_flag;

WITH trade_yearly AS (
    SELECT
        dd.calendar_year AS calendar_year,
        dp.partner_key AS partner_key,
        dp.partner_name AS partner_name,
        sumIf(toFloat64(f.primary_value_usd), f.flow_key = 1) AS export_usd,
        sumIf(toFloat64(f.primary_value_usd), f.flow_key = 2) AS import_usd,
        sum(toFloat64(f.primary_value_usd)) AS total_trade_usd
    FROM olap_xnk.fact_trade AS f
    INNER JOIN olap_xnk.dim_date AS dd    ON dd.date_key = f.date_key
    INNER JOIN olap_xnk.dim_partner AS dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, dp.partner_key, dp.partner_name
),
macro_yearly AS (
    SELECT
        dd.calendar_year AS calendar_year,
        fm.partner_key AS partner_key,
        max(CASE WHEN di.code_wb = 'NY.GDP.MKTP.CD' THEN toFloat64(fm.value) END) AS gdp_usd,
        max(CASE WHEN di.code_wb = 'PA.NUS.FCRF' THEN toFloat64(fm.value) END)    AS exchange_rate_lcu_usd
    FROM olap_xnk.fact_macro_indicator AS fm
    INNER JOIN olap_xnk.dim_date AS dd      ON dd.date_key = fm.date_key
    INNER JOIN olap_xnk.dim_indicator AS di ON di.indicator_key = fm.indicator_key
    WHERE dd.granularity = 'YEAR'
    GROUP BY dd.calendar_year, fm.partner_key
)
SELECT
    t.calendar_year,
    t.partner_name,
    round(t.total_trade_usd / 1e9, 2) AS total_trade_bil_usd,
    round(m.gdp_usd / 1e9, 2) AS partner_gdp_bil_usd,
    round(m.exchange_rate_lcu_usd, 2) AS exchange_rate_lcu_usd,
    round(100.0 * t.total_trade_usd / nullIf(m.gdp_usd, 0), 4) AS trade_to_partner_gdp_pct
FROM trade_yearly AS t
INNER JOIN macro_yearly AS m
  ON m.calendar_year = t.calendar_year
 AND m.partner_key   = t.partner_key
ORDER BY t.partner_name, t.calendar_year;
