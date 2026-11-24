# Báo cáo Benchmark kiến trúc Data Warehouse mã nguồn mở (3 tầng)

- Thời điểm đo: `2026-11-24T06:47:17+00:00`
- So sánh 3 tầng: **PostgreSQL 16 Core (Fact Constellation Schema)** vs **PostgreSQL Partitioned + Materialized Views** vs **ClickHouse 24.8 Columnar OLAP**.

| Mã | Kịch bản | PG Core Warm (ms) | PG Part/MV Warm (ms) | ClickHouse Warm (ms) | Số dòng |
|:---:|---|---:|---:|---:|---:|
| **B1** | Annual Trade Rollup (Year x Region x Flow) | 40.25 | 5.34 | 23.18 | 90 |
| **B2** | Bilateral Trade Balance (14 HS6 Scope) | 37.97 | 1.95 | 22.68 | 864 |
| **B3** | Market Concentration Index (HHI & CR-4) | 47.40 | 0.33 | 21.40 | 18 |
| **B4** | Partition Pruning Slice (Year = 2023 x Commodity) | 4.21 | 4.48 | 9.04 | 28 |
| **B5** | 2024 Mirror Reconciliation & Coverage Aggregation | 171.25 | 10.48 | 6.43 | 1 |