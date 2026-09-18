# COVERAGE MATRIX — TUẦN 1

Mục đích: gom kết quả smoke test và mirror check để xác định nguồn/tổ hợp nào có dữ liệu, nguồn/tổ hợp nào thiếu, từ đó chuẩn bị chốt scope đề tài.

## 1. Input

| File | Vai trò |
|---|---|
| `results/week1/api_smoke_test_results.csv` | Bằng chứng gọi thử Comtrade, WITS, World Bank |
| `results/week1/mirror_check_results.csv` | Bằng chứng đối chiếu VN-reported và partner-mirror |

Script `build_coverage_matrix.py` không gọi API mới; chỉ gom và chuẩn hóa hai file trên.

## 2. Tóm tắt coverage

- Tổng số dòng coverage: `18`
- Dòng trade/mirror: `8`
- Dòng tariff/WITS: `3`
- Dòng macro/World Bank: `3`

### 2.1. Theo coverage status

| Status | Số dòng |
|---|---:|
| AVAILABLE | 8 |
| HIGH | 2 |
| LOW | 2 |
| MISSING_OR_FAILED | 1 |
| MISSING_VN_REPORTED | 3 |
| MODERATE | 1 |
| NO_DATA_BUT_API_OK | 1 |

### 2.2. Theo khuyến nghị scope

| Recommendation | Số dòng |
|---|---:|
| CORE_CANDIDATE | 2 |
| CORE_CANDIDATE_WITH_FLAG | 1 |
| MACRO_CONTEXT_AVAILABLE | 3 |
| MIRROR_FALLBACK_DEMO | 3 |
| RECONCILIATION_DEMO | 2 |
| TARIFF_BASELINE_AVAILABLE | 1 |
| TARIFF_PREF_AVAILABLE | 1 |
| TARIFF_PREF_COVERAGE_RISK | 1 |
| TRADE_RECENT_YEAR_GAP | 1 |
| TRADE_SOURCE_AVAILABLE | 3 |

## 3. Ma trận coverage rút gọn

| Row | Area | Direction | Partner | HS6/Indicator | Period | VN | Mirror | WITS MFN | WITS PREF | WB | Status | Recommendation |
|---|---|---|---|---|---:|:---:|:---:|:---:|:---:|:---:|---|---|
| TRADE-001 | TRADE_MIRROR | EXPORT | Japan | 090111 | 202301 | YES | YES | UNKNOWN | UNKNOWN | UNKNOWN | HIGH | RECONCILIATION_DEMO |
| TRADE-002 | TRADE_MIRROR | EXPORT | Japan | 090111 | 202401 | NO | YES | UNKNOWN | UNKNOWN | UNKNOWN | MISSING_VN_REPORTED | MIRROR_FALLBACK_DEMO |
| TRADE-003 | TRADE_MIRROR | EXPORT | United States | 090111 | 202301 | YES | YES | UNKNOWN | UNKNOWN | UNKNOWN | HIGH | RECONCILIATION_DEMO |
| TRADE-004 | TRADE_MIRROR | EXPORT | Germany | 090111 | 202301 | YES | YES | UNKNOWN | UNKNOWN | UNKNOWN | LOW | CORE_CANDIDATE |
| TRADE-005 | TRADE_MIRROR | IMPORT | China | 851762 | 202301 | YES | YES | UNKNOWN | UNKNOWN | UNKNOWN | LOW | CORE_CANDIDATE |
| TRADE-006 | TRADE_MIRROR | IMPORT | Rep. of Korea | 854231 | 202301 | YES | YES | UNKNOWN | UNKNOWN | UNKNOWN | MODERATE | CORE_CANDIDATE_WITH_FLAG |
| TRADE-007 | TRADE_MIRROR | IMPORT | China | 851762 | 202401 | NO | YES | UNKNOWN | UNKNOWN | UNKNOWN | MISSING_VN_REPORTED | MIRROR_FALLBACK_DEMO |
| TRADE-008 | TRADE_MIRROR | IMPORT | Rep. of Korea | 854231 | 202401 | NO | YES | UNKNOWN | UNKNOWN | UNKNOWN | MISSING_VN_REPORTED | MIRROR_FALLBACK_DEMO |
| SMOKE-009 | TRADE_SMOKE | EXPORT |  |  | 2023 | YES | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AVAILABLE | TRADE_SOURCE_AVAILABLE |
| SMOKE-010 | TRADE_SMOKE | EXPORT |  |  | 2024 | NO | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NO_DATA_BUT_API_OK | TRADE_RECENT_YEAR_GAP |
| SMOKE-011 | TRADE_SMOKE | EXPORT |  |  | 2023M01 | YES | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | AVAILABLE | TRADE_SOURCE_AVAILABLE |
| SMOKE-012 | TRADE_SMOKE | IMPORT |  |  | 2024M01 | UNKNOWN | YES | UNKNOWN | UNKNOWN | UNKNOWN | AVAILABLE | TRADE_SOURCE_AVAILABLE |
| TARIFF-013 | TARIFF_MFN | IMPORT_TARIFF | World | 090111 | 2018 | UNKNOWN | UNKNOWN | YES | UNKNOWN | UNKNOWN | AVAILABLE | TARIFF_BASELINE_AVAILABLE |
| TARIFF-014 | TARIFF_PREF | IMPORT_TARIFF | Japan | 090111 | 2018 | UNKNOWN | UNKNOWN | UNKNOWN | YES | UNKNOWN | AVAILABLE | TARIFF_PREF_AVAILABLE |
| TARIFF-015 | TARIFF_PREF | EXPORT_TARIFF | Japan | 090111 | 2018 | UNKNOWN | UNKNOWN | UNKNOWN | NO | UNKNOWN | MISSING_OR_FAILED | TARIFF_PREF_COVERAGE_RISK |
| MACRO-016 | MACRO_INDICATOR | MACRO | Viet Nam | NY.GDP.MKTP.CD | 2024 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | YES | AVAILABLE | MACRO_CONTEXT_AVAILABLE |
| MACRO-017 | MACRO_INDICATOR | MACRO | Viet Nam | PA.NUS.FCRF | 2024 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | YES | AVAILABLE | MACRO_CONTEXT_AVAILABLE |
| MACRO-018 | MACRO_INDICATOR | MACRO | Viet Nam | DPANUSSPB | 2024M01:2024M12 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | YES | AVAILABLE | MACRO_CONTEXT_AVAILABLE |

## 4. Diễn giải quan trọng

### 4.1. Trade và mirror

- Có nhiều tổ hợp hai phía đều có dữ liệu, ví dụ Germany/coffee 202301 và China/network equipment 202301.
- Có tổ hợp chênh lệch thấp, vừa và cao; do đó dashboard nên có cờ `discrepancy_level`.
- Có nhiều case năm 2024 bị `MISSING_VN_REPORTED` nhưng partner mirror có dữ liệu; đây là bằng chứng cho nhu cầu mirror fallback/reference.

### 4.2. WITS/tariff

- WITS có MFN và PREF cho chiều Việt Nam nhập khẩu hàng xuất xứ Nhật HS090111 năm 2018.
- WITS thiếu một case chiều Nhật áp thuế lên hàng Việt Nam HS090111 năm 2018, nên tariff dashboard cần được xem là phạm vi phụ/conditional cho tới khi profiling thêm.
- Không dùng dữ liệu WITS để kết luận tỷ lệ tận dụng FTA; chỉ dùng để phân tích MFN/PREF/tariff gap ở nơi có dữ liệu.

### 4.3. World Bank

- World Bank có GDP 2024, tỷ giá năm 2024 và tỷ giá tháng candidate 2024M01–2024M12.
- Dữ liệu vĩ mô nên đưa vào `FACT_MACRO_INDICATOR`, không đưa vào `DIM_DATE`.

## 5. Khuyến nghị scope sơ bộ cho Nhiệm vụ 6

| Thành phần | Khuyến nghị |
|---|---|
| Thời gian lõi | 2015–2023 cho VN-reported monthly; 2024 dùng như năm kiểm tra gap/mirror hoặc partial nếu coverage đủ |
| Partner lõi ban đầu | Japan, United States, Germany, China, Rep. of Korea; sau profiling có thể mở rộng top 10 |
| HS6 đã có bằng chứng | 090111, 851762, 854231 |
| Dashboard chính | Trade trend, partner/commodity analysis, mirror reconciliation |
| Dashboard phụ/conditional | Tariff gap MFN/PREF nếu WITS coverage đủ |
| Điểm mới | Mirror-reconciled trade data warehouse với perspective và discrepancy flag |

## 6. Kết luận

> Coverage Matrix cho thấy dữ liệu trade/mirror và macro đủ cơ sở để tiếp tục đề tài. WITS có dữ liệu nhưng thưa theo chiều partner/HS/year, nên phần tariff nên được giữ có điều kiện. Phạm vi nên ưu tiên dashboard trade + mirror reconciliation, sau đó bổ sung tariff gap ở các tổ hợp đã xác nhận có dữ liệu.

## 7. Output

| File | Nội dung |
|---|---|
| `results/week1/Coverage_Matrix.csv` | Ma trận coverage chính dạng bảng |
| `results/week1/Coverage_Matrix.json` | Ma trận coverage dạng JSON |
| `results/week1/Coverage_Matrix.md` | Bản đọc nhanh và diễn giải |