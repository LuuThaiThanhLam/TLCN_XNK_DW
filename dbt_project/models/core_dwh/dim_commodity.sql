{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['commodity_key'], 'unique': True},
            {'columns': ['hs6'], 'unique': True}
        ]
    )
}}

SELECT
    ROW_NUMBER() OVER (ORDER BY hs6)::INTEGER AS commodity_key,
    hs6,
    hs4,
    hs2,
    name_en,
    commodity_group,
    bridge_flag,
    bridge_note,
    dbt_valid_from AS valid_from,
    dbt_valid_to   AS valid_to,
    (dbt_valid_to IS NULL) AS is_current
FROM {{ ref('snap_dim_commodity') }}
WHERE dbt_valid_to IS NULL
