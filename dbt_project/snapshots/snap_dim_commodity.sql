{% snapshot snap_dim_commodity %}

{{
    config(
      target_schema='snapshots',
      unique_key='hs6',
      strategy='check',
      check_cols=['name_en', 'commodity_group', 'bridge_flag']
    )
}}

WITH targets AS (
    SELECT DISTINCT hs6_mapped AS hs6 FROM {{ ref('stg_comtrade_vn') }}
    UNION
    SELECT DISTINCT hs6_mapped AS hs6 FROM {{ ref('stg_comtrade_mirror') }}
),
latest_desc AS (
    SELECT hs6, commodity_desc
    FROM (
        SELECT
            hs6_mapped AS hs6,
            commodity_desc,
            ROW_NUMBER() OVER (
                PARTITION BY hs6_mapped
                ORDER BY
                    CASE WHEN commodity_desc LIKE '[BRIDGED%' THEN 1 ELSE 0 END,
                    date_key DESC
            ) AS rn
        FROM {{ ref('stg_comtrade_vn') }}
        WHERE NULLIF(TRIM(commodity_desc), '') IS NOT NULL
    ) ranked
    WHERE rn = 1
),
bridge AS (
    SELECT DISTINCT hs6_target, note FROM {{ ref('ref_hs_bridge') }}
)
SELECT
    t.hs6::CHAR(6) AS hs6,
    LEFT(t.hs6, 4)::CHAR(4) AS hs4,
    LEFT(t.hs6, 2)::CHAR(2) AS hs2,
    COALESCE(d.commodity_desc, t.hs6) AS name_en,
    CASE
        WHEN t.hs6 IN ('851713', '851762', '854231', '847330', '854442') THEN 'Nhóm 1 · Điện tử – viễn thông'
        WHEN t.hs6 IN ('610910', '640399', '540761')                      THEN 'Nhóm 2 · Dệt may – giày dép'
        WHEN t.hs6 IN ('090111', '090411', '100630', '080132')             THEN 'Nhóm 3 · Nông sản – thực phẩm'
        WHEN t.hs6 IN ('390120', '721049')                                THEN 'Nhóm 4 · Nhựa – công nghiệp nặng'
        ELSE 'Khác'
    END AS commodity_group,
    (b.hs6_target IS NOT NULL) AS bridge_flag,
    b.note AS bridge_note
FROM targets t
LEFT JOIN latest_desc d ON d.hs6 = t.hs6
LEFT JOIN bridge b ON b.hs6_target = t.hs6

{% endsnapshot %}
