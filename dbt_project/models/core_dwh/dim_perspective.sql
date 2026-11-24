{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['perspective_key'], 'unique': True},
            {'columns': ['code'], 'unique': True}
        ]
    )
}}

SELECT
    1::SMALLINT AS perspective_key,
    'VN_REPORTED'::VARCHAR(20) AS code,
    'Việt Nam khai'::VARCHAR(40) AS label_vi,
    'Số liệu chính thức phía Việt Nam báo cáo trên UN Comtrade (2015–2023; gián đoạn năm 2024).'::VARCHAR(300) AS reliability_note
UNION ALL
SELECT
    2::SMALLINT AS perspective_key,
    'PARTNER_MIRROR'::VARCHAR(20) AS code,
    'Đối tác khai về VN'::VARCHAR(40) AS label_vi,
    'Số liệu gương do 5 đối tác chiến lược báo cáo song phương với Việt Nam (2015–2024).'::VARCHAR(300) AS reliability_note
