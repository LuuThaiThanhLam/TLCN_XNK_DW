SELECT
    dd.calendar_year,
    dp.region,
    df.name_vi AS flow_name,
    ROUND(SUM(f.primary_value_usd) / 1e6, 2) AS total_million_usd,
    GROUPING(dd.calendar_year, dp.region, df.name_vi) AS grouping_id
FROM core_dwh.fact_trade f
JOIN core_dwh.dim_date dd    ON dd.date_key    = f.date_key
JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
JOIN core_dwh.dim_flow df    ON df.flow_key    = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = FALSE
  AND dd.granularity = 'MONTH'
GROUP BY ROLLUP (dd.calendar_year, dp.region, df.name_vi)
ORDER BY grouping_id, dd.calendar_year, dp.region, df.name_vi;

SELECT
    dd.calendar_year,
    dc.commodity_group,
    dp.has_fta_with_vn,
    df.name_vi AS flow_name,
    ROUND(SUM(f.primary_value_usd) / 1e6, 2) AS total_million_usd,
    GROUPING(dd.calendar_year, dc.commodity_group, dp.has_fta_with_vn) AS gs_level
FROM core_dwh.fact_trade f
JOIN core_dwh.dim_date dd      ON dd.date_key      = f.date_key
JOIN core_dwh.dim_partner dp   ON dp.partner_key   = f.partner_key
JOIN core_dwh.dim_commodity dc ON dc.commodity_key = f.commodity_key
JOIN core_dwh.dim_flow df      ON df.flow_key      = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = FALSE
  AND dd.granularity = 'MONTH'
GROUP BY GROUPING SETS (
    (dd.calendar_year, dc.commodity_group, df.name_vi),
    (dd.calendar_year, dp.has_fta_with_vn, df.name_vi),
    (df.name_vi)
)
ORDER BY gs_level, dd.calendar_year;

WITH yearly_export AS (
    SELECT
        dd.calendar_year,
        dp.partner_name,
        SUM(f.primary_value_usd) AS export_usd
    FROM core_dwh.fact_trade f
    JOIN core_dwh.dim_date dd    ON dd.date_key    = f.date_key
    JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND f.flow_key = 1
      AND dp.is_aggregate = FALSE
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, dp.partner_name
)
SELECT
    calendar_year,
    partner_name,
    ROUND(export_usd / 1e6, 2) AS export_mil_usd,
    ROUND(LAG(export_usd) OVER (PARTITION BY partner_name ORDER BY calendar_year) / 1e6, 2) AS prev_year_mil_usd,
    ROUND(
        100.0 * (export_usd - LAG(export_usd) OVER (PARTITION BY partner_name ORDER BY calendar_year))
        / NULLIF(LAG(export_usd) OVER (PARTITION BY partner_name ORDER BY calendar_year), 0),
        2
    ) AS yoy_growth_pct
FROM yearly_export
WHERE partner_name IN ('USA', 'China', 'Rep. of Korea', 'Japan', 'Germany')
ORDER BY partner_name, calendar_year;

SELECT
    calendar_year,
    flow_name,
    hhi_index,
    cr4_pct,
    active_partner_count
FROM mart.mart_market_concentration
ORDER BY flow_name, calendar_year;

SELECT
    calendar_year,
    tariff_type_code,
    ROUND(
        SUM(weighted_avg_tariff_pct * total_tariff_lines) / NULLIF(SUM(total_tariff_lines), 0),
        4
    ) AS overall_weighted_tariff_pct,
    SUM(total_tariff_lines) AS total_lines
FROM mart.mart_tariff_weighted
GROUP BY calendar_year, tariff_type_code
ORDER BY calendar_year, tariff_type_code;

SELECT
    calendar_year,
    data_source_flag,
    COUNT(*) AS cell_count,
    ROUND(SUM(best_estimate_usd) / 1e6, 2) AS best_estimate_mil_usd
FROM mart.mart_trade_reconciliation
GROUP BY calendar_year, data_source_flag
ORDER BY calendar_year, data_source_flag;

WITH trade_yearly AS (
    SELECT
        dd.calendar_year,
        dp.partner_key,
        dp.partner_name,
        SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END) AS export_usd,
        SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END) AS import_usd,
        SUM(f.primary_value_usd) AS total_trade_usd
    FROM core_dwh.fact_trade f
    JOIN core_dwh.dim_date dd    ON dd.date_key    = f.date_key
    JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = FALSE
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, dp.partner_key, dp.partner_name
),
macro_yearly AS (
    SELECT
        dd.calendar_year,
        fm.partner_key,
        MAX(CASE WHEN di.code_wb = 'NY.GDP.MKTP.CD' THEN fm.value END) AS gdp_usd,
        MAX(CASE WHEN di.code_wb = 'PA.NUS.FCRF' THEN fm.value END)    AS exchange_rate_lcu_usd
    FROM core_dwh.fact_macro_indicator fm
    JOIN core_dwh.dim_date dd      ON dd.date_key      = fm.date_key
    JOIN core_dwh.dim_indicator di ON di.indicator_key = fm.indicator_key
    WHERE dd.granularity = 'YEAR'
    GROUP BY dd.calendar_year, fm.partner_key
)
SELECT
    t.calendar_year,
    t.partner_name,
    ROUND((t.total_trade_usd / 1e9)::NUMERIC, 2) AS total_trade_bil_usd,
    ROUND((m.gdp_usd / 1e9)::NUMERIC, 2) AS partner_gdp_bil_usd,
    ROUND(m.exchange_rate_lcu_usd::NUMERIC, 2) AS exchange_rate_lcu_usd,
    ROUND((100.0 * t.total_trade_usd / NULLIF(m.gdp_usd, 0))::NUMERIC, 4) AS trade_to_partner_gdp_pct
FROM trade_yearly t
JOIN macro_yearly m
  ON m.calendar_year = t.calendar_year
 AND m.partner_key   = t.partner_key
ORDER BY t.partner_name, t.calendar_year;
