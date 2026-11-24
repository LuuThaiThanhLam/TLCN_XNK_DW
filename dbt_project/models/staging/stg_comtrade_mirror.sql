WITH src AS (
    SELECT * FROM {{ source('raw', 'partner_mirror') }}
),
bridge AS (
    SELECT hs6_source, hs6_target FROM {{ ref('ref_hs_bridge') }}
),
cleaned AS (
    SELECT
        TRIM(s.batch_id)                                            AS batch_id,
        CAST(TRIM(s.period) AS INTEGER)                             AS date_key,
        CAST(TRIM(s.year) AS SMALLINT)                              AS calendar_year,
        CAST(TRIM(s.month) AS SMALLINT)                             AS month,
        TRIM(s.flow_code)                                           AS flow_code,
        TRIM(s.reporter_code)                                       AS reporter_code,
        TRIM(s.partner_code)                                        AS partner_code_src,
        TRIM(s.reporter_code)                                       AS partner_code_comtrade,
        FALSE                                                       AS is_aggregate_partner,
        LPAD(
            COALESCE(
                NULLIF(TRIM(s.maps_to_hs6), ''),
                b.hs6_target,
                TRIM(s.hs6)
            ),
            6, '0'
        )                                                           AS hs6_mapped,
        LPAD(
            COALESCE(NULLIF(TRIM(s.hs6_original), ''), TRIM(s.hs6)),
            6, '0'
        )                                                           AS hs6_reported,
        TRIM(s.commodity_desc)                                      AS commodity_desc,
        NULLIF(TRIM(s.primary_value_usd), '')::NUMERIC(18, 3)       AS primary_value_usd,
        NULLIF(TRIM(s.fob_value_usd), '')::NUMERIC(18, 3)           AS fob_value_usd,
        NULLIF(TRIM(s.cif_value_usd), '')::NUMERIC(18, 3)           AS cif_value_usd,
        NULLIF(TRIM(s.net_wgt_kg), '')::NUMERIC(18, 3)              AS net_wgt_kg,
        NULLIF(TRIM(s.qty), '')::NUMERIC(18, 3)                     AS qty,
        TRIM(s.source_system)                                       AS source_system,
        TRIM(s.reporting_perspective)                               AS reporting_perspective,
        TRIM(s.extracted_at)                                        AS extracted_at,
        (UPPER(TRIM(s.is_reported)) IN ('TRUE', '1', 'T'))          AS is_reported,
        TRIM(s.mirror_role)                                         AS mirror_role
    FROM src s
    LEFT JOIN bridge b
      ON b.hs6_source = LPAD(TRIM(s.hs6), 6, '0')
    WHERE NULLIF(TRIM(s.period), '') IS NOT NULL
      AND TRIM(s.flow_code) IN ('X', 'M')
)
SELECT * FROM cleaned
