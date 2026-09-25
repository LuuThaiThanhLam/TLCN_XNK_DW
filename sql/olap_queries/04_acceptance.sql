/* =============================================================
  04_acceptance.sql — nghiem thu V1..V7 (docs/13 §9)
  chay SAU 03. Moi muc tra bang kieu ten_kiem_tra | expected | actual | RESULT.
  Toan bo PASS = kho du lieu dat hop dong grain voi bang chung Tuan 1-2 (da commit).
  ============================================================= */
USE TLCN_XNK;
GO
SET NOCOUNT ON;

/* ---------- V0: so luong LZ (chan doan som — phai = so dong csv) ---------- */
SELECT N'V0' AS check_id, t.what, t.expected, a.actual,
       CASE WHEN t.expected = a.actual THEN N'PASS' ELSE N'FAIL' END AS result
FROM (VALUES (N'lz.vn_reported', 13725), (N'lz.vn_bridge', 958), (N'lz.partner_mirror', 13252),
             (N'lz.wits_tariff', 419), (N'lz.wb_macro', 300)) AS t(what, expected)
OUTER APPLY (SELECT actual = CASE t.what
    WHEN N'lz.vn_reported'     THEN (SELECT COUNT_BIG(*) FROM lz.vn_reported)
    WHEN N'lz.vn_bridge'       THEN (SELECT COUNT_BIG(*) FROM lz.vn_bridge)
    WHEN N'lz.partner_mirror'  THEN (SELECT COUNT_BIG(*) FROM lz.partner_mirror)
    WHEN N'lz.wits_tariff'     THEN (SELECT COUNT_BIG(*) FROM lz.wits_tariff)
    ELSE (SELECT COUNT_BIG(*) FROM lz.wb_macro) END) AS a;
GO

/* ---------- V1: dong so fact + dim hop dong ---------- */
SELECT N'V1' AS check_id, t.what, t.expected, a.actual,
       CASE WHEN t.expected = a.actual THEN N'PASS' ELSE N'FAIL' END AS result
FROM (VALUES (N'FACT_TRADE (13725+958+13252)', 27935),
             (N'FACT_TRADE perspective=1 (core+bridge)', 14683),
             (N'FACT_TRADE perspective=2', 13252),
             (N'FACT_TARIFF_RATE', 419),
             (N'FACT_MACRO_INDICATOR', 300),
             (N'DIM_PARTNER', 7),
             (N'DIM_COMMODITY', 14),
             (N'DIM_DATE (120 thang + 10 nam sentinel)', 130),
             (N'DIM_AUDIT (18+14+49+2)', 83),
             (N'DW_USAGE_RULE', 5),
             (N'VW_TRADE_RECONCILIATION (co o MISSING_VN_REPORTED cua 2024)', 1)) AS t(what, expected)
CROSS APPLY (SELECT actual = CASE t.what
    WHEN N'FACT_TRADE (13725+958+13252)' THEN (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE)
    WHEN N'FACT_TRADE perspective=1 (core+bridge)' THEN (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE WHERE perspective_key = 1)
    WHEN N'FACT_TRADE perspective=2' THEN (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE WHERE perspective_key = 2)
    WHEN N'FACT_TARIFF_RATE' THEN (SELECT COUNT_BIG(*) FROM dbo.FACT_TARIFF_RATE)
    WHEN N'FACT_MACRO_INDICATOR' THEN (SELECT COUNT_BIG(*) FROM dbo.FACT_MACRO_INDICATOR)
    WHEN N'DIM_PARTNER' THEN (SELECT COUNT_BIG(*) FROM dbo.DIM_PARTNER)
    WHEN N'DIM_COMMODITY' THEN (SELECT COUNT_BIG(*) FROM dbo.DIM_COMMODITY)
    WHEN N'DIM_DATE (120 thang + 10 nam sentinel)' THEN (SELECT COUNT_BIG(*) FROM dbo.DIM_DATE)
    WHEN N'DIM_AUDIT (18+14+49+2)' THEN (SELECT COUNT_BIG(*) FROM dbo.DIM_AUDIT)
    WHEN N'DW_USAGE_RULE' THEN (SELECT COUNT_BIG(*) FROM dbo.DW_USAGE_RULE)
ELSE (SELECT CASE WHEN COUNT_BIG(*) >= 1 THEN 1 ELSE 0 END FROM dbo.VW_TRADE_RECONCILIATION
          WHERE discrepancy_level = 'MISSING_VN_REPORTED') END) AS a;
GO

/* ---------- V2: grain hop dong — 0 trung ---------- */
SELECT N'V2' AS check_id, N'FACT_TRADE trung grain' AS what, 0 AS expected,
       (SELECT COUNT_BIG(*) FROM (
           SELECT date_key, partner_key, commodity_key, flow_key, perspective_key
           FROM dbo.FACT_TRADE GROUP BY date_key, partner_key, commodity_key, flow_key, perspective_key
           HAVING COUNT_BIG(*) > 1) d) AS actual,
       CASE WHEN (SELECT COUNT_BIG(*) FROM (
           SELECT date_key, partner_key, commodity_key, flow_key, perspective_key
           FROM dbo.FACT_TRADE GROUP BY date_key, partner_key, commodity_key, flow_key, perspective_key
           HAVING COUNT_BIG(*) > 1) d) = 0 THEN N'PASS' ELSE N'FAIL' END AS result;
GO

/* ---------- V2b: core va bridge KHONG duoc chong nam tren cung o (hop dong docs/13 §5.1) ---------- */
SELECT N'V2b' AS check_id, N'851713 2015-2021: o co ca batch w2_* lan br_*' AS what, 0 AS expected,
       COUNT_BIG(*) AS actual,
       CASE WHEN COUNT_BIG(*) = 0 THEN N'PASS' ELSE N'FAIL — DUNG NAP, kiem tra lai bridge' END AS result
FROM (SELECT f.date_key, f.partner_key, f.commodity_key, f.flow_key
      FROM dbo.FACT_TRADE f JOIN dbo.DIM_AUDIT a ON a.audit_key = f.audit_key
      WHERE f.perspective_key = 1 AND f.commodity_key = (SELECT commodity_key FROM dbo.DIM_COMMODITY WHERE hs6 = '851713')
        AND f.date_key BETWEEN 201501 AND 202112 AND a.batch_id LIKE 'w2[_]%'
      INTERSECT
      SELECT f.date_key, f.partner_key, f.commodity_key, f.flow_key
      FROM dbo.FACT_TRADE f JOIN dbo.DIM_AUDIT a ON a.audit_key = f.audit_key
      WHERE f.perspective_key = 1 AND f.commodity_key = (SELECT commodity_key FROM dbo.DIM_COMMODITY WHERE hs6 = '851713')
        AND f.date_key BETWEEN 201501 AND 202112 AND a.batch_id LIKE 'br[_]%') x;
GO

/* ---------- V3: khoa ngoai — 0 mo coi ---------- */
SELECT N'V3' AS check_id, v.what, 0 AS expected, v.actual,
       CASE WHEN v.actual = 0 THEN N'PASS' ELSE N'FAIL' END AS result
FROM (VALUES
 (N'FT.date_key → DIM_DATE',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE f LEFT JOIN dbo.DIM_DATE d ON d.date_key = f.date_key WHERE d.date_key IS NULL)),
 (N'FT.partner_key → DIM_PARTNER',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE f LEFT JOIN dbo.DIM_PARTNER p ON p.partner_key = f.partner_key WHERE p.partner_key IS NULL)),
 (N'FT.commodity_key → DIM_COMMODITY',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE f LEFT JOIN dbo.DIM_COMMODITY c ON c.commodity_key = f.commodity_key WHERE c.commodity_key IS NULL)),
 (N'FT.audit_key → DIM_AUDIT',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE f LEFT JOIN dbo.DIM_AUDIT a ON a.audit_key = f.audit_key WHERE a.audit_key IS NULL)),
 (N'TR.audit_key → DIM_AUDIT',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_TARIFF_RATE f LEFT JOIN dbo.DIM_AUDIT a ON a.audit_key = f.audit_key WHERE a.audit_key IS NULL)),
(N'MC.partner_key (iso3) → DIM_PARTNER',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_MACRO_INDICATOR f LEFT JOIN dbo.DIM_PARTNER p ON p.partner_key = f.partner_key WHERE p.partner_key IS NULL)),
 (N'mirror rows co partner_code_src=704 (invariant Q1)',
  (SELECT COUNT_BIG(*) FROM dbo.FACT_TRADE f JOIN dbo.DIM_PERSPECTIVE p ON p.perspective_key = f.perspective_key
    WHERE p.code = 'PARTNER_MIRROR' AND f.partner_code_src <> '704'))
) AS v(what, actual);
GO

/* ---------- V4: 14 NEO — sum World 2023 cua FACT_TRADE phai = bang chung audit Tuan 2 ---------- */
;WITH calc AS (
    SELECT c.hs6, f.flow_key, SUM(f.primary_value_usd) AS total
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_COMMODITY c ON c.commodity_key = f.commodity_key
    JOIN dbo.DIM_PARTNER  p ON p.partner_key = f.partner_key
    WHERE f.perspective_key = 1 AND p.code_comtrade = '0' AND f.date_key BETWEEN 202301 AND 202312
    GROUP BY c.hs6, f.flow_key
)
SELECT N'V4' AS check_id, a.flow + N'/' + a.hs6 AS what, a.anchor AS expected,
       COALESCE(x.total, 0) AS actual,
       CASE WHEN x.total IS NOT NULL AND ABS(x.total - a.anchor) <= a.anchor * 0.0001
            THEN N'PASS' ELSE N'FAIL' END AS result
FROM (VALUES ('X','851713',26460317776.0), ('X','640399',4991396908.0), ('X','100630',4060727368.0),
             ('X','090111',2977954667.0), ('X','080132',2916825905.0), ('X','854442',2062142409.0),
             ('X','610910',1401669880.0), ('X','090411',683211713.0),
             ('M','854231',17797673474.0), ('M','847330',928122689.0), ('M','851762',841528135.0),
             ('M','390120',827368947.0), ('M','540761',484289054.0), ('M','721049',137743539.0))
     AS a(flow, hs6, anchor)
LEFT JOIN calc x ON x.hs6 = a.hs6 AND x.flow_key = CASE a.flow WHEN 'X' THEN 1 ELSE 2 END
ORDER BY result DESC, what;
GO

/* ---------- V5: 7 o mirror da chinh xac tu results/week2/mirror_partner_extract.json ----------
   (o thu 8 — EXP_JPN_COFFEE_202301 — doi chieu tay trong json do, khong hard-code o day.) ---------- */
;WITH cells(rep, flow, hs6, period, val) AS (
    SELECT * FROM (VALUES ('392','M','090111',202401,35660719.503), ('842','M','090111',202301,37790801.000),
           ('276','M','090111',202301,38271554.955), ('156','X','851762',202301,29945226.000),
           ('410','X','854231',202301,217401413.000), ('156','X','851762',202401,62727085.000),
           ('410','X','854231',202401,412589570.000)) AS v(rep, flow, hs6, period, val)
)
SELECT N'V5' AS check_id, c.rep + N'/' + c.flow + N'/' + c.hs6 + N'/' + CAST(c.period AS VARCHAR(6)) AS what,
       c.val AS expected, COALESCE(f.primary_value_usd, 0) AS actual,
       CASE WHEN f.primary_value_usd IS NOT NULL AND ABS(f.primary_value_usd - c.val) <= 0.001
            THEN N'PASS' ELSE N'FAIL' END AS result
FROM cells c
LEFT JOIN dbo.FACT_TRADE f
       ON f.perspective_key = 2 AND f.reporter_code = c.rep
      AND f.flow_key = CASE c.flow WHEN 'X' THEN 1 ELSE 2 END
      AND f.date_key = c.period
AND f.commodity_key = (SELECT commodity_key FROM dbo.DIM_COMMODITY WHERE hs6 = c.hs6)
      AND f.partner_key     = (SELECT partner_key  FROM dbo.DIM_PARTNER   WHERE code_comtrade = c.rep)
ORDER BY result DESC, what;
GO

/* ---------- V6: tong theo perspective (thong ke — KHONG co phep cong 2 perspective) ---------- */
SELECT N'V6' AS check_id, p.label_vi AS what,
       CAST(NULL AS FLOAT) AS expected,
       SUM(f.primary_value_usd) AS actual, N'INFO' AS result
FROM dbo.FACT_TRADE f JOIN dbo.DIM_PERSPECTIVE p ON p.perspective_key = f.perspective_key
GROUP BY p.label_vi
ORDER BY what;
GO

/* ---------- V7: view co du 5 nhan, co dong 2024 MISSING_VN_REPORTED, va con dong uoc luong (Q6 khong loc) ---------- */
SELECT N'V7' AS check_id, N'view: so nhan khac nhau' AS what, 5 AS expected,
       COUNT(DISTINCT discrepancy_level) AS actual,
       CASE WHEN COUNT(DISTINCT discrepancy_level) = 5 THEN N'PASS' ELSE N'FAIL' END AS result
FROM dbo.VW_TRADE_RECONCILIATION
UNION ALL
SELECT N'V7', N'view: 2024 missing_vn_reported > 0', 1,
       CASE WHEN EXISTS (SELECT 1 FROM dbo.VW_TRADE_RECONCILIATION v
                         WHERE v.discrepancy_level = 'MISSING_VN_REPORTED'
                           AND v.date_key BETWEEN 202401 AND 202412) THEN 1 ELSE 0 END,
       CASE WHEN EXISTS (SELECT 1 FROM dbo.VW_TRADE_RECONCILIATION v
                         WHERE v.discrepancy_level = 'MISSING_VN_REPORTED'
                           AND v.date_key BETWEEN 202401 AND 202412) THEN N'PASS' ELSE N'FAIL' END
UNION ALL
SELECT N'V7', N'view: con dong uoc luong (mirror_is_reported = 0) — Q6 "khong loc" dang hieu luc', 1,
       CASE WHEN EXISTS (SELECT 1 FROM dbo.VW_TRADE_RECONCILIATION WHERE mirror_is_reported = 0) THEN 1 ELSE 0 END,
       CASE WHEN EXISTS (SELECT 1 FROM dbo.VW_TRADE_RECONCILIATION WHERE mirror_is_reported = 0) THEN N'PASS' ELSE N'FAIL' END;
GO

PRINT N'Xong V0–V7. moi FAIL: mo docs/13 §5 + §9 va sql/README.md muc ''su co''; DUNG sua so lieu truc tiep trong fact.';
GO
