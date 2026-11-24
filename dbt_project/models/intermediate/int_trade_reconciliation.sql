WITH vn AS (
    SELECT
        f.date_key,
        f.partner_key,
        f.commodity_key,
        f.flow_key,
        f.primary_value_usd AS vn_value
    FROM {{ ref('fact_trade') }} f
    JOIN {{ ref('dim_partner') }} dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = FALSE
),
mi AS (
    SELECT
        f.date_key,
        f.partner_key,
        f.commodity_key,
        CASE f.flow_key WHEN 1 THEN 2::SMALLINT ELSE 1::SMALLINT END AS flow_key,
        f.primary_value_usd AS mirror_value_raw,
        f.is_reported       AS mirror_is_reported,
        f.mirror_role,
        dc.commodity_group,
        dp.region,
        dp.sub_region
    FROM {{ ref('fact_trade') }} f
    JOIN {{ ref('dim_commodity') }} dc ON dc.commodity_key = f.commodity_key
    JOIN {{ ref('dim_partner') }} dp   ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 2
),
factors AS (
    SELECT commodity_group, transport_route, factor_pct
    FROM {{ ref('ref_cif_fob_factor') }}
)
SELECT
    COALESCE(vn.date_key, mi.date_key)           AS date_key,
    COALESCE(vn.partner_key, mi.partner_key)     AS partner_key,
    COALESCE(vn.commodity_key, mi.commodity_key) AS commodity_key,
    COALESCE(vn.flow_key, mi.flow_key)           AS flow_key,
    vn.vn_value,
    mi.mirror_value_raw,
    mi.mirror_is_reported,
    mi.mirror_role,
    COALESCE(cf.factor_pct, 6.00)::NUMERIC(5, 2) AS cif_fob_factor_pct,
    CASE
        WHEN mi.mirror_value_raw IS NOT NULL THEN
            ROUND(mi.mirror_value_raw / (1.0 + COALESCE(cf.factor_pct, 6.00) / 100.0), 3)::NUMERIC(18, 3)
        ELSE NULL
    END AS mirror_value_adjusted,
    CASE
        WHEN vn.vn_value IS NOT NULL THEN vn.vn_value
        WHEN mi.mirror_value_raw IS NOT NULL THEN
            ROUND(mi.mirror_value_raw / (1.0 + COALESCE(cf.factor_pct, 6.00) / 100.0), 3)::NUMERIC(18, 3)
        ELSE NULL
    END AS best_estimate_usd,
    ABS(COALESCE(mi.mirror_value_raw, 0) - COALESCE(vn.vn_value, 0))::NUMERIC(18, 3) AS abs_diff_usd,
    CASE
        WHEN vn.vn_value IS NULL OR vn.vn_value = 0 THEN NULL
        ELSE ROUND(100.0 * (mi.mirror_value_raw - vn.vn_value) / vn.vn_value, 4)::NUMERIC(12, 4)
    END AS pct_diff_vs_vn,
    CASE
        WHEN vn.vn_value IS NULL THEN 'MISSING_VN_REPORTED'
        WHEN mi.mirror_value_raw IS NULL THEN 'MISSING_MIRROR'
        WHEN vn.vn_value = 0 THEN 'HIGH'
        WHEN ABS(100.0 * (mi.mirror_value_raw - vn.vn_value) / vn.vn_value) <= 10 THEN 'LOW'
        WHEN ABS(100.0 * (mi.mirror_value_raw - vn.vn_value) / vn.vn_value) <= 30 THEN 'MODERATE'
        ELSE 'HIGH'
    END::VARCHAR(24) AS discrepancy_level,
    CASE
        WHEN vn.vn_value IS NOT NULL AND mi.mirror_value_raw IS NOT NULL THEN 'BOTH_AVAILABLE'
        WHEN vn.vn_value IS NOT NULL THEN 'VN_OFFICIAL_ONLY'
        WHEN mi.mirror_value_raw IS NOT NULL THEN 'MIRROR_ESTIMATED'
        ELSE 'NO_DATA'
    END::VARCHAR(24) AS data_source_flag,
    CASE
        WHEN vn.vn_value IS NULL THEN 'Việt Nam chưa công bố — dùng giá trị gương quy đổi CIF/FOB'
        WHEN mi.mirror_value_raw IS NULL THEN 'Dữ liệu Việt Nam là nguồn duy nhất cho ô này'
        WHEN vn.vn_value = 0 THEN 'VN khai 0 trong khi đối tác khai dương — cần kiểm tra đơn vị/kỳ'
        ELSE NULL
    END::VARCHAR(160) AS reconciliation_note
FROM vn
FULL OUTER JOIN mi
  ON mi.date_key      = vn.date_key
 AND mi.partner_key   = vn.partner_key
 AND mi.commodity_key = vn.commodity_key
 AND mi.flow_key      = vn.flow_key
LEFT JOIN factors cf
  ON cf.commodity_group = COALESCE(mi.commodity_group, 'Mặc định')
 AND cf.transport_route = CASE
       WHEN COALESCE(mi.region, '') = 'Châu Á'
         OR COALESCE(mi.sub_region, '') IN ('Đông Nam Á', 'Đông Bắc Á', 'Đông Á', 'Nam Á', 'Tây Á', 'Trung Á')
         THEN 'INTRA_ASIA'
       WHEN COALESCE(mi.region, '') = 'Châu Mỹ'
         OR COALESCE(mi.sub_region, '') IN ('Bắc Mỹ', 'Nam Mỹ', 'Trung Mỹ', 'Vùng Caribbean')
         THEN 'TRANS_PACIFIC'
       WHEN COALESCE(mi.region, '') = 'Châu Âu'
         OR COALESCE(mi.sub_region, '') IN ('Tây Âu', 'Đông Âu', 'Bắc Âu', 'Nam Âu')
         THEN 'ASIA_EUROPE'
       ELSE 'UNKNOWN'
     END
