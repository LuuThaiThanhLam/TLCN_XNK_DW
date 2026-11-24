# Hướng dẫn cấu hình Metabase BI (tầng Serving phụ trợ)

> **Lưu ý vai trò:** Trong đồ án `TLCN_DW_XNK`, Metabase đóng vai trò tầng trực quan hóa kiểm chứng đầu-cuối (kết nối trực tiếp tới `PostgreSQL` schema `mart` và `ClickHouse` database `olap_xnk`), phục vụ minh chứng 3 bài toán ban đầu (~25% báo cáo).

---

## 1. Kết nối cơ sở dữ liệu trên Metabase (`http://localhost:3000`)

*(Vì Metabase chạy bên trong mạng Docker `dwh_net`, ô **Host** dùng tên service `postgres` và `clickhouse`, không dùng `localhost`.)*

### Kết nối 1: PostgreSQL 16 (Serving Layer & Materialized Views)
- **Database type:** `PostgreSQL`
- **Display name:** `TLCN DWH - PostgreSQL (Mart)`
- **Host:** `postgres`
- **Port:** `5432`
- **Database name:** `tlcn_dwh`
- **Username:** `dwh_admin`
- **Password:** giá trị `POSTGRES_PASSWORD` trong [.env](../.env)

### Kết nối 2: ClickHouse 24.8 (Columnar OLAP)
- **Database type:** `ClickHouse` (driver tích hợp sẵn trong Metabase `v0.55.12.2`)
- **Display name:** `TLCN DWH - ClickHouse (OLAP)`
- **Host:** `clickhouse`
- **Port:** `8123`
- **Database name:** `olap_xnk`
- **Username:** `olap_user`
- **Password:** giá trị `CLICKHOUSE_PASSWORD` trong [.env](../.env)

---

## 2. Tổ chức thư mục `TLCN_DW_XNK` và thiết lập 3 Dashboard tương ứng 3 bài toán ban đầu

*(Tạo Collection riêng **`TLCN_DW_XNK`** dưới `Our analytics`, di chuyển cả 3 Dashboard và 7 Question từ `Examples` sang đây rồi ghim 3 Dashboard lên đầu để tách biệt hoàn toàn với dữ liệu mẫu `E-commerce Insights`.)*

### Dashboard 1: Thuế quan & FTA
- **Nguồn:** `TLCN DWH - PostgreSQL (Mart)` → bảng `mart.mart_tariff_weighted` (tuân thủ Luật R2: bình quân gia quyền theo `total_tariff_lines`).
- **Bố cục gợi ý:** 2 biểu đồ nằm ngang cạnh nhau (`12 + 12` ô) + 1 thẻ văn bản chú thích phía dưới giải thích phạm vi WITS TRAINS (AHS/PREF công bố đến 2021; năm 2022–2023 phản ánh MFN thị trường xuất khẩu sau gộp dòng HS2022 và MFN Việt Nam ~3.36%–4.30%).

#### Biểu đồ 1.1 — Thuế suất bình quân gia quyền MFN và AHS theo năm
- **Loại biểu đồ:** Bar (Grouped)
- **Nhãn hiển thị (Display):** Trục X = `Năm`; Trục Y = `Thuế suất (%)`; Chú giải = `Thuế MFN (%)`, `Thuế ưu đãi AHS (%)`.
```sql
SELECT
    calendar_year::TEXT AS nam,
    ROUND(SUM(CASE WHEN tariff_type_code = 'MFN' THEN weighted_avg_tariff_pct * total_tariff_lines ELSE 0 END)
        / NULLIF(SUM(CASE WHEN tariff_type_code = 'MFN' THEN total_tariff_lines ELSE 0 END), 0), 2) AS thue_mfn_pct,
    ROUND(SUM(CASE WHEN tariff_type_code = 'PREF' THEN weighted_avg_tariff_pct * total_tariff_lines ELSE 0 END)
        / NULLIF(SUM(CASE WHEN tariff_type_code = 'PREF' THEN total_tariff_lines ELSE 0 END), 0), 2) AS thue_uu_dai_ahs_pct
FROM mart.mart_tariff_weighted
GROUP BY calendar_year
ORDER BY calendar_year;
```

#### Biểu đồ 1.2 — Thuế suất bình quân gia quyền MFN và AHS theo 4 nhóm hàng
- **Loại biểu đồ:** Row (thanh ngang nhóm đôi — bật *Show values on data points* để thấy rõ giá trị `0.07%` của Nhóm 1)
- **Nhãn hiển thị (Display):** Trục Y = `Nhóm hàng`; Trục X = `Thuế suất (%)`; Chú giải = `Thuế MFN (%)`, `Thuế ưu đãi AHS (%)`.
```sql
SELECT
    commodity_group,
    ROUND(SUM(CASE WHEN tariff_type_code = 'MFN' THEN weighted_avg_tariff_pct * total_tariff_lines ELSE 0 END)
        / NULLIF(SUM(CASE WHEN tariff_type_code = 'MFN' THEN total_tariff_lines ELSE 0 END), 0), 2) AS thue_mfn_pct,
    ROUND(SUM(CASE WHEN tariff_type_code = 'PREF' THEN weighted_avg_tariff_pct * total_tariff_lines ELSE 0 END)
        / NULLIF(SUM(CASE WHEN tariff_type_code = 'PREF' THEN total_tariff_lines ELSE 0 END), 0), 2) AS thue_uu_dai_ahs_pct
FROM mart.mart_tariff_weighted
GROUP BY commodity_group
ORDER BY thue_mfn_pct DESC;
```

---

### Dashboard 2: Xu hướng mùa vụ & Cán cân thương mại
- **Nguồn:** `mart.mart_seasonality_monthly` (Luật R5: chỉ tổng hợp độ mịn `MONTH`) và `mart.mart_trade_balance` (Luật R3: loại `World`, phạm vi 14 mã HS6).
- **Bố cục gợi ý:** 2 biểu đồ nằm ngang cạnh nhau (`12 + 12` ô) + 1 thẻ văn bản chú thích phía dưới nêu rõ phạm vi 14 mã HS6 (đã loại `World` theo Luật R3) và quy ước `Other Asia, nes` là Đài Loan (Taiwan) theo UN Comtrade M49.

#### Biểu đồ 2.1 — Chu kỳ mùa vụ 12 tháng (xuất khẩu và nhập khẩu)
- **Loại biểu đồ:** Line (tắt *Show values*, màu tương phản Xanh dương vs Cam, giới hạn trục Y `75–125`, bật *Goal line* ở mức `100`)
- **Nhãn hiển thị (Display):** Trục X = `Tháng`; Trục Y = `Chỉ số mùa vụ (%)`; Chú giải = `Xuất khẩu (%)`, `Nhập khẩu (%)`.
```sql
SELECT
    LPAD(month::TEXT, 2, '0') AS thang,
    MAX(CASE WHEN flow_key = 1 THEN seasonal_index_pct END) AS xuat_khau_pct,
    MAX(CASE WHEN flow_key = 2 THEN seasonal_index_pct END) AS nhap_khau_pct
FROM mart.mart_seasonality_monthly
GROUP BY month
ORDER BY month;
```

#### Biểu đồ 2.2 — Cán cân thương mại 14 mã HS6 theo đối tác (Top 6 xuất siêu và Top 2 nhập siêu)
- **Loại biểu đồ:** Row (thanh ngang màu xanh trung tính, bật *Show values on data points* để thấy rõ giá trị âm `-18.87` và `-7.14`)
- **Nhãn hiển thị (Display):** Trục Y = `Đối tác thương mại`; Trục X = `Cán cân ròng (tỷ USD)`.
```sql
WITH agg AS (
    SELECT
        partner_name,
        ROUND(SUM(trade_balance_usd) / 1e9, 2) AS net_balance_billion_usd
    FROM mart.mart_trade_balance
    GROUP BY partner_name
),
top_pos AS (
    SELECT * FROM agg
    WHERE net_balance_billion_usd > 0
    ORDER BY net_balance_billion_usd DESC
    LIMIT 6
),
top_neg AS (
    SELECT * FROM agg
    WHERE net_balance_billion_usd < 0
    ORDER BY net_balance_billion_usd ASC
    LIMIT 2
)
SELECT * FROM top_pos
UNION ALL
SELECT * FROM top_neg
ORDER BY net_balance_billion_usd DESC;
```

---

### Dashboard 3: Rủi ro thị trường HHI & Dữ liệu gương 2024
- **Nguồn:** `mart.mart_trade_reconciliation` (hoặc `olap_xnk.mart_trade_reconciliation` trên ClickHouse) và `mart.mart_market_concentration`.
- **Bố cục gợi ý:** Biểu đồ `3.1` và `3.2` xếp song song hàng trên (`12 + 12`), biểu đồ `3.3` kéo rộng hết hàng dưới (`24` ô).

#### Biểu đồ 3.1 — Phục hồi dữ liệu gương năm 2024
- **Loại biểu đồ:** Bar (bật **Stack**, trục X = `Ordinal` để hiện đủ 10 năm `2015–2024`) — nhấn mạnh năm `2024` phục hồi **1,393 ô (`90,770.01 triệu USD`)**.
- **Nhãn hiển thị (Display):** Trục X = `Năm`; Trục Y = `Số ô dữ liệu`; Chú giải = `Chỉ VN công bố`, `Có cả 2 nguồn`, `Phục hồi từ đối tác (Mirror)`.
```sql
SELECT
    calendar_year::TEXT AS nam,
    COUNT(*) FILTER (WHERE data_source_flag = 'VN_OFFICIAL_ONLY') AS vn_official_only,
    COUNT(*) FILTER (WHERE data_source_flag = 'BOTH_AVAILABLE')   AS both_available,
    COUNT(*) FILTER (WHERE data_source_flag = 'MIRROR_ESTIMATED') AS mirror_estimated
FROM mart.mart_trade_reconciliation
GROUP BY calendar_year
ORDER BY calendar_year;
```

#### Biểu đồ 3.2 — Độ lệch thống kê trước và sau quy đổi CIF–FOB
- **Loại biểu đồ:** Bar (Grouped, bật *Show values on data points*)
- **Nhãn hiển thị (Display):** Trục X = `Đối tác`; Trục Y = `Độ lệch (%)`; Chú giải = `Trước quy đổi CIF–FOB (%)`, `Sau quy đổi CIF–FOB (%)`.
```sql
SELECT
    partner_name,
    ROUND(100.0 * ABS(SUM(vn_value) - SUM(mirror_value_raw)) / NULLIF(SUM(vn_value), 0), 2) AS lech_truoc_cif_fob_pct,
    ROUND(100.0 * ABS(SUM(vn_value) - SUM(mirror_value_adjusted)) / NULLIF(SUM(vn_value), 0), 2) AS lech_sau_cif_fob_pct
FROM mart.mart_trade_reconciliation
WHERE data_source_flag = 'BOTH_AVAILABLE'
  AND partner_name IN ('USA', 'China', 'Germany', 'Japan', 'Rep. of Korea')
GROUP BY partner_name
ORDER BY lech_truoc_cif_fob_pct DESC;
```

#### Biểu đồ 3.3 — Chỉ số tập trung thị trường HHI và CR-4
- **Loại biểu đồ:** Combo (Left Y-axis: `hhi_xuat_khau`, `hhi_nhap_khau` dạng Bar; Right Y-axis: `cr4_xuat_khau_pct`, `cr4_nhap_khau_pct` dạng Line; xóa custom Y-axis label để tránh trùng lặp trên 2 trục).
- **Nhãn hiển thị (Display):** Trục X = `Năm`; Chú giải = `HHI xuất khẩu`, `HHI nhập khẩu`, `CR-4 xuất khẩu (%)`, `CR-4 nhập khẩu (%)`.
```sql
SELECT
    calendar_year::TEXT AS nam,
    MAX(CASE WHEN flow_key = 1 THEN hhi_index END) AS hhi_xuat_khau,
    MAX(CASE WHEN flow_key = 2 THEN hhi_index END) AS hhi_nhap_khau,
    MAX(CASE WHEN flow_key = 1 THEN cr4_pct END)   AS cr4_xuat_khau_pct,
    MAX(CASE WHEN flow_key = 2 THEN cr4_pct END)   AS cr4_nhap_khau_pct
FROM mart.mart_market_concentration
GROUP BY calendar_year
ORDER BY calendar_year;
```
