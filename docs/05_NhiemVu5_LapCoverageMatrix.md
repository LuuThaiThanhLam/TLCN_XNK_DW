# NHIỆM VỤ 5 — LẬP COVERAGE MATRIX

## 1. Mục tiêu

Nhiệm vụ 5 dùng để gom kết quả từ các bước trước thành một **ma trận coverage**.

Nói dễ hiểu:

> Sau khi đã gọi thử API và kiểm tra mirror, nhóm cần lập một bảng cho biết tổ hợp nào có dữ liệu, tổ hợp nào thiếu dữ liệu, nguồn nào đủ tin cậy để đưa vào phạm vi chính.

Coverage Matrix giúp trả lời:

- Nguồn Comtrade có đủ dữ liệu trade không?
- Tổ hợp nào có cả `VN_REPORTED` và `PARTNER_MIRROR`?
- Tổ hợp nào bị thiếu dữ liệu phía Việt Nam nhưng mirror có dữ liệu?
- WITS có đủ dữ liệu tariff không?
- World Bank có đủ dữ liệu vĩ mô không?
- Phần nào nên đưa vào scope chính, phần nào nên để phụ/conditional?

---

## 2. Input của nhiệm vụ 5

Nhiệm vụ này dùng kết quả đã có từ Nhiệm vụ 3 và 4:

```text
results/week1/api_smoke_test_results.csv
results/week1/mirror_check_results.csv
```

Trong đó:

| File | Vai trò |
|---|---|
| `api_smoke_test_results.csv` | Bằng chứng gọi thử Comtrade, WITS, World Bank |
| `mirror_check_results.csv` | Bằng chứng so sánh VN-reported và partner-mirror |

Nhiệm vụ 5 **không cần gọi API mới**. Chỉ cần chuẩn hóa và tổng hợp kết quả.

---

## 3. Script dùng cho nhiệm vụ 5

File script:

```text
scripts/profiling/build_coverage_matrix.py
```

Script này sẽ:

1. Đọc `api_smoke_test_results.csv`.
2. Đọc `mirror_check_results.csv`.
3. Chuẩn hóa các dòng coverage.
4. Gắn cờ `YES`, `NO`, `UNKNOWN` cho từng nguồn.
5. Gắn khuyến nghị scope cho từng dòng.
6. Ghi kết quả ra `results/week1/Coverage_Matrix.*`.

---

## 4. Cách chạy trên Windows Git Bash

Chạy:

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate
python scripts/profiling/build_coverage_matrix.py
```

Nếu terminal đã có `(.venv)` rồi thì chỉ cần:

```bash
python scripts/profiling/build_coverage_matrix.py
```

---

## 5. Output sau khi chạy

Script sẽ tạo/cập nhật:

```text
results/week1/Coverage_Matrix.csv
results/week1/Coverage_Matrix.json
results/week1/Coverage_Matrix.md
```

Ý nghĩa:

| File | Ý nghĩa |
|---|---|
| `Coverage_Matrix.csv` | Ma trận chính, có thể mở bằng Excel |
| `Coverage_Matrix.json` | Dạng máy đọc, dùng lại cho script sau |
| `Coverage_Matrix.md` | Bản dễ đọc để báo cáo/trao đổi |

---

## 6. Các cột quan trọng trong Coverage Matrix

| Cột | Ý nghĩa |
|---|---|
| `coverage_area` | Nhóm coverage: trade, tariff, macro |
| `business_question` | Câu hỏi nghiệp vụ mà dòng dữ liệu hỗ trợ |
| `direction` | EXPORT/IMPORT/IMPORT_TARIFF/EXPORT_TARIFF/MACRO |
| `partner_name` | Đối tác hoặc quốc gia |
| `hs6` | Mã HS6 nếu là trade/tariff |
| `year_or_month` | Kỳ dữ liệu |
| `comtrade_vn_reported_available` | Có dữ liệu Việt Nam báo cáo không |
| `comtrade_mirror_available` | Có dữ liệu mirror không |
| `wits_mfn_available` | Có dữ liệu MFN không |
| `wits_pref_available` | Có dữ liệu PREF không |
| `worldbank_available` | Có dữ liệu World Bank không |
| `coverage_status` | Trạng thái coverage quan sát được |
| `scope_recommendation` | Khuyến nghị đưa vào scope hay cần kiểm tra thêm |

---

## 7. Cách đọc `scope_recommendation`

| Recommendation | Ý nghĩa |
|---|---|
| `CORE_CANDIDATE` | Có thể đưa vào phạm vi lõi |
| `CORE_CANDIDATE_WITH_FLAG` | Có thể đưa vào phạm vi lõi nhưng cần gắn cờ chênh lệch |
| `RECONCILIATION_DEMO` | Phù hợp để demo chức năng đối chiếu do chênh lệch cao |
| `MIRROR_FALLBACK_DEMO` | Phù hợp để demo trường hợp Việt Nam thiếu dữ liệu nhưng mirror có dữ liệu |
| `TRADE_SOURCE_AVAILABLE` | Nguồn trade có dữ liệu |
| `TRADE_RECENT_YEAR_GAP` | Có khoảng trống năm gần đây |
| `TARIFF_BASELINE_AVAILABLE` | Có MFN baseline |
| `TARIFF_PREF_AVAILABLE` | Có thuế ưu đãi PREF |
| `TARIFF_PREF_COVERAGE_RISK` | Thiếu dữ liệu PREF ở một chiều/tổ hợp |
| `MACRO_CONTEXT_AVAILABLE` | Có dữ liệu vĩ mô |
| `RETRY_REQUIRED` | Cần chạy lại do lỗi kỹ thuật/API |

---

## 8. Kết quả workspace đã chạy thử

Trong workspace, script chạy thành công và tạo 18 dòng coverage:

| Nhóm | Số dòng |
|---|---:|
| Trade/mirror | 8 |
| Tariff/WITS | 3 |
| Macro/World Bank | 3 |
| Smoke evidence khác | 4 |

Tóm tắt trạng thái:

| Status | Số dòng |
|---|---:|
| `AVAILABLE` | 8 |
| `LOW` | 2 |
| `MODERATE` | 1 |
| `HIGH` | 2 |
| `MISSING_VN_REPORTED` | 3 |
| `NO_DATA_BUT_API_OK` | 1 |
| `MISSING_OR_FAILED` | 1 |

Ý nghĩa:

- Trade/mirror có dữ liệu đủ để tiếp tục.
- Có bằng chứng về chênh lệch thấp/vừa/cao.
- Có bằng chứng thiếu dữ liệu Việt Nam năm 2024 nhưng mirror có dữ liệu.
- World Bank có thể dùng làm dữ liệu vĩ mô.
- WITS dùng được nhưng còn rủi ro coverage, nên phần tariff cần giữ có điều kiện.

---

## 9. Khuyến nghị scope sơ bộ từ Coverage Matrix

| Thành phần | Khuyến nghị |
|---|---|
| Thời gian lõi | 2015–2023 cho VN-reported monthly |
| Năm 2024 | Dùng như năm kiểm tra gap/mirror hoặc partial nếu coverage đủ |
| Partner lõi ban đầu | Japan, United States, Germany, China, Rep. of Korea |
| HS6 đã có bằng chứng | 090111, 851762, 854231 |
| Dashboard chính | Trade trend, partner/commodity analysis, mirror reconciliation |
| Dashboard phụ | Tariff gap MFN/PREF nếu WITS coverage đủ |
| Điểm mới | Mirror-reconciled trade data warehouse |

---

## 10. Checklist hoàn thành Nhiệm vụ 5

- [ ] Có file `scripts/profiling/build_coverage_matrix.py`.
- [ ] Đã có `api_smoke_test_results.csv` từ Nhiệm vụ 3.
- [ ] Đã có `mirror_check_results.csv` từ Nhiệm vụ 4.
- [ ] Chạy script không lỗi Python.
- [ ] Có `results/week1/Coverage_Matrix.csv`.
- [ ] Có `results/week1/Coverage_Matrix.md`.
- [ ] Đọc được tổ hợp nào dùng được, tổ hợp nào thiếu.
- [ ] Có khuyến nghị scope sơ bộ cho Nhiệm vụ 6.

---

## 11. Commit lên GitHub

Sau khi chạy xong trên máy local, commit:

```bash
git status
git add scripts/profiling/build_coverage_matrix.py docs/05_NhiemVu5_LapCoverageMatrix.md
git add results/week1/Coverage_Matrix.csv results/week1/Coverage_Matrix.json results/week1/Coverage_Matrix.md
git commit -m "add week1 coverage matrix"
git push
```

Nếu có file báo cáo phân tích coverage ở `reports/`, có thể add thêm:

```bash
git add reports/03_PhanTich_Coverage_Matrix_Tuan1.md
```

---

## 12. Chuẩn bị cho nhiệm vụ tiếp theo

Kết quả Coverage Matrix là đầu vào cho:

> **Nhiệm vụ 6 — Chốt phạm vi đề tài**

Ở Nhiệm vụ 6, nhóm sẽ dựa vào coverage để chốt:

- Thời gian chính thức.
- Danh sách partner chính.
- Danh sách HS6 chính.
- Dashboard chính/phụ.
- Những phần nào không làm để tránh quá phạm vi TLCN.
