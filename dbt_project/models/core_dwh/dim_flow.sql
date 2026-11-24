{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['flow_key'], 'unique': True},
            {'columns': ['flow_code'], 'unique': True}
        ]
    )
}}

SELECT
    1::SMALLINT AS flow_key,
    'X'::CHAR(1) AS flow_code,
    'Xuất khẩu'::VARCHAR(20) AS name_vi,
    'VN_REPORTED: Việt Nam xuất khẩu sang đối tác.'::VARCHAR(160) AS vn_side_meaning,
    'PARTNER_MIRROR: Đối tác nhập khẩu từ Việt Nam (đọc đối chiếu chiều xuất của VN).'::VARCHAR(160) AS mirror_side_meaning
UNION ALL
SELECT
    2::SMALLINT AS flow_key,
    'M'::CHAR(1) AS flow_code,
    'Nhập khẩu'::VARCHAR(20) AS name_vi,
    'VN_REPORTED: Việt Nam nhập khẩu từ đối tác.'::VARCHAR(160) AS vn_side_meaning,
    'PARTNER_MIRROR: Đối tác xuất khẩu sang Việt Nam (đọc đối chiếu chiều nhập của VN).'::VARCHAR(160) AS mirror_side_meaning
