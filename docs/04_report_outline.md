# Đề cương báo cáo Tiểu luận chuyên ngành (định hướng kiến trúc Data Warehouse)

> **Tên đề tài:** Xây dựng kiến trúc Data Warehouse mã nguồn mở hỗ trợ phân tích xuất nhập khẩu hàng hóa Việt Nam  
> **Cơ cấu tỷ trọng mới:** **~75% Kiến trúc & Kỹ thuật Data Warehouse** (Thiết kế, ELT, SCD Type 2, Partitioning, Data Quality, Benchmark) | **~25% Bài toán XNK minh chứng**  
> **Thể thức:** Tiểu luận chuyên ngành Hệ thống Thông tin (5 tín chỉ) — Khoa CNTT, HCMUTE.

---

## CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI (~10%)

- **1.1. Đặt vấn đề:** Nhu cầu tích hợp dữ liệu thương mại đa nguồn rời rạc (UN Comtrade, WITS TRAINS, World Bank WDI) có độ mịn khác nhau (Tháng vs Năm), phiên bản phân loại hàng hóa thay đổi (`HS2017 -> HS2022`), và hiện tượng đứt gãy dữ liệu năm 2024 của Việt Nam trên UN Comtrade.
- **1.2. Mục tiêu đề tài:**
  - Thiết kế và triển khai một **kiến trúc Data Warehouse 5 tầng hoàn toàn trên công nghệ mã nguồn mở** đóng gói bằng Docker Compose (`Airflow`, `MinIO`, `PostgreSQL 16`, `dbt Core`, `ClickHouse`, `Metabase`).
  - Trọng tâm kỹ thuật: Mô hình hóa `Fact Constellation Schema` (`Galaxy Schema`), giải quyết đa độ mịn (`YYYY00`), xử lý cầu nối mã HS (*As-Is* vs *As-Mapped*), quản trị **Hybrid SCD Type 2**, ràng buộc toàn vẹn vật lý PK/FK, tự động hóa kiểm định chất lượng (*Summarizability Governance*) và đối chiếu đa góc nhìn chống cộng trùng.
  - Phần phụ trợ: Minh chứng vận hành kho qua 7 truy vấn SQL OLAP tiêu biểu (bao gồm Cross-Fact Drill-Across Q7) và 3 Dashboard trên Metabase tương ứng 3 bài toán ban đầu (Thuế quan & FTA; Xu hướng mùa vụ & Cán cân; Rủi ro thị trường HHI & Dữ liệu gương 2024).
- **1.3. Phạm vi dữ liệu thực nghiệm:** Giai đoạn 2015–2024; 98 thực thể đối tác (97 đối tác + Việt Nam + World); 14 phân nhóm HS6 trọng điểm; 5 chỉ số vĩ mô; thuế suất MFN và Effectively Applied (AHS).

---

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT KIẾN TRÚC DATA WAREHOUSE (~15%)

- **2.1. Kiến trúc Data Warehouse hiện đại & mô hình ELT:** So sánh ETL truyền thống và ELT (Raw Object Storage + In-warehouse Transformation); kiến trúc 5 tầng (Orchestration → Raw/Landing → Core Warehouse → Columnar OLAP → BI).
- **2.2. Mô hình hóa đa chiều Kimball:** Quy trình 4 bước (Business Process → Grain → Dimensions → Facts); Enterprise Bus Matrix; Conformed Dimensions; **Fact Constellation Schema (Galaxy Schema)**; SCD Type 1 và SCD Type 2.
- **2.3. Lý thuyết tính cộng gộp (Summarizability):** Phân loại độ đo **Additive** (cộng gộp toàn phần), **Bán cộng gộp** (áp dụng cho tồn kho/số dư theo thời gian), và **Non-additive** (phi cộng gộp — nhấn mạnh thuế suất `ad_valorem_pct` bắt buộc tính bình quân gia quyền theo `total_lines`); các điều kiện bảo toàn tính toàn vẹn tổng hợp.
- **2.4. Lưu trữ hướng dòng vs hướng cột (Row-store vs Columnar OLAP):** Cơ chế Declarative Range Partitioning, Materialized View với `UNIQUE INDEX` hỗ trợ `REFRESH CONCURRENTLY`, và cấu trúc lưu trữ hướng cột `MergeTree` trên ClickHouse.
- **2.5. Khái niệm nghiệp vụ XNK (tóm tắt ~2 trang):** Mã HS, giá FOB vs CIF và bất đối xứng gương, thuế MFN vs Effectively Applied (AHS), chỉ số HHI và CR-4.

---

## CHƯƠNG 3: THIẾT KẾ KIẾN TRÚC DATA WAREHOUSE (`TLCN_DW_XNK`) (~25% — TRỌNG TÂM 1)

- **3.1. Sơ đồ kiến trúc tổng thể 5 tầng và luồng dữ liệu (Data Flow):** Phân tách trách nhiệm từng tầng từ MinIO (`tlcn-raw`) đến PostgreSQL (`raw` → `staging` → `snapshots` → `intermediate` → `core_dwh` → `mart`) và ClickHouse (`olap_xnk`).
- **3.2. Thiết kế kho trung tâm theo Fact Constellation Schema:**
  - Ma trận Bus giữa 4 quy trình nghiệp vụ và 8 Conformed Dimensions.
  - Khai báo Grain Contract, ràng buộc vật lý PK/FK và sơ đồ ERD chi tiết cho `fact_trade`, `fact_tariff_rate`, `fact_macro_indicator`.
- **3.3. Các cơ chế kiến trúc giải quyết thách thức dữ liệu:**
  - Xử lý đa độ mịn thời gian bằng khóa Year Sentinel `YYYY00` trong `dim_date`.
  - Cầu nối phiên bản mã HS (`ref_hs_bridge`) theo nguyên tắc *As-Is* (`hs6_reported`) vs *As-Mapped* (`dim_commodity.hs6`).
  - Thiết kế **tầng đối chiếu đa góc nhìn (`Multi-Perspective Architecture`)**: tách bạch `perspective_key` (1 vs 2) ở `fact_trade`, đẩy toàn bộ phép ghép `FULL OUTER JOIN` và quy đổi `CIF -> FOB` (`ref_cif_fob_factor`) ra tầng `intermediate`/`mart_trade_reconciliation` để triệt tiêu nguy cơ cộng trùng.
- **3.4. Thiết kế quản trị chất lượng, SCD Type 2 & Data Lineage:**
  - Thiết kế **Hybrid SCD Type 2** với `snap_dim_partner` và `snap_dim_commodity`.
  - Thiết kế 5 quy tắc `dw_usage_rule` (R1–R5) và đặc tả các kiểm định tự động trong dbt.

---

## CHƯƠNG 4: HIỆN THỰC HÓA HỆ THỐNG TRÊN MÃ NGUỒN MỞ (~25% — TRỌNG TÂM 2)

- **4.1. Đóng gói hạ tầng bằng Docker Compose:** Cấu hình dịch vụ, mạng nội bộ `dwh_net`, healthchecks, giới hạn tài nguyên RAM phù hợp máy trạm 16 GB, và khởi tạo schema tự động (`init_databases.sql`, `init_olap.sql`).
- **4.2. Hiện thực tầng thu thập & điều phối (Python + MinIO + Airflow):**
  - Thiết kế 4 module trích xuất Python hỗ trợ hai chế độ (`seed` tái lập offline và `api` trực tiếp với exponential backoff).
  - Tải lên MinIO kèm kiểm tra toàn vẹn `SHA-256` manifest và nạp vào PostgreSQL `raw.*` bằng `COPY FROM STDIN` kèm bảng vết `audit.etl_batch_log`.
  - 3 DAG Airflow (`dag_01_ingest_raw_to_minio`, `dag_02_dwh_elt_pipeline`, `dag_03_benchmark_and_audit`).
- **4.3. Hiện thực tầng biến đổi, SCD Type 2 & kiểm định tự động bằng dbt Core:**
  - Chuẩn hóa dữ liệu tại `staging` (zero-pad HS6, chuẩn hóa boolean, xử lý chuỗi rỗng và số khoa học, sửa ánh xạ đối tác `ANCHOR` của WITS).
  - Hiện thực 8 Dimensions + 3 Facts, cấu hình `dbt snapshot`, 11 singular `dbt test` + kiểm định `relationships` / `not_null` đối xứng 100% cho cả 3 Fact (kiểm thử grain, sentinel, Weighted-Average Bounds Check và đối soát neo), mart liên Fact `mart_trade_macro_yearly` (45 dòng), và sinh tài liệu `dbt docs` (Data Lineage).
- **4.4. Tối ưu vật lý trên PostgreSQL & đồng bộ ClickHouse OLAP:**
  - Gắn PK/FK vật lý (`00_constraints.sql`), Declarative Range Partitioning (`fact_trade_partitioned` theo `calendar_year`), Covering/BRIN Indexes (`01_partitioning_and_indexes.sql`).
  - 4 Materialized Views (`mv_trade_summary`, `mv_trade_balance`, `mv_market_concentration`, `mv_trade_reconciliation`) vận hành `REFRESH MATERIALIZED VIEW CONCURRENTLY` (`02_materialized_views.sql`).
  - Đồng bộ idempotent toàn bộ 8 Dimensions + 3 Facts + `mart_trade_reconciliation` sang ClickHouse (`MergeTree`).

---

## CHƯƠNG 5: KIỂM THỬ KIẾN TRÚC & MINH CHỨNG BÀI TOÁN XNK (~25% — PHẦN KIỂM CHỨNG)

- **5.1. Kiểm thử chất lượng dữ liệu & toàn vẹn kho (V0–V7, R1–R5):**
  - Tổng hợp kết quả `41/41 PASS` offline và `111/111 PASS` `dbt test` (`98,596` dòng `VN_REPORTED` + `13,252` dòng `PARTNER_MIRROR` = `111,848` dòng `fact_trade`; `419` dòng `fact_tariff_rate`; `300` dòng `fact_macro_indicator`; `98` đối tác; `14` mã HS6; `130` mốc ngày; `177` batches; 0 trùng grain; 0 khóa ngoại mồ côi; khớp 14/14 mốc World 2023 và 7/7 ô Mirror).
- **5.2. Đánh giá hiệu năng kiến trúc (3-Tier Benchmark):**
  - Phương pháp đo (Cold/Warm latency, `EXPLAIN (ANALYZE, BUFFERS)`): so sánh giữa **PostgreSQL Core (Fact Constellation Schema)**, **PostgreSQL Partitioned + Materialized Views** và **ClickHouse Columnar OLAP** trên 5 kịch bản (B1–B5).
- **5.3. Minh chứng giải quyết 3 bài toán XNK (Case Study phụ):**
  - *Bài toán 1 (Thuế quan & FTA):* Thuế suất bình quân gia quyền MFN (`9.26%–15.08%`) vs Effectively Applied AHS (`1.30%–2.13%`) qua các năm và 4 nhóm hàng.
  - *Bài toán 2 (Xu hướng mùa vụ & Cán cân 14 mã HS6):* Chỉ số mùa vụ 12 tháng (`01–12`) và cán cân song phương **trong phạm vi rổ 14 mã HS6 khảo sát** (Hoa Kỳ `+115.40` tỷ USD, UAE `+31.06` tỷ USD, Trung Quốc `+30.35` tỷ USD, Ireland `-18.87` tỷ USD).
  - *Bài toán 3 (Rủi ro HHI/CR-4 & Phục hồi dữ liệu gương 2024):* Thống kê HHI & CR-4 trên 97 đối tác thực (`HHI XK 588–1,377`, `CR-4 XK 39.38%–55.56%`; `HHI NK 1,453–2,207`, `CR-4 NK 67.28%–79.68%`) và kết quả phục hồi **1,393 ô năm 2024** (`90,770.01 triệu USD` sau quy đổi CIF/FOB).
- **5.4. Kết luận & hướng phát triển:** Đánh giá ưu/nhược điểm của kiến trúc mã nguồn mở hiện tại và định hướng mở rộng (Incremental dbt models, Iceberg/Delta khi dữ liệu tăng quy mô).
