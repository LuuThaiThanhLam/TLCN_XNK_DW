WITH src AS (
    SELECT * FROM {{ source('raw', 'wb_macro') }}
)
SELECT
    CAST(TRIM(year) AS INTEGER) * 100                               AS date_key,
    CAST(TRIM(year) AS SMALLINT)                                    AS calendar_year,
    UPPER(TRIM(country_iso3))                                       AS country_iso3,
    TRIM(country_name)                                              AS country_name,
    TRIM(indicator)                                                 AS code_wb,
    TRIM(indicator_name)                                            AS indicator_name,
    NULLIF(TRIM(value), '')::DOUBLE PRECISION::NUMERIC(18, 2)       AS value,
    TRIM(source_system)                                             AS source_system,
    TRIM(extracted_at)                                              AS extracted_at
FROM src
WHERE NULLIF(TRIM(year), '') IS NOT NULL
  AND NULLIF(TRIM(country_iso3), '') IS NOT NULL
