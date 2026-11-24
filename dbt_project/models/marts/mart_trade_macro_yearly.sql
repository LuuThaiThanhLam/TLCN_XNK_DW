{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['calendar_year', 'partner_key'], 'unique': True}
        ]
    )
}}

WITH trade_yearly AS (
    SELECT
        dd.calendar_year,
        dp.partner_key,
        dp.partner_name,
        dp.iso3,
        dp.region,
        SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END)::NUMERIC(18, 3) AS export_value_usd,
        SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END)::NUMERIC(18, 3) AS import_value_usd,
        SUM(f.primary_value_usd)::NUMERIC(18, 3) AS total_trade_usd
    FROM {{ ref('fact_trade') }} f
    JOIN {{ ref('dim_date') }} dd    ON dd.date_key    = f.date_key
    JOIN {{ ref('dim_partner') }} dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = FALSE
      AND dd.granularity = 'MONTH'
    GROUP BY
        dd.calendar_year,
        dp.partner_key,
        dp.partner_name,
        dp.iso3,
        dp.region
),
macro_pivoted AS (
    SELECT
        dd.calendar_year,
        fm.partner_key,
        MAX(CASE WHEN di.code_wb = 'NY.GDP.MKTP.CD' THEN fm.value END)::NUMERIC(18, 2) AS gdp_usd,
        MAX(CASE WHEN di.code_wb = 'NY.GDP.PCAP.CD' THEN fm.value END)::NUMERIC(18, 2) AS gdp_per_capita_usd,
        MAX(CASE WHEN di.code_wb = 'FP.CPI.TOTL.ZG' THEN fm.value END)::NUMERIC(10, 4) AS cpi_inflation_pct,
        MAX(CASE WHEN di.code_wb = 'PA.NUS.FCRF' THEN fm.value END)::NUMERIC(14, 4)    AS exchange_rate_lcu_usd,
        MAX(CASE WHEN di.code_wb = 'NE.TRD.GNFS.ZS' THEN fm.value END)::NUMERIC(10, 4) AS trade_pct_of_gdp
    FROM {{ ref('fact_macro_indicator') }} fm
    JOIN {{ ref('dim_date') }} dd      ON dd.date_key      = fm.date_key
    JOIN {{ ref('dim_indicator') }} di ON di.indicator_key = fm.indicator_key
    WHERE dd.granularity = 'YEAR'
    GROUP BY
        dd.calendar_year,
        fm.partner_key
)
SELECT
    t.calendar_year,
    t.partner_key,
    t.partner_name,
    t.iso3,
    t.region,
    t.export_value_usd,
    t.import_value_usd,
    t.total_trade_usd,
    m.gdp_usd,
    m.gdp_per_capita_usd,
    m.cpi_inflation_pct,
    m.exchange_rate_lcu_usd,
    m.trade_pct_of_gdp,
    ROUND((100.0 * t.total_trade_usd / NULLIF(m.gdp_usd, 0))::NUMERIC, 4) AS vn_trade_to_partner_gdp_pct
FROM trade_yearly t
JOIN macro_pivoted m
  ON m.calendar_year = t.calendar_year
 AND m.partner_key   = t.partner_key
ORDER BY t.partner_name, t.calendar_year
