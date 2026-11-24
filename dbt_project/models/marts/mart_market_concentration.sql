{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['calendar_year', 'flow_key'], 'unique': True}
        ]
    )
}}

WITH yearly_partner AS (
    SELECT
        dd.calendar_year,
        f.flow_key,
        dp.partner_key,
        dp.partner_name,
        SUM(f.primary_value_usd) AS partner_value,
        SUM(SUM(f.primary_value_usd)) OVER (
            PARTITION BY dd.calendar_year, f.flow_key
        ) AS year_total
    FROM {{ ref('fact_trade') }} f
    JOIN {{ ref('dim_date') }} dd    ON dd.date_key    = f.date_key
    JOIN {{ ref('dim_partner') }} dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = FALSE
      AND dd.granularity = 'MONTH'
    GROUP BY dd.calendar_year, f.flow_key, dp.partner_key, dp.partner_name
),
shares AS (
    SELECT
        calendar_year,
        flow_key,
        partner_key,
        partner_name,
        100.0 * partner_value / NULLIF(year_total, 0) AS market_share_pct,
        RANK() OVER (PARTITION BY calendar_year, flow_key ORDER BY partner_value DESC) AS partner_rank
    FROM yearly_partner
)
SELECT
    s.calendar_year,
    s.flow_key,
    df.name_vi AS flow_name,
    ROUND(SUM(POWER(s.market_share_pct, 2))::NUMERIC, 0)::INTEGER AS hhi_index,
    ROUND(SUM(CASE WHEN s.partner_rank <= 4 THEN s.market_share_pct ELSE 0 END)::NUMERIC, 2)::NUMERIC(6, 2) AS cr4_pct,
    COUNT(DISTINCT s.partner_key)::INTEGER AS active_partner_count
FROM shares s
JOIN {{ ref('dim_flow') }} df ON df.flow_key = s.flow_key
GROUP BY s.calendar_year, s.flow_key, df.name_vi
ORDER BY s.calendar_year, s.flow_key
