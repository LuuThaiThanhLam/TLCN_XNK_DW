{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['calendar_year', 'partner_key', 'commodity_key', 'flow_key'], 'unique': True},
            {'columns': ['region', 'calendar_year']},
            {'columns': ['commodity_group', 'calendar_year']}
        ]
    )
}}

SELECT
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    dp.sub_region,
    dp.has_fta_with_vn,
    dp.fta_name,
    dc.commodity_key,
    dc.hs6,
    dc.hs4,
    dc.hs2,
    dc.commodity_group,
    dc.name_en AS commodity_name,
    df.flow_key,
    df.name_vi AS flow_name,
    SUM(f.primary_value_usd)::NUMERIC(18, 3) AS total_value_usd,
    SUM(COALESCE(f.net_wgt_kg, 0))::NUMERIC(18, 3) AS total_net_wgt_kg,
    SUM(COALESCE(f.fob_value_usd, 0))::NUMERIC(18, 3) AS total_fob_usd,
    SUM(COALESCE(f.cif_value_usd, 0))::NUMERIC(18, 3) AS total_cif_usd,
    COUNT(*)::INTEGER AS monthly_record_count
FROM {{ ref('fact_trade') }} f
JOIN {{ ref('dim_date') }} dd      ON dd.date_key      = f.date_key
JOIN {{ ref('dim_partner') }} dp   ON dp.partner_key   = f.partner_key
JOIN {{ ref('dim_commodity') }} dc ON dc.commodity_key = f.commodity_key
JOIN {{ ref('dim_flow') }} df      ON df.flow_key      = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = FALSE
  AND dd.granularity = 'MONTH'
GROUP BY
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    dp.sub_region,
    dp.has_fta_with_vn,
    dp.fta_name,
    dc.commodity_key,
    dc.hs6,
    dc.hs4,
    dc.hs2,
    dc.commodity_group,
    dc.name_en,
    df.flow_key,
    df.name_vi
