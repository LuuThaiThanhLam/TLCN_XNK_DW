# Báo cáo Kiểm chứng Offline — TLCN_DW_XNK (Phương án A)

- Thời điểm chạy: `2026-11-24T06:48:46+00:00`
- Kết luận tổng thể: **100% PASS**

## 1. Kiểm tra Tĩnh (Syntax, YAML, Thuật ngữ & Sạch mã nguồn cũ)

- Python `py_compile`: **PASS** (0 lỗi)
- YAML / Docker Compose structure: **PASS** (0 lỗi)
- Quét sạch T-SQL / Microsoft stack / lỗi thuật ngữ: **PASS** (0 phát hiện)
- CLI Extractors selftest & MinIO dry-run: **PASS** (0 lỗi)

## 2. Kết quả Kiểm định Kho dữ liệu End-to-End (V0–V7 & Luật R1–R5)

| Mã Test | Hạng mục | Kỳ vọng | Thực tế | Kết quả |
|---|---|---:|---:|:---:|
| `V1-FT1` | fact_trade perspective=1 (VN_REPORTED) | `98596` | `98596` | **PASS** |
| `V1-FT2` | fact_trade perspective=2 (PARTNER_MIRROR) | `13252` | `13252` | **PASS** |
| `V1-TR` | fact_tariff_rate | `419` | `419` | **PASS** |
| `V1-MC` | fact_macro_indicator | `300` | `300` | **PASS** |
| `V1-DP` | dim_partner | `98` | `98` | **PASS** |
| `V1-DC` | dim_commodity | `14` | `14` | **PASS** |
| `V1-DD` | dim_date (120 months + 10 year sentinels) | `130` | `130` | **PASS** |
| `V1-DA` | dim_audit (>=126 batches) | `>=126` | `177` | **PASS** |
| `V1-RL` | dw_usage_rule | `5` | `5` | **PASS** |
| `V2-FT` | fact_trade grain duplicates | `0` | `0` | **PASS** |
| `V2-TR` | fact_tariff_rate grain duplicates | `0` | `0` | **PASS** |
| `V2-MC` | fact_macro_indicator grain duplicates | `0` | `0` | **PASS** |
| `V3-MIR` | Mirror partner_code_src = '704' invariant | `0` | `0` | **PASS** |
| `V3-R5-FT` | fact_trade strictly MONTH granularity | `0` | `0` | **PASS** |
| `V3-R5-TR` | fact_tariff_rate strictly YEAR sentinel | `0` | `0` | **PASS** |
| `V3-R5-MC` | fact_macro_indicator strictly YEAR sentinel | `0` | `0` | **PASS** |
| `V3-WITS-ANCHOR` | WITS ANCHOR mapped to World('0') and Japan('392') | `['0', '392']` | `['0', '392']` | **PASS** |
| `V4-X-851713` | World 2023 anchor X/851713 | `26460317776.0` | `26460317776.13` | **PASS** |
| `V4-X-640399` | World 2023 anchor X/640399 | `4991396908.0` | `4991396908.06` | **PASS** |
| `V4-X-100630` | World 2023 anchor X/100630 | `4060727368.0` | `4060727367.8` | **PASS** |
| `V4-X-090111` | World 2023 anchor X/090111 | `2977954667.0` | `2977954667.29` | **PASS** |
| `V4-X-080132` | World 2023 anchor X/080132 | `2916825905.0` | `2916825905.16` | **PASS** |
| `V4-X-854442` | World 2023 anchor X/854442 | `2062142409.0` | `2062142409.28` | **PASS** |
| `V4-X-610910` | World 2023 anchor X/610910 | `1401669880.0` | `1401669879.95` | **PASS** |
| `V4-X-090411` | World 2023 anchor X/090411 | `683211713.0` | `683211712.93` | **PASS** |
| `V4-M-854231` | World 2023 anchor M/854231 | `17797673474.0` | `17797673473.56` | **PASS** |
| `V4-M-847330` | World 2023 anchor M/847330 | `928122689.0` | `928122689.03` | **PASS** |
| `V4-M-851762` | World 2023 anchor M/851762 | `841528135.0` | `841528134.71` | **PASS** |
| `V4-M-390120` | World 2023 anchor M/390120 | `827368947.0` | `827368947.42` | **PASS** |
| `V4-M-540761` | World 2023 anchor M/540761 | `484289054.0` | `484289054.31` | **PASS** |
| `V4-M-721049` | World 2023 anchor M/721049 | `137743539.0` | `137743539.0` | **PASS** |
| `V5-392-M-090111-202401` | Mirror cell 392/M/090111/202401 | `35660719.503` | `35660719.5` | **PASS** |
| `V5-842-M-090111-202301` | Mirror cell 842/M/090111/202301 | `37790801.0` | `37790801.0` | **PASS** |
| `V5-276-M-090111-202301` | Mirror cell 276/M/090111/202301 | `38271554.955` | `38271554.96` | **PASS** |
| `V5-156-X-851762-202301` | Mirror cell 156/X/851762/202301 | `29945226.0` | `29945226.0` | **PASS** |
| `V5-410-X-854231-202301` | Mirror cell 410/X/854231/202301 | `217401413.0` | `217401413.0` | **PASS** |
| `V5-156-X-851762-202401` | Mirror cell 156/X/851762/202401 | `62727085.0` | `62727085.0` | **PASS** |
| `V5-410-X-854231-202401` | Mirror cell 410/X/854231/202401 | `412589570.0` | `412589570.0` | **PASS** |
| `V7-LEVELS` | 5 distinct discrepancy levels | `5` | `5` | **PASS** |
| `V7-2024` | 2024 Mirror recovery cells > 0 | `>0` | `1393` | **PASS** |
| `V7-TARIFF-R2` | Weighted-Average Bounds Check (>=0 and within [min, max] of components) | `0` | `0` | **PASS** |

## 3. Bộ Số liệu Nhất quán Đã Kiểm chứng (Single Source of Truth)

- Tổng số ô trong `mart_trade_reconciliation`: **97,946** ô
- Năm 2024 phục hồi qua dữ liệu gương (`MIRROR_ESTIMATED`): **1,393** ô, tương đương **90,770.01 triệu USD**

### Phân bổ `data_source_flag` trong `mart_trade_reconciliation`

| Cờ nguồn dữ liệu | Số ô | Tỷ trọng (%) | Giá trị Best Estimate (Triệu USD) |
|---|---:|---:|---:|
| `VN_OFFICIAL_ONLY` | 84,694 | 86.5% | 381,854.14 |
| `BOTH_AVAILABLE` | 10,884 | 11.1% | 364,834.57 |
| `MIRROR_ESTIMATED` | 2,368 | 2.4% | 91,233.12 |

### Chỉ số tập trung thị trường HHI & CR-4 (2015–2023, trong phạm vi 14 mã HS6)

| Năm | HHI Xuất khẩu | CR-4 Xuất khẩu (%) | HHI Nhập khẩu | CR-4 Nhập khẩu (%) |
|:---:|---:|---:|---:|---:|
| 2015 | 594 | 39.62% | 2,207 | 76.97% |
| 2016 | 653 | 40.41% | 1,915 | 73.64% |
| 2017 | 588 | 39.38% | 1,747 | 75.10% |
| 2018 | 698 | 42.71% | 1,745 | 76.77% |
| 2019 | 839 | 44.65% | 1,868 | 79.68% |
| 2020 | 1,152 | 52.15% | 1,650 | 76.89% |
| 2021 | 1,141 | 52.59% | 1,453 | 70.02% |
| 2022 | 1,377 | 55.56% | 1,464 | 67.52% |
| 2023 | 1,096 | 52.17% | 1,461 | 67.28% |

### Top 5 đối tác theo tổng kim ngạch (2015–2023, trong phạm vi rổ 14 mã HS6 khảo sát)

| Đối tác | Xuất khẩu (Tỷ USD) | Nhập khẩu (Tỷ USD) | Cán cân ròng rổ 14 HS6 (Tỷ USD) |
|---|---:|---:|---:|
| USA | 145.46 | 30.06 | +115.40 |
| China | 70.83 | 40.48 | +30.35 |
| Rep. of Korea | 18.14 | 20.18 | -2.05 |
| United Arab Emirates | 31.55 | 0.49 | +31.06 |
| China, Hong Kong SAR | 27.88 | 1.35 | +26.53 |
