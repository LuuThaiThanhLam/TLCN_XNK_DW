{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['calendar_year', 'partner_key'], 'unique': True}
        ]
    )
}}

SELECT
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    dp.has_fta_with_vn,
    dp.fta_name,
    SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END)::NUMERIC(18, 3) AS export_value_usd,
    SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END)::NUMERIC(18, 3) AS import_value_usd,
    (
        SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END)
        - SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END)
    )::NUMERIC(18, 3) AS trade_balance_usd,
    COUNT(DISTINCT f.commodity_key)::INTEGER AS commodity_diversity,
    'Trong phạm vi rổ 14 mã HS6 khảo sát'::VARCHAR(80) AS scope_note
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
    dp.region,
    dp.has_fta_with_vn,
    dp.fta_name
