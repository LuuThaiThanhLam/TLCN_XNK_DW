CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mv_trade_summary AS
SELECT
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    dp.sub_region,
    dp.has_fta_with_vn,
    dc.commodity_key,
    dc.hs6,
    dc.commodity_group,
    df.flow_key,
    df.name_vi AS flow_name,
    SUM(f.primary_value_usd)::NUMERIC(18, 3) AS total_value_usd,
    SUM(COALESCE(f.net_wgt_kg, 0))::NUMERIC(18, 3) AS total_net_wgt_kg,
    COUNT(*)::INTEGER AS record_count
FROM core_dwh.fact_trade_partitioned f
JOIN core_dwh.dim_date dd      ON dd.date_key      = f.date_key
JOIN core_dwh.dim_partner dp   ON dp.partner_key   = f.partner_key
JOIN core_dwh.dim_commodity dc ON dc.commodity_key = f.commodity_key
JOIN core_dwh.dim_flow df      ON df.flow_key      = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = FALSE
  AND dd.granularity = 'MONTH'
GROUP BY
    dd.calendar_year, dp.partner_key, dp.partner_name, dp.region, dp.sub_region,
    dp.has_fta_with_vn, dc.commodity_key, dc.hs6, dc.commodity_group, df.flow_key, df.name_vi
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_trade_summary
    ON mart.mv_trade_summary (calendar_year, partner_key, commodity_key, flow_key);

CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mv_trade_balance AS
SELECT
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END)::NUMERIC(18, 3) AS export_value_usd,
    SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END)::NUMERIC(18, 3) AS import_value_usd,
    (
        SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END)
        - SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END)
    )::NUMERIC(18, 3) AS trade_balance_usd
FROM core_dwh.fact_trade_partitioned f
JOIN core_dwh.dim_date dd    ON dd.date_key    = f.date_key
JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = FALSE
  AND dd.granularity = 'MONTH'
GROUP BY dd.calendar_year, dp.partner_key, dp.partner_name, dp.region
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_trade_balance
    ON mart.mv_trade_balance (calendar_year, partner_key);

CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mv_market_concentration AS
WITH yearly_partner AS (
    SELECT
        dd.calendar_year,
        f.flow_key,
        dp.partner_key,
        SUM(f.primary_value_usd) AS partner_value,
        SUM(SUM(f.primary_value_usd)) OVER (PARTITION BY dd.calendar_year, f.flow_key) AS year_total
    FROM core_dwh.fact_trade_partitioned f
    JOIN core_dwh.dim_date dd    ON dd.date_key    = f.date_key
    JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = FALSE
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, f.flow_key, dp.partner_key
),
shares AS (
    SELECT
        calendar_year,
        flow_key,
        100.0 * partner_value / NULLIF(year_total, 0) AS share_pct,
        RANK() OVER (PARTITION BY calendar_year, flow_key ORDER BY partner_value DESC) AS rk
    FROM yearly_partner
)
SELECT
    s.calendar_year,
    s.flow_key,
    df.name_vi AS flow_name,
    ROUND(SUM(POWER(s.share_pct, 2))::NUMERIC, 0)::INTEGER AS hhi_index,
    ROUND(SUM(CASE WHEN s.rk <= 4 THEN s.share_pct ELSE 0 END)::NUMERIC, 2)::NUMERIC(6, 2) AS cr4_pct
FROM shares s
JOIN core_dwh.dim_flow df ON df.flow_key = s.flow_key
GROUP BY s.calendar_year, s.flow_key, df.name_vi
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_market_concentration
    ON mart.mv_market_concentration (calendar_year, flow_key);

CREATE MATERIALIZED VIEW IF NOT EXISTS mart.mv_trade_reconciliation AS
SELECT
    date_key,
    calendar_year,
    date_label,
    partner_key,
    partner_name,
    region,
    sub_region,
    commodity_key,
    hs6,
    commodity_group,
    flow_key,
    flow_name,
    vn_value,
    mirror_value_raw,
    cif_fob_factor_pct,
    mirror_value_adjusted,
    best_estimate_usd,
    abs_diff_usd,
    pct_diff_vs_vn,
    discrepancy_level,
    data_source_flag
FROM mart.mart_trade_reconciliation
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_trade_reconciliation
    ON mart.mv_trade_reconciliation (date_key, partner_key, commodity_key, flow_key);

ANALYZE mart.mv_trade_summary;
ANALYZE mart.mv_trade_balance;
ANALYZE mart.mv_market_concentration;
ANALYZE mart.mv_trade_reconciliation;
