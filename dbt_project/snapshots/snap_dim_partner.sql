{% snapshot snap_dim_partner %}

{{
    config(
      target_schema='snapshots',
      unique_key='code_comtrade',
      strategy='check',
      check_cols=['partner_name', 'region', 'sub_region', 'income_group', 'has_fta_with_vn', 'fta_name']
    )
}}

WITH codes AS (
    SELECT partner_code AS code FROM {{ ref('stg_comtrade_vn') }}
    UNION
    SELECT partner_code_comtrade AS code FROM {{ ref('stg_comtrade_mirror') }}
    UNION
    SELECT '704'::VARCHAR(10) AS code
    UNION
    SELECT '0'::VARCHAR(10) AS code
),
latest_names AS (
    SELECT code, partner_name
    FROM (
        SELECT
            partner_code AS code,
            partner_name,
            ROW_NUMBER() OVER (PARTITION BY partner_code ORDER BY date_key DESC) AS rn
        FROM {{ ref('stg_comtrade_vn') }}
        WHERE NULLIF(TRIM(partner_name), '') IS NOT NULL
    ) ranked
    WHERE rn = 1
),
ref_c AS (
    SELECT * FROM {{ ref('ref_country_codes') }}
)
SELECT
    c.code::VARCHAR(10) AS code_comtrade,
    COALESCE(
        NULLIF(TRIM(r.country_name_en), ''),
        n.partner_name,
        CASE c.code WHEN '704' THEN 'Viet Nam' WHEN '0' THEN 'World' END
    ) AS partner_name,
    NULLIF(TRIM(COALESCE(r.iso3, CASE c.code WHEN '704' THEN 'VNM' ELSE NULL END)), '') AS iso3,
    (c.code = '0' OR COALESCE(r.is_aggregate, 0) = 1) AS is_aggregate,
    (c.code = '704') AS is_vietnam,
    NULLIF(TRIM(r.region), '') AS region,
    NULLIF(TRIM(r.sub_region), '') AS sub_region,
    NULLIF(TRIM(r.income_group), '') AS income_group,
    (COALESCE(r.has_fta_with_vn, 0) = 1) AS has_fta_with_vn,
    NULLIF(TRIM(r.fta_name), '') AS fta_name,
    CASE WHEN c.code = '0'
         THEN 'Aggregate entity for Anchor Audit only (excluded by Rule R3 in rankings)'
         ELSE NULL
    END AS usage_note
FROM codes c
LEFT JOIN latest_names n ON n.code = c.code
LEFT JOIN ref_c r ON TRIM(r.code_comtrade) = c.code

{% endsnapshot %}
