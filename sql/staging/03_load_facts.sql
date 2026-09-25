/* =============================================================
  03_load_facts.sql — lz.* → 3 fact + hop dong grain (docs/13 §5)
  chay SAU 02. Idempotent: WHERE NOT EXISTS theo grain — chay lai khong tao dong trung.
  Luong nap: vn_reported → vn_bridge → partner_mirror (ca ba vao CUNG FACT_TRADE,
  phan biet bang perspective_key — docs/06: HAI GOC NHIN TRONG MOT BANG, KHONG TRON KHI TONG HOP).
  ============================================================= */
USE TLCN_XNK;
GO

/* ---------- 1. FACT_TRADE ← lz.vn_reported (perspective 1) ---------- */
INSERT INTO dbo.FACT_TRADE
    (date_key, partner_key, commodity_key, flow_key, perspective_key, audit_key,
     primary_value_usd, net_wgt_kg, qty, fob_value_usd, cif_value_usd,
     hs6_reported, reporter_code, partner_code_src, is_aggregate_partner, year, [month],
     mirror_role, is_reported)
SELECT
    TRY_CAST(s.period AS INT),
    dp.partner_key,
    dc.commodity_key,
    df.flow_key,
    1,
    da.audit_key,
    TRY_CONVERT(DECIMAL(18,3), s.primary_value_usd),
    TRY_CONVERT(DECIMAL(18,3), s.net_wgt_kg),
    TRY_CONVERT(DECIMAL(18,3), s.qty),
    TRY_CONVERT(DECIMAL(18,3), s.fob_value_usd),
    TRY_CONVERT(DECIMAL(18,3), s.cif_value_usd),
    LTRIM(RTRIM(s.hs6)),
    LTRIM(RTRIM(s.reporter_code)),
    LTRIM(RTRIM(s.partner_code)),
    CASE WHEN LTRIM(RTRIM(s.is_aggregate_partner)) = N'True' THEN 1 ELSE 0 END,
    TRY_CAST(s.year AS SMALLINT), TRY_CAST(s.month AS TINYINT),
    NULL, NULL
FROM lz.vn_reported s
JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade = LTRIM(RTRIM(s.partner_code))
JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = LTRIM(RTRIM(s.hs6))
JOIN dbo.DIM_FLOW      df ON df.flow_code = LTRIM(RTRIM(s.flow_code))
JOIN dbo.DIM_AUDIT     da ON da.batch_id = LTRIM(RTRIM(s.batch_id))
WHERE NOT EXISTS (SELECT 1 FROM dbo.FACT_TRADE f
                  WHERE f.date_key = TRY_CAST(s.period AS INT)
                    AND f.partner_key = dp.partner_key
                    AND f.commodity_key = dc.commodity_key
                    AND f.flow_key = df.flow_key
                    AND f.perspective_key = 1);
PRINT CONCAT(N'FACT_TRADE ← vn_reported: ', @@ROWCOUNT, N' dong (tong luy ke = 13.725 neu load lan dau)');
GO

/* ---------- 2. FACT_TRADE ← lz.vn_bridge (perspective 1; commodity theo MA DICH — Q3) ---------- */
INSERT INTO dbo.FACT_TRADE
    (date_key, partner_key, commodity_key, flow_key, perspective_key, audit_key,
     primary_value_usd, net_wgt_kg, qty, fob_value_usd, cif_value_usd,
     hs6_reported, reporter_code, partner_code_src, is_aggregate_partner, year, [month],
     mirror_role, is_reported)
SELECT
    TRY_CAST(s.period AS INT),
    dp.partner_key,
    dc.commodity_key,
    df.flow_key,
    1,
    da.audit_key,
    TRY_CONVERT(DECIMAL(18,3), s.primary_value_usd),
    TRY_CONVERT(DECIMAL(18,3), s.net_wgt_kg),
    TRY_CONVERT(DECIMAL(18,3), s.qty),
    TRY_CONVERT(DECIMAL(18,3), s.fob_value_usd),
    TRY_CONVERT(DECIMAL(18,3), s.cif_value_usd),
    LTRIM(RTRIM(s.hs6)),                              -- giu nguyen 851712 de truy vet ve raw
    LTRIM(RTRIM(s.reporter_code)),
    LTRIM(RTRIM(s.partner_code)),
    CASE WHEN LTRIM(RTRIM(s.is_aggregate_partner)) = N'True' THEN 1 ELSE 0 END,
    TRY_CAST(s.year AS SMALLINT), TRY_CAST(s.month AS TINYINT),
    NULL, NULL
FROM lz.vn_bridge s
JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade = LTRIM(RTRIM(s.partner_code))
JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = COALESCE(NULLIF(LTRIM(RTRIM(s.maps_to_hs6)), N''), LTRIM(RTRIM(s.hs6)))
JOIN dbo.DIM_FLOW      df ON df.flow_code = LTRIM(RTRIM(s.flow_code))
JOIN dbo.DIM_AUDIT     da ON da.batch_id = LTRIM(RTRIM(s.batch_id))
WHERE NOT EXISTS (SELECT 1 FROM dbo.FACT_TRADE f
                  WHERE f.date_key = TRY_CAST(s.period AS INT)
                    AND f.partner_key = dp.partner_key
                    AND f.commodity_key = dc.commodity_key
                    AND f.flow_key = df.flow_key
                    AND f.perspective_key = 1);
PRINT CONCAT(N'FACT_TRADE ← bridge: ', @@ROWCOUNT, N' dong (ky vong 958; hop dong V2b: 0 trung grain voi core)');
GO

/* ---------- 3. FACT_TRADE ← lz.partner_mirror (perspective 2; partner = nuoc bao cao — Q1) ---------- */
INSERT INTO dbo.FACT_TRADE
    (date_key, partner_key, commodity_key, flow_key, perspective_key, audit_key,
     primary_value_usd, net_wgt_kg, qty, fob_value_usd, cif_value_usd,
     hs6_reported, reporter_code, partner_code_src, is_aggregate_partner, year, [month],
     mirror_role, is_reported)
SELECT
    TRY_CAST(s.period AS INT),
    dp.partner_key,                                     -- Q1: DIM_PARTNER lay theo REPORTER cua dong mirror
    dc.commodity_key,
    df.flow_key,
    2,
    da.audit_key,
    TRY_CONVERT(DECIMAL(18,3), s.primary_value_usd),
    TRY_CONVERT(DECIMAL(18,3), s.net_wgt_kg),
    TRY_CONVERT(DECIMAL(18,3), s.qty),
    TRY_CONVERT(DECIMAL(18,3), s.fob_value_usd),
    TRY_CONVERT(DECIMAL(18,3), s.cif_value_usd),
    COALESCE(NULLIF(LTRIM(RTRIM(s.hs6_original)), N''), LTRIM(RTRIM(s.hs6))),  -- ma goc bao cao ve UN (bridge: 851712)
    LTRIM(RTRIM(s.reporter_code)),
    LTRIM(RTRIM(s.partner_code)),
    0,                                                  -- mirror khong co dong aggregate trong pham vi nay
    TRY_CAST(s.year AS SMALLINT), TRY_CAST(s.month AS TINYINT),
    LTRIM(RTRIM(s.mirror_role)),
    CASE LTRIM(RTRIM(s.is_reported)) WHEN N'True' THEN 1 WHEN N'False' THEN 0 END
FROM lz.partner_mirror s
JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade = LTRIM(RTRIM(s.reporter_code))
JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = COALESCE(NULLIF(LTRIM(RTRIM(s.maps_to_hs6)), N''), LTRIM(RTRIM(s.hs6)))
JOIN dbo.DIM_FLOW      df ON df.flow_code = LTRIM(RTRIM(s.flow_code))
JOIN dbo.DIM_AUDIT     da ON da.batch_id = LTRIM(RTRIM(s.batch_id))
WHERE NOT EXISTS (SELECT 1 FROM dbo.FACT_TRADE f
                  WHERE f.date_key = TRY_CAST(s.period AS INT)
                    AND f.partner_key = dp.partner_key
                    AND f.commodity_key = dc.commodity_key
                    AND f.flow_key = df.flow_key
                    AND f.perspective_key = 2);
PRINT CONCAT(N'FACT_TRADE ← mirror: ', @@ROWCOUNT, N' dong (ky vong 13.252)');
GO

/* ---------- 4. FACT_TARIFF_RATE ← lz.wits_tariff ---------- */
INSERT INTO dbo.FACT_TARIFF_RATE
    (date_key, partner_key, commodity_key, tariff_type_key, audit_key, combo_code,
     ad_valorem_pct, measure_label, min_rate, max_rate, total_lines, mfn_lines, pref_lines, datatype)
SELECT
    TRY_CAST(s.year AS INT) * 100,
    dp.partner_key,
    dc.commodity_key,
    dt.tariff_type_key,
    da.audit_key,
    LTRIM(RTRIM(s.combo_type)),
    TRY_CONVERT(DECIMAL(9,4), s.rate_pct),
    NULLIF(LTRIM(RTRIM(s.measure)), N''),
    TRY_CONVERT(DECIMAL(9,4), s.min_rate), TRY_CONVERT(DECIMAL(9,4), s.max_rate),
    TRY_CAST(s.total_lines AS INT), TRY_CAST(s.mfn_lines AS INT), TRY_CAST(s.pref_lines AS INT),
    NULLIF(LTRIM(RTRIM(s.datatype)), N'')
FROM lz.wits_tariff s
JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade =
        CASE WHEN LTRIM(RTRIM(s.combo_type)) LIKE N'VN_IMPORT%'
             THEN CASE WHEN LTRIM(RTRIM(s.partner_code)) = '000' THEN '0'
                       ELSE LTRIM(RTRIM(s.partner_code)) END
             ELSE LTRIM(RTRIM(s.reporter_code)) END
OUTER APPLY (SELECT TOP 1 NULLIF(LTRIM(RTRIM(maps_to_hs6)), N'') AS mapped_hs6 
             FROM lz.vn_bridge WHERE LTRIM(RTRIM(hs6)) = LTRIM(RTRIM(s.hs6))) b
JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = COALESCE(b.mapped_hs6, LTRIM(RTRIM(s.hs6)))
JOIN dbo.DIM_TARIFF_TYPE dt ON dt.code = LTRIM(RTRIM(s.tariff_type))
JOIN dbo.DIM_AUDIT     da ON da.batch_id = N'wits_week2'
WHERE NOT EXISTS (SELECT 1 FROM dbo.FACT_TARIFF_RATE f
                  WHERE f.date_key = TRY_CAST(s.year AS INT) * 100
                    AND f.partner_key = dp.partner_key
                    AND f.commodity_key = dc.commodity_key
                    AND f.tariff_type_key = dt.tariff_type_key
                    AND f.combo_code = LTRIM(RTRIM(s.combo_type)));
PRINT CONCAT(N'FACT_TARIFF_RATE: ', @@ROWCOUNT, N' dong (ky vong 419)');
GO

/* ---------- 5. FACT_MACRO_INDICATOR ← lz.wb_macro ---------- */
INSERT INTO dbo.FACT_MACRO_INDICATOR (date_key, partner_key, indicator_key, audit_key, [value])
SELECT
    TRY_CAST(s.year AS INT) * 100,
    dp.partner_key,
    di.indicator_key,
    da.audit_key,
    TRY_CONVERT(DECIMAL(18,2), s.value)
FROM lz.wb_macro s
JOIN dbo.DIM_PARTNER   dp ON dp.iso3 = LTRIM(RTRIM(s.country_iso3))
JOIN dbo.DIM_INDICATOR di ON di.code_wb = LTRIM(RTRIM(s.indicator))
JOIN dbo.DIM_AUDIT     da ON da.batch_id = N'wb_week2'
WHERE NOT EXISTS (SELECT 1 FROM dbo.FACT_MACRO_INDICATOR f
                  WHERE f.date_key = TRY_CAST(s.year AS INT) * 100
                    AND f.partner_key = dp.partner_key
                    AND f.indicator_key = di.indicator_key);
PRINT CONCAT(N'FACT_MACRO_INDICATOR: ', @@ROWCOUNT, N' dong (ky vong 300)');
GO
