{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['calendar_year', 'partner_key', 'commodity_group', 'tariff_type_code', 'combo_code']}
        ]
    )
}}

SELECT
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.has_fta_with_vn,
    dp.fta_name,
    dc.commodity_group,
    dtt.code AS tariff_type_code,
    dtt.label_vi AS tariff_type_label,
    ft.combo_code,
    CASE
        WHEN SUM(COALESCE(ft.total_lines, 0)) > 0
        THEN ROUND((SUM(ft.ad_valorem_pct * ft.total_lines) / SUM(ft.total_lines))::NUMERIC, 4)
        ELSE NULL
    END::NUMERIC(9, 4) AS weighted_avg_tariff_pct,
    SUM(COALESCE(ft.total_lines, 0))::INTEGER AS total_tariff_lines
FROM {{ ref('fact_tariff_rate') }} ft
JOIN {{ ref('dim_date') }} dd        ON dd.date_key        = ft.date_key
JOIN {{ ref('dim_partner') }} dp     ON dp.partner_key     = ft.partner_key
JOIN {{ ref('dim_commodity') }} dc   ON dc.commodity_key   = ft.commodity_key
JOIN {{ ref('dim_tariff_type') }} dtt ON dtt.tariff_type_key = ft.tariff_type_key
WHERE ft.ad_valorem_pct IS NOT NULL
  AND dd.granularity = 'YEAR'
GROUP BY
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.has_fta_with_vn,
    dp.fta_name,
    dc.commodity_group,
    dtt.code,
    dtt.label_vi,
    ft.combo_code
