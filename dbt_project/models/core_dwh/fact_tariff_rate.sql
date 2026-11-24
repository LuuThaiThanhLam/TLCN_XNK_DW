{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['tariff_key'], 'unique': True},
            {'columns': ['date_key', 'partner_key', 'commodity_key', 'tariff_type_key', 'combo_code'], 'unique': True},
            {'columns': ['calendar_year', 'partner_key']}
        ]
    )
}}

SELECT
    ROW_NUMBER() OVER (
        ORDER BY dd.date_key, dp.partner_key, dc.commodity_key, dt.tariff_type_key, s.combo_code
    )::BIGINT AS tariff_key,
    dd.date_key,
    dd.calendar_year,
    dp.partner_key,
    dc.commodity_key,
    dt.tariff_type_key,
    da.audit_key,
    s.combo_code,
    s.ad_valorem_pct,
    s.measure_label,
    s.min_rate,
    s.max_rate,
    s.total_lines,
    s.mfn_lines,
    s.pref_lines,
    s.datatype
FROM {{ ref('stg_wits_tariff') }} s
JOIN {{ ref('dim_date') }} dd        ON dd.date_key = s.date_key
JOIN {{ ref('dim_partner') }} dp     ON dp.code_comtrade = s.partner_code_comtrade
JOIN {{ ref('dim_commodity') }} dc   ON dc.hs6 = s.hs6_mapped
JOIN {{ ref('dim_tariff_type') }} dt ON dt.code = s.tariff_type_code
JOIN {{ ref('dim_audit') }} da       ON da.batch_id = 'wits_tariff_batch'
