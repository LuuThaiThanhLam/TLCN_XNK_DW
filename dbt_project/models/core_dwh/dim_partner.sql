{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['partner_key'], 'unique': True},
            {'columns': ['code_comtrade'], 'unique': True}
        ]
    )
}}

SELECT
    ROW_NUMBER() OVER (ORDER BY code_comtrade)::INTEGER AS partner_key,
    code_comtrade,
    partner_name,
    iso3,
    is_aggregate,
    is_vietnam,
    region,
    sub_region,
    income_group,
    has_fta_with_vn,
    fta_name,
    usage_note,
    dbt_valid_from AS valid_from,
    dbt_valid_to   AS valid_to,
    (dbt_valid_to IS NULL) AS is_current
FROM {{ ref('snap_dim_partner') }}
WHERE dbt_valid_to IS NULL
