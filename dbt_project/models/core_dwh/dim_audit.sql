{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['audit_key'], 'unique': True},
            {'columns': ['batch_id'], 'unique': True}
        ]
    )
}}

WITH batches AS (
    SELECT
        batch_id,
        source_system,
        'stg_comtrade_all_partners_monthly.csv'::VARCHAR(120) AS staging_file,
        MAX(extracted_at) AS extracted_at,
        COUNT(*) AS row_count
    FROM {{ ref('stg_comtrade_vn') }}
    GROUP BY batch_id, source_system

    UNION ALL

    SELECT
        batch_id,
        source_system,
        'stg_comtrade_partner_mirror.csv'::VARCHAR(120) AS staging_file,
        MAX(extracted_at) AS extracted_at,
        COUNT(*) AS row_count
    FROM {{ ref('stg_comtrade_mirror') }}
    GROUP BY batch_id, source_system

    UNION ALL

    SELECT
        'wits_tariff_batch'::VARCHAR(50) AS batch_id,
        MAX(source_system) AS source_system,
        'stg_wits_tariff.csv'::VARCHAR(120) AS staging_file,
        MAX(extracted_at) AS extracted_at,
        COUNT(*) AS row_count
    FROM {{ ref('stg_wits_tariff') }}

    UNION ALL

    SELECT
        'wb_macro_batch'::VARCHAR(50) AS batch_id,
        MAX(source_system) AS source_system,
        'stg_wb_macro.csv'::VARCHAR(120) AS staging_file,
        MAX(extracted_at) AS extracted_at,
        COUNT(*) AS row_count
    FROM {{ ref('stg_wb_macro') }}
)
SELECT
    ROW_NUMBER() OVER (ORDER BY source_system, batch_id)::INTEGER AS audit_key,
    batch_id,
    source_system,
    staging_file,
    extracted_at,
    row_count
FROM batches
