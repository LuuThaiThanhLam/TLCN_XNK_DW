# TLCN_DW_XNK — Kiến trúc Data Warehouse mã nguồn mở (XNK Việt Nam)

Đề tài **Tiểu luận chuyên ngành Hệ thống Thông tin (HCMUTE)**: thiết kế và hiện thực hóa một **kiến trúc Data Warehouse hiện đại 100% mã nguồn mở** theo phương pháp luận Kimball (ELT + `Fact Constellation Schema` + *Automated Data Quality* + *Columnar OLAP*), sử dụng dữ liệu xuất nhập khẩu hàng hóa Việt Nam (UN Comtrade, WITS TRAINS, World Bank WDI) làm bài toán kiểm chứng đầu-cuối.

> **Trọng tâm của dự án:** Kiến trúc Data Warehouse 5 tầng đóng gói bằng Docker Compose (Airflow, MinIO, PostgreSQL 16, dbt Core, ClickHouse, Metabase), kiểm soát chất lượng tự động, quản trị lịch sử Hybrid SCD Type 2, ràng buộc PK/FK vật lý, phân vùng bảng, và đánh giá hiệu năng giữa Row-store vs Materialized View vs Columnar OLAP.

---

## 1. Kiến trúc 5 tầng mã nguồn mở

```text
[Open APIs: UN Comtrade, WITS TRAINS, World Bank WDI]  (hoặc data/seed_staging/)
        │  Python Extractors (seed | api mode, exponential backoff)
        ▼
[1. Orchestration]    Apache Airflow 2.10 (LocalExecutor)
        │             DAG 01: Extract -> MinIO | DAG 02: ELT + dbt + Sync | DAG 03: Benchmark
        ▼
[2. Raw / Landing]    MinIO (S3-compatible, bucket tlcn-raw, manifest SHA-256)
        │             PostgreSQL schema raw.* (COPY FROM STDIN + audit.etl_batch_log)
        ▼
[3. Core Warehouse]   PostgreSQL 16 + dbt Core 1.8
                      ├─ staging        : làm sạch, zero-pad HS6, cầu nối HS2017->HS2022, chuẩn hóa WITS
                      ├─ snapshots      : SCD Type 2 thực thụ (snap_dim_partner, snap_dim_commodity)
                      ├─ intermediate   : hợp nhất góc nhìn & đối chiếu song phương CIF/FOB
                      ├─ core_dwh       : Fact Constellation / Galaxy Schema (3 Fact + 8 Conformed Dim)
                      │                   + PK/FK vật lý + Declarative Range Partitioning + Indexes
                      └─ mart           : Summary Tables + Materialized Views (REFRESH CONCURRENTLY)
                      + dbt test (tự động hóa V0–V7 & 5 luật Summarizability) + dbt docs (Data Lineage)
        │
        ▼
[4. Columnar OLAP]    ClickHouse 24.8 (MergeTree, PARTITION BY calendar_year, đồng bộ đủ 8 Dim + 3 Fact)
                      → Benchmark 3 tầng: PG Core vs PG Partitioned/MV vs ClickHouse Columnar
        │
        ▼
[5. BI & Serving]     Metabase Open-Source (3 Dashboard tương ứng 3 bài toán ban đầu)
```

---

## 2. Cấu trúc thư mục

```text
TLCN_DW_XNK/
├── docker-compose.yml              # Toàn bộ stack: postgres, minio, clickhouse, airflow, metabase
├── .env.example                    # Mẫu biến môi trường (copy thành .env trước khi chạy)
├── run.ps1                         # Công cụ dòng lệnh nhanh cho Windows PowerShell
├── Makefile                        # Lệnh thao tác nhanh cho Linux/macOS
├── docker/
│   ├── airflow/                    # Dockerfile + requirements cho Airflow + dbt-postgres
│   ├── postgres/init_databases.sql # Khởi tạo DB airflow, metabase, tlcn_dwh (7 schemas + raw.* + audit.*)
│   └── clickhouse/init_olap.sql    # Khởi tạo olap_xnk.* (MergeTree: 8 Dim + 3 Fact + mart)
├── data/seed_staging/              # Dữ liệu staging đã trích xuất để tái lập offline 100%
├── ingestion/
│   ├── common.py                   # Cấu hình dùng chung, S3/PG/CH clients, SHA-256
│   ├── extract/                    # 4 script Python trích xuất (hỗ trợ --mode seed và --mode api)
│   ├── load_to_minio.py            # Đẩy dữ liệu + manifest SHA-256 lên MinIO
│   ├── load_minio_to_pg_raw.py     # Kiểm tra checksum và nạp raw.* bằng COPY FROM STDIN
│   └── sync_pg_to_clickhouse.py    # Đồng bộ đủ 8 Dim + 3 Fact + mart sang ClickHouse
├── airflow/dags/
│   ├── dag_01_ingest_raw_to_minio.py
│   ├── dag_02_dwh_elt_pipeline.py
│   └── dag_03_benchmark_and_audit.py
├── dbt_project/
│   ├── dbt_project.yml / profiles.yml
│   ├── macros/generate_schema_name.sql
│   ├── seeds/                      # ref_country_codes, ref_cif_fob_factor, ref_hs_bridge, dw_usage_rule
│   ├── snapshots/                  # snap_dim_partner, snap_dim_commodity (SCD Type 2)
│   ├── models/                     # staging/ -> intermediate/ -> core_dwh/ -> marts/
│   └── tests/                      # 11 singular tests (V0-V7 & Luật R1-R5 + Grain)
├── sql/
│   ├── postgres/                   # 00_constraints.sql, 01_partitioning_and_indexes.sql, 02_materialized_views.sql, 03_olap_queries.sql
│   └── clickhouse/                 # 01_olap_queries.sql
├── scripts/
│   ├── setup_windows_host.ps1      # Cài đặt Docker Desktop + DBeaver trên Windows
│   ├── verify_offline.py           # Kiểm chứng tĩnh + mô phỏng end-to-end toàn bộ Data Warehouse
│   └── benchmark_architecture.py   # Đo hiệu năng 3 tầng (PG Core vs PG Part/MV vs ClickHouse)
├── docs/
│   ├── 01_architecture_design.md   # Đặc tả kiến trúc Data Warehouse 5 tầng
│   ├── 02_terminology_glossary.md  # Bảng chuẩn hóa thuật ngữ chuyên ngành
│   ├── 03_metabase_dashboard_guide.md
│   └── 04_report_outline.md        # Đề cương chi tiết 5 chương (75% Kiến trúc / 25% Case study)
└── results/
    ├── offline_verification_report.md
    └── benchmark_report.md
```

---

## 3. Khởi chạy nhanh (Quickstart)

### Chạy kiểm chứng offline (không cần Docker)
```powershell
python scripts/verify_offline.py
```

### Chạy toàn bộ hệ thống trên Windows với Docker Compose
1. Tạo cấu hình môi trường (nếu chưa có `.env`):
   ```powershell
   Copy-Item .env.example .env
   ```
2. Khởi chạy toàn bộ dịch vụ và kích hoạt 3 Airflow DAGs:
   ```powershell
   .\run.ps1 up
   .\run.ps1 trigger-all
   ```
3. Truy cập các giao diện & kết nối:
   - **Apache Airflow UI:** `http://localhost:8080` (`admin` / `admin`)
   - **Metabase BI:** `http://localhost:3000`
   - **ClickHouse HTTP:** `http://localhost:8123` (`olap_user` / `olap_secret_change_me`)
   - **PostgreSQL 16 (DBeaver):** `localhost:5432` (DB `tlcn_dwh`, user `dwh_admin`)
   - **MinIO S3 API:** `http://localhost:9000` (kiểm tra object bằng `docker exec tlcn_minio mc ls --recursive local/tlcn-raw`; lưu ý bản `bitnamilegacy/minio:2025-05-24` không mở Web Console ở `:9001`)
   - **dbt Docs (Data Lineage, bật khi cần):** `.\run.ps1 dbt-docs` → `http://localhost:8081`

---

## 4. Kết quả kiểm chứng kỹ thuật

- **Kiểm chứng offline (`scripts/verify_offline.py`):** 0 lỗi `py_compile`, 0 lỗi cấu trúc YAML/Compose, 0 vi phạm thuật ngữ, **41/41 DWH Acceptance Tests PASS**.
- **Pipeline live (`dag_01` → `dag_02` → `dag_03`):**
  - `dbt test`: kiểm định đối xứng 100% khóa ngoại, độ duy nhất grain cho cả 3 bảng Fact và 5 luật Summarizability (`WARN=0`, `ERROR=0`).
  - `core_dwh.fact_trade`: **111,848 dòng** (`98,596` `VN_REPORTED` + `13,252` `PARTNER_MIRROR`), **0** trùng grain, **11 PK + 15 FK** vật lý; phân vùng thành 12 partition theo năm trên `fact_trade_partitioned`.
  - `core_dwh.fact_tariff_rate`: **419 dòng** (Year Sentinel `YYYY00`); `core_dwh.fact_macro_indicator`: **300 dòng** (`YYYY00`).
  - **Kimball Cross-Fact Drill-Across:** `mart.mart_trade_macro_yearly` (**45 dòng**, 5 đối tác chiến lược × 9 năm) và truy vấn Q7 trên PostgreSQL & ClickHouse kết hợp kim ngạch XNK với GDP & tỷ giá đối tác.
  - Đối soát **14/14** mốc kim ngạch World 2023 và **7/7** ô gương; `mart_trade_reconciliation` (**97,946 ô**) khôi phục **1,393 ô năm 2024** (`90,770.01 triệu USD`) qua dữ liệu gương quy đổi CIF/FOB.
  - Đồng bộ khớp 100% sang ClickHouse `olap_xnk` (**8/8 Dimensions + 3 Facts + `mart_trade_reconciliation`**) và đo Benchmark 3 tầng tại [results/benchmark_report.md](results/benchmark_report.md).
