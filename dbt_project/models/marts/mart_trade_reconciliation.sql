{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['date_key', 'partner_key', 'commodity_key', 'flow_key'], 'unique': True},
            {'columns': ['calendar_year', 'discrepancy_level']},
            {'columns': ['data_source_flag', 'calendar_year']}
        ]
    )
}}

SELECT
    r.date_key,
    dd.calendar_year,
    dd.date_label,
    r.partner_key,
    dp.partner_name,
    dp.region,
    dp.sub_region,
    r.commodity_key,
    dc.hs6,
    dc.commodity_group,
    r.flow_key,
    df.name_vi AS flow_name,
    r.vn_value,
    r.mirror_value_raw,
    r.cif_fob_factor_pct,
    r.mirror_value_adjusted,
    r.best_estimate_usd,
    r.abs_diff_usd,
    r.pct_diff_vs_vn,
    r.discrepancy_level,
    r.data_source_flag,
    r.reconciliation_note
FROM {{ ref('int_trade_reconciliation') }} r
JOIN {{ ref('dim_date') }} dd      ON dd.date_key      = r.date_key
JOIN {{ ref('dim_partner') }} dp   ON dp.partner_key   = r.partner_key
JOIN {{ ref('dim_commodity') }} dc ON dc.commodity_key = r.commodity_key
JOIN {{ ref('dim_flow') }} df      ON df.flow_key      = r.flow_key
