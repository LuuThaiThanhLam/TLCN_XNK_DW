WITH vn AS (
    SELECT
        batch_id,
        date_key,
        calendar_year,
        month,
        flow_code,
        reporter_code,
        partner_code                                                AS partner_code_comtrade,
        partner_code                                                AS partner_code_src,
        is_aggregate_partner,
        hs6_mapped,
        hs6_reported,
        primary_value_usd,
        fob_value_usd,
        cif_value_usd,
        net_wgt_kg,
        qty,
        'VN_REPORTED'::VARCHAR(20)                                  AS perspective_code,
        source_system,
        CAST(NULL AS VARCHAR(20))                                   AS mirror_role,
        CAST(NULL AS BOOLEAN)                                       AS is_reported
    FROM {{ ref('stg_comtrade_vn') }}
),
mirror AS (
    SELECT
        batch_id,
        date_key,
        calendar_year,
        month,
        flow_code,
        reporter_code,
        partner_code_comtrade,
        partner_code_src,
        is_aggregate_partner,
        hs6_mapped,
        hs6_reported,
        primary_value_usd,
        fob_value_usd,
        cif_value_usd,
        net_wgt_kg,
        qty,
        'PARTNER_MIRROR'::VARCHAR(20)                               AS perspective_code,
        source_system,
        mirror_role,
        is_reported
    FROM {{ ref('stg_comtrade_mirror') }}
)
SELECT * FROM vn
UNION ALL
SELECT * FROM mirror
