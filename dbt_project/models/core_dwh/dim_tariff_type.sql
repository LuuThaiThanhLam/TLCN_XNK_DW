{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['tariff_type_key'], 'unique': True},
            {'columns': ['code'], 'unique': True}
        ]
    )
}}

SELECT
    1::SMALLINT AS tariff_type_key,
    'MFN'::VARCHAR(10) AS code,
    'Thuế MFN (Tối huệ quốc)'::VARCHAR(60) AS label_vi,
    'Thuế suất tối huệ quốc áp dụng chung (2015–2023).'::VARCHAR(300) AS coverage_note
UNION ALL
SELECT
    2::SMALLINT AS tariff_type_key,
    'PREF'::VARCHAR(10) AS code,
    'Thuế ưu đãi (Effectively Applied - AHS)'::VARCHAR(60) AS label_vi,
    'Thuế suất ưu đãi thực tế áp dụng theo hiệp định song phương từ WITS TRAINS.'::VARCHAR(300) AS coverage_note
