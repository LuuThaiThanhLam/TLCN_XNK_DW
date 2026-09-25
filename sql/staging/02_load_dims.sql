/* =============================================================
  02_load_dims.sql — nap 5 file staging → lz.* (landing) → 8 chieu
  TLCN Kho du lieu XNK Viet Nam (Tuan 3) — theo docs/13
  -------------------------------------------------------------
  Chuan bi (xem sql/README.md):
    1. Copy 5 file trong `data/staging/` may vua Tuan 2 sang  C:\TLCN_DATA\
       (giu nguyen ten): stg_comtrade_vn_reported.csv · stg_comtrade_vn_reported_bridge.csv
       stg_comtrade_partner_mirror.csv · stg_wits_tariff.csv · stg_wb_macro.csv
    2. Neu dat khac, thay 'C:\TLCN_DATA\' duoi day (Find/Replace toan file).
    3. Chay 01_star_ddl.sql truoc. SQL Server 2019+ (FORMAT='CSV' tu 2017).
  Idempotent: LZ duoc make trong moi lan chay; chieu nap theo kieu khong-trung-lap.
  ============================================================= */
USE TLCN_XNK;
GO

EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'Ad Hoc Distributed Queries', 1; RECONFIGURE;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'lz') EXEC (N'CREATE SCHEMA lz');
GO

/* ---------- 1. LZ: ban day du 5 file CSV (moi cot NVARCHAR, chuyen kieu o buoc sau) ---------- */

DROP TABLE IF EXISTS lz.vn_reported;
CREATE TABLE lz.vn_reported (
    batch_id NVARCHAR(50), period NVARCHAR(10), year NVARCHAR(10), month NVARCHAR(10),
    flow_code NVARCHAR(5), reporter_code NVARCHAR(10), partner_code NVARCHAR(10),
    partner_name NVARCHAR(200), is_aggregate_partner NVARCHAR(10), hs6 NVARCHAR(10),
    commodity_desc NVARCHAR(300), primary_value_usd NVARCHAR(40), fob_value_usd NVARCHAR(40),
    cif_value_usd NVARCHAR(40), net_wgt_kg NVARCHAR(40), qty NVARCHAR(40),
    source_system NVARCHAR(120), reporting_perspective NVARCHAR(30), extracted_at NVARCHAR(40)
);
BULK INSERT lz.vn_reported
FROM N'D:\Tiểu luận chuyên ngành\TLCN_XNK_DW\data\staging\stg_comtrade_vn_reported.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, CODEPAGE = '65001', FIELDTERMINATOR = N',', ROWTERMINATOR = N'0x0d0a');
PRINT CONCAT(N'lz.vn_reported  = ', @@ROWCOUNT, N' dong (ky vong 13.725)');
GO

DROP TABLE IF EXISTS lz.vn_bridge;
CREATE TABLE lz.vn_bridge (
    batch_id NVARCHAR(50), period NVARCHAR(10), year NVARCHAR(10), month NVARCHAR(10),
    flow_code NVARCHAR(5), reporter_code NVARCHAR(10), partner_code NVARCHAR(10),
    partner_name NVARCHAR(200), is_aggregate_partner NVARCHAR(10), hs6 NVARCHAR(10),
    commodity_desc NVARCHAR(300), primary_value_usd NVARCHAR(40), fob_value_usd NVARCHAR(40),
    cif_value_usd NVARCHAR(40), net_wgt_kg NVARCHAR(40), qty NVARCHAR(40),
    source_system NVARCHAR(120), reporting_perspective NVARCHAR(30), extracted_at NVARCHAR(40),
    hs_nomenclature NVARCHAR(60), maps_to_hs6 NVARCHAR(10)
);
BULK INSERT lz.vn_bridge
FROM N'D:\Tiểu luận chuyên ngành\TLCN_XNK_DW\data\staging\stg_comtrade_vn_reported_bridge.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, CODEPAGE = '65001', FIELDTERMINATOR = N',', ROWTERMINATOR = N'0x0d0a');
PRINT CONCAT(N'lz.vn_bridge    = ', @@ROWCOUNT, N' dong (ky vong 958)');
GO

DROP TABLE IF EXISTS lz.partner_mirror;
CREATE TABLE lz.partner_mirror (
    batch_id NVARCHAR(50), period NVARCHAR(10), year NVARCHAR(10), month NVARCHAR(10),
    flow_code NVARCHAR(5), reporter_code NVARCHAR(10), partner_code NVARCHAR(10),
    partner_name NVARCHAR(200), is_aggregate_partner NVARCHAR(10), hs6 NVARCHAR(10),
    commodity_desc NVARCHAR(300), primary_value_usd NVARCHAR(40), fob_value_usd NVARCHAR(40),
    cif_value_usd NVARCHAR(40), net_wgt_kg NVARCHAR(40), qty NVARCHAR(40),
    source_system NVARCHAR(120), reporting_perspective NVARCHAR(30), extracted_at NVARCHAR(40),
    is_reported NVARCHAR(10), mirror_role NVARCHAR(30), hs6_original NVARCHAR(10),
    maps_to_hs6 NVARCHAR(10), hs_nomenclature NVARCHAR(60)
);
BULK INSERT lz.partner_mirror
FROM N'D:\Tiểu luận chuyên ngành\TLCN_XNK_DW\data\staging\stg_comtrade_partner_mirror.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, CODEPAGE = '65001', FIELDTERMINATOR = N',', ROWTERMINATOR = N'0x0d0a');
PRINT CONCAT(N'lz.partner_mirror = ', @@ROWCOUNT, N' dong (ky vong 13.252)');
GO

DROP TABLE IF EXISTS lz.wits_tariff;
CREATE TABLE lz.wits_tariff (
    combo_type NVARCHAR(30), reporter_code NVARCHAR(10), partner_code NVARCHAR(10),
    hs6 NVARCHAR(10), year NVARCHAR(10), tariff_type NVARCHAR(10), rate_pct NVARCHAR(40),
    measure NVARCHAR(60), min_rate NVARCHAR(40), max_rate NVARCHAR(40), total_lines NVARCHAR(20),
    pref_lines NVARCHAR(20), mfn_lines NVARCHAR(20), nomenclature NVARCHAR(10),
    datatype NVARCHAR(20), source_system NVARCHAR(120), extracted_at NVARCHAR(40)
);
BULK INSERT lz.wits_tariff
FROM N'D:\Tiểu luận chuyên ngành\TLCN_XNK_DW\data\staging\stg_wits_tariff.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, CODEPAGE = '65001', FIELDTERMINATOR = N',', ROWTERMINATOR = N'0x0d0a');
PRINT CONCAT(N'lz.wits_tariff  = ', @@ROWCOUNT, N' dong (ky vong 419)');
GO

DROP TABLE IF EXISTS lz.wb_macro;
CREATE TABLE lz.wb_macro (
    country_iso3 NVARCHAR(10), country_name NVARCHAR(120), indicator NVARCHAR(30),
    indicator_name NVARCHAR(200), year NVARCHAR(10), value NVARCHAR(40),
    source_system NVARCHAR(120), extracted_at NVARCHAR(40)
);
BULK INSERT lz.wb_macro
FROM N'D:\Tiểu luận chuyên ngành\TLCN_XNK_DW\data\staging\stg_wb_macro.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, CODEPAGE = '65001', FIELDTERMINATOR = N',', ROWTERMINATOR = N'0x0d0a');
PRINT CONCAT(N'lz.wb_macro     = ', @@ROWCOUNT, N' dong (ky vong 300)');
GO

/* ---------- 2. DIM_PARTNER ---------- */
/* Ten lay TU DONG VN_REPORTED (quy tac docs/13 §4.2: khong bao giu lay ten tu dong mirror). */
;WITH codes AS (
    SELECT LTRIM(RTRIM(partner_code))  AS code FROM lz.vn_reported
    UNION SELECT LTRIM(RTRIM(partner_code))  FROM lz.vn_bridge
    UNION SELECT LTRIM(RTRIM(reporter_code)) FROM lz.partner_mirror   -- Q1: mirror → nuoc bao cao
    UNION SELECT '704' UNION SELECT '0'
), nm AS (
    SELECT code, name FROM (
        SELECT LTRIM(RTRIM(partner_code)) AS code, LTRIM(RTRIM(partner_name)) AS name,
               ROW_NUMBER() OVER (PARTITION BY LTRIM(RTRIM(partner_code)) ORDER BY period DESC) AS rn
        FROM lz.vn_reported
    ) x WHERE rn = 1
)
MERGE dbo.DIM_PARTNER AS t
USING (SELECT c.code,
              COALESCE(n.name, CASE c.code WHEN '704' THEN N'Viet Nam' WHEN '0' THEN N'World' END) AS name
       FROM codes c LEFT JOIN nm n ON n.code = c.code) AS s
ON t.code_comtrade = s.code
WHEN MATCHED THEN UPDATE SET partner_name = s.name
WHEN NOT MATCHED THEN INSERT (code_comtrade, partner_name, iso3, is_aggregate, is_vietnam, usage_note)
VALUES (s.code, s.name,
        CASE s.code WHEN '704' THEN 'VNM' WHEN '156' THEN 'CHN' WHEN '392' THEN 'JPN'
                    WHEN '410' THEN 'KOR' WHEN '276' THEN 'DEU' WHEN '842' THEN 'USA' END,
        CASE WHEN s.code = '0' THEN 1 ELSE 0 END,
        CASE WHEN s.code = '704' THEN 1 ELSE 0 END,
        CASE WHEN s.code = '0' THEN N'Dong kiem tra cheo — nguyen lyc xep hang (R3)' END);
PRINT CONCAT(N'DIM_PARTNER = ', @@ROWCOUNT, N' (hien tai 7: 0/156/276/392/410/704/842)');
GO

/* ---------- 3. DIM_DATE ---------- */
;WITH months AS (
    SELECT DISTINCT TRY_CAST(period AS INT) AS date_key
    FROM (SELECT period FROM lz.vn_reported UNION ALL
          SELECT period FROM lz.vn_bridge   UNION ALL
          SELECT period FROM lz.partner_mirror) u
    WHERE TRY_CAST(period AS INT) IS NOT NULL
), years AS (
    SELECT DISTINCT LEFT(m.period, 4) + '00' AS yk
    FROM (SELECT period AS period FROM lz.vn_reported UNION ALL
          SELECT year FROM lz.wits_tariff UNION ALL
          SELECT year          FROM lz.wb_macro) m
)
MERGE dbo.DIM_DATE AS t
USING (SELECT date_key, 'MONTH' AS gran FROM months
       UNION
       SELECT TRY_CAST(yk AS INT), 'YEAR' FROM years WHERE TRY_CAST(yk AS INT) IS NOT NULL) AS s(date_key, granularity)
ON t.date_key = s.date_key
WHEN NOT MATCHED THEN INSERT (date_key, calendar_year, quarter, [month], granularity, date_label)
VALUES (s.date_key, s.date_key / 100,
        CASE WHEN s.granularity = 'MONTH' THEN (s.date_key % 100 - 1) / 3 + 1 END,
        CASE WHEN s.granularity = 'MONTH' THEN s.date_key % 100 END,
        s.granularity,
        CASE WHEN s.granularity = 'MONTH'
             THEN CAST(s.date_key / 100 AS VARCHAR(4)) + '-' + RIGHT('0' + CAST(s.date_key % 100 AS VARCHAR(2)), 2)
             ELSE CAST(s.date_key / 100 AS VARCHAR(4)) END);
PRINT CONCAT(N'DIM_DATE = ', @@ROWCOUNT, N' dong nap them (month 201501–202412 + sentinel nam)');
GO

/* ---------- 4. DIM_COMMODITY ---------- */
;WITH targets AS (
    SELECT LTRIM(RTRIM(hs6)) AS hs6 FROM lz.vn_reported
    UNION
    SELECT COALESCE(NULLIF(LTRIM(RTRIM(maps_to_hs6)), N''), LTRIM(RTRIM(hs6))) FROM lz.vn_bridge
    UNION
    SELECT COALESCE(NULLIF(LTRIM(RTRIM(maps_to_hs6)), N''), LTRIM(RTRIM(hs6))) FROM lz.partner_mirror
), nm AS (
    SELECT hs6_t AS hs6, name FROM (
        SELECT LTRIM(RTRIM(hs6)) AS hs6_t,
               LTRIM(RTRIM(commodity_desc)) AS name,
               ROW_NUMBER() OVER (PARTITION BY LTRIM(RTRIM(hs6)) ORDER BY period DESC) AS rn
        FROM lz.vn_reported
    ) x WHERE rn = 1
)
MERGE dbo.DIM_COMMODITY AS t
USING (SELECT tg.hs6, COALESCE(nm.name, LEFT(tg.hs6, 6)) AS name
       FROM targets tg LEFT JOIN nm ON nm.hs6 = tg.hs6) AS s
ON t.hs6 = s.hs6
WHEN MATCHED THEN UPDATE SET name_en = s.name
WHEN NOT MATCHED THEN INSERT (hs6, hs4, hs2, name_en, commodity_group, bridge_flag, bridge_note)
VALUES (s.hs6, LEFT(s.hs6, 4), LEFT(s.hs6, 2), s.name,
        CASE
            WHEN s.hs6 IN ('851713','851714','854231','851762','847330','854442') THEN N'Nhóm 1 · Điện tử – viễn thông'
            WHEN s.hs6 IN ('610910','640399','540761')                            THEN N'Nhóm 2 · Dệt may – giày dép'
            WHEN s.hs6 IN ('090111','090411','100630','080132')                   THEN N'Nhóm 3 · Nông sản – thực phẩm'
            WHEN s.hs6 IN ('390120','721049')                                      THEN N'Nhóm 4 · Nhựa – công nghiệp nặng'
        END,
        CASE WHEN s.hs6 = '851713' THEN 1 ELSE 0 END,
        CASE WHEN s.hs6 = '851713'
             THEN N'2015–2021 theo mã cũ 851712 (gồm cả điện thoại thường) — xấp xỉ có chủ đích (docs/09 §2b)'
             WHEN s.hs6 = '851714'
             THEN N'Series bắt đầu 2022 (HS2022 revision), không bridge — thiếu tuyệt đối 2015–2021' END);
PRINT CONCAT(N'DIM_COMMODITY = ', @@ROWCOUNT, N' dong nap them (hop dong: 14 ma + 851712→851713 da du gop)');
GO

/* ---------- 5. Cac chieu tinh ---------- */
MERGE dbo.DIM_FLOW AS t
USING (VALUES
 (CAST(1 AS TINYINT), 'X', N'Xuất khẩu',
  N'VN_REPORTED: Việt Nam xuất đi đối tác.', N'PARTNER_MIRROR: đối tác nhập về từ Việt Nam — đọc là đối soát chiều xuất của ta.'),
 (CAST(2 AS TINYINT), 'M', N'Nhập khẩu',
  N'VN_REPORTED: Việt Nam nhập từ đối tác.', N'PARTNER_MIRROR: đối tác xuất sang Việt Nam — đọc là đối soát chiều nhập của ta.')
) AS s(flow_key, flow_code, name_vi, vn_side_meaning, mirror_side_meaning)
ON t.flow_key = s.flow_key
WHEN MATCHED THEN UPDATE SET flow_code = s.flow_code, name_vi = s.name_vi,
     vn_side_meaning = s.vn_side_meaning, mirror_side_meaning = s.mirror_side_meaning
WHEN NOT MATCHED THEN INSERT VALUES (s.flow_key, s.flow_code, s.name_vi, s.vn_side_meaning, s.mirror_side_meaning);

MERGE dbo.DIM_PERSPECTIVE AS t
USING (VALUES
 (CAST(1 AS TINYINT), 'VN_REPORTED',   N'Việt Nam khai',
  N'Nguồn chính thức của VN; 2024 chưa có số (độ trễ nguồn — đã chứng minh 2 lần, docs/07–08).'),
 (CAST(2 AS TINYINT), 'PARTNER_MIRROR', N'Đối tác khai về VN',
  N'Đi trước VN ~3 năm ở kỳ kiểm tra; tỷ lệ dòng ước lượng theo từng reporter — xem results/week3/is_reported_check.md (Q6).')
) AS s(perspective_key, code, label_vi, reliability_note)
ON t.perspective_key = s.perspective_key
WHEN MATCHED THEN UPDATE SET code = s.code, label_vi = s.label_vi, reliability_note = s.reliability_note
WHEN NOT MATCHED THEN INSERT VALUES (s.perspective_key, s.code, s.label_vi, s.reliability_note);

MERGE dbo.DIM_TARIFF_TYPE AS t
USING (VALUES
 (CAST(1 AS TINYINT), 'MFN',  N'Rộng nhất — không phân biệt nguồn gốc', N'Đủ 2015–2023 cả hai chiều có dữ liệu.'),
 (CAST(2 AS TINYINT), 'PREF', N'Ưu đãi có điều kiện theo nguồn gốc',     N'PREF song phương phía VN dừng ở 2021; chiều đối tác không có trên endpoint miễn phí (docs/11).')
) AS s(tariff_type_key, code, label_vi, coverage_note)
ON t.tariff_type_key = s.tariff_type_key
WHEN MATCHED THEN UPDATE SET code = s.code, label_vi = s.label_vi, coverage_note = s.coverage_note
WHEN NOT MATCHED THEN INSERT VALUES (s.tariff_type_key, s.code, s.label_vi, s.coverage_note);

MERGE dbo.DIM_INDICATOR AS t
USING (VALUES
 (CAST(1 AS TINYINT), 'NY.GDP.MKTP.CD', N'GDP (current US$)', 'USD', CAST(NULL AS NVARCHAR(200))),
 (CAST(2 AS TINYINT), 'NY.GDP.PCAP.CD', N'GDP per capita (current US$)', 'USD', NULL),
 (CAST(3 AS TINYINT), 'FP.CPI.TOTL.ZG', N'Inflation, CPI (annual %)', '%', NULL),
 (CAST(4 AS TINYINT), 'PA.NUS.FCRF', N'Official exchange rate (LCU per US$, period average)', 'LCU/USD', NULL),
 (CAST(5 AS TINYINT), 'NE.TRD.GNFS.ZS', N'Trade (% of GDP)', '%',
  N'Mã cũ BN.TOTL.GD.ZS đã chết (WB error 120) — thay và test lại, xem results/week2/wb_macro.md')
) AS s(indicator_key, code_wb, name_en, unit, note)
ON t.indicator_key = s.indicator_key
WHEN MATCHED THEN UPDATE SET code_wb = s.code_wb, name_en = s.name_en, unit = s.unit, note = s.note
WHEN NOT MATCHED THEN INSERT VALUES (s.indicator_key, s.code_wb, s.name_en, s.unit, s.note);
PRINT N'Chiếu tĩnh: FLOW=2 · PERSPECTIVE=2 · TARIFF_TYPE=2 · INDICATOR=5';
GO

/* ---------- 6. DIM_AUDIT (moi batch staging mot dong; wits/wb khong co batch_id → 1 batch/tong nguon) ---------- */
;WITH b AS (
    SELECT LTRIM(RTRIM(batch_id)) AS batch_id, LTRIM(RTRIM(source_system)) AS source_system,
           N'stg_comtrade_vn_reported.csv' AS staging_file,
           MAX(TRY_CONVERT(DATETIME2(0), LEFT(extracted_at, 19))) AS extracted_at,
           COUNT(*) AS row_count
    FROM lz.vn_reported GROUP BY LTRIM(RTRIM(batch_id)), LTRIM(RTRIM(source_system))
    UNION ALL
    SELECT LTRIM(RTRIM(batch_id)), LTRIM(RTRIM(source_system)), N'stg_comtrade_vn_reported_bridge.csv',
           MAX(TRY_CONVERT(DATETIME2(0), LEFT(extracted_at, 19))), COUNT(*)
    FROM lz.vn_bridge GROUP BY LTRIM(RTRIM(batch_id)), LTRIM(RTRIM(source_system))
    UNION ALL
    SELECT LTRIM(RTRIM(batch_id)), LTRIM(RTRIM(source_system)), N'stg_comtrade_partner_mirror.csv',
           MAX(TRY_CONVERT(DATETIME2(0), LEFT(extracted_at, 19))), COUNT(*)
    FROM lz.partner_mirror GROUP BY LTRIM(RTRIM(batch_id)), LTRIM(RTRIM(source_system))
    UNION ALL
    SELECT N'wits_week2', N'WITS/TRAINS (SDMX-XML)', N'stg_wits_tariff.csv',
           MAX(TRY_CONVERT(DATETIME2(0), LEFT(extracted_at, 19))), COUNT(*) FROM lz.wits_tariff
    UNION ALL
    SELECT N'wb_week2', N'World Bank WDI API v2', N'stg_wb_macro.csv',
           MAX(TRY_CONVERT(DATETIME2(0), LEFT(extracted_at, 19))), COUNT(*) FROM lz.wb_macro
)
MERGE dbo.DIM_AUDIT AS t
USING b ON t.batch_id = b.batch_id
WHEN MATCHED THEN UPDATE SET row_count = b.row_count, staging_file = b.staging_file,
     source_system = b.source_system, extracted_at = b.extracted_at
WHEN NOT MATCHED THEN INSERT (batch_id, source_system, staging_file, raw_dir, extracted_at, row_count)
VALUES (b.batch_id, b.source_system, b.staging_file, N'data/raw/week2_extract/', b.extracted_at, b.row_count);
PRINT CONCAT(N'DIM_AUDIT = ', @@ROWCOUNT, N' dong nap them (20 w2_* + 14 br_* + 50 mir_* + 2 batch tong hop)');
GO
