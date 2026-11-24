{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['trade_key'], 'unique': True},
            {'columns': ['date_key', 'partner_key', 'commodity_key', 'flow_key', 'perspective_key'], 'unique': True},
            {'columns': ['commodity_key', 'date_key']},
            {'columns': ['partner_key', 'date_key']},
            {'columns': ['calendar_year', 'perspective_key']}
        ]
    )
}}

SELECT
    ROW_NUMBER() OVER (
        ORDER BY u.date_key, dp.partner_key, dc.commodity_key, df.flow_key, dv.perspective_key
    )::BIGINT AS trade_key,
    dd.date_key,
    dd.calendar_year,
    u.month,
    dp.partner_key,
    dc.commodity_key,
    df.flow_key,
    dv.perspective_key,
    da.audit_key,
    u.primary_value_usd,
    u.net_wgt_kg,
    u.qty,
    u.fob_value_usd,
    u.cif_value_usd,
    u.hs6_reported::CHAR(6) AS hs6_reported,
    u.reporter_code,
    u.partner_code_src,
    u.is_aggregate_partner,
    u.mirror_role,
    u.is_reported
FROM {{ ref('int_trade_unified') }} u
JOIN {{ ref('dim_date') }} dd        ON dd.date_key = u.date_key
JOIN {{ ref('dim_partner') }} dp     ON dp.code_comtrade = u.partner_code_comtrade
JOIN {{ ref('dim_commodity') }} dc   ON dc.hs6 = u.hs6_mapped
JOIN {{ ref('dim_flow') }} df        ON df.flow_code = u.flow_code
JOIN {{ ref('dim_perspective') }} dv ON dv.code = u.perspective_code
JOIN {{ ref('dim_audit') }} da       ON da.batch_id = u.batch_id
