/* =============================================================
  03_load_facts.sql — lz.* → 3 fact + hop dong grain (docs/13 §5)
  chay SAU 02. Idempotent: SU DUNG MERGE (UPSERT) THEO QUY DINH TUAN 8.
  Luong nap: vn_reported → vn_bridge → partner_mirror (ca ba vao CUNG FACT_TRADE,
  phan biet bang perspective_key — docs/06: HAI GOC NHIN TRONG MOT BANG, KHONG TRON KHI TONG HOP).
  ============================================================= */
USE TLCN_XNK;
GO

/* ---------- 1. FACT_TRADE ← lz.vn_reported (perspective 1) ---------- */
MERGE INTO dbo.FACT_TRADE AS Target
USING (
    SELECT
        TRY_CAST(s.period AS INT) AS date_key,
        dp.partner_key,
        dc.commodity_key,
        df.flow_key,
        1 AS perspective_key,
        da.audit_key,
        TRY_CONVERT(DECIMAL(18,3), s.primary_value_usd) AS primary_value_usd,
        TRY_CONVERT(DECIMAL(18,3), s.net_wgt_kg) AS net_wgt_kg,
        TRY_CONVERT(DECIMAL(18,3), s.qty) AS qty,
        TRY_CONVERT(DECIMAL(18,3), s.fob_value_usd) AS fob_value_usd,
        TRY_CONVERT(DECIMAL(18,3), s.cif_value_usd) AS cif_value_usd,
        LTRIM(RTRIM(s.hs6)) AS hs6_reported,
        LTRIM(RTRIM(s.reporter_code)) AS reporter_code,
        LTRIM(RTRIM(s.partner_code)) AS partner_code_src,
        CASE WHEN LTRIM(RTRIM(s.is_aggregate_partner)) = N'True' THEN 1 ELSE 0 END AS is_aggregate_partner,
        TRY_CAST(s.year AS SMALLINT) AS year, TRY_CAST(s.month AS TINYINT) AS [month],
        CAST(NULL AS VARCHAR(20)) AS mirror_role, CAST(NULL AS TINYINT) AS is_reported
    FROM lz.vn_reported s
    JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade = LTRIM(RTRIM(s.partner_code))
    JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = LTRIM(RTRIM(s.hs6))
    JOIN dbo.DIM_FLOW      df ON df.flow_code = LTRIM(RTRIM(s.flow_code))
    JOIN dbo.DIM_AUDIT     da ON da.batch_id = LTRIM(RTRIM(s.batch_id))
) AS Source
ON (Target.date_key = Source.date_key
    AND Target.partner_key = Source.partner_key
    AND Target.commodity_key = Source.commodity_key
    AND Target.flow_key = Source.flow_key
    AND Target.perspective_key = Source.perspective_key)
WHEN MATCHED THEN
    UPDATE SET 
        audit_key = Source.audit_key,
        primary_value_usd = Source.primary_value_usd,
        net_wgt_kg = Source.net_wgt_kg,
        qty = Source.qty,
        fob_value_usd = Source.fob_value_usd,
        cif_value_usd = Source.cif_value_usd,
        hs6_reported = Source.hs6_reported,
        reporter_code = Source.reporter_code,
        partner_code_src = Source.partner_code_src,
        is_aggregate_partner = Source.is_aggregate_partner,
        year = Source.year,
        [month] = Source.month,
        mirror_role = Source.mirror_role,
        is_reported = Source.is_reported
WHEN NOT MATCHED THEN
    INSERT (date_key, partner_key, commodity_key, flow_key, perspective_key, audit_key, primary_value_usd, net_wgt_kg, qty, fob_value_usd, cif_value_usd, hs6_reported, reporter_code, partner_code_src, is_aggregate_partner, year, [month], mirror_role, is_reported)
    VALUES (Source.date_key, Source.partner_key, Source.commodity_key, Source.flow_key, Source.perspective_key, Source.audit_key, Source.primary_value_usd, Source.net_wgt_kg, Source.qty, Source.fob_value_usd, Source.cif_value_usd, Source.hs6_reported, Source.reporter_code, Source.partner_code_src, Source.is_aggregate_partner, Source.year, Source.month, Source.mirror_role, Source.is_reported);
PRINT CONCAT(N'FACT_TRADE ← vn_reported MERGED: ', @@ROWCOUNT, N' dong');
GO

/* ---------- 2. FACT_TRADE ← lz.vn_bridge (perspective 1; commodity theo MA DICH — Q3) ---------- */
MERGE INTO dbo.FACT_TRADE AS Target
USING (
    SELECT
        TRY_CAST(s.period AS INT) AS date_key,
        dp.partner_key,
        dc.commodity_key,
        df.flow_key,
        1 AS perspective_key,
        da.audit_key,
        TRY_CONVERT(DECIMAL(18,3), s.primary_value_usd) AS primary_value_usd,
        TRY_CONVERT(DECIMAL(18,3), s.net_wgt_kg) AS net_wgt_kg,
        TRY_CONVERT(DECIMAL(18,3), s.qty) AS qty,
        TRY_CONVERT(DECIMAL(18,3), s.fob_value_usd) AS fob_value_usd,
        TRY_CONVERT(DECIMAL(18,3), s.cif_value_usd) AS cif_value_usd,
        LTRIM(RTRIM(s.hs6)) AS hs6_reported,
        LTRIM(RTRIM(s.reporter_code)) AS reporter_code,
        LTRIM(RTRIM(s.partner_code)) AS partner_code_src,
        CASE WHEN LTRIM(RTRIM(s.is_aggregate_partner)) = N'True' THEN 1 ELSE 0 END AS is_aggregate_partner,
        TRY_CAST(s.year AS SMALLINT) AS year, TRY_CAST(s.month AS TINYINT) AS [month],
        CAST(NULL AS VARCHAR(20)) AS mirror_role, CAST(NULL AS TINYINT) AS is_reported
    FROM lz.vn_bridge s
    JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade = LTRIM(RTRIM(s.partner_code))
    JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = COALESCE(NULLIF(LTRIM(RTRIM(s.maps_to_hs6)), N''), LTRIM(RTRIM(s.hs6)))
    JOIN dbo.DIM_FLOW      df ON df.flow_code = LTRIM(RTRIM(s.flow_code))
    JOIN dbo.DIM_AUDIT     da ON da.batch_id = LTRIM(RTRIM(s.batch_id))
) AS Source
ON (Target.date_key = Source.date_key
    AND Target.partner_key = Source.partner_key
    AND Target.commodity_key = Source.commodity_key
    AND Target.flow_key = Source.flow_key
    AND Target.perspective_key = Source.perspective_key)
WHEN MATCHED THEN
    UPDATE SET 
        audit_key = Source.audit_key,
        primary_value_usd = Source.primary_value_usd,
        net_wgt_kg = Source.net_wgt_kg,
        qty = Source.qty,
        fob_value_usd = Source.fob_value_usd,
        cif_value_usd = Source.cif_value_usd,
        hs6_reported = Source.hs6_reported,
        reporter_code = Source.reporter_code,
        partner_code_src = Source.partner_code_src,
        is_aggregate_partner = Source.is_aggregate_partner,
        year = Source.year,
        [month] = Source.month,
        mirror_role = Source.mirror_role,
        is_reported = Source.is_reported
WHEN NOT MATCHED THEN
    INSERT (date_key, partner_key, commodity_key, flow_key, perspective_key, audit_key, primary_value_usd, net_wgt_kg, qty, fob_value_usd, cif_value_usd, hs6_reported, reporter_code, partner_code_src, is_aggregate_partner, year, [month], mirror_role, is_reported)
    VALUES (Source.date_key, Source.partner_key, Source.commodity_key, Source.flow_key, Source.perspective_key, Source.audit_key, Source.primary_value_usd, Source.net_wgt_kg, Source.qty, Source.fob_value_usd, Source.cif_value_usd, Source.hs6_reported, Source.reporter_code, Source.partner_code_src, Source.is_aggregate_partner, Source.year, Source.month, Source.mirror_role, Source.is_reported);
PRINT CONCAT(N'FACT_TRADE ← bridge MERGED: ', @@ROWCOUNT, N' dong');
GO

/* ---------- 3. FACT_TRADE ← lz.partner_mirror (perspective 2; partner = nuoc bao cao — Q1) ---------- */
MERGE INTO dbo.FACT_TRADE AS Target
USING (
    SELECT
        TRY_CAST(s.period AS INT) AS date_key,
        dp.partner_key,
        dc.commodity_key,
        df.flow_key,
        2 AS perspective_key,
        da.audit_key,
        TRY_CONVERT(DECIMAL(18,3), s.primary_value_usd) AS primary_value_usd,
        TRY_CONVERT(DECIMAL(18,3), s.net_wgt_kg) AS net_wgt_kg,
        TRY_CONVERT(DECIMAL(18,3), s.qty) AS qty,
        TRY_CONVERT(DECIMAL(18,3), s.fob_value_usd) AS fob_value_usd,
        TRY_CONVERT(DECIMAL(18,3), s.cif_value_usd) AS cif_value_usd,
        COALESCE(NULLIF(LTRIM(RTRIM(s.hs6_original)), N''), LTRIM(RTRIM(s.hs6))) AS hs6_reported,
        LTRIM(RTRIM(s.reporter_code)) AS reporter_code,
        LTRIM(RTRIM(s.partner_code)) AS partner_code_src,
        0 AS is_aggregate_partner,
        TRY_CAST(s.year AS SMALLINT) AS year, TRY_CAST(s.month AS TINYINT) AS [month],
        LTRIM(RTRIM(s.mirror_role)) AS mirror_role,
        CASE LTRIM(RTRIM(s.is_reported)) WHEN N'True' THEN 1 WHEN N'False' THEN 0 END AS is_reported
    FROM lz.partner_mirror s
    JOIN dbo.DIM_PARTNER   dp ON dp.code_comtrade = LTRIM(RTRIM(s.reporter_code))
    JOIN dbo.DIM_COMMODITY dc ON dc.hs6 = COALESCE(NULLIF(LTRIM(RTRIM(s.maps_to_hs6)), N''), LTRIM(RTRIM(s.hs6)))
    JOIN dbo.DIM_FLOW      df ON df.flow_code = LTRIM(RTRIM(s.flow_code))
    JOIN dbo.DIM_AUDIT     da ON da.batch_id = LTRIM(RTRIM(s.batch_id))
) AS Source
ON (Target.date_key = Source.date_key
    AND Target.partner_key = Source.partner_key
    AND Target.commodity_key = Source.commodity_key
    AND Target.flow_key = Source.flow_key
    AND Target.perspective_key = Source.perspective_key)
WHEN MATCHED THEN
    UPDATE SET 
        audit_key = Source.audit_key,
        primary_value_usd = Source.primary_value_usd,
        net_wgt_kg = Source.net_wgt_kg,
        qty = Source.qty,
        fob_value_usd = Source.fob_value_usd,
        cif_value_usd = Source.cif_value_usd,
        hs6_reported = Source.hs6_reported,
        reporter_code = Source.reporter_code,
        partner_code_src = Source.partner_code_src,
        is_aggregate_partner = Source.is_aggregate_partner,
        year = Source.year,
        [month] = Source.month,
        mirror_role = Source.mirror_role,
        is_reported = Source.is_reported
WHEN NOT MATCHED THEN
    INSERT (date_key, partner_key, commodity_key, flow_key, perspective_key, audit_key, primary_value_usd, net_wgt_kg, qty, fob_value_usd, cif_value_usd, hs6_reported, reporter_code, partner_code_src, is_aggregate_partner, year, [month], mirror_role, is_reported)
    VALUES (Source.date_key, Source.partner_key, Source.commodity_key, Source.flow_key, Source.perspective_key, Source.audit_key, Source.primary_value_usd, Source.net_wgt_kg, Source.qty, Source.fob_value_usd, Source.cif_value_usd, Source.hs6_reported, Source.reporter_code, Source.partner_code_src, Source.is_aggregate_partner, Source.year, Source.month, Source.mirror_role, Source.is_reported);
PRINT CONCAT(N'FACT_TRADE ← mirror MERGED: ', @@ROWCOUNT, N' dong');
GO

/* ---------- 4. FACT_TARIFF_RATE ← lz.wits_tariff ---------- */
MERGE INTO dbo.FACT_TARIFF_RATE AS Target
USING (
    SELECT
        TRY_CAST(s.year AS INT) * 100 AS date_key,
        dp.partner_key,
        dc.commodity_key,
        dt.tariff_type_key,
        da.audit_key,
        LTRIM(RTRIM(s.combo_type)) AS combo_code,
        TRY_CONVERT(DECIMAL(9,4), s.rate_pct) AS ad_valorem_pct,
        NULLIF(LTRIM(RTRIM(s.measure)), N'') AS measure_label,
        TRY_CONVERT(DECIMAL(9,4), s.min_rate) AS min_rate, 
        TRY_CONVERT(DECIMAL(9,4), s.max_rate) AS max_rate,
        TRY_CAST(s.total_lines AS INT) AS total_lines, 
        TRY_CAST(s.mfn_lines AS INT) AS mfn_lines, 
        TRY_CAST(s.pref_lines AS INT) AS pref_lines, 
        NULLIF(LTRIM(RTRIM(s.datatype)), N'') AS datatype
    FROM (
        SELECT *,
               ROW_NUMBER() OVER(PARTITION BY year, reporter_code, partner_code, hs6, tariff_type, combo_type 
                                 ORDER BY nomenclature DESC) AS rn
        FROM lz.wits_tariff
    ) s
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
    WHERE s.rn = 1 
) AS Source
ON (Target.date_key = Source.date_key
    AND Target.partner_key = Source.partner_key
    AND Target.commodity_key = Source.commodity_key
    AND Target.tariff_type_key = Source.tariff_type_key
    AND Target.combo_code = Source.combo_code)
WHEN MATCHED THEN
    UPDATE SET 
        audit_key = Source.audit_key,
        ad_valorem_pct = Source.ad_valorem_pct,
        measure_label = Source.measure_label,
        min_rate = Source.min_rate,
        max_rate = Source.max_rate,
        total_lines = Source.total_lines,
        mfn_lines = Source.mfn_lines,
        pref_lines = Source.pref_lines,
        datatype = Source.datatype
WHEN NOT MATCHED THEN
    INSERT (date_key, partner_key, commodity_key, tariff_type_key, audit_key, combo_code, ad_valorem_pct, measure_label, min_rate, max_rate, total_lines, mfn_lines, pref_lines, datatype)
    VALUES (Source.date_key, Source.partner_key, Source.commodity_key, Source.tariff_type_key, Source.audit_key, Source.combo_code, Source.ad_valorem_pct, Source.measure_label, Source.min_rate, Source.max_rate, Source.total_lines, Source.mfn_lines, Source.pref_lines, Source.datatype);
PRINT CONCAT(N'FACT_TARIFF_RATE MERGED: ', @@ROWCOUNT, N' dong');
GO

/* ---------- 5. FACT_MACRO_INDICATOR ← lz.wb_macro ---------- */
MERGE INTO dbo.FACT_MACRO_INDICATOR AS Target
USING (
    SELECT
        TRY_CAST(s.year AS INT) * 100 AS date_key,
        dp.partner_key,
        di.indicator_key,
        da.audit_key,
        TRY_CONVERT(DECIMAL(18,2), s.value) AS [value]
    FROM lz.wb_macro s
    JOIN dbo.DIM_PARTNER   dp ON dp.iso3 = LTRIM(RTRIM(s.country_iso3))
    JOIN dbo.DIM_INDICATOR di ON di.code_wb = LTRIM(RTRIM(s.indicator))
    JOIN dbo.DIM_AUDIT     da ON da.batch_id = N'wb_week2'
) AS Source
ON (Target.date_key = Source.date_key
    AND Target.partner_key = Source.partner_key
    AND Target.indicator_key = Source.indicator_key)
WHEN MATCHED THEN
    UPDATE SET 
        audit_key = Source.audit_key,
        [value] = Source.value
WHEN NOT MATCHED THEN
    INSERT (date_key, partner_key, indicator_key, audit_key, [value])
    VALUES (Source.date_key, Source.partner_key, Source.indicator_key, Source.audit_key, Source.value);
PRINT CONCAT(N'FACT_MACRO_INDICATOR MERGED: ', @@ROWCOUNT, N' dong');
GO
