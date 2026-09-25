/* =============================================================
  01_star_ddl.sql — TLCN Kho du lieu XNK Viet Nam (Tuan 3)
  Thiet ke theo docs/13 (duyet 23/09). Chay tren SQL Server 2019+ / Azure SQL.
  Cach chay: SSMS -> Open file -> Execute (hoac: sqlcmd -S localhost -E -i sql\01_star_ddl.sql)
  File nay CHI tao schema (idempotent: co the chay lai khong sao).
  ============================================================= */
IF DB_ID(N'TLCN_XNK') IS NULL
    CREATE DATABASE TLCN_XNK;
GO
USE TLCN_XNK;
GO

/* ---------- NHOM CHIEU (7 + DIM_DATE) ---------- */

IF OBJECT_ID(N'dbo.DIM_DATE', N'U') IS NULL
CREATE TABLE dbo.DIM_DATE (
    date_key      INT           NOT NULL,      -- YYYYMM ( thang ) | YYYY00 ( nam sentinel — Q2 )
    calendar_year SMALLINT      NOT NULL,
    quarter       TINYINT       NULL,          -- NULL o dong nam
    [month]       TINYINT       NULL,          -- NULL o dong nam
    granularity   CHAR(5)       NOT NULL,      -- 'MONTH' | 'YEAR'
    date_label    VARCHAR(7)    NOT NULL,      -- '2023-01' | '2023'
    CONSTRAINT PK_DIM_DATE PRIMARY KEY CLUSTERED (date_key),
    CONSTRAINT CK_DIM_DATE_GRAN CHECK (granularity IN ('MONTH','YEAR')),
    CONSTRAINT CK_DIM_DATE_YEAR_SENTINEL CHECK (
        (granularity = 'MONTH' AND date_key % 100 BETWEEN 1 AND 12) OR
        (granularity = 'YEAR'  AND date_key % 100 = 0)
    )
);
GO

IF OBJECT_ID(N'dbo.DIM_PARTNER', N'U') IS NULL
CREATE TABLE dbo.DIM_PARTNER (
    partner_key   INT IDENTITY(1,1) NOT NULL,
    code_comtrade CHAR(3)        NOT NULL,
    partner_name  NVARCHAR(120)  NOT NULL,
    iso3          CHAR(3)        NULL,         -- cho join vĩ mô (Q4)
    is_aggregate  BIT            NOT NULL CONSTRAINT DF_PARTNER_AGG DEFAULT 0,
    is_vietnam    BIT            NOT NULL CONSTRAINT DF_PARTNER_VN  DEFAULT 0,
    usage_note    NVARCHAR(160)  NULL,
    CONSTRAINT PK_DIM_PARTNER PRIMARY KEY CLUSTERED (partner_key),
    CONSTRAINT UQ_DIM_PARTNER_CODE UNIQUE (code_comtrade)
);
GO

IF OBJECT_ID(N'dbo.DIM_COMMODITY', N'U') IS NULL
CREATE TABLE dbo.DIM_COMMODITY (
    commodity_key INT IDENTITY(1,1) NOT NULL,
    hs6           CHAR(6)         NOT NULL,    -- ma chuan HS2022 (sau bridge — Q3)
    hs4           CHAR(4)         NOT NULL,    -- roll-up, khong co dong HS4 rieng (ke hoach #6)
    hs2           CHAR(2)         NOT NULL,
    name_en       NVARCHAR(200)   NULL,
    commodity_group NVARCHAR(60)  NULL,        -- seed da duyet docs/13 §7.1
    bridge_flag   BIT             NOT NULL CONSTRAINT DF_COMM_BRIDGE DEFAULT 0,
    bridge_note   NVARCHAR(200)   NULL,
    CONSTRAINT PK_DIM_COMMODITY PRIMARY KEY CLUSTERED (commodity_key),
    CONSTRAINT UQ_DIM_COMMODITY_HS6 UNIQUE (hs6)
);
GO

IF OBJECT_ID(N'dbo.DIM_FLOW', N'U') IS NULL
CREATE TABLE dbo.DIM_FLOW (
    flow_key            TINYINT      NOT NULL,
    flow_code           CHAR(1)      NOT NULL,
    name_vi             NVARCHAR(20) NOT NULL,
    vn_side_meaning     NVARCHAR(140) NULL,
    mirror_side_meaning NVARCHAR(140) NULL,
    CONSTRAINT PK_DIM_FLOW PRIMARY KEY CLUSTERED (flow_key),
    CONSTRAINT UQ_DIM_FLOW_CODE UNIQUE (flow_code)
);
GO

IF OBJECT_ID(N'dbo.DIM_PERSPECTIVE', N'U') IS NULL
CREATE TABLE dbo.DIM_PERSPECTIVE (
    perspective_key TINYINT       NOT NULL,
    code            VARCHAR(20)   NOT NULL,
    label_vi        NVARCHAR(40)  NOT NULL,
    reliability_note NVARCHAR(300) NULL,
    CONSTRAINT PK_DIM_PERSPECTIVE PRIMARY KEY CLUSTERED (perspective_key),
    CONSTRAINT UQ_DIM_PERSPECTIVE_CODE UNIQUE (code)
);
GO

IF OBJECT_ID(N'dbo.DIM_TARIFF_TYPE', N'U') IS NULL
CREATE TABLE dbo.DIM_TARIFF_TYPE (
    tariff_type_key TINYINT       NOT NULL,
    code          VARCHAR(10)     NOT NULL,
    label_vi      NVARCHAR(60)    NOT NULL,
    coverage_note NVARCHAR(300)   NULL,
    CONSTRAINT PK_DIM_TARIFF_TYPE PRIMARY KEY CLUSTERED (tariff_type_key),
    CONSTRAINT UQ_DIM_TARIFF_TYPE_CODE UNIQUE (code)
);
GO

IF OBJECT_ID(N'dbo.DIM_INDICATOR', N'U') IS NULL
CREATE TABLE dbo.DIM_INDICATOR (
    indicator_key TINYINT        NOT NULL,
    code_wb     VARCHAR(20)      NOT NULL,
    name_en     NVARCHAR(120)    NOT NULL,
    unit        VARCHAR(10)      NOT NULL,
    note        NVARCHAR(200)    NULL,
    CONSTRAINT PK_DIM_INDICATOR PRIMARY KEY CLUSTERED (indicator_key),
    CONSTRAINT UQ_DIM_INDICATOR_CODE UNIQUE (code_wb)
);
GO

IF OBJECT_ID(N'dbo.DIM_AUDIT', N'U') IS NULL
CREATE TABLE dbo.DIM_AUDIT (
    audit_key    INT IDENTITY(1,1) NOT NULL,
    batch_id     VARCHAR(32)     NOT NULL,
    source_system VARCHAR(80)    NOT NULL,
    staging_file VARCHAR(120)    NULL,
    raw_dir      VARCHAR(120)    NULL,
    extracted_at DATETIME2(0)    NULL,
    row_count    INT             NULL,
    CONSTRAINT PK_DIM_AUDIT PRIMARY KEY CLUSTERED (audit_key),
    CONSTRAINT UQ_DIM_AUDIT_BATCH UNIQUE (batch_id)
);
GO

/* ---------- NHOM FACT ---------- */

IF OBJECT_ID(N'dbo.FACT_TRADE', N'U') IS NULL
CREATE TABLE dbo.FACT_TRADE (
    trade_key       INT IDENTITY(1,1) NOT NULL,
    date_key        INT             NOT NULL,
    partner_key     INT             NOT NULL,   -- doi tac CUA VIET NAM ca 2 perspective (Q1)
    commodity_key   INT             NOT NULL,
    flow_key        TINYINT         NOT NULL,   -- X=1, M=2 (luon theo reporter cua dong — docs/13 §4.4)
    perspective_key TINYINT         NOT NULL,   -- 1=VN_REPORTED, 2=PARTNER_MIRROR
    audit_key       INT             NOT NULL,
    /* measures */
    primary_value_usd DECIMAL(18,3) NOT NULL,
    net_wgt_kg        DECIMAL(18,3) NULL,
    qty               DECIMAL(18,3) NULL,       -- CAM SUM (DW_USAGE_RULE R1)
    fob_value_usd     DECIMAL(18,3) NULL,
    cif_value_usd     DECIMAL(18,3) NULL,
    /* trace-ve-nguyen-ver */
    hs6_reported    CHAR(6)         NOT NULL,   -- ma goc trong API (851712 cua bridge/nhu-vay)
    reporter_code   CHAR(3)         NOT NULL,
    partner_code_src CHAR(3)        NOT NULL,
    is_aggregate_partner BIT        NOT NULL,
    year            SMALLINT        NOT NULL,
    [month]         TINYINT         NOT NULL,
    /* mo */
    mirror_role     VARCHAR(20)     NULL,
    is_reported     BIT             NULL,       -- Q6: pending ket qua check_is_reported.py
    CONSTRAINT PK_FACT_TRADE PRIMARY KEY CLUSTERED (trade_key),
    CONSTRAINT FK_FT_DATE        FOREIGN KEY (date_key)        REFERENCES dbo.DIM_DATE (date_key),
    CONSTRAINT FK_FT_PARTNER     FOREIGN KEY (partner_key)     REFERENCES dbo.DIM_PARTNER (partner_key),
    CONSTRAINT FK_FT_COMMODITY   FOREIGN KEY (commodity_key)   REFERENCES dbo.DIM_COMMODITY (commodity_key),
    CONSTRAINT FK_FT_FLOW        FOREIGN KEY (flow_key)        REFERENCES dbo.DIM_FLOW (flow_key),
    CONSTRAINT FK_FT_PERSPECTIVE FOREIGN KEY (perspective_key) REFERENCES dbo.DIM_PERSPECTIVE (perspective_key),
    CONSTRAINT FK_FT_AUDIT      FOREIGN KEY (audit_key)       REFERENCES dbo.DIM_AUDIT (audit_key),
    CONSTRAINT CK_FT_MIRROR_ROLE CHECK (
        (perspective_key = 2 AND mirror_role IS NOT NULL) OR   -- moi dong mirror co vai tro
        (perspective_key = 1 AND mirror_role IS NULL)          -- dong VN khong co vai tro
    )
);
-- grain hop dong (docs/13 §5.1): 1 o = thang × doi tac × HS6 × flow × perspective
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_FT_GRAIN' AND object_id = OBJECT_ID(N'dbo.FACT_TRADE'))
    CREATE UNIQUE NONCLUSTERED INDEX UQ_FT_GRAIN
        ON dbo.FACT_TRADE (date_key, partner_key, commodity_key, flow_key, perspective_key);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_FT_COMMODITY_DATE' AND object_id = OBJECT_ID(N'dbo.FACT_TRADE'))
    CREATE NONCLUSTERED INDEX IX_FT_COMMODITY_DATE ON dbo.FACT_TRADE (commodity_key, date_key)
        INCLUDE (primary_value_usd, perspective_key);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_FT_PARTNER_DATE' AND object_id = OBJECT_ID(N'dbo.FACT_TRADE'))
    CREATE NONCLUSTERED INDEX IX_FT_PARTNER_DATE ON dbo.FACT_TRADE (partner_key, date_key)
        INCLUDE (primary_value_usd, perspective_key);
GO

IF OBJECT_ID(N'dbo.FACT_TARIFF_RATE', N'U') IS NULL
CREATE TABLE dbo.FACT_TARIFF_RATE (
    tariff_key    INT IDENTITY(1,1) NOT NULL,
    date_key      INT            NOT NULL,      -- sentinel YYYY00
    partner_key   INT            NOT NULL,      -- doi tac thuong mai (VN_IMPORT_*: partner_code; MKT_*: reporter_code)
    commodity_key INT            NOT NULL,
    tariff_type_key TINYINT      NOT NULL,
    audit_key     INT            NOT NULL,
    combo_code    VARCHAR(20)    NOT NULL,      -- VN_IMPORT_MFN | VN_IMPORT_PREF | MKT_EXPORT_MFN
    ad_valorem_pct DECIMAL(9,4) NULL,          -- KHONG cong — trung binh quyen so theo total_lines (R2)
    measure_label VARCHAR(60)    NULL,
    min_rate      DECIMAL(9,4)   NULL,
    max_rate      DECIMAL(9,4)   NULL,
    total_lines   INT            NULL,
    mfn_lines     INT            NULL,
    pref_lines    INT            NULL,
    datatype      VARCHAR(10)    NULL,
    CONSTRAINT PK_FACT_TARIFF PRIMARY KEY CLUSTERED (tariff_key),
    CONSTRAINT FK_TR_DATE      FOREIGN KEY (date_key)        REFERENCES dbo.DIM_DATE (date_key),
    CONSTRAINT FK_TR_PARTNER   FOREIGN KEY (partner_key)     REFERENCES dbo.DIM_PARTNER (partner_key),
    CONSTRAINT FK_TR_COMMODITY FOREIGN KEY (commodity_key)   REFERENCES dbo.DIM_COMMODITY (commodity_key),
    CONSTRAINT FK_TR_TYPE      FOREIGN KEY (tariff_type_key) REFERENCES dbo.DIM_TARIFF_TYPE (tariff_type_key),
    CONSTRAINT FK_TR_AUDIT     FOREIGN KEY (audit_key)       REFERENCES dbo.DIM_AUDIT (audit_key),
    CONSTRAINT CK_TR_YEAR_SENTINEL CHECK (date_key % 100 = 0)
);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_TR_GRAIN' AND object_id = OBJECT_ID(N'dbo.FACT_TARIFF_RATE'))
    CREATE UNIQUE NONCLUSTERED INDEX UQ_TR_GRAIN
        ON dbo.FACT_TARIFF_RATE (date_key, partner_key, commodity_key, tariff_type_key, combo_code);
GO

IF OBJECT_ID(N'dbo.FACT_MACRO_INDICATOR', N'U') IS NULL
CREATE TABLE dbo.FACT_MACRO_INDICATOR (
    macro_key     INT IDENTITY(1,1) NOT NULL,
    date_key      INT             NOT NULL,    -- sentinel YYYY00
    partner_key   INT             NOT NULL,    -- qua iso3 → DIM_PARTNER (Q4)
    indicator_key TINYINT         NOT NULL,
    audit_key     INT             NOT NULL,
    [value]       DECIMAL(18,2)   NULL,        -- NULL = WB khong co so (khac 0)
    CONSTRAINT PK_FACT_MACRO PRIMARY KEY CLUSTERED (macro_key),
    CONSTRAINT FK_MC_DATE      FOREIGN KEY (date_key)      REFERENCES dbo.DIM_DATE (date_key),
    CONSTRAINT FK_MC_PARTNER   FOREIGN KEY (partner_key)   REFERENCES dbo.DIM_PARTNER (partner_key),
    CONSTRAINT FK_MC_INDICATOR FOREIGN KEY (indicator_key) REFERENCES dbo.DIM_INDICATOR (indicator_key),
    CONSTRAINT FK_MC_AUDIT     FOREIGN KEY (audit_key)     REFERENCES dbo.DIM_AUDIT (audit_key),
    CONSTRAINT CK_MC_YEAR_SENTINEL CHECK (date_key % 100 = 0),
    CONSTRAINT UQ_MC_GRAIN UNIQUE (date_key, partner_key, indicator_key)
);
GO

/* ---------- LOI SU DUNG (duyet 23/09: rule phai nam TRONG KHO, khong phai trong dau) ---------- */

IF OBJECT_ID(N'dbo.DW_USAGE_RULE', N'U') IS NULL
CREATE TABLE dbo.DW_USAGE_RULE (
    rule_id  VARCHAR(4)      NOT NULL,
    applies_to NVARCHAR(120) NOT NULL,
    rule_vi  NVARCHAR(400)   NOT NULL,
    enforcement NVARCHAR(200) NOT NULL,
    CONSTRAINT PK_DW_USAGE_RULE PRIMARY KEY CLUSTERED (rule_id)
);
GO
MERGE dbo.DW_USAGE_RULE AS t
USING (VALUES
 ('R1', 'FACT_TRADE.qty',
   N'Cấm SUM cộng gộp qty: đơn vị đo khác nhau giữa mã (cái/kg/chiếc…) — chỉ dùng ở mức chi tiết một mã HS6 đã lọc.',
   N'Power BI: cột qty đặt Sum By = Disabled; SSAS: không tạo measure SUM; DAX mẫu chỉ dùng CALCULATE(SUM(qty)) sau khi slicer 1 hs6.'),
 ('R2', 'FACT_TARIFF_RATE.ad_valorem_pct',
   N'Thuế suất là measure KHÔNG cộng được; tổng hợp đúng = trung bình có quyền theo total_lines, không phải AVG trần.',
   N'View/mart tuần 10 chỉ xuất SUM(pct*total_lines)/SUM(total_lines); mọi query khác bị xem là sai nghiệp vụ.'),
 ('R3', 'FACT_TRADE.is_aggregate_partner',
   N'Dòng World (partner 0) giữ trong kho để kiểm tra chéo nhưng không vào xếp hạng đối tác/KPI cộng theo partner.',
   N'Mọi view D2/dashboard xếp hạng đều WHERE is_aggregate_partner = 0 (đã ghi docs/06 §5, luật khóa).'),
 ('R4', 'FACT_TRADE.reporting_perspective',
   N'Không bao giờ SUM/AVG mà chưa lọc reporting_perspective; không cộng vn_value + mirror_value (đối chiếu, không hợp nhất).',
   N'VIEW reconciliation tách 2 CTE; semantic layer bắt buộc slicer perspective mặc định = VN_REPORTED (ke hoạch chỉnh sửa #1).'),
 ('R5', 'DIM_DATE.granularity',
   N'fact granularity năm (tari, macro) không join/trộn số với fact tháng; năm của trade = Σ 12 tháng (docs/09 §2b).',
   N'CK_<fact>_YEAR_SENTINEL chặn sentinel vào FACT_TRADE; query trộngranularity phải đi qua DIM_DATE.granularity — mart tuần 10 chỉ chọn 1 giá trị mỗi truy vấn.')
) AS s(rule_id, applies_to, rule_vi, enforcement)
ON t.rule_id = s.rule_id
WHEN MATCHED THEN UPDATE SET applies_to = s.applies_to, rule_vi = s.rule_vi, enforcement = s.enforcement
WHEN NOT MATCHED THEN INSERT VALUES (s.rule_id, s.applies_to, s.rule_vi, s.enforcement);
GO

/* ---------- LOI DOI CHIEU (docs/13 §6) — chi ghep, khong sinh so ---------- */

CREATE OR ALTER VIEW dbo.VW_TRADE_RECONCILIATION AS
WITH vn AS (
    SELECT f.date_key, f.partner_key, f.commodity_key, f.flow_key,
           f.primary_value_usd AS vn_value
    FROM dbo.FACT_TRADE f
    WHERE f.perspective_key = 1 AND f.partner_code_src <> '0'      -- bo World
), mi AS (
    SELECT f.date_key, f.partner_key, f.commodity_key,
           CASE f.flow_key WHEN 1 THEN 2 ELSE 1 END AS flow_key,   -- nguoc chieu (ban nhap = ta xuat)
           f.primary_value_usd AS mirror_value,
           f.is_reported AS mirror_is_reported,
           f.mirror_role
    FROM dbo.FACT_TRADE f
    WHERE f.perspective_key = 2
)
SELECT
    COALESCE(vn.date_key, mi.date_key)             AS date_key,
    COALESCE(vn.partner_key, mi.partner_key)       AS partner_key,
    COALESCE(vn.commodity_key, mi.commodity_key)   AS commodity_key,
    COALESCE(vn.flow_key, mi.flow_key)             AS flow_key,
    vn.vn_value,
    mi.mirror_value,
    mi.mirror_is_reported,
    mi.mirror_role,
    ABS(COALESCE(mi.mirror_value, 0) - COALESCE(vn.vn_value, 0)) AS abs_diff_usd,
    CASE WHEN vn.vn_value IS NULL OR vn.vn_value = 0 THEN NULL
         ELSE 100.0 * (mi.mirror_value - vn.vn_value) / vn.vn_value END AS pct_diff_vs_vn,
    CASE
        WHEN vn.vn_value IS NULL THEN 'MISSING_VN_REPORTED'
        WHEN mi.mirror_value IS NULL THEN 'MISSING_MIRROR'
        WHEN vn.vn_value = 0 THEN 'HIGH'
        WHEN ABS(100.0*(mi.mirror_value - vn.vn_value)/vn.vn_value) <= 10 THEN 'LOW'
        WHEN ABS(100.0*(mi.mirror_value - vn.vn_value)/vn.vn_value) <= 30 THEN 'MODERATE'
        ELSE 'HIGH'
    END AS discrepancy_level,
    CASE
        WHEN vn.vn_value IS NULL THEN N'Kỳ này Việt Nam chưa công bố — số tham chiếu từ đối tác'
        WHEN mi.mirror_value IS NULL THEN N'Dữ liệu Việt Nam là nguồn duy nhất cho ô này'
        WHEN vn.vn_value = 0 THEN N'VN khai 0, đối tác khai dương — kiểm tra chiều/đơn vị trước khi dùng'
        ELSE NULL
    END AS reconciliation_note
    /* Q6 (pending): khi ket qua check_is_reported.py ve, neu ty le uoc luong cao se them
       WHERE (mi.mirror_is_reported = 1 OR mi.mirror_is_reported IS NULL) o day — DUY NHAT mot cho. */
FROM vn
FULL OUTER JOIN mi
  ON  mi.date_key      = vn.date_key
  AND mi.partner_key   = vn.partner_key
  AND mi.commodity_key = vn.commodity_key
  AND mi.flow_key      = vn.flow_key;
GO

PRINT N'01_star_ddl.sql xong: 8 dim + 3 fact + DW_USAGE_RULE (5 rule) + VW_TRADE_RECONCILIATION.';
GO
