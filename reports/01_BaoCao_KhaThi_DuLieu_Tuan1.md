# BÁO CÁO KHẢ THI DỮ LIỆU — TUẦN 1

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Nhóm:** Nguyễn Khắc Dương — Lưu Thái Thanh Lâm  
**Tuần:** 1  
**Ngày cập nhật:** 19/09/2026  

> Mọi số liệu trong báo cáo này lấy từ các lần gọi API **thật** đã commit trong repo (`results/week1/`). Chế độ gọi: UN Comtrade **public preview** (chưa dùng subscription key) — đủ để kiểm chứng khả thi, chưa đủ để extract khối lượng lớn (xem §7).

---

## 1. Mục tiêu kiểm chứng

Tuần 1 không nhằm xây kho dữ liệu ngay, mà nhằm trả lời 4 câu hỏi:

1. Các API chính có gọi được không?
2. Dữ liệu có đủ để trả lời các câu hỏi nghiệp vụ không?
3. Phạm vi đối tác/mã HS/năm nào là khả thi?
4. Rủi ro dữ liệu lớn nhất là gì và cần giảm phạm vi ra sao?

**Kết luận nhanh: cả 4 câu đã có trả lời bằng số liệu — khả thi để chốt phạm vi theo §6.**

---

## 2. Nguồn dữ liệu kiểm chứng

| Nguồn | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| UN Comtrade (public preview `public/v1/preview`) | Kim ngạch theo tháng/năm, 2 chiều, 2 perspective | **OK** — 4/4 test Comtrade HTTP 200 | Preview giới hạn ~50 records/query → cần subscription key cho bước extract tuần 2; script đã tự đọc `.env` để chuyển endpoint `data/v1/get` khi có key |
| WITS/UNCTAD TRAINS | Thuế MFN/PREF | **OK, nhưng thưa** — 2/3 case có dữ liệu, 1 case 404 | Annual 2015–2022; chỉ kết luận được chênh lệch mức thuế biểu, **không** kết luận tỷ lệ tận dụng FTA |
| World Bank Indicators | GDP, tỷ giá, lạm phát, thương mại/GDP | **OK** — 3/3 test 200 | GDP, tỷ giá năm và tỷ giá **tháng** (12/12 kỳ 2024) đều có |

---

## 3. Kết quả smoke test API

Chi tiết đầy đủ (kèm URL và raw JSON từng response): `results/week1/api_smoke_test_results.md` / `.csv` / `.json` — 10 test, **9/10 HTTP 200, 0 lỗi kết nối**, trường hợp "0 bản ghi" là phát hiện nghiệp vụ có chủ đích (gap 2024) chứ không phải lỗi API.

| # | Test | Kết quả | Nhận xét |
|---:|---|---|---|
| 1 | Comtrade VN annual 2023 (export TOTAL → World) | ✅ 200, 1 record | Kim ngạch gốc 353,077,513,296 USD; `isAggregate=true` trên dòng World → xác nhận phải gắn cờ aggregate |
| 2 | Comtrade VN annual 2024 gap check | ✅ 200, **count=0** | HTTP OK nhưng VN chưa nộp dữ liệu năm 2024 → bằng chứng trực tiếp cho quyết định "2024 = partial" |
| 3 | Comtrade monthly VN → Japan, HS090111, 2023M01 | ✅ 200, 1 record | Chuỗi tháng hoạt động; 10,127,757.60 USD |
| 4 | Comtrade monthly mirror: Japan import từ VN, 2024M01 | ✅ 200, 1 record | **Mirror có dữ liệu kỳ mà VN-reported thiếu** → hợp lệ hóa cơ chế mirror fallback |
| 5 | WITS MFN — VN áp dụng cho hàng World, HS090111, 2018 | ✅ 200 | MFN ≈ 15% |
| 6 | WITS PREF — VN áp dụng cho hàng Nhật, HS090111, 2018 | ✅ 200 | PREF ≈ 8% → `tariff_gap` 7 điểm % tính được trên tổ hợp thật |
| 7 | WITS PREF — Nhật áp dụng cho hàng VN, HS090111, 2018 | ❌ 404 NoRecordsFound | Coverage TRAINS thưa theo hướng đối tác → tariff là **phụ/conditional** |
| 8 | WB GDP (NY.GDP.MKTP.CD) VN 2024 | ✅ 200 | ≈ 476.3 tỷ USD |
| 9 | WB tỷ giá năm (PA.NUS.FCRF) VN 2024 | ✅ 200 | 24,164.9 LCU/USD |
| 10 | WB tỷ giá tháng (DPANUSSPB) VN 2024M01–M12 | ✅ 200, 12 records | Đủ grain tháng nếu dashboard cần phân tích tỷ giá-tháng |

---

## 4. Ma trận coverage (18 dòng — bản đầy đủ: `results/week1/Coverage_Matrix.md`)

Bố trí: 8 dòng trade/mirror + 4 dòng smoke + 3 dòng tariff + 3 dòng macro. Trạng thái: AVAILABLE 8, HIGH 2, LOW 2, MODERATE 1, MISSING_VN_REPORTED 3, MISSING_OR_FAILED 1, NO_DATA_BUT_API_OK 1.

### 4.1. Đối chiếu VN-reported vs partner-mirror (8 case, nguồn `mirror_check_results.md`)

| Case | Kỳ | VN-reported (USD) | Mirror (USD) | Chênh vs VN | Mức |
|---|---|---:|---:|---:|---|
| VN export coffee → Japan | 2023M01 | 10,127,757.60 | 16,784,397.26 | +65.73% | HIGH |
| VN export coffee → USA | 2023M01 | 20,201,618.07 | 37,790,801.00 | +87.07% | HIGH |
| VN export coffee → Germany | 2023M01 | 41,199,796.46 | 38,271,554.95 | −7.11% | LOW |
| VN import network equip ← China | 2023M01 | 29,869,079.44 | 29,945,226.00 | +0.25% | LOW |
| VN import IC ← Korea | 2023M01 | 252,083,766.17 | 217,401,413.00 | −13.76% | MODERATE |
| 3 case kỳ 2024M01 (Japan/China/Korea) | 2024M01 | **count=0** | có dữ liệu | — | MISSING_VN_REPORTED |

Diễn giải: chênh **dương** ở Japan/USA đúng mô hình VN khai FOB – đối tác khai CIF; nhưng Germany (−7.11%) và Korea (−13.76%) chứng minh mirror cũng có thể **thấp hơn** → không giả định chiều lệch, phải tính và gắn cờ cho cả hai phía. **Không có case nào lỗi API**; 3/8 case chứng minh nhu cầu mirror fallback khi VN trễ số liệu.

> Lưu ý đọc số: bảng trên ghi **chênh có dấu** để dễ diễn giải; các file kết quả gốc (`mirror_check_results.*`) lưu `pct_diff_vs_vn` là **giá trị tuyệt đối** — phân loại LOW/MODERATE/HIGH dựa trên trị tuyệt đối, không dựa trên dấu.

### 4.2. Tariff + macro

- Tariff: 2/3 tổ hợp có dữ liệu (chiều VN áp dụng), 1/3 404 (chiều đối tác áp dụng) → đưa vào scope có điều kiện, chỉ công bố số ở tổ hợp đã kiểm chứng.
- Macro: 3/3 AVAILABLE (GDP, tỷ giá năm, tỷ giá tháng) → vào `FACT_MACRO_INDICATOR`, grain tách riêng, không nhét vào `DIM_DATE`.

### 4.3. Profile 14 mã HS6 ứng viên (Nhiệm vụ 6, `scope_profile_results.md`)

14/14 mã có số liệu VN-reported thật cho cả 2022 và 2023 (partner World, annual), tên mô tả Comtrade khớp nhóm hàng. Kim ngạch 2023 từ 137.7 triệu USD (721049 thép mạ) đến 26.46 tỷ USD (851713 điện thoại). **Không mã nào bị loại.** Gap check 2024 toàn ngành: count=0 → xác nhận lại mục 4 của §6.

---

## 5. Câu hỏi nghiệp vụ có/không trả lời được

| Câu hỏi | Trả lời được? | Nguồn dữ liệu | Ghi chú giới hạn |
|---|---|---|---|
| Kim ngạch theo tháng/năm/đối tác/HS6 | **Có** | Comtrade monthly, 18/18 dòng trade AVAILABLE | 2024 thiếu phía VN → gắn cờ |
| Mùa vụ theo nhóm hàng | **Có** | Chuỗi tháng 2015–2023 (9 năm) | heatmap per HS6 |
| Cấu trúc & tập trung thị trường | **Có** | Comtrade, 5 partner lõi + World | World chỉ dùng tính tỷ trọng, không xếp hạng |
| Đối chiếu VN-reported vs mirror | **Có** — **điểm mới** | 8 case §4.1, diff 0.25%→87.07% | discrepancy flag 3 mức; nguyên nhân chính là FOB/CIF |
| Tariff gap MFN/PREF | **Một phần (conditional)** | WITS 2015–2022 | chỉ công bố tổ hợp đã xác nhận có dữ liệu |
| GDP/tỷ giá làm bối cảnh | **Có** | WB API | grain năm (+ tháng cho tỷ giá) |
| Tỷ lệ tận dụng FTA thực tế | **Không** | cần C/O, tờ khai hải quan | Ngoài phạm vi — ghi rõ để tránh overclaim |

---

## 6. Phạm vi chốt sau tuần 1 (bản full: `docs/06_NhiemVu6_ChotPhamViDeTai.md`)

| Thành phần | Chốt |
|---|---|
| Giai đoạn lõi | **2015–2023** monthly, VN-reported, 14 HS6 × 5 partner + World × 2 flow |
| 2024 | **Dùng với cờ partial**: chỉ làm năm minh họa gap + mirror fallback, không vào chỉ tiêu tổng hợp chính (bằng chứng: §3 test 2 và §4.1) |
| 2025 trở đi | **Không dùng** — chưa kiểm chứng độ phủ |
| Đối tác | China (156), USA (842), Rep. of Korea (410), Japan (392), Germany (276) + World (0, `is_aggregate`) |
| Mã HS6 | **14 mã** — xuất: 090111, 100630, 080132, 090411, 610910, 640399, 851713, 854442; nhập: 851762, 854231, 847330, 721049, 540761, 390120. Phương án thay thế nếu chuỗi thiếu khi extract: 030617, 720839, 640299, 441239 |
| Flow / perspective | X và M; `VN_REPORTED` (chính) và `PARTNER_MIRROR` (đối chiếu) lưu riêng trong grain, **không bao giờ cộng trộn** |
| Dashboard chính | D1 Tổng quan XNK · D2 Thị trường & mặt hàng (share, mùa vụ, độ tập trung top-3) · D3 **Mirror reconciliation** (bảng diff %, cờ màu, kỳ MISSING_VN_REPORTED) |
| Dashboard phụ/conditional | D4 Tariff gap MFN−PREF (tổ hợp có dữ liệu) · D5 Bối cảnh vĩ mô |
| Điểm mới | DW 2 reporting_perspective + lớp reconciliation có `discrepancy_level` — dashboard trả lời thêm "con số đáng tin đến đâu", không chỉ "bao nhiêu" |

---

## 7. Rủi ro và phương án xử lý

| Rủi ro | Mức độ | Cách xử lý |
|---|---|---|
| Preview cap ~50 records/query — **chặn ở bước extract** | **Cao** | Đăng ký subscription key (free tier "My Comtrade") trước tuần 2; key đặt `.env` (đã gitignore); script đã hỗ trợ tự chuyển `data/v1/get` |
| Comtrade 429 rate limit khi gọi dày | Trung bình | Các script đã có sleep 2.2s + retry/backoff; batch theo năm; cache raw JSON |
| WITS thiếu dữ liệu theo chiều/đối tác (đã gặp 404) | Trung bình | Tariff để **phụ/conditional**; chỉ extract tổ hợp đã xác nhận; không kết luận tận dụng FTA |
| 2024 VN trễ số liệu (count=0, đã kiểm chứng 2 lần) | Đã xảy ra | Thiết kế partial + mirror fallback; biến thành nội dung phân tích ở D3 |
| Chênh mirror lớn (tới 87%) bị hiểu là "dữ liệu sai" | Trung bình | Mọi kết quả diff kèm note FOB/CIF + `reconciliation_note`; case US coffee chỉ demo cờ, không dùng làm chỉ tiêu |
| Double counting mode/customs | Thấp | Đã kiểm tra: **toàn bộ 4/4 URL Comtrade smoke + 16/16 URL mirror** đều mang `motCode=0&customsCode=C00&partner2Code=0` (bằng chứng grep trong raw JSON) |
| Nhầm chiều tariff (đối tác áp lên hàng VN vs VN áp lên hàng đối tác) | Thấp | Test 5–7 tách 2 hướng riêng; 404 chỉ ở chiều ngược → logic chiều đã kiểm soát |
| World aggregate bị cộng nhầm vào tổng partner | Thấp | Cờ `is_aggregate` trong DIM_PARTNER (chính `isAggregate=true` ở test 1 chứng minh nguồn flag đáng tin); query xếp hạng luôn loại aggregate |
| Chiếm dụng thời gian ETL/SSAS tuần 2–4 | Cao | grain + schema + luật đã chốt xong ở tuần 1 → transform còn là việc cơ giới |

---

## 8. Kết luận tuần 1

- **Nguồn dùng được:** UN Comtrade (nguồn chính, full pipeline smoke→mirror→profile đã chạy bằng số liệu thật); World Bank (bối cảnh vĩ mô).
- **Nguồn có rủi ro:** WITS/TRAINS — chạy được nhưng coverage thưa theo chiều/năm, chấp nhận ở vai trò phụ có điều kiện.
- **Phạm vi chốt để trình GVHD:** 2015–2023 (+2024 partial), 5 partner + World, 14 HS6, 2 flow, 2 perspective không trộn, 3 dashboard chính (D3 mirror là điểm mới), tariff/macro phụ. 4 câu hỏi xin xác nhận ghi tại `docs/06_NhiemVu6_ChotPhamViDeTai.md` §10.
- **Việc tuần 2:** (1) đăng ký Comtrade subscription key → `.env`; (2) extract lõi theo batch (≈12–16 request khi có key), cache raw vào `data/raw/week2_extract/`; (3) dựng DDL staging + star schema đúng §5 docs/06; (4) SSIS package đầu tiên cho FACT_TRADE; (5) nộp biên bản phản hồi GVHD (điền vào docs/06 §11).

---

## 9. Phụ lục — bằng chứng và reproduce

| Artifact | Đường dẫn | Commit |
|---|---|---|
| Hướng dẫn NV1–NV6 | `docs/00`→`docs/06` | tới `d496ad9` |
| Smoke test (script + raw + results) | `scripts/profiling/api_smoke_test.py`, `results/week1/api_smoke_test_results.*` | repo main |
| Mirror check | `scripts/profiling/mirror_check.py`, `results/week1/mirror_check_results.*` | repo main |
| Coverage matrix | `scripts/profiling/build_coverage_matrix.py`, `results/week1/Coverage_Matrix.*` | `bde9bc3`→`c6341ec` |
| Scope profile 14 HS6 | `scripts/profiling/scope_validation_profile.py`, `results/week1/scope_profile_results.*` | `d496ad9` |

Reproduce trên máy bất kỳ: chạy 3 script theo thứ tự `api_smoke_test.py` → `mirror_check.py` → `build_coverage_matrix.py` (không cần key, ~3 phút tổng). Số liệu phải khớp vì mọi query đã khóa params như §7; nếu Comtrade đã cập nhật kỳ mới thì phần `period` có thể tiến theo — đó là hành vi mong đợi.
