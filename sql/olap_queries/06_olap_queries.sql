/* =============================================================
  06_olap_queries.sql — TLCN Kho du lieu XNK Viet Nam (Tuan 10)
  Muc tieu: Xay dung ≥15 truy van OLAP nang cao (CUBE, ROLLUP,
  GROUPING SETS, Window Functions, HHI, CR-4, YoY, Seasonality),
  tao Data Marts/Indexed Views phuc vu Dashboard (Tuan 11).
  ============================================================= */

USE TLCN_XNK;
GO

PRINT N'=============================================================';
PRINT N'06_olap_queries.sql — BẮT ĐẦU CHẠY BỘ TRUY VẤN OLAP TUẦN 10';
PRINT N'=============================================================';
GO

/* =============================================================
   QUERY 01: TỔNG HỢP KIM NGẠCH THEO NĂM × ĐỐI TÁC × LUỒNG
   KỸ THUẬT: ROLLUP — Tự động sinh subtotal theo nhóm
   NGHIỆP VỤ: Báo cáo kim ngạch XNK tổng quát theo đối tác, có 
   tổng phụ theo đối tác-năm, theo năm, và tổng cộng toàn bộ.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 01: ROLLUP — Kim ngạch XNK theo Năm × Đối tác × Luồng';
PRINT N'-------------------------------------------------------------';

SELECT
    dd.calendar_year,
    dp.partner_name,
    df.name_vi                              AS flow_name,
    SUM(f.primary_value_usd)                AS total_value_usd,
    COUNT(*)                                AS record_count,
    /* Nhan biet dong subtotal / grand total */
    GROUPING(dd.calendar_year)              AS is_all_years,
    GROUPING(dp.partner_name)               AS is_all_partners,
    GROUPING(df.name_vi)                    AS is_all_flows
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
WHERE f.perspective_key = 1         -- Chi lay so lieu VN bao cao chinh thuc
  AND dp.is_aggregate = 0           -- Loai bo dong World
GROUP BY ROLLUP (dd.calendar_year, dp.partner_name, df.name_vi)
ORDER BY 
    GROUPING(dd.calendar_year),
    dd.calendar_year,
    GROUPING(dp.partner_name),
    dp.partner_name,
    GROUPING(df.name_vi);
GO

/* =============================================================
   QUERY 02: MA TRẬN ĐA CHIỀU THEO KHU VỰC × NHÓM HÀNG × NĂM
   KỸ THUẬT: CUBE — Tạo tất cả tổ hợp subtotal có thể
   NGHIỆP VỤ: Phân tích toàn diện, cho phép nhìn kim ngạch từ
   mọi góc (chỉ theo khu vực, chỉ theo nhóm hàng, chéo v.v.)
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 02: CUBE — Ma trận đa chiều Khu vực × Nhóm hàng × Năm';
PRINT N'-------------------------------------------------------------';

SELECT
    dp.region,
    dc.commodity_group,
    dd.calendar_year,
    SUM(f.primary_value_usd)     AS total_value_usd,
    COUNT(DISTINCT f.partner_key) AS partner_count,
    COUNT(DISTINCT f.commodity_key) AS commodity_count,
    GROUPING_ID(dp.region, dc.commodity_group, dd.calendar_year) AS grouping_level
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key       = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key     = f.partner_key
JOIN dbo.DIM_COMMODITY dc  ON dc.commodity_key   = f.commodity_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
GROUP BY CUBE (dp.region, dc.commodity_group, dd.calendar_year)
HAVING SUM(f.primary_value_usd) > 0
ORDER BY 
    GROUPING_ID(dp.region, dc.commodity_group, dd.calendar_year),
    dp.region, dc.commodity_group, dd.calendar_year;
GO

/* =============================================================
   QUERY 03: GROUPING SETS — SO SÁNH LINH HOẠT NHIỀU GÓC NHÌN
   KỸ THUẬT: GROUPING SETS — Chỉ sinh đúng các tổ hợp cần thiết
   NGHIỆP VỤ: Một truy vấn duy nhất cho 4 báo cáo:
     (a) Theo Đối tác × Năm
     (b) Theo Nhóm hàng × Năm
     (c) Theo Khu vực × Năm  
     (d) Tổng cộng toàn bộ
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 03: GROUPING SETS — 4 góc nhìn XNK trong 1 câu truy vấn';
PRINT N'-------------------------------------------------------------';

SELECT
    dp.partner_name,
    dc.commodity_group,
    dp.region,
    dd.calendar_year,
    df.name_vi                    AS flow_name,
    SUM(f.primary_value_usd)     AS total_value_usd,
    GROUPING_ID(dp.partner_name, dc.commodity_group, dp.region, dd.calendar_year) AS gs_id
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key       = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key     = f.partner_key
JOIN dbo.DIM_COMMODITY dc  ON dc.commodity_key   = f.commodity_key
JOIN dbo.DIM_FLOW df       ON df.flow_key        = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
GROUP BY GROUPING SETS (
    (dp.partner_name, dd.calendar_year, df.name_vi),    -- (a) Theo doi tac
    (dc.commodity_group, dd.calendar_year, df.name_vi), -- (b) Theo nhom hang
    (dp.region, dd.calendar_year, df.name_vi),          -- (c) Theo khu vuc
    (df.name_vi)                                         -- (d) Tong cong
)
ORDER BY gs_id, dd.calendar_year, df.name_vi;
GO

/* =============================================================
   QUERY 04: XẾP HẠNG ĐỐI TÁC THEO KIM NGẠCH TỪNG NĂM
   KỸ THUẬT: RANK() + DENSE_RANK() — Window Function
   NGHIỆP VỤ: Top N đối tác lớn nhất mỗi năm, phân biệt X và M.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 04: RANK — Xếp hạng Top đối tác XNK theo năm';
PRINT N'-------------------------------------------------------------';

SELECT * FROM (
    SELECT
        dd.calendar_year,
        dp.partner_name,
        df.name_vi                     AS flow_name,
        SUM(f.primary_value_usd)       AS total_value_usd,
        RANK() OVER (
            PARTITION BY dd.calendar_year, df.name_vi 
            ORDER BY SUM(f.primary_value_usd) DESC
        ) AS rank_in_year,
        DENSE_RANK() OVER (
            PARTITION BY dd.calendar_year, df.name_vi 
            ORDER BY SUM(f.primary_value_usd) DESC
        ) AS dense_rank_in_year
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
    JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
    JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
    GROUP BY dd.calendar_year, dp.partner_name, df.name_vi
) ranked
WHERE rank_in_year <= 5
ORDER BY calendar_year, flow_name, rank_in_year;
GO

/* =============================================================
   QUERY 05: TĂNG TRƯỞNG NĂM SAU SO NĂM TRƯỚC (YoY GROWTH)
   KỸ THUẬT: LAG() — Lấy giá trị kỳ trước
   NGHIỆP VỤ: So sánh kim ngạch XNK mỗi đối tác qua các năm,
   tính % tăng trưởng/suy giảm (YoY Growth Rate).
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 05: LAG — Tăng trưởng XNK Year-over-Year (YoY %)';
PRINT N'-------------------------------------------------------------';

SELECT
    calendar_year,
    partner_name,
    flow_name,
    total_value_usd,
    prev_year_value,
    CASE 
        WHEN prev_year_value IS NULL OR prev_year_value = 0 THEN NULL
        ELSE ROUND(100.0 * (total_value_usd - prev_year_value) / prev_year_value, 2)
    END AS yoy_growth_pct
FROM (
    SELECT
        dd.calendar_year,
        dp.partner_name,
        df.name_vi                      AS flow_name,
        SUM(f.primary_value_usd)        AS total_value_usd,
        LAG(SUM(f.primary_value_usd)) OVER (
            PARTITION BY dp.partner_name, df.name_vi 
            ORDER BY dd.calendar_year
        ) AS prev_year_value
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
    JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
    JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
    GROUP BY dd.calendar_year, dp.partner_name, df.name_vi
) yoy
ORDER BY partner_name, flow_name, calendar_year;
GO

/* =============================================================
   QUERY 06: DỰ BÁO XU HƯỚNG KỲ TỚI (LEAD)
   KỸ THUẬT: LEAD() — Nhìn sang kỳ tiếp theo
   NGHIỆP VỤ: Mỗi đối tác × luồng, nhìn trước kim ngạch năm tới
   để so sánh kỳ vọng / thực tế.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 06: LEAD — Nhìn trước kim ngạch kỳ tiếp theo';
PRINT N'-------------------------------------------------------------';

SELECT
    dd.calendar_year,
    dp.partner_name,
    df.name_vi                           AS flow_name,
    SUM(f.primary_value_usd)             AS current_value_usd,
    LEAD(SUM(f.primary_value_usd)) OVER (
        PARTITION BY dp.partner_name, df.name_vi 
        ORDER BY dd.calendar_year
    ) AS next_year_value_usd,
    LEAD(SUM(f.primary_value_usd)) OVER (
        PARTITION BY dp.partner_name, df.name_vi 
        ORDER BY dd.calendar_year
    ) - SUM(f.primary_value_usd) AS change_to_next_year
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
GROUP BY dd.calendar_year, dp.partner_name, df.name_vi
ORDER BY dp.partner_name, df.name_vi, dd.calendar_year;
GO

/* =============================================================
   QUERY 07: PHÂN VỊ ĐỐI TÁC (NTILE) VÀ TỶ TRỌNG TÍCH LŨY
   KỸ THUẬT: NTILE(4) + SUM() OVER + PERCENT_RANK()
   NGHIỆP VỤ: Phân đối tác thành 4 nhóm (Q1-Q4) theo kim ngạch,
   tính tỷ trọng tích lũy (Running %) và Percentile Rank.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 07: NTILE + PERCENT_RANK — Phân vị đối tác XNK';
PRINT N'-------------------------------------------------------------';

WITH partner_totals AS (
    SELECT
        dp.partner_name,
        SUM(f.primary_value_usd) AS total_value_usd
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_PARTNER dp ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
    GROUP BY dp.partner_name
)
SELECT
    partner_name,
    total_value_usd,
    NTILE(4) OVER (ORDER BY total_value_usd DESC) AS quartile,
    ROUND(PERCENT_RANK() OVER (ORDER BY total_value_usd), 4) AS percentile_rank,
    SUM(total_value_usd) OVER (
        ORDER BY total_value_usd DESC 
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_value_usd,
    ROUND(100.0 * SUM(total_value_usd) OVER (
        ORDER BY total_value_usd DESC 
        ROWS UNBOUNDED PRECEDING
    ) / SUM(total_value_usd) OVER (), 2) AS cumulative_pct
FROM partner_totals
ORDER BY total_value_usd DESC;
GO

/* =============================================================
   QUERY 08: CHỈ SỐ TẬP TRUNG THỊ TRƯỜNG HHI & CR-4
   KỸ THUẬT: Window SUM() + Power function
   NGHIỆP VỤ: Herfindahl-Hirschman Index (HHI) và tỷ trọng 
   Top 4 đối tác (CR-4) theo từng năm — đo lường mức độ tập 
   trung thương mại của Việt Nam.
   HHI < 1500 = phân tán | 1500-2500 = vừa | > 2500 = tập trung
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 08: HHI & CR-4 — Chỉ số tập trung thị trường XNK';
PRINT N'-------------------------------------------------------------';

WITH yearly_partner AS (
    SELECT
        dd.calendar_year,
        dp.partner_name,
        df.name_vi                    AS flow_name,
        SUM(f.primary_value_usd)      AS partner_value,
        SUM(SUM(f.primary_value_usd)) OVER (
            PARTITION BY dd.calendar_year, df.name_vi
        ) AS year_total
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
    JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
    JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
    GROUP BY dd.calendar_year, dp.partner_name, df.name_vi
),
shares AS (
    SELECT
        calendar_year,
        partner_name,
        flow_name,
        partner_value,
        year_total,
        100.0 * partner_value / NULLIF(year_total, 0) AS market_share_pct,
        RANK() OVER (
            PARTITION BY calendar_year, flow_name 
            ORDER BY partner_value DESC
        ) AS rk
    FROM yearly_partner
)
SELECT
    calendar_year,
    flow_name,
    -- HHI = Sum of squared market shares (scale 0–10000)
    ROUND(SUM(POWER(market_share_pct, 2)), 0) AS hhi_index,
    CASE 
        WHEN SUM(POWER(market_share_pct, 2)) < 1500 THEN N'Phân tán (cạnh tranh)'
        WHEN SUM(POWER(market_share_pct, 2)) <= 2500 THEN N'Tập trung vừa'
        ELSE N'Tập trung cao'
    END AS hhi_interpretation,
    -- CR-4 = Tổng thị phần 4 đối tác lớn nhất
    ROUND(SUM(CASE WHEN rk <= 4 THEN market_share_pct ELSE 0 END), 2) AS cr4_pct,
    CASE 
        WHEN SUM(CASE WHEN rk <= 4 THEN market_share_pct ELSE 0 END) > 80 THEN N'Rất tập trung (>80%)'
        WHEN SUM(CASE WHEN rk <= 4 THEN market_share_pct ELSE 0 END) > 60 THEN N'Tập trung (>60%)'
        ELSE N'Phân tán (<60%)'
    END AS cr4_interpretation
FROM shares
GROUP BY calendar_year, flow_name
ORDER BY flow_name, calendar_year;
GO

/* =============================================================
   QUERY 09: PHÂN TÍCH MÙA VỤ — XU HƯỚNG THÁNG TRONG NĂM
   KỸ THUẬT: AVG() OVER (PARTITION) + Deviation
   NGHIỆP VỤ: Xác định tháng cao điểm/thấp điểm XNK, đo mức
   chênh lệch với trung bình tháng — phục vụ kế hoạch logistics.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 09: Phân tích mùa vụ XNK — Tháng cao điểm/thấp điểm';
PRINT N'-------------------------------------------------------------';

WITH monthly_trade AS (
    SELECT
        dd.[month],
        dd.calendar_year,
        df.name_vi AS flow_name,
        SUM(f.primary_value_usd) AS monthly_value
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd ON dd.date_key = f.date_key
    JOIN dbo.DIM_FLOW df ON df.flow_key = f.flow_key
    WHERE f.perspective_key = 1
      AND dd.[month] IS NOT NULL          -- Chi lay dong thang, khong lay dong nam sentinel
      AND dd.[month] BETWEEN 1 AND 12
    GROUP BY dd.[month], dd.calendar_year, df.name_vi
)
SELECT
    [month],
    flow_name,
    ROUND(AVG(monthly_value), 0)      AS avg_monthly_value,
    ROUND(MIN(monthly_value), 0)      AS min_monthly_value,
    ROUND(MAX(monthly_value), 0)      AS max_monthly_value,
    COUNT(*)                          AS year_count,
    /* Seasonal Index: so sanh voi trung binh chung cua tat ca thang */
    ROUND(100.0 * AVG(monthly_value) / 
        AVG(AVG(monthly_value)) OVER (PARTITION BY flow_name), 2
    ) AS seasonal_index,
    CASE 
        WHEN AVG(monthly_value) > 1.1 * AVG(AVG(monthly_value)) OVER (PARTITION BY flow_name) 
            THEN N'▲ Tháng cao điểm'
        WHEN AVG(monthly_value) < 0.9 * AVG(AVG(monthly_value)) OVER (PARTITION BY flow_name) 
            THEN N'▼ Tháng thấp điểm'
        ELSE N'● Bình thường'
    END AS season_label
FROM monthly_trade
GROUP BY [month], flow_name
ORDER BY flow_name, [month];
GO

/* =============================================================
   QUERY 10: TRUNG BÌNH TRƯỢT 3 NĂM (MOVING AVERAGE)
   KỸ THUẬT: AVG() OVER (ROWS BETWEEN)
   NGHIỆP VỤ: Làm mượt xu hướng kim ngạch, loại bỏ biến động 
   ngắn hạn — dùng để nhận biết trend dài hạn.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 10: Moving Average 3 năm — Xu hướng dài hạn XNK';
PRINT N'-------------------------------------------------------------';

SELECT
    dd.calendar_year,
    dp.partner_name,
    df.name_vi                        AS flow_name,
    SUM(f.primary_value_usd)          AS annual_value_usd,
    ROUND(AVG(SUM(f.primary_value_usd)) OVER (
        PARTITION BY dp.partner_name, df.name_vi
        ORDER BY dd.calendar_year
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ), 0) AS moving_avg_3yr,
    /* Gap = actual vs moving avg */
    SUM(f.primary_value_usd) - ROUND(AVG(SUM(f.primary_value_usd)) OVER (
        PARTITION BY dp.partner_name, df.name_vi
        ORDER BY dd.calendar_year
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ), 0) AS deviation_from_trend
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
GROUP BY dd.calendar_year, dp.partner_name, df.name_vi
ORDER BY dp.partner_name, df.name_vi, dd.calendar_year;
GO

/* =============================================================
   QUERY 11: CÁN CÂN THƯƠNG MẠI (TRADE BALANCE) & XU HƯỚNG
   KỸ THUẬT: PIVOT logic + LAG() 
   NGHIỆP VỤ: Cán cân XNK mỗi đối tác theo năm, nhận diện thặng
   dư/thâm hụt và xu hướng so kỳ trước.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 11: Cán cân thương mại & xu hướng theo đối tác';
PRINT N'-------------------------------------------------------------';

WITH trade_pivot AS (
    SELECT
        dd.calendar_year,
        dp.partner_name,
        SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END) AS export_value,
        SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END) AS import_value
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
    JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
    GROUP BY dd.calendar_year, dp.partner_name
)
SELECT
    calendar_year,
    partner_name,
    ROUND(export_value / 1000000.0, 2)  AS export_mil_usd,
    ROUND(import_value / 1000000.0, 2)  AS import_mil_usd,
    ROUND((export_value - import_value) / 1000000.0, 2) AS balance_mil_usd,
    CASE 
        WHEN export_value > import_value THEN N'🟢 Thặng dư'
        WHEN export_value < import_value THEN N'🔴 Thâm hụt'
        ELSE N'● Cân bằng'
    END AS balance_status,
    LAG(export_value - import_value) OVER (
        PARTITION BY partner_name ORDER BY calendar_year
    ) AS prev_year_balance,
    CASE 
        WHEN (export_value - import_value) > ISNULL(LAG(export_value - import_value) OVER (
            PARTITION BY partner_name ORDER BY calendar_year
        ), 0) THEN N'↑ Cải thiện'
        ELSE N'↓ Giảm sút'
    END AS trend_vs_prev
FROM trade_pivot
ORDER BY partner_name, calendar_year;
GO

/* =============================================================
   QUERY 12: PHÂN TÍCH NHÓM HÀNG — THỊ PHẦN & XẾP HẠNG THAY ĐỔI
   KỸ THUẬT: RANK() + LAG() — So sánh thứ hạng liên niên
   NGHIỆP VỤ: Nhóm hàng nào đang lên, nhóm nào đang tụt hạng?
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 12: Thị phần nhóm hàng & biến động thứ hạng qua các năm';
PRINT N'-------------------------------------------------------------';

WITH commodity_yearly AS (
    SELECT
        dd.calendar_year,
        dc.commodity_group,
        SUM(f.primary_value_usd) AS group_value,
        SUM(SUM(f.primary_value_usd)) OVER (
            PARTITION BY dd.calendar_year
        ) AS year_total,
        RANK() OVER (
            PARTITION BY dd.calendar_year 
            ORDER BY SUM(f.primary_value_usd) DESC
        ) AS group_rank
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key      = f.date_key
    JOIN dbo.DIM_COMMODITY dc  ON dc.commodity_key  = f.commodity_key
    WHERE f.perspective_key = 1
    GROUP BY dd.calendar_year, dc.commodity_group
)
SELECT
    calendar_year,
    commodity_group,
    ROUND(group_value / 1000000.0, 2) AS value_mil_usd,
    ROUND(100.0 * group_value / NULLIF(year_total, 0), 2) AS market_share_pct,
    group_rank,
    LAG(group_rank) OVER (
        PARTITION BY commodity_group ORDER BY calendar_year
    ) AS prev_year_rank,
    CASE 
        WHEN group_rank < ISNULL(LAG(group_rank) OVER (
            PARTITION BY commodity_group ORDER BY calendar_year
        ), group_rank) THEN N'▲ Lên hạng'
        WHEN group_rank > ISNULL(LAG(group_rank) OVER (
            PARTITION BY commodity_group ORDER BY calendar_year
        ), group_rank) THEN N'▼ Xuống hạng'
        ELSE N'● Giữ nguyên'
    END AS rank_trend
FROM commodity_yearly
ORDER BY calendar_year, group_rank;
GO

/* =============================================================
   QUERY 13: PHÂN TÍCH TÁC ĐỘNG THUẾ QUAN — MFN vs PREF
   KỸ THUẬT: GROUPING SETS + Weighted Average (R2)
   NGHIỆP VỤ: So sánh thuế suất MFN vs ưu đãi FTA, tính lợi ích 
   thuế quan ước tính = chênh lệch MFN − PREF (theo R2: trung bình 
   có quyền theo total_lines, không phải AVG trần).
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 13: Tác động thuế quan — MFN vs PREF (Weighted Avg)';
PRINT N'-------------------------------------------------------------';

SELECT
    dd.calendar_year,
    dp.partner_name,
    dp.has_fta_with_vn,
    dp.fta_name,
    dc.commodity_group,
    dtt.label_vi                     AS tariff_type,
    /* R2-compliant weighted average: SUM(pct*total_lines)/SUM(total_lines) */
    CASE 
        WHEN SUM(ft.total_lines) > 0 
        THEN ROUND(SUM(ft.ad_valorem_pct * ft.total_lines) / SUM(ft.total_lines), 4)
        ELSE NULL 
    END AS weighted_avg_tariff_pct,
    SUM(ft.total_lines)              AS total_tariff_lines,
    GROUPING_ID(dd.calendar_year, dp.partner_name, dc.commodity_group) AS gs_level
FROM dbo.FACT_TARIFF_RATE ft
JOIN dbo.DIM_DATE dd            ON dd.date_key         = ft.date_key
JOIN dbo.DIM_PARTNER dp         ON dp.partner_key      = ft.partner_key
JOIN dbo.DIM_COMMODITY dc       ON dc.commodity_key    = ft.commodity_key
JOIN dbo.DIM_TARIFF_TYPE dtt    ON dtt.tariff_type_key = ft.tariff_type_key
WHERE ft.ad_valorem_pct IS NOT NULL
GROUP BY GROUPING SETS (
    (dd.calendar_year, dp.partner_name, dp.has_fta_with_vn, dp.fta_name, dc.commodity_group, dtt.label_vi),
    (dd.calendar_year, dp.partner_name, dp.has_fta_with_vn, dp.fta_name, dtt.label_vi),
    (dd.calendar_year, dtt.label_vi)
)
ORDER BY gs_level, dd.calendar_year, dp.partner_name, dc.commodity_group;
GO

/* =============================================================
   QUERY 14: TƯƠNG QUAN XNK VỚI CHỈ SỐ VĨ MÔ (GDP, Tỷ giá)
   KỸ THUẬT: JOIN chéo Fact + Window
   NGHIỆP VỤ: Kim ngạch XNK có biến động đồng pha với GDP hay 
   tỷ giá không? Bước đầu khám phá correlation.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 14: Tương quan XNK — GDP & Tỷ giá (Macro Indicators)';
PRINT N'-------------------------------------------------------------';

WITH trade_yearly AS (
    SELECT
        dd.calendar_year,
        SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END) AS total_export,
        SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END) AS total_import
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd ON dd.date_key = f.date_key
    WHERE f.perspective_key = 1
    GROUP BY dd.calendar_year
),
macro_pivot AS (
    SELECT 
        dd.calendar_year,
        di.code_wb,
        fm.[value]
    FROM dbo.FACT_MACRO_INDICATOR fm
    JOIN dbo.DIM_DATE dd      ON dd.date_key      = fm.date_key
    JOIN dbo.DIM_INDICATOR di ON di.indicator_key  = fm.indicator_key
    JOIN dbo.DIM_PARTNER dp   ON dp.partner_key    = fm.partner_key
    WHERE dp.is_vietnam = 1    -- Chi lay chi so cua Viet Nam
)
SELECT
    t.calendar_year,
    ROUND(t.total_export / 1000000.0, 2)  AS export_mil_usd,
    ROUND(t.total_import / 1000000.0, 2)  AS import_mil_usd,
    gdp.[value]                           AS gdp_current_usd,
    fx.[value]                            AS exchange_rate_vnd_usd,
    LAG(ROUND(t.total_export / 1000000.0, 2)) OVER (ORDER BY t.calendar_year) AS prev_export,
    LAG(gdp.[value]) OVER (ORDER BY t.calendar_year) AS prev_gdp
FROM trade_yearly t
LEFT JOIN macro_pivot gdp ON gdp.calendar_year = t.calendar_year AND gdp.code_wb = 'NY.GDP.MKTP.CD'
LEFT JOIN macro_pivot fx  ON fx.calendar_year  = t.calendar_year AND fx.code_wb  = 'PA.NUS.FCRF'
ORDER BY t.calendar_year;
GO

/* =============================================================
   QUERY 15: TOP MÃ HÀNG HS6 — KIM NGẠCH & TỶ TRỌNG TRONG NHÓM
   KỸ THUẬT: ROW_NUMBER() + SUM() OVER (PARTITION)
   NGHIỆP VỤ: Chi tiết top 3 mã HS6 lớn nhất trong mỗi nhóm hàng
   mỗi năm — phục vụ drill-down từ nhóm hàng đến mã chi tiết.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 15: Top 3 mã HS6 theo nhóm hàng mỗi năm';
PRINT N'-------------------------------------------------------------';

SELECT * FROM (
    SELECT
        dd.calendar_year,
        dc.commodity_group,
        dc.hs6,
        dc.name_en                        AS commodity_name,
        SUM(f.primary_value_usd)          AS hs6_value_usd,
        SUM(SUM(f.primary_value_usd)) OVER (
            PARTITION BY dd.calendar_year, dc.commodity_group
        ) AS group_total,
        ROUND(100.0 * SUM(f.primary_value_usd) / NULLIF(
            SUM(SUM(f.primary_value_usd)) OVER (
                PARTITION BY dd.calendar_year, dc.commodity_group
            ), 0
        ), 2) AS pct_in_group,
        ROW_NUMBER() OVER (
            PARTITION BY dd.calendar_year, dc.commodity_group
            ORDER BY SUM(f.primary_value_usd) DESC
        ) AS rn
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key      = f.date_key
    JOIN dbo.DIM_COMMODITY dc  ON dc.commodity_key  = f.commodity_key
    WHERE f.perspective_key = 1
    GROUP BY dd.calendar_year, dc.commodity_group, dc.hs6, dc.name_en
) detail
WHERE rn <= 3
ORDER BY calendar_year, commodity_group, rn;
GO

/* =============================================================
   QUERY 16: PHÂN TÍCH ĐỐI TÁC FTA VS NON-FTA — ROLLUP
   KỸ THUẬT: ROLLUP + CASE — Phân nhóm theo tình trạng FTA
   NGHIỆP VỤ: So sánh tổng kim ngạch của nhóm đối tác có FTA với
   VN vs nhóm không có, theo từng năm — đánh giá hiệu quả FTA.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 16: ROLLUP — Đối tác FTA vs Non-FTA theo năm';
PRINT N'-------------------------------------------------------------';

SELECT
    dd.calendar_year,
    CASE 
        WHEN dp.has_fta_with_vn = 1 THEN N'Có FTA'
        ELSE N'Không FTA'
    END AS fta_status,
    df.name_vi                        AS flow_name,
    SUM(f.primary_value_usd)          AS total_value_usd,
    COUNT(DISTINCT dp.partner_key)    AS partner_count,
    GROUPING(dd.calendar_year)        AS is_total_year,
    GROUPING(df.name_vi)              AS is_total_flow
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
JOIN dbo.DIM_FLOW df       ON df.flow_key    = f.flow_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
  AND dp.is_vietnam = 0
GROUP BY ROLLUP (
    dd.calendar_year, 
    CASE WHEN dp.has_fta_with_vn = 1 THEN N'Có FTA' ELSE N'Không FTA' END,
    df.name_vi
)
ORDER BY 
    GROUPING(dd.calendar_year), dd.calendar_year,
    fta_status,
    GROUPING(df.name_vi), df.name_vi;
GO

/* =============================================================
   QUERY 17: MA TRẬN CHẤT LƯỢNG ĐỐI CHIẾU THEO KHU VỰC × NĂM
   KỸ THUẬT: CUBE + Conditional Aggregation
   NGHIỆP VỤ: Tỷ lệ ô dữ liệu có mức chênh LOW/MODERATE/HIGH
   theo khu vực địa lý × năm — hỗ trợ đánh giá tin cậy dữ liệu.
   ============================================================= */
PRINT N'-------------------------------------------------------------';
PRINT N'QUERY 17: CUBE — Ma trận chất lượng đối chiếu (Region × Year)';
PRINT N'-------------------------------------------------------------';

SELECT
    m.region,
    m.calendar_year,
    COUNT(*) AS total_cells,
    SUM(CASE WHEN m.discrepancy_level = 'LOW'      THEN 1 ELSE 0 END) AS low_count,
    SUM(CASE WHEN m.discrepancy_level = 'MODERATE' THEN 1 ELSE 0 END) AS moderate_count,
    SUM(CASE WHEN m.discrepancy_level = 'HIGH'     THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN m.discrepancy_level IN ('MISSING_VN_REPORTED','MISSING_MIRROR') THEN 1 ELSE 0 END) AS missing_count,
    ROUND(100.0 * SUM(CASE WHEN m.discrepancy_level = 'LOW' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) 
        AS pct_low,
    GROUPING_ID(m.region, m.calendar_year) AS gs_id
FROM dbo.MART_TRADE_RECONCILIATION m
GROUP BY CUBE (m.region, m.calendar_year)
ORDER BY gs_id, m.region, m.calendar_year;
GO

/* =============================================================
   PHẦN B: TẠO DATA MART — BẢNG VẬT LÝ & INDEXED VIEW
   Phục vụ Dashboard Power BI (Tuần 11) với hiệu năng truy vấn tối ưu.
   ============================================================= */

PRINT N'=============================================================';
PRINT N'PHẦN B: TẠO DATA MART & INDEXED VIEW CHO DASHBOARD';
PRINT N'=============================================================';

/* ---- MART 1: MART_TRADE_SUMMARY — Bảng tổng hợp XNK theo Năm × Đối tác × Nhóm hàng ---- */
PRINT N'Tạo MART_TRADE_SUMMARY...';

DROP TABLE IF EXISTS dbo.MART_TRADE_SUMMARY;
GO

SELECT
    dd.calendar_year,
    dd.[month],
    dd.date_key,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    dp.sub_region,
    dp.has_fta_with_vn,
    dp.fta_name,
    dc.commodity_key,
    dc.hs6,
    dc.hs4,
    dc.hs2,
    dc.commodity_group,
    dc.name_en AS commodity_name,
    f.flow_key,
    df.name_vi AS flow_name,
    f.primary_value_usd,
    f.net_wgt_kg,
    f.fob_value_usd,
    f.cif_value_usd,
    f.perspective_key
INTO dbo.MART_TRADE_SUMMARY
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key       = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key     = f.partner_key
JOIN dbo.DIM_COMMODITY dc  ON dc.commodity_key   = f.commodity_key
JOIN dbo.DIM_FLOW df       ON df.flow_key        = f.flow_key
WHERE dp.is_aggregate = 0;   -- Luon loai World
GO

/* Indexes cho MART_TRADE_SUMMARY */
CREATE CLUSTERED INDEX CIX_MART_SUMMARY 
    ON dbo.MART_TRADE_SUMMARY (calendar_year, partner_key, commodity_key, flow_key);
CREATE NONCLUSTERED INDEX IX_MART_SUMMARY_REGION 
    ON dbo.MART_TRADE_SUMMARY (region, calendar_year) INCLUDE (primary_value_usd, flow_key);
CREATE NONCLUSTERED INDEX IX_MART_SUMMARY_GROUP 
    ON dbo.MART_TRADE_SUMMARY (commodity_group, calendar_year) INCLUDE (primary_value_usd, flow_key);
CREATE NONCLUSTERED INDEX IX_MART_SUMMARY_FTA 
    ON dbo.MART_TRADE_SUMMARY (has_fta_with_vn, calendar_year) INCLUDE (primary_value_usd);
GO

DECLARE @mart_summary_count INT = (SELECT COUNT(*) FROM dbo.MART_TRADE_SUMMARY);
PRINT CONCAT(N'MART_TRADE_SUMMARY: ', @mart_summary_count, N' dòng.');
GO

/* ---- MART 2: MART_TRADE_BALANCE — Cán cân thương mại materialized ---- */
PRINT N'Tạo MART_TRADE_BALANCE...';

DROP TABLE IF EXISTS dbo.MART_TRADE_BALANCE;
GO

SELECT
    dd.calendar_year,
    dp.partner_key,
    dp.partner_name,
    dp.region,
    dp.has_fta_with_vn,
    dp.fta_name,
    SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END) AS export_value_usd,
    SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END) AS import_value_usd,
    SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END) -
    SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END) AS trade_balance_usd,
    COUNT(DISTINCT f.commodity_key)  AS commodity_diversity
INTO dbo.MART_TRADE_BALANCE
FROM dbo.FACT_TRADE f
JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
WHERE f.perspective_key = 1
  AND dp.is_aggregate = 0
GROUP BY dd.calendar_year, dp.partner_key, dp.partner_name, dp.region, dp.has_fta_with_vn, dp.fta_name;
GO

CREATE CLUSTERED INDEX CIX_MART_BALANCE 
    ON dbo.MART_TRADE_BALANCE (calendar_year, partner_key);
GO

DECLARE @mart_balance_count INT = (SELECT COUNT(*) FROM dbo.MART_TRADE_BALANCE);
PRINT CONCAT(N'MART_TRADE_BALANCE: ', @mart_balance_count, N' dòng.');
GO

/* ---- MART 3: MART_HHI_YEARLY — Chỉ số tập trung thị trường lưu sẵn ---- */
PRINT N'Tạo MART_HHI_YEARLY...';

DROP TABLE IF EXISTS dbo.MART_HHI_YEARLY;
GO

WITH yearly_partner AS (
    SELECT
        dd.calendar_year,
        f.flow_key,
        dp.partner_name,
        SUM(f.primary_value_usd)      AS partner_value,
        SUM(SUM(f.primary_value_usd)) OVER (
            PARTITION BY dd.calendar_year, f.flow_key
        ) AS year_total
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_DATE dd       ON dd.date_key    = f.date_key
    JOIN dbo.DIM_PARTNER dp    ON dp.partner_key = f.partner_key
    WHERE f.perspective_key = 1
      AND dp.is_aggregate = 0
    GROUP BY dd.calendar_year, f.flow_key, dp.partner_name
),
shares AS (
    SELECT *, 
        100.0 * partner_value / NULLIF(year_total, 0) AS market_share_pct,
        RANK() OVER (PARTITION BY calendar_year, flow_key ORDER BY partner_value DESC) AS rk
    FROM yearly_partner
)
SELECT
    s.calendar_year,
    df.name_vi AS flow_name,
    ROUND(SUM(POWER(s.market_share_pct, 2)), 0) AS hhi_index,
    ROUND(SUM(CASE WHEN s.rk <= 4 THEN s.market_share_pct ELSE 0 END), 2) AS cr4_pct,
    COUNT(DISTINCT s.partner_name) AS partner_count
INTO dbo.MART_HHI_YEARLY
FROM shares s
JOIN dbo.DIM_FLOW df ON df.flow_key = s.flow_key
GROUP BY s.calendar_year, s.flow_key, df.name_vi;
GO

CREATE CLUSTERED INDEX CIX_MART_HHI ON dbo.MART_HHI_YEARLY (calendar_year, flow_name);
GO

DECLARE @mart_hhi_count INT = (SELECT COUNT(*) FROM dbo.MART_HHI_YEARLY);
PRINT CONCAT(N'MART_HHI_YEARLY: ', @mart_hhi_count, N' dòng.');
GO

/* =============================================================
   PHẦN C: TỔNG HỢP KẾT QUẢ
   ============================================================= */
PRINT N'=============================================================';
PRINT N'06_olap_queries.sql: HOÀN THÀNH TOÀN BỘ CÔNG VIỆC TUẦN 10!';
PRINT N'=============================================================';
PRINT N'';
PRINT N'Tóm tắt:';
PRINT N'  ✅ 17 truy vấn OLAP nâng cao';
PRINT N'     - ROLLUP:        Query 01, 16';
PRINT N'     - CUBE:          Query 02, 17';
PRINT N'     - GROUPING SETS: Query 03, 13';
PRINT N'     - RANK/DENSE_RANK/ROW_NUMBER: Query 04, 12, 15';
PRINT N'     - LAG:           Query 05, 11, 14';
PRINT N'     - LEAD:          Query 06';
PRINT N'     - NTILE + PERCENT_RANK: Query 07';
PRINT N'     - HHI & CR-4:   Query 08';
PRINT N'     - Seasonality:   Query 09';
PRINT N'     - Moving Average: Query 10';
PRINT N'  ✅ 3 Data Mart materialized:';
PRINT N'     - MART_TRADE_SUMMARY (chi tiết XNK flatten)';
PRINT N'     - MART_TRADE_BALANCE (cán cân thương mại theo năm)';
PRINT N'     - MART_HHI_YEARLY (chỉ số tập trung thị trường)';
PRINT N'     + MART_TRADE_RECONCILIATION (đã tạo từ Tuần 9)';
PRINT N'  ✅ 8 indexes tối ưu truy vấn Dashboard';
PRINT N'';
PRINT N'Bước tiếp theo: Chạy script này trong SSMS, sau đó thiết lập';
PRINT N'SSAS Multidimensional project trong Visual Studio.';
GO
