{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['date_key'], 'unique': True},
            {'columns': ['calendar_year', 'granularity']}
        ]
    )
}}

WITH months AS (
    SELECT DISTINCT date_key
    FROM {{ ref('stg_comtrade_vn') }}
    UNION
    SELECT DISTINCT date_key
    FROM {{ ref('stg_comtrade_mirror') }}
),
years AS (
    SELECT DISTINCT (calendar_year::INTEGER * 100) AS date_key
    FROM {{ ref('stg_comtrade_vn') }}
    UNION
    SELECT DISTINCT (calendar_year::INTEGER * 100) AS date_key
    FROM {{ ref('stg_comtrade_mirror') }}
    UNION
    SELECT DISTINCT date_key
    FROM {{ ref('stg_wits_tariff') }}
    UNION
    SELECT DISTINCT date_key
    FROM {{ ref('stg_wb_macro') }}
),
combined AS (
    SELECT date_key, 'MONTH'::VARCHAR(5) AS granularity FROM months
    UNION
    SELECT date_key, 'YEAR'::VARCHAR(5)  AS granularity FROM years
)
SELECT
    date_key,
    (date_key / 100)::SMALLINT AS calendar_year,
    CASE WHEN granularity = 'MONTH'
         THEN (((date_key % 100) - 1) / 3 + 1)::SMALLINT
         ELSE NULL
    END AS quarter,
    CASE WHEN granularity = 'MONTH'
         THEN (date_key % 100)::SMALLINT
         ELSE NULL
    END AS month,
    granularity,
    CASE WHEN granularity = 'MONTH'
         THEN (date_key / 100)::TEXT || '-' || LPAD((date_key % 100)::TEXT, 2, '0')
         ELSE (date_key / 100)::TEXT
    END::VARCHAR(7) AS date_label
FROM combined
ORDER BY date_key
