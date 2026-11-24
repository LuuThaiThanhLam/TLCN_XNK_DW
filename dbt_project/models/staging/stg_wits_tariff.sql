WITH src AS (
    SELECT * FROM {{ source('raw', 'wits_tariff') }}
),
bridge AS (
    SELECT hs6_source, hs6_target FROM {{ ref('ref_hs_bridge') }}
),
ranked AS (
    SELECT
        CAST(TRIM(s.year) AS INTEGER) * 100                         AS date_key,
        CAST(TRIM(s.year) AS SMALLINT)                              AS calendar_year,
        CASE
            WHEN TRIM(s.reporter_code) = '704' THEN
                CASE WHEN TRIM(s.partner_code) IN ('000', '0') THEN '0'
                     ELSE TRIM(s.partner_code)
                END
            ELSE TRIM(s.reporter_code)
        END                                                         AS partner_code_comtrade,
        LPAD(
            COALESCE(b.hs6_target, TRIM(s.hs6)),
            6, '0'
        )                                                           AS hs6_mapped,
        LPAD(TRIM(s.hs6), 6, '0')                                   AS hs6_reported,
        TRIM(s.tariff_type)                                         AS tariff_type_code,
        TRIM(s.combo_type)                                          AS combo_code,
        NULLIF(TRIM(s.rate_pct), '')::NUMERIC(9, 4)                 AS ad_valorem_pct,
        NULLIF(TRIM(s.measure), '')                                 AS measure_label,
        NULLIF(TRIM(s.min_rate), '')::NUMERIC(9, 4)                 AS min_rate,
        NULLIF(TRIM(s.max_rate), '')::NUMERIC(9, 4)                 AS max_rate,
        NULLIF(TRIM(s.total_lines), '')::INTEGER                    AS total_lines,
        NULLIF(TRIM(s.mfn_lines), '')::INTEGER                      AS mfn_lines,
        NULLIF(TRIM(s.pref_lines), '')::INTEGER                     AS pref_lines,
        NULLIF(TRIM(s.nomenclature), '')                            AS nomenclature,
        NULLIF(TRIM(s.datatype), '')                                AS datatype,
        TRIM(s.source_system)                                       AS source_system,
        TRIM(s.extracted_at)                                        AS extracted_at,
        ROW_NUMBER() OVER (
            PARTITION BY
                CAST(TRIM(s.year) AS SMALLINT),
                TRIM(s.reporter_code),
                TRIM(s.partner_code),
                LPAD(COALESCE(b.hs6_target, TRIM(s.hs6)), 6, '0'),
                TRIM(s.tariff_type),
                TRIM(s.combo_type)
            ORDER BY NULLIF(TRIM(s.nomenclature), '') DESC NULLS LAST
        )                                                           AS rn
    FROM src s
    LEFT JOIN bridge b
      ON b.hs6_source = LPAD(TRIM(s.hs6), 6, '0')
    WHERE NULLIF(TRIM(s.year), '') IS NOT NULL
)
SELECT
    date_key,
    calendar_year,
    partner_code_comtrade,
    hs6_mapped,
    hs6_reported,
    tariff_type_code,
    combo_code,
    ad_valorem_pct,
    measure_label,
    min_rate,
    max_rate,
    total_lines,
    mfn_lines,
    pref_lines,
    nomenclature,
    datatype,
    source_system,
    extracted_at
FROM ranked
WHERE rn = 1
