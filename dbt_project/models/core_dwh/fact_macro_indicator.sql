{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['macro_key'], 'unique': True},
            {'columns': ['date_key', 'partner_key', 'indicator_key'], 'unique': True}
        ]
    )
}}

SELECT
    ROW_NUMBER() OVER (
        ORDER BY dd.date_key, dp.partner_key, di.indicator_key
    )::BIGINT AS macro_key,
    dd.date_key,
    dd.calendar_year,
    dp.partner_key,
    di.indicator_key,
    da.audit_key,
    s.value
FROM {{ ref('stg_wb_macro') }} s
JOIN {{ ref('dim_date') }} dd      ON dd.date_key = s.date_key
JOIN {{ ref('dim_partner') }} dp   ON dp.iso3 = s.country_iso3
JOIN {{ ref('dim_indicator') }} di ON di.code_wb = s.code_wb
JOIN {{ ref('dim_audit') }} da     ON da.batch_id = 'wb_macro_batch'
