/* =============================================================
  05_reconciliation_mart.sql — TLCN Kho du lieu XNK Viet Nam (Tuan 9)
  Muc tieu: Hoan thien tang Doi chieu du lieu guong (Trade Reconciliation),
            lap bang he so quy doi CIF/FOB, tao View uoc tinh toi uu
            VW_TRADE_BEST_ESTIMATE va bo truy van phan tich do bat doi xung.
  ============================================================= */

USE TLCN_XNK;
GO

/* =============================================================
   1. NANG CAP DIM_PARTNER: THEM THUOC TINH PHAN CAP KHU VUC
   ============================================================= */
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.DIM_PARTNER') AND name = N'region')
    ALTER TABLE dbo.DIM_PARTNER ADD region NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.DIM_PARTNER') AND name = N'sub_region')
    ALTER TABLE dbo.DIM_PARTNER ADD sub_region NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.DIM_PARTNER') AND name = N'income_group')
    ALTER TABLE dbo.DIM_PARTNER ADD income_group NVARCHAR(50) NULL;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.DIM_PARTNER') AND name = N'has_fta_with_vn')
    ALTER TABLE dbo.DIM_PARTNER ADD has_fta_with_vn BIT NOT NULL CONSTRAINT DF_PARTNER_FTA DEFAULT 0;

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID(N'dbo.DIM_PARTNER') AND name = N'fta_name')
    ALTER TABLE dbo.DIM_PARTNER ADD fta_name NVARCHAR(200) NULL;
GO

-- Cap nhat du lieu phan cap cho cac doi tac hien tai
UPDATE dbo.DIM_PARTNER
SET region = N'Châu Á', sub_region = N'Đông Bắc Á', income_group = N'Upper-middle income', has_fta_with_vn = 1, fta_name = N'RCEP, ACFTA'
WHERE code_comtrade = '156'; -- China

UPDATE dbo.DIM_PARTNER
SET region = N'Châu Mỹ', sub_region = N'Bắc Mỹ', income_group = N'High income', has_fta_with_vn = 0, fta_name = NULL
WHERE code_comtrade = '842'; -- USA

UPDATE dbo.DIM_PARTNER
SET region = N'Châu Á', sub_region = N'Đông Bắc Á', income_group = N'High income', has_fta_with_vn = 1, fta_name = N'VKFTA, RCEP, AKFTA'
WHERE code_comtrade = '410'; -- Korea

UPDATE dbo.DIM_PARTNER
SET region = N'Châu Á', sub_region = N'Đông Bắc Á', income_group = N'High income', has_fta_with_vn = 1, fta_name = N'VJEPA, CPTPP, RCEP, AJCEP'
WHERE code_comtrade = '392'; -- Japan

UPDATE dbo.DIM_PARTNER
SET region = N'Châu Âu', sub_region = N'Tây Âu', income_group = N'High income', has_fta_with_vn = 1, fta_name = N'EVFTA'
WHERE code_comtrade = '276'; -- Germany

UPDATE dbo.DIM_PARTNER
SET region = N'Châu Á', sub_region = N'Đông Nam Á', income_group = N'Lower-middle income', has_fta_with_vn = 1, fta_name = N'Domestic'
WHERE code_comtrade = '704'; -- Viet Nam

UPDATE dbo.DIM_PARTNER
SET region = N'Toàn cầu', sub_region = N'Toàn cầu', income_group = N'All', has_fta_with_vn = 0, fta_name = NULL
WHERE code_comtrade = '0'; -- World
GO

PRINT N'1. Da cap nhat phan cap khu vuc dia ly cho DIM_PARTNER.';
GO

/* =============================================================
   2. BANG THAM CHIEU HE SO QUY DOI CIF -> FOB (REF_CIF_FOB_FACTOR)
   Co so: Nghien cuu IMF DOTS & OECD Trade Facilitation
   ============================================================= */
IF OBJECT_ID(N'dbo.REF_CIF_FOB_FACTOR', N'U') IS NULL
CREATE TABLE dbo.REF_CIF_FOB_FACTOR (
    commodity_group  NVARCHAR(60)  NOT NULL,
    transport_route  NVARCHAR(50)  NOT NULL,  -- INTRA_ASIA, TRANS_PACIFIC, ASIA_EUROPE, UNKNOWN
    factor_pct       DECIMAL(5,2)  NOT NULL,  -- Ty le chi phi van tai & bao hiem (VD: 8.5%)
    source_reference NVARCHAR(200) NULL,
    CONSTRAINT PK_REF_CIF_FOB PRIMARY KEY CLUSTERED (commodity_group, transport_route)
);
GO

MERGE dbo.REF_CIF_FOB_FACTOR AS t
USING (VALUES
    (N'Nhóm 3 · Nông sản – thực phẩm',   N'INTRA_ASIA',     5.0,  N'OECD Trade Facilitation 2020'),
    (N'Nhóm 3 · Nông sản – thực phẩm',   N'TRANS_PACIFIC', 12.0,  N'IMF DOTS methodology'),
    (N'Nhóm 3 · Nông sản – thực phẩm',   N'ASIA_EUROPE',   10.0,  N'IMF DOTS methodology'),
    (N'Nhóm 1 · Điện tử – viễn thông',  N'INTRA_ASIA',     2.5,  N'OECD Trade Facilitation 2020'),
    (N'Nhóm 1 · Điện tử – viễn thông',  N'TRANS_PACIFIC',  4.0,  N'IMF DOTS methodology'),
    (N'Nhóm 1 · Điện tử – viễn thông',  N'ASIA_EUROPE',    3.5,  N'IMF DOTS methodology'),
    (N'Nhóm 2 · Dệt may – giày dép',     N'INTRA_ASIA',     4.0,  N'OECD Trade Facilitation 2020'),
    (N'Nhóm 2 · Dệt may – giày dép',     N'TRANS_PACIFIC',  8.0,  N'IMF DOTS methodology'),
    (N'Nhóm 2 · Dệt may – giày dép',     N'ASIA_EUROPE',    7.0,  N'IMF DOTS methodology'),
    (N'Nhóm 4 · Nhựa – công nghiệp nặng',N'INTRA_ASIA',     8.0,  N'OECD Trade Facilitation 2020'),
    (N'Nhóm 4 · Nhựa – công nghiệp nặng',N'TRANS_PACIFIC', 18.0,  N'IMF DOTS methodology'),
    (N'Nhóm 4 · Nhựa – công nghiệp nặng',N'ASIA_EUROPE',   15.0,  N'IMF DOTS methodology'),
    (N'Mặc định',                        N'UNKNOWN',        6.0,  N'IMF global average estimate')
) AS s(commodity_group, transport_route, factor_pct, source_reference)
ON t.commodity_group = s.commodity_group AND t.transport_route = s.transport_route
WHEN MATCHED THEN UPDATE SET factor_pct = s.factor_pct, source_reference = s.source_reference
WHEN NOT MATCHED THEN INSERT VALUES (s.commodity_group, s.transport_route, s.factor_pct, s.source_reference);
GO

PRINT N'2. Da khoi tao bang REF_CIF_FOB_FACTOR.';
GO

/* =============================================================
   3. VIEW UOC TINH TOI UU: VW_TRADE_BEST_ESTIMATE
   Ket hop so lieu VN chinh thuc va so lieu Mirror da dieu chinh CIF/FOB,
   co co nguon goc minh bach data_source_flag phuc vu Power BI.
   ============================================================= */
CREATE OR ALTER VIEW dbo.VW_TRADE_BEST_ESTIMATE AS
WITH base AS (
    SELECT 
        f.date_key,
        f.partner_key,
        f.commodity_key,
        f.flow_key,
        f.primary_value_usd,
        f.perspective_key,
        dc.commodity_group,
        dp.sub_region
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_COMMODITY dc ON dc.commodity_key = f.commodity_key
    JOIN dbo.DIM_PARTNER dp ON dp.partner_key = f.partner_key
    WHERE dp.is_aggregate = 0 -- Bo World
),
vn AS (
    SELECT 
        date_key, partner_key, commodity_key, flow_key,
        primary_value_usd AS vn_value
    FROM base
    WHERE perspective_key = 1
),
mi AS (
    SELECT 
        date_key, partner_key, commodity_key,
        CASE flow_key WHEN 1 THEN 2 ELSE 1 END AS flow_key, -- Nguoc chieu luong
        primary_value_usd AS mirror_value_raw,
        commodity_group,
        sub_region
    FROM base
    WHERE perspective_key = 2
)
SELECT
    COALESCE(vn.date_key, mi.date_key)             AS date_key,
    COALESCE(vn.partner_key, mi.partner_key)       AS partner_key,
    COALESCE(vn.commodity_key, mi.commodity_key)   AS commodity_key,
    COALESCE(vn.flow_key, mi.flow_key)             AS flow_key,
    
    -- So lieu goc hai phia
    vn.vn_value,
    mi.mirror_value_raw,
    
    -- He so dieu chinh CIF/FOB da ap dung
    COALESCE(cf.factor_pct, 6.0) AS cif_fob_factor_pct,
    
    -- So lieu guong sau khi dieu chinh CIF -> FOB
    CASE 
        WHEN mi.mirror_value_raw IS NOT NULL THEN
            ROUND(mi.mirror_value_raw / (1.0 + COALESCE(cf.factor_pct, 6.0) / 100.0), 3)
        ELSE NULL
    END AS mirror_value_adjusted,
    
    -- SO LIEU UOC TINH TOI UU (BEST ESTIMATE):
    -- Uu tien so VN chinh thuc; neu khuyet thi lay so Mirror da quy doi CIF -> FOB
    CASE
        WHEN vn.vn_value IS NOT NULL THEN vn.vn_value
        WHEN mi.mirror_value_raw IS NOT NULL THEN
            ROUND(mi.mirror_value_raw / (1.0 + COALESCE(cf.factor_pct, 6.0) / 100.0), 3)
        ELSE NULL
    END AS best_estimate_usd,
    
    -- CO PHAN LOAI NGUON GOC DU LIEU (Data Lineage / Transparency Flag)
    CASE
        WHEN vn.vn_value IS NOT NULL AND mi.mirror_value_raw IS NOT NULL THEN 'BOTH_AVAILABLE'
        WHEN vn.vn_value IS NOT NULL THEN 'VN_OFFICIAL_ONLY'
        WHEN mi.mirror_value_raw IS NOT NULL THEN 'MIRROR_ESTIMATED'
        ELSE 'NO_DATA'
    END AS data_source_flag

FROM vn
FULL OUTER JOIN mi
  ON  mi.date_key      = vn.date_key
  AND mi.partner_key   = vn.partner_key
  AND mi.commodity_key = vn.commodity_key
  AND mi.flow_key      = vn.flow_key
LEFT JOIN dbo.REF_CIF_FOB_FACTOR cf
  ON  cf.commodity_group = COALESCE(mi.commodity_group, N'Mặc định')
  AND cf.transport_route = CASE 
        WHEN COALESCE(mi.sub_region, '') IN (N'Đông Nam Á', N'Đông Bắc Á', N'Nam Á') THEN 'INTRA_ASIA'
        WHEN COALESCE(mi.sub_region, '') IN (N'Bắc Mỹ', N'Nam Mỹ') THEN 'TRANS_PACIFIC'
        WHEN COALESCE(mi.sub_region, '') IN (N'Tây Âu', N'Đông Âu', N'Bắc Âu', N'Nam Âu') THEN 'ASIA_EUROPE'
        ELSE 'UNKNOWN'
      END;
GO

PRINT N'3. Da tao thanh cong View dbo.VW_TRADE_BEST_ESTIMATE.';
GO

/* =============================================================
   4. TAO BANG VAT LY (DATA MART) LUU TRU KET QUA HOI THAO DOI CHIEU
   De tang toc truy van phan tich & phuc vu truc quan hoa Dashboard.
   ============================================================= */
DROP TABLE IF EXISTS dbo.MART_TRADE_RECONCILIATION;
GO

SELECT 
    r.date_key,
    r.partner_key,
    dp.partner_name,
    dp.region,
    dp.sub_region,
    r.commodity_key,
    dc.hs6,
    dc.commodity_group,
    r.flow_key,
    df.name_vi AS flow_name,
    dd.calendar_year,
    dd.date_label,
    r.vn_value,
    r.mirror_value,
    r.abs_diff_usd,
    r.pct_diff_vs_vn,
    r.discrepancy_level,
    r.reconciliation_note
INTO dbo.MART_TRADE_RECONCILIATION
FROM dbo.VW_TRADE_RECONCILIATION r
JOIN dbo.DIM_PARTNER dp ON dp.partner_key = r.partner_key
JOIN dbo.DIM_COMMODITY dc ON dc.commodity_key = r.commodity_key
JOIN dbo.DIM_FLOW df ON df.flow_key = r.flow_key
JOIN dbo.DIM_DATE dd ON dd.date_key = r.date_key;
GO

CREATE CLUSTERED INDEX CIX_MART_RECON ON dbo.MART_TRADE_RECONCILIATION (date_key, partner_key, commodity_key, flow_key);
CREATE NONCLUSTERED INDEX IX_MART_RECON_YEAR ON dbo.MART_TRADE_RECONCILIATION (calendar_year, discrepancy_level);
GO

DECLARE @mart_count INT = (SELECT COUNT(*) FROM dbo.MART_TRADE_RECONCILIATION);
PRINT CONCAT(N'4. Da tao bang vat ly MART_TRADE_RECONCILIATION voi ', @mart_count, N' dong.');
GO

/* =============================================================
   5. BO TRUY VAN PHAN TICH DOI CHIEU & DANH GIA CHAT LUONG (TUAN 9)
   ============================================================= */

PRINT N'=============================================================';
PRINT N'BÁO CÁO 1: TỔNG HỢP MỨC ĐỘ BẤT ĐỐI XỨNG THEO ĐỐI TÁC (2015-2023)';
PRINT N'=============================================================';
SELECT 
    partner_name,
    flow_name,
    COUNT(*) AS total_months_items,
    ROUND(SUM(vn_value) / 1000000.0, 2) AS total_vn_million_usd,
    ROUND(SUM(mirror_value) / 1000000.0, 2) AS total_mirror_million_usd,
    ROUND(100.0 * (SUM(mirror_value) - SUM(vn_value)) / NULLIF(SUM(vn_value), 0), 2) AS avg_pct_diff
FROM dbo.MART_TRADE_RECONCILIATION
WHERE calendar_year BETWEEN 2015 AND 2023 AND vn_value IS NOT NULL AND mirror_value IS NOT NULL
GROUP BY partner_name, flow_name
ORDER BY partner_name, flow_name;

PRINT N'=============================================================';
PRINT N'BÁO CÁO 2: TỶ LỆ COVERAGE & GIA TRỊ PHỤC HỒI NĂM 2024 (MISSING VN)';
PRINT N'=============================================================';
SELECT 
    be.data_source_flag,
    COUNT(*) AS cell_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) AS pct_share,
    ROUND(SUM(be.best_estimate_usd) / 1000000.0, 2) AS total_estimate_million_usd
FROM dbo.VW_TRADE_BEST_ESTIMATE be
JOIN dbo.DIM_DATE dd ON dd.date_key = be.date_key
WHERE dd.calendar_year = 2024
GROUP BY be.data_source_flag;

PRINT N'=============================================================';
PRINT N'BÁO CÁO 3: MA TRẬN ĐỘ PHỦ DỮ LIỆU TOÀN GIAI ĐOẠN 2015 - 2024';
PRINT N'=============================================================';
SELECT 
    dd.calendar_year,
    COUNT(*) AS total_cells,
    SUM(CASE WHEN be.data_source_flag = 'BOTH_AVAILABLE' THEN 1 ELSE 0 END) AS both_available,
    SUM(CASE WHEN be.data_source_flag = 'VN_OFFICIAL_ONLY' THEN 1 ELSE 0 END) AS vn_only,
    SUM(CASE WHEN be.data_source_flag = 'MIRROR_ESTIMATED' THEN 1 ELSE 0 END) AS mirror_estimated,
    CAST(100.0 * SUM(CASE WHEN be.data_source_flag IN ('BOTH_AVAILABLE','VN_OFFICIAL_ONLY') THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,1)) AS vn_coverage_pct,
    CAST(100.0 * SUM(CASE WHEN be.data_source_flag <> 'NO_DATA' THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,1)) AS total_coverage_pct
FROM dbo.VW_TRADE_BEST_ESTIMATE be
JOIN dbo.DIM_DATE dd ON dd.date_key = be.date_key
GROUP BY dd.calendar_year
ORDER BY dd.calendar_year;

PRINT N'=============================================================';
PRINT N'05_reconciliation_mart.sql: HOÀN THÀNH TOÀN BỘ CÔNG VIỆC TUẦN 9!';
PRINT N'=============================================================';
GO
