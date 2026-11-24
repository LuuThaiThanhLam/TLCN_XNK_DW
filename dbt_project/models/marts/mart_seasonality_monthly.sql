{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['month', 'flow_key'], 'unique': True}
        ]
    )
}}

WITH monthly_totals AS (
    SELECT
        dd.month,
        dd.calendar_year,
        f.flow_key,
        df.name_vi AS flow_name,
        SUM(f.primary_value_usd) AS monthly_value_usd
    FROM {{ ref('fact_trade') }} f
    JOIN {{ ref('dim_date') }} dd    ON dd.date_key    = f.date_key
    JOIN {{ ref('dim_partner') }} dp ON dp.partner_key = f.partner_key
    JOIN {{ ref('dim_flow') }} df    ON df.flow_key    = f.flow_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = FALSE
      AND dd.granularity = 'MONTH'
      AND dd.month BETWEEN 1 AND 12
    GROUP BY dd.month, dd.calendar_year, f.flow_key, df.name_vi
),
monthly_stats AS (
    SELECT
        month,
        flow_key,
        flow_name,
        AVG(monthly_value_usd) AS avg_monthly_usd,
        MIN(monthly_value_usd) AS min_monthly_usd,
        MAX(monthly_value_usd) AS max_monthly_usd,
        COUNT(*)::INTEGER AS year_count
    FROM monthly_totals
    GROUP BY month, flow_key, flow_name
)
SELECT
    month,
    flow_key,
    flow_name,
    ROUND(avg_monthly_usd::NUMERIC, 0)::NUMERIC(18, 0) AS avg_monthly_usd,
    ROUND(min_monthly_usd::NUMERIC, 0)::NUMERIC(18, 0) AS min_monthly_usd,
    ROUND(max_monthly_usd::NUMERIC, 0)::NUMERIC(18, 0) AS max_monthly_usd,
    year_count,
    ROUND((100.0 * avg_monthly_usd / NULLIF(AVG(avg_monthly_usd) OVER (PARTITION BY flow_key), 0))::NUMERIC, 2)::NUMERIC(6, 2) AS seasonal_index_pct,
    CASE
        WHEN avg_monthly_usd > 1.10 * AVG(avg_monthly_usd) OVER (PARTITION BY flow_key) THEN 'Cao điểm'
        WHEN avg_monthly_usd < 0.90 * AVG(avg_monthly_usd) OVER (PARTITION BY flow_key) THEN 'Thấp điểm'
        ELSE 'Bình thường'
    END::VARCHAR(20) AS season_label
FROM monthly_stats
ORDER BY flow_key, month
