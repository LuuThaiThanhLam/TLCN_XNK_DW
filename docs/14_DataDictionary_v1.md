# Từ điển Dữ liệu (Data Dictionary) — TLCN Kho dữ liệu XNK Việt Nam

**Phiên bản:** v1 (Tuần 4)  
**Tạo từ:** `sql/ddl/01_star_ddl.sql` + `docs/13_Tuan3_BusMatrix_Grain_Schema.md`  
**Cơ sở dữ liệu:** `TLCN_XNK` (SQL Server 2019+)  
**Schema:** `dbo`

> **Quy ước bảng này:**  
> - **PK** = Primary Key | **FK** = Foreign Key | **UQ** = Unique | **AI** = IDENTITY (Auto-Increment)  
> - **Ràng buộc CHECK** ghi rút gọn trong cột "Ràng buộc"  
> - Cột có dấu ⚠️ = có luật dùng đặc biệt trong `DW_USAGE_RULE`

---

## MỤC LỤC

| Loại | Tên bảng | Mô tả ngắn |
|---|---|---|
| Dimension | [DIM_DATE](#1-dim_date) | Lịch thời gian (tháng + năm sentinel) |
| Dimension | [DIM_PARTNER](#2-dim_partner) | Đối tác thương mại của Việt Nam |
| Dimension | [DIM_COMMODITY](#3-dim_commodity) | Mã hàng hóa HS6 (chuẩn HS2022) |
| Dimension | [DIM_FLOW](#4-dim_flow) | Chiều dòng thương mại (Xuất/Nhập) |
| Dimension | [DIM_PERSPECTIVE](#5-dim_perspective) | Góc nhìn khai báo (VN hoặc Mirror) |
| Dimension | [DIM_TARIFF_TYPE](#6-dim_tariff_type) | Loại thuế quan (MFN / PREF) |
| Dimension | [DIM_INDICATOR](#7-dim_indicator) | Chỉ số vĩ mô (World Bank) |
| Dimension | [DIM_AUDIT](#8-dim_audit) | Kiểm toán lô ETL (batch lineage) |
| Fact | [FACT_TRADE](#9-fact_trade) | Kim ngạch XNK theo tháng |
| Fact | [FACT_TARIFF_RATE](#10-fact_tariff_rate) | Thuế suất theo năm |
| Fact | [FACT_MACRO_INDICATOR](#11-fact_macro_indicator) | Chỉ số vĩ mô theo năm |
| View | [VW_TRADE_RECONCILIATION](#12-vw_trade_reconciliation) | Đối chiếu số liệu gương VN vs Đối tác |
| Rule | [DW_USAGE_RULE](#13-dw_usage_rule) | Luật sử dụng kho dữ liệu |

---

## 1. DIM_DATE

**Mô tả:** Bảng chiều thời gian. Lưu hai loại dòng: (1) dòng **tháng** (granularity = 'MONTH') cho `FACT_TRADE`; (2) dòng **năm sentinel** (granularity = 'YEAR') cho `FACT_TARIFF_RATE` và `FACT_MACRO_INDICATOR`. Hai loại này **không bao giờ được trộn lẫn** trong một phép cộng.

**Nguồn dữ liệu:** Sinh tự động từ tập hợp `period` của các file staging.  
**Số dòng dự kiến:** 120 dòng tháng (2015-01 → 2024-12) + 11 dòng năm sentinel (2015–2025) = **~131 dòng**.

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `date_key` | `INT` | **PK** | Khóa thay thế dạng số. Tháng: `YYYYMM` (vd: `202301`). Năm sentinel: `YYYY00` (vd: `202300`). Luật: `date_key % 100` phải thuộc `0` (năm) hoặc `1–12` (tháng). |
| 2 | `calendar_year` | `SMALLINT` | NOT NULL | Năm dương lịch. Phạm vi: 2015–2025. |
| 3 | `quarter` | `TINYINT` | NULL | Quý trong năm (1–4). **NULL** đối với dòng năm sentinel. |
| 4 | `month` | `TINYINT` | NULL | Tháng trong năm (1–12). **NULL** đối với dòng năm sentinel. |
| 5 | `granularity` | `CHAR(5)` | CHECK IN ('MONTH','YEAR') | Độ mịn thời gian. 'MONTH' cho thương mại hàng tháng; 'YEAR' cho tariff và macro. |
| 6 | `date_label` | `VARCHAR(7)` | NOT NULL | Nhãn hiển thị trên dashboard. Dạng: `'2023-01'` (tháng) hoặc `'2023'` (năm). |

---

## 2. DIM_PARTNER

**Mô tả:** Bảng chiều đối tác thương mại của Việt Nam. Gồm các quốc gia/vùng lãnh thổ trong phạm vi đề tài (top 15–20 đối tác) và 2 dòng đặc biệt: Việt Nam (`code='704'`) và Thế giới-tổng hợp (`code='0'`).

**Nguồn dữ liệu:** `partner_code` + `partner_name` từ `stg_comtrade_vn_reported.csv`; `iso3` map tay cho 7 mã cần join vĩ mô.  
**Số dòng dự kiến:** ~22 dòng (20 đối tác + Vietnam + World).

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `partner_key` | `INT` | **PK, AI** | Khóa thay thế tự tăng. |
| 2 | `code_comtrade` | `CHAR(3)` | **UQ**, NOT NULL | Mã quốc gia UN Comtrade (3 chữ số). VD: `'156'` (Trung Quốc), `'842'` (Mỹ), `'0'` (World). |
| 3 | `partner_name` | `NVARCHAR(120)` | NOT NULL | Tên quốc gia/vùng lãnh thổ. Nguồn: `partnerDesc` từ API VN_REPORTED. **Cấm** lấy từ dòng mirror (cột đó luôn mang giá trị "Vietnam"). |
| 4 | `iso3` | `CHAR(3)` | NULL | Mã ISO 3166-1 alpha-3 (vd: `'CHN'`, `'USA'`). Dùng để join sang `FACT_MACRO_INDICATOR` (World Bank trả về iso3). NULL nếu chưa map. |
| 5 | `is_aggregate` | `BIT` | NOT NULL, DEFAULT 0 | = 1 chỉ với World (`code='0'`). Dòng này **không được dùng trong xếp hạng đối tác** (Rule R3). |
| 6 | `is_vietnam` | `BIT` | NOT NULL, DEFAULT 0 | = 1 chỉ với Việt Nam (`code='704'`). |
| 7 | `usage_note` | `NVARCHAR(160)` | NULL | Ghi chú quản trị. VD: "World chỉ dùng kiểm tra chéo, không vào xếp hạng". |

---

## 3. DIM_COMMODITY

**Mô tả:** Bảng chiều mã hàng hóa. Lưu 20–30 mã HS6 trọng điểm của đề tài đã được **chuẩn hóa về phiên bản HS2022**. Áp dụng kỹ thuật "As-Mapped" (cột `hs6`) để đảm bảo phân tích xu hướng 10 năm liền mạch, dù API các năm cũ trả về mã HS2012/2017 khác nhau.

**Nguồn dữ liệu:** `stg_comtrade_vn_reported.csv` + `stg_comtrade_vn_reported_bridge.csv`.  
**Số dòng dự kiến:** 20–30 dòng.

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `commodity_key` | `INT` | **PK, AI** | Khóa thay thế tự tăng. |
| 2 | `hs6` | `CHAR(6)` | **UQ**, NOT NULL | Mã HS6 đã chuẩn hóa về **HS2022** ("As-Mapped"). Đây là khóa tra cứu chính. VD: `'851713'` (điện thoại thông minh). |
| 3 | `hs4` | `CHAR(4)` | NOT NULL | 4 chữ số đầu của HS6. Dùng cho roll-up lên cấp chương 4. VD: `'8517'`. |
| 4 | `hs2` | `CHAR(2)` | NOT NULL | 2 chữ số đầu của HS6. Dùng cho roll-up lên cấp chương 2. VD: `'85'`. |
| 5 | `name_en` | `NVARCHAR(200)` | NULL | Tên hàng hóa tiếng Anh (từ `commodity_desc` trong API). Lấy của kỳ gần nhất có dòng. |
| 6 | `commodity_group` | `NVARCHAR(60)` | NULL | Nhóm hàng do nhóm tự phân loại (VD: 'Điện tử', 'Nông sản', 'Dệt may'). Seed 14 mã — dùng cho drill-down trong dashboard. |
| 7 | `bridge_flag` | `BIT` | NOT NULL, DEFAULT 0 | = 1 nếu mã này là kết quả ánh xạ từ mã HS cũ (đã trải qua HS revision). VD: `851713` nhận bridge từ `851712`. |
| 8 | `bridge_note` | `NVARCHAR(200)` | NULL | Giải thích chi tiết việc ánh xạ. VD: `'2015–2021 theo mã cũ 851712, gồm cả điện thoại thường — xấp xỉ có chủ đích'`. |

---

## 4. DIM_FLOW

**Mô tả:** Bảng chiều hướng dòng thương mại. Chỉ có 2 dòng: Xuất khẩu và Nhập khẩu. **Lưu ý quan trọng:** `flow_key` luôn đọc theo reporter của dòng đó — với dòng mirror, ý nghĩa phía VN phải suy qua `DIM_PERSPECTIVE`.

**Số dòng:** **2 dòng** cố định (seed tĩnh).

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `flow_key` | `TINYINT` | **PK** | 1 = Xuất khẩu, 2 = Nhập khẩu. |
| 2 | `flow_code` | `CHAR(1)` | **UQ**, NOT NULL | Mã ký tự: `'X'` (Xuất) hoặc `'M'` (Nhập). |
| 3 | `name_vi` | `NVARCHAR(20)` | NOT NULL | Tên tiếng Việt: `'Xuất khẩu'` hoặc `'Nhập khẩu'`. |
| 4 | `vn_side_meaning` | `NVARCHAR(140)` | NULL | Ý nghĩa chiều này khi `perspective_key=1` (VN khai). VD: "VN xuất hàng sang đối tác". |
| 5 | `mirror_side_meaning` | `NVARCHAR(140)` | NULL | Ý nghĩa chiều này khi `perspective_key=2` (Mirror). VD: "Đối tác nhập từ VN → tương đương VN xuất". |

---

## 5. DIM_PERSPECTIVE

**Mô tả:** Bảng chiều góc nhìn khai báo. Phân biệt **ai là người báo cáo số liệu** — VN tự khai hay đối tác khai về VN (dữ liệu gương/mirror). **Tuyệt đối không cộng gộp dữ liệu của 2 perspective** mà chưa lọc (Rule R4).

**Số dòng:** **2 dòng** cố định (seed tĩnh).

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `perspective_key` | `TINYINT` | **PK** | 1 = VN tự báo cáo; 2 = Đối tác báo cáo về VN (mirror). |
| 2 | `code` | `VARCHAR(20)` | **UQ**, NOT NULL | Mã chuỗi: `'VN_REPORTED'` hoặc `'PARTNER_MIRROR'`. |
| 3 | `label_vi` | `NVARCHAR(40)` | NOT NULL | Nhãn hiển thị: `'Việt Nam khai'` hoặc `'Đối tác khai về VN'`. |
| 4 | `reliability_note` | `NVARCHAR(300)` | NULL | Ghi chú về độ tin cậy. VD: VN_REPORTED độ trễ ~1 năm; PARTNER_MIRROR thường đi trước ~3 năm nhưng cách đo khác (FOB/CIF). |

---

## 6. DIM_TARIFF_TYPE

**Mô tả:** Bảng chiều loại thuế quan. Phân biệt thuế MFN (Most Favoured Nation — áp chung cho mọi đối tác WTO) và PREF (Preferential — ưu đãi song phương theo FTA).

**Số dòng:** **2 dòng** cố định (seed tĩnh).

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `tariff_type_key` | `TINYINT` | **PK** | 1 = MFN; 2 = PREF. |
| 2 | `code` | `VARCHAR(10)` | **UQ**, NOT NULL | Mã chuỗi: `'MFN'` hoặc `'PREF'`. |
| 3 | `label_vi` | `NVARCHAR(60)` | NOT NULL | Tên tiếng Việt: `'Thuế MFN (không phân biệt nguồn gốc)'` hoặc `'Thuế ưu đãi (PREF - theo FTA)'`. |
| 4 | `coverage_note` | `NVARCHAR(300)` | NULL | Ghi chú phạm vi dữ liệu. VD: "PREF song phương VN–đối tác dừng ở 2021 trên endpoint miễn phí WITS; chiều MKT_EXPORT không có PREF". |

---

## 7. DIM_INDICATOR

**Mô tả:** Bảng chiều chỉ số kinh tế vĩ mô từ World Bank (WDI — World Development Indicators). Seed cố định 5 chỉ số đã được kiểm chứng có dữ liệu thực từ API.

**Số dòng:** **5 dòng** cố định (seed tĩnh).

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `indicator_key` | `TINYINT` | **PK** | Khóa số nhỏ cố định (1–5). |
| 2 | `code_wb` | `VARCHAR(20)` | **UQ**, NOT NULL | Mã chỉ số World Bank. VD: `'NY.GDP.MKTP.CD'`. **Lưu ý:** `BN.TOTL.GD.ZS` là mã chết (WB error 120) đã bị thay thế. |
| 3 | `name_en` | `NVARCHAR(120)` | NOT NULL | Tên tiếng Anh đầy đủ của chỉ số. |
| 4 | `unit` | `VARCHAR(10)` | NOT NULL | Đơn vị đo lường: `'USD'`, `'%'`, `'LCU/USD'`. |
| 5 | `note` | `NVARCHAR(200)` | NULL | Ghi chú bổ sung. VD: giải thích `LCU/USD` là tỷ giá trung bình kỳ kế toán. |

**Seed dữ liệu 5 chỉ số:**

| indicator_key | code_wb | name_en | unit |
|:---:|---|---|---|
| 1 | `NY.GDP.MKTP.CD` | GDP (current US$) | USD |
| 2 | `NY.GDP.PCAP.CD` | GDP per capita (current US$) | USD |
| 3 | `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) | % |
| 4 | `PA.NUS.FCRF` | Official exchange rate (LCU per US$, period average) | LCU/USD |
| 5 | `NE.TRD.GNFS.ZS` | Trade (% of GDP) | % |

---

## 8. DIM_AUDIT

**Mô tả:** Bảng chiều kiểm toán lô ETL (Audit Dimension theo tinh thần Kimball). Mỗi dòng đại diện cho **một lô trích xuất (batch)** dữ liệu. `audit_key` là **Foreign Key thuần túy** trong các bảng Fact — tuyệt đối **không phải thành phần của Grain/Unique Index**.

**Nguồn dữ liệu:** Script ETL tự INSERT vào bảng này trước khi nạp Fact.

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `audit_key` | `INT` | **PK, AI** | Khóa thay thế tự tăng. |
| 2 | `batch_id` | `VARCHAR(32)` | **UQ**, NOT NULL | Mã định danh lô duy nhất. VD: `'w2_X_2015'`, `'mir_156_2023'`. Đặt theo quy tắc nhất quán trong script ETL. |
| 3 | `source_system` | `VARCHAR(80)` | NOT NULL | Hệ thống nguồn. VD: `'UN_COMTRADE_API_v1'`, `'WITS_TRAINS'`, `'WORLD_BANK_WDI'`. |
| 4 | `staging_file` | `VARCHAR(120)` | NULL | Tên file CSV staging tương ứng. VD: `'stg_comtrade_vn_reported.csv'`. |
| 5 | `raw_dir` | `VARCHAR(120)` | NULL | Đường dẫn thư mục chứa response thô. VD: `'data/raw/week2_extract/'`. |
| 6 | `extracted_at` | `DATETIME2(0)` | NULL | Thời điểm trích xuất (giờ UTC). Lấy `MAX(extracted_at)` của batch. |
| 7 | `row_count` | `INT` | NULL | Số dòng đã trích xuất trong batch. Dùng để kiểm tra chéo sau ETL. |

---

## 9. FACT_TRADE

**Mô tả:** Bảng sự kiện chính. Lưu **kim ngạch thương mại XNK theo tháng** giữa Việt Nam và từng đối tác, theo từng mã HS6. Chứa **cả hai góc nhìn** (VN khai và Mirror) trong cùng một bảng — phân biệt qua `perspective_key`. Đây là Fact "nặng" nhất và quan trọng nhất trong schema.

**Grain (hợp đồng không thay đổi):**  
> *"Một dòng = một cam kết khai báo của một nước cho UN Comtrade về trị giá thương mại tháng (YYYYMM) giữa Việt Nam và đúng một đối tác, cho đúng một mã HS6, theo đúng một chiều (X/M), dưới đúng một góc nhìn khai báo (VN_REPORTED hoặc PARTNER_MIRROR)."*

**Unique Index (đại diện Grain):** `UQ_FT_GRAIN (date_key, partner_key, commodity_key, flow_key, perspective_key)`  
**Nguồn dữ liệu:** `stg_comtrade_vn_reported.csv` + `stg_comtrade_partner_mirror.csv`  
**Phương thức nạp:** Bắt buộc dùng lệnh `MERGE` (UPSERT) — không dùng `INSERT` trực tiếp.

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `trade_key` | `INT` | **PK, AI** | Khóa thay thế kỹ thuật. Không có ý nghĩa nghiệp vụ. |
| 2 | `date_key` | `INT` | **FK → DIM_DATE**, NOT NULL | Tháng giao dịch dạng `YYYYMM`. Chỉ dùng dòng MONTH của DIM_DATE. |
| 3 | `partner_key` | `INT` | **FK → DIM_PARTNER**, NOT NULL | Đối tác thương mại **của Việt Nam**. Với dòng VN_REPORTED: lấy `partner_code`; với dòng PARTNER_MIRROR: lấy `reporter_code` (vì reporter là đối tác đang khai về VN). |
| 4 | `commodity_key` | `INT` | **FK → DIM_COMMODITY**, NOT NULL | Mã hàng hóa đã chuẩn hóa về HS2022 (As-Mapped). |
| 5 | `flow_key` | `TINYINT` | **FK → DIM_FLOW**, NOT NULL | Chiều dòng thương mại: 1=Xuất, 2=Nhập. Luôn đọc theo reporter của dòng. |
| 6 | `perspective_key` | `TINYINT` | **FK → DIM_PERSPECTIVE**, NOT NULL | Góc nhìn: 1=VN khai, 2=Đối tác khai về VN. ⚠️ **Luật R4**: Cấm cộng gộp khi chưa lọc perspective. |
| 7 | `audit_key` | `INT` | **FK → DIM_AUDIT**, NOT NULL | Truy vết batch ETL. **Không phải thành phần Grain** — chỉ là FK thuần túy. |
| 8 | `primary_value_usd` | `DECIMAL(18,3)` | NOT NULL | Giá trị thương mại chính (USD). Additive — có thể SUM khi cùng perspective và cùng chiều. |
| 9 | `net_wgt_kg` | `DECIMAL(18,3)` | NULL | Trọng lượng tịnh (kg). Additive — dùng để cộng gộp chéo HS thay cho `qty`. NULL nếu API không trả. |
| 10 | `qty` | `DECIMAL(18,3)` | NULL | ⚠️ **Số lượng theo đơn vị riêng của mã HS** (cái/chiếc/lít/m²...). **Luật R1: CẤM SUM chéo HS.** Chỉ dùng khi đã lọc duy nhất 1 mã HS6. |
| 11 | `fob_value_usd` | `DECIMAL(18,3)` | NULL | Giá trị FOB (Free On Board) nếu API trả về. NULL nếu không có. |
| 12 | `cif_value_usd` | `DECIMAL(18,3)` | NULL | Giá trị CIF (Cost + Insurance + Freight) nếu API trả về. NULL nếu không có. |
| 13 | `hs6_reported` | `CHAR(6)` | NOT NULL | Mã HS nguyên bản từ API ("As-Is") — **không** quy đổi về HS2022. Phục vụ lineage và đối chiếu với dữ liệu gốc. |
| 14 | `reporter_code` | `CHAR(3)` | NOT NULL | Mã nước người báo cáo (Comtrade). VD: `'704'` (VN) hoặc mã đối tác. |
| 15 | `partner_code_src` | `CHAR(3)` | NOT NULL | Mã đối tác nguyên bản từ API. Dùng để lọc bỏ World (`'0'`) trong View đối chiếu. |
| 16 | `is_aggregate_partner` | `BIT` | NOT NULL | = 1 nếu đối tác là "World" (`code='0'`). ⚠️ **Luật R3**: Dòng World **không vào xếp hạng đối tác** và **không cộng theo partner**. |
| 17 | `year` | `SMALLINT` | NOT NULL | Năm của giao dịch. Denormalize để tăng hiệu năng truy vấn theo năm. |
| 18 | `month` | `TINYINT` | NOT NULL | Tháng của giao dịch. Denormalize để tăng hiệu năng. |
| 19 | `mirror_role` | `VARCHAR(20)` | NULL | Vai trò của dòng mirror. Giá trị: `'RECON_VN_EXPORT'`, `'RECON_VN_IMPORT'`, `'INFO_EXTRA'`. NULL với dòng VN_REPORTED. |
| 20 | `is_reported` | `BIT` | NULL | Cờ đánh dấu liệu đối tác có thực sự báo cáo số hay đây là số ước tính của UN. NULL với dòng VN; chờ kết quả `check_is_reported.py` (Q6). |

**Index hỗ trợ truy vấn:**

| Tên Index | Cột | Mục đích |
|---|---|---|
| `UQ_FT_GRAIN` | `(date_key, partner_key, commodity_key, flow_key, perspective_key)` | Đảm bảo Grain; kiểm tra duplicate |
| `IX_FT_COMMODITY_DATE` | `(commodity_key, date_key) INCLUDE(primary_value_usd, perspective_key)` | Tăng tốc truy vấn xu hướng theo mã hàng |
| `IX_FT_PARTNER_DATE` | `(partner_key, date_key) INCLUDE(primary_value_usd, perspective_key)` | Tăng tốc truy vấn xếp hạng đối tác |

---

## 10. FACT_TARIFF_RATE

**Mô tả:** Bảng sự kiện thuế quan. Lưu **mức thuế suất theo năm** cho từng cặp (đối tác × mã HS6 × loại thuế). Độ mịn thời gian bắt buộc ở mức **năm** (Year Sentinel = `YYYY00`) vì API WITS công khai chỉ cung cấp thuế tổng hợp theo năm.

**Grain:**  
> *"Một dòng = mức thuế áp dụng (ad valorem %) của một nước reporter đối với hàng từ một nước partner, cho một mã HS6, một loại thuế (MFN/PREF), trong một năm, theo một tổ hợp combo_code."*

**Unique Index:** `UQ_TR_GRAIN (date_key, partner_key, commodity_key, tariff_type_key, combo_code)`  
**Nguồn dữ liệu:** `stg_wits_tariff.csv` (~419 dòng)

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `tariff_key` | `INT` | **PK, AI** | Khóa thay thế kỹ thuật. |
| 2 | `date_key` | `INT` | **FK → DIM_DATE**, NOT NULL, CHECK(`date_key % 100 = 0`) | Năm dạng **Year Sentinel** (`YYYY00`). Ràng buộc `CK_TR_YEAR_SENTINEL` ngăn nạp sai dạng tháng. |
| 3 | `partner_key` | `INT` | **FK → DIM_PARTNER**, NOT NULL | Đối tác thương mại. Với `VN_IMPORT_*`: đối tác xuất hàng vào VN; với `MKT_EXPORT_*`: reporter (nước áp thuế lên hàng VN xuất). |
| 4 | `commodity_key` | `INT` | **FK → DIM_COMMODITY**, NOT NULL | Mã hàng hóa HS6 chuẩn HS2022. |
| 5 | `tariff_type_key` | `TINYINT` | **FK → DIM_TARIFF_TYPE**, NOT NULL | Loại thuế: 1=MFN, 2=PREF. |
| 6 | `audit_key` | `INT` | **FK → DIM_AUDIT**, NOT NULL | Truy vết batch ETL. Không phải Grain. |
| 7 | `combo_code` | `VARCHAR(20)` | NOT NULL | Tổ hợp xác định chiều phân tích. Giá trị: `'VN_IMPORT_MFN'`, `'VN_IMPORT_PREF'`, `'MKT_EXPORT_MFN'`. Đọc hướng dẫn trong `results/week2/wits_tariff_extract.md §4`. |
| 8 | `ad_valorem_pct` | `DECIMAL(9,4)` | NULL | ⚠️ Thuế suất ad valorem (%). **Luật R2: CẤM SUM hoặc AVG trần.** Tổng hợp đúng = trung bình có quyền theo `total_lines`: `SUM(ad_valorem_pct * total_lines) / SUM(total_lines)`. |
| 9 | `measure_label` | `VARCHAR(60)` | NULL | Nhãn phương pháp tính của WITS. VD: `'SimpleAverage'`, `'WeightedAverage'`. |
| 10 | `min_rate` | `DECIMAL(9,4)` | NULL | Thuế suất thấp nhất trong nhóm dòng HS. Nguyên liệu phân tích phân phối thuế. |
| 11 | `max_rate` | `DECIMAL(9,4)` | NULL | Thuế suất cao nhất trong nhóm dòng HS. |
| 12 | `total_lines` | `INT` | NULL | Tổng số dòng tariff trong HS6 (dùng làm trọng số khi tính `ad_valorem_pct` tổng hợp). |
| 13 | `mfn_lines` | `INT` | NULL | Số dòng MFN trong tổng `total_lines`. |
| 14 | `pref_lines` | `INT` | NULL | Số dòng PREF trong tổng `total_lines`. |
| 15 | `datatype` | `VARCHAR(10)` | NULL | Kiểu dữ liệu WITS. VD: `'Reported'`, `'Estimated'`. |

---

## 11. FACT_MACRO_INDICATOR

**Mô tả:** Bảng sự kiện chỉ số vĩ mô. Lưu giá trị các chỉ số kinh tế (GDP, lạm phát, tỷ giá...) của từng quốc gia theo **năm**. Phục vụ phân tích tương quan giữa thương mại XNK và điều kiện kinh tế vĩ mô.

**Grain:**  
> *"Một dòng = giá trị một chỉ số vĩ mô của một quốc gia trong một năm."*

**Unique Index:** `UQ_MC_GRAIN (date_key, partner_key, indicator_key)` (ràng buộc trực tiếp)  
**Nguồn dữ liệu:** `stg_wb_macro.csv` (~300 dòng)

| # | Cột | Kiểu | Ràng buộc | Mô tả nghiệp vụ |
|:---:|---|---|---|---|
| 1 | `macro_key` | `INT` | **PK, AI** | Khóa thay thế kỹ thuật. |
| 2 | `date_key` | `INT` | **FK → DIM_DATE**, NOT NULL, CHECK(`date_key % 100 = 0`) | Năm dạng **Year Sentinel** (`YYYY00`). |
| 3 | `partner_key` | `INT` | **FK → DIM_PARTNER**, NOT NULL | Quốc gia của chỉ số. Join qua `DIM_PARTNER.iso3` vì World Bank trả về iso3. |
| 4 | `indicator_key` | `TINYINT` | **FK → DIM_INDICATOR**, NOT NULL | Chỉ số vĩ mô. Tham chiếu seed 5 dòng trong DIM_INDICATOR. |
| 5 | `audit_key` | `INT` | **FK → DIM_AUDIT**, NOT NULL | Truy vết batch ETL. Không phải Grain. |
| 6 | `value` | `DECIMAL(18,2)` | NULL | Giá trị chỉ số. **NULL có nghĩa World Bank không có số cho năm/nước đó** — phân biệt rõ với `0` (giá trị = không). Non-additive — không SUM theo chỉ số. |

---

## 12. VW_TRADE_RECONCILIATION

**Mô tả:** View đối chiếu dữ liệu gương. **Không phải bảng vật lý** — là view tính toán real-time từ `FACT_TRADE`. Trả về kết quả so sánh số liệu VN khai (VN_REPORTED) với số liệu đối tác khai về VN (PARTNER_MIRROR) cho cùng ô thương mại.

> **Lưu ý kiến trúc:** Dùng `FULL OUTER JOIN` để xử lý cả 3 trường hợp: (1) VN có số, đối tác có số; (2) chỉ VN có số; (3) chỉ đối tác có số. Không loại bỏ World (`partner_code_src <> '0'`).

| # | Cột đầu ra | Mô tả |
|:---:|---|---|
| 1 | `date_key` | Tháng (YYYYMM) |
| 2 | `partner_key` | Đối tác |
| 3 | `commodity_key` | Mã hàng HS6 |
| 4 | `flow_key` | Chiều nhìn từ **phía Việt Nam** |
| 5 | `vn_value` | Giá trị VN khai (USD). NULL nếu VN chưa công bố kỳ này. |
| 6 | `mirror_value` | Giá trị đối tác khai về VN (USD). NULL nếu đối tác không báo cáo. |
| 7 | `mirror_is_reported` | Cờ đối tác có thực báo cáo hay không (chờ Q6). |
| 8 | `mirror_role` | Vai trò dòng mirror: `RECON_VN_EXPORT`, `RECON_VN_IMPORT`, `INFO_EXTRA`. |
| 9 | `abs_diff_usd` | Chênh lệch tuyệt đối (USD): `|mirror_value - vn_value|`. |
| 10 | `pct_diff_vs_vn` | Chênh lệch tương đối (%): `100 * (mirror - vn) / vn`. NULL nếu `vn_value = 0`. |
| 11 | `discrepancy_level` | Mức độ chênh lệch: `'LOW'` (≤10%), `'MODERATE'` (≤30%), `'HIGH'` (>30%), `'MISSING_VN_REPORTED'`, `'MISSING_MIRROR'`. |
| 12 | `reconciliation_note` | Ghi chú giải thích nguyên nhân chênh lệch (tiếng Việt). |

---

## 13. DW_USAGE_RULE

**Mô tả:** Bảng nội quy sử dụng kho dữ liệu. Lưu các luật quản trị nghiệp vụ dưới dạng văn bản, được kiểm soát thi hành tại **tầng Semantic (Power BI/SSAS)** — không phải tầng SQL.

| # | rule_id | applies_to | Tóm tắt luật | Phương thức thi hành |
|:---:|:---:|---|---|---|
| 1 | `R1` | `FACT_TRADE.qty` | **Cấm SUM** `qty` chéo HS — đơn vị đo khác nhau giữa các mã. | Power BI: `Sum By = Disabled`; DAX chỉ dùng `CALCULATE(SUM(qty))` sau khi lọc 1 HS6 duy nhất. |
| 2 | `R2` | `FACT_TARIFF_RATE.ad_valorem_pct` | Thuế suất **không cộng được**; tổng hợp đúng = trung bình có quyền theo `total_lines`. | View/mart tuần 10 xuất `SUM(pct*lines)/SUM(lines)`; mọi query dùng AVG trần bị xem là sai. |
| 3 | `R3` | `FACT_TRADE.is_aggregate_partner` | Dòng `World` (partner=0) **không vào xếp hạng** đối tác hoặc KPI cộng theo partner. | Mọi view dashboard xếp hạng phải có `WHERE is_aggregate_partner = 0`. |
| 4 | `R4` | `FACT_TRADE.perspective_key` | **Không bao giờ SUM** khi chưa lọc `perspective_key`; cấm cộng VN + Mirror. | Semantic layer: slicer perspective mặc định = `VN_REPORTED`; view reconciliation tách 2 CTE riêng. |
| 5 | `R5` | `DIM_DATE.granularity` | Fact **tháng** (`FACT_TRADE`) **không trộn** với Fact **năm** (`FACT_TARIFF_RATE`, `FACT_MACRO_INDICATOR`) trong một phép cộng. | `CK_TR_YEAR_SENTINEL` chặn SQL level; mart tuần 10 chỉ SELECT 1 granularity mỗi truy vấn. |

---

## PHỤ LỤC: Tóm tắt các Measures và Quy tắc tổng hợp

| Measure | Bảng | Loại | Quy tắc tổng hợp |
|---|---|:---:|---|
| `primary_value_usd` | FACT_TRADE | **Additive** | SUM theo mọi chiều, sau khi đã lọc `perspective_key` (Rule R4) |
| `net_wgt_kg` | FACT_TRADE | **Additive** | SUM hợp lệ khi cùng định nghĩa trọng lượng |
| `qty` | FACT_TRADE | **Non-additive** ⚠️ | Chỉ SUM trong scope 1 mã HS6 (Rule R1) |
| `fob_value_usd` | FACT_TRADE | **Additive** | SUM tương tự `primary_value_usd` |
| `ad_valorem_pct` | FACT_TARIFF_RATE | **Non-additive** ⚠️ | Trung bình có quyền `SUM(pct*total_lines)/SUM(total_lines)` (Rule R2) |
| `total_lines` | FACT_TARIFF_RATE | **Additive** | SUM — dùng làm mẫu số khi tính trọng số |
| `value` | FACT_MACRO_INDICATOR | **Non-additive** | Không SUM theo chỉ số khác nhau; dùng LAST/AVG tùy câu hỏi |
| `vn_value` | VW_TRADE_RECONCILIATION | **Derived** | Không SUM trực tiếp — dùng để so sánh với `mirror_value` |
| `abs_diff_usd` | VW_TRADE_RECONCILIATION | **Derived** | AVG để báo cáo mức chênh lệch trung bình |
| `pct_diff_vs_vn` | VW_TRADE_RECONCILIATION | **Derived/Non-additive** | AVG có điều kiện; loại bỏ NULL trước khi tính |
