# NHIỆM VỤ 6 — CHỐT PHẠM VI ĐỀ TÀI

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Trạng thái:** Bản chốt lần 1 (draft để trình GVHD phê duyệt)  
**Căn cứ:** Nhiệm vụ 2–5 (`docs/01_Data_Source_Catalog.md`, `results/week1/api_smoke_test_results.*`, `results/week1/mirror_check_results.*`, `results/week1/Coverage_Matrix.*`) và bằng chứng profile HS6 `results/week1/scope_profile_results.*`

> Nguyên tắc của tài liệu này: mọi dòng phạm vi đều phải trỏ về một bằng chứng dữ liệu đã kiểm chứng, không chốt theo cảm tính.

---

## 1. Định vị đề tài

| Yếu tố | Nội dung |
|---|---|
| Loại đồ án | Tiểu luận tốt nghiệp (TLCN) — tên đã được GV chốt, không đổi |
| Quy mô | 5 tín chỉ, 2 thành viên, 13 tuần |
| Trọng tâm kỹ thuật | Data Warehouse theo Kimball: ETL (SSIS) → relational DW → OLAP cube (SSAS) → dashboard (Power BI) |
| Nguồn dữ liệu | API thực tế (UN Comtrade, WITS/UNCTAD TRAINS, World Bank), không dùng CSV/Excel tải sẵn làm nguồn chính |
| Đối tượng quyết định | Nhà phân tích chính sách thương mại / doanh nghiệp XNK (persona giả định khi thuyết minh) |

---

## 2. Câu hỏi nghiệp vụ — trả lời được hay không, bằng cái gì

| # | Câu hỏi nghiệp vụ | Trả lời được? | Nguồn bằng chứng |
|---|---|---|---|
| Q1 | Kim ngạch XNK theo tháng/năm, theo đối tác, theo nhóm hàng HS6 biến động thế nào? | **Có** | Comtrade monthly, 18/18 dòng trade AVAILABLE (NV3–4) |
| Q2 | Cấu trúc thị trường: đối tác nào chiếm tỷ trọng lớn, có rủi ro tập trung không? | **Có** | Comtrade, partner code 156/392/410/842/276 đã chứng minh |
| Q3 | Tính mùa vụ theo nhóm hàng (cà phê, gạo, thủy sản...)? | **Có** | Chuỗi monthly 9 năm (2015–2023), heatmaps |
| Q4 | Số liệu Việt Nam tự khai khác gì số liệu đối tác báo cáo (mirror), kỳ nào Việt Nam thiếu dữ liệu? | **Có** — điểm mới chính | NV4: 5/8 case hai phía có dữ liệu, 3 case MISSING_VN_REPORTED, diff 0.25%→87% |
| Q5 | Chênh lệch thuế MFN vs ưu đãi (PREF) theo HS6/đối tác, để thấy dư địa hưởng lợi FTA về mặt biểu thuế? | **Một phần (conditional)** | WITS: MFN 15% và PREF 8% cho 090111/2018; 1/3 case 404 → chỉ làm cho tổ hợp có dữ liệu |
| Q6 | Tỷ lệ tận dụng FTA thực tế (bao nhiêu % lô hàng có C/O ưu đãi)? | **KHÔNG** — ngoài phạm vi | Cần tờ khai/C/O hải quan, không có trong API công khai |
| Q7 | Bối cảnh vĩ mô (GDP, tỷ giá, lạm phát) đặt cạnh kim ngạch? | **Có** | World Bank API: GDP 476.3 tỷ USD 2024, tỷ giá năm + tháng OK |

---

## 3. Phạm vi dữ liệu chốt

### 3.1. Thời gian

| Tập | Quyết định | Lý do / bằng chứng |
|---|---|---|
| **2015–2023** | **Lõi chính thức** | Chuỗi monthly VN-reported có dữ liệu (NV3–5); 9 năm đủ cho YoY, trend, mùa vụ |
| **2024** | **Phụ / partial** | Comtrade VN annual 2024 `count=0`; mirror 2024 có dữ liệu (3 case `MISSING_VN_REPORTED`). 2024 chỉ đưa vào như năm minh họa khoảng trống dữ liệu + mirror fallback, không đưa vào chỉ tiêu tổng hợp chính |
| 2025 trở đi | Loại | Chưa có độ phủ kiểm chứng |
| WITS tariff | 2015–2022, năm nào có lấy năm đó | TRAINS là annual, coverage thưa; không canh theo monthly |

### 3.2. Đối tác (chuẩn hóa theo góc nhìn Việt Nam)

| Nhóm | Partner | Code | Vai trò |
|---|---|---|---|
| Lõi | China | 156 | Nhập khẩu lớn nhất, có case mirror lệch 0.25% (chuẩn đối chiếu đẹp) |
| Lõi | United States | 842 | Thị trường xuất khẩu lớn nhất, có case lệch cao (demo cờ chất lượng) |
| Lõi | Rep. of Korea | 410 | Nhập IC/máy móc, case MODERATE 13.76% |
| Lõi | Japan | 392 | Đối tác FTA thế hệ mới (CPTPP/VJEPA), cà phê HIGH |
| Lõi | Germany | 276 | Cửa ngõ EU, case LOW 7.11% |
| Aggregate | World | 0 | Chỉ để tính tỷ trọng / kiểm soát tổng; **không xếp hạng cùng partner đơn** |

Mở rộng cho phép: 3–5 partner phụ (vd. ASEAN peers) **chỉ khi** dữ liệu 2015–2023 đầy đủ trong tuần 2 — ưu tiên giảm hơn là tăng.

### 3.3. Nhóm hàng HS6 — 14 mã đã có bằng chứng số liệu thật

Bằng chứng: `results/week1/scope_profile_results.md` (script `scope_validation_profile.py`, chạy 2026-09-19, Comtrade preview, VN-reported, partner World, 2022+2023). **14/14 KEEP**, không mã nào phải loại.

| HS6 | Nhóm hàng | Chiều chính | Kim ngạch 2023 (USD, VN-reported) |
|---|---|---|---:|
| 851713 | Điện thoại thông minh | EXPORT | 26,460,317,776 |
| 640399 | Giày da | EXPORT | 4,991,396,908 |
| 100630 | Gạo | EXPORT | 4,060,727,368 |
| 090111 | Cà phê nhân | EXPORT | 2,977,954,667 |
| 080132 | Hạt điều | EXPORT | 2,916,825,905 |
| 854442 | Dây điện có đầu nối | EXPORT | 2,062,142,409 |
| 610910 | Áo thun cotton | EXPORT | 1,401,669,880 |
| 090411 | Hồ tiêu | EXPORT | 683,211,713 |
| 854231 | Vi mạch IC | IMPORT | 17,797,673,474 |
| 851762 | Thiết bị truyền dẫn dữ liệu | IMPORT | 841,528,135 |
| 847330 | Linh kiện máy vi tính | IMPORT | 928,122,689 |
| 390120 | Polyethylene thô | IMPORT | 827,368,947 |
| 540761 | Vải polyester dệt thoi | IMPORT | 484,289,054 |
| 721049 | Thép cán dẹt mạ kẽm | IMPORT | 137,743,539 |

Quy tắc:
- Danh sách chốt ở **cấp mã HS6**; mỗi mã gắn `commodity_group` khi lên DIM (Nông sản / Điện tử–viễn thông / Dệt may–da giày / Công nghiệp phụ trợ / Nguyên vật liệu) để dashboard nhóm lại.
- "Chiều chính" chỉ để thuyết minh tính đại diện; fact vẫn lưu **cả hai chiều X và M** cho mọi mã (tránh mất thông tin nhập khẩu cà phê/ xuất khẩu IC).
- 3 mã đã có sẵn bằng chứng mirror 2 phía (090111, 851762, 854231) — giữ nguyên làm bộ case demo reconciliation.
- Phương án thay thế nếu mã nào đó khi extract thật thiếu chuỗi: 030617 (tôm đông lạnh), 720839 (thép cuộn cán nóng), 640299 (giày nhựa), 441239 (gỗ dán).

### 3.4. Flow và reporting perspective

| Quyết định | Chi tiết |
|---|---|
| Flow | `X` và `M` theo góc nhìn Việt Nam, mã hóa 1 chiều duy nhất trong fact (`flow_code`) |
| Perspective | `VN_REPORTED` (chính) và `PARTNER_MIRROR` (đối chiếu) — lưu riêng, **không bao giờ cộng trộn**; do ETL gán theo chiều truy vấn, không dùng `isReported` |
| Mirror chỉ lấy cho 5 partner lõi | Không tồn tại mirror của World; aggregate chỉ có ở VN_REPORTED |

### 3.5. Thuế quan (phụ, conditional)

- Chỉ lấy **chiều Việt Nam áp dụng** (reporter=704) cho hàng xuất xứ 5 partner lõi + World, MFN và PREF, các năm có dữ liệu 2015–2022.
- Chỉ tiêu: `tariff_gap = MFN − PREF`, tính **chỉ khi cả hai giá trị cùng tồn tại** đúng chiều.
- Ngôn ngữ bắt buộc: "chênh lệch mức thuế biểu MFN và ưu đãi", **không dùng** "tỷ lệ tận dụng FTA".

### 3.6. Vĩ mô (bổ trợ)

| Indicator | Grain | Ghi chú |
|---|---|---|
| NY.GDP.MKTP.CD, NY.GDP.MKTP.KD.ZG (tăng trưởng), FP.CPI.TOTL.ZG (lạm phát) | Năm, 2015–2024 | World Bank API đã test OK |
| PA.NUS.FCRF | Năm | Đã test OK (24,164.9 LCU/USD 2024) |
| DPANUSSPB | Tháng | Đã test OK 12/12 tháng 2024 — dùng cho phân tích tỷ giá-tháng nếu cần |

---

## 4. Khối lượng dữ liệu dự kiến (đủ lớn, vẫn kiểm soát được)

| Layer | Ước lượng | Cách tính |
|---|---:|---|
| FACT_TRADE VN_REPORTED | ≤ ~18,100 dòng | 14 HS6 × 6 partner (5+World) × 2 flow × 108 tháng |
| FACT_TRADE PARTNER_MIRROR | ~15,100 dòng | 14 × 5 × 2 × 108 (một phần kỳ sẽ null vì thiếu như 2024 — chính là nội dung phân tích) |
| FACT_TARIFF_RATE | ~vài trăm dòng | 14 HS6 × 6 partner × 2 loại × số năm có dữ liệu |
| FACT_MACRO_INDICATOR | ~60 dòng | 5–6 indicator × 10 năm |
| Số request extract | **~12–16 request** (khi có key) | Comtrade cho phép nhiều period (`201501:202312`) và nhiều cmdCode trong một query; preview cap 50 records/query nên **bắt buộc API key cho bước extract tuần 2** |

Quy mô ~35k dòng fact: vượt xa tầm đồ án môn học 3 tín chỉ (thường vài trăm dòng), nhưng vừa sức 2 người trong 13 tuần vì mọi luật grain/lock đã chốt ở đây.

---

## 5. Lược đồ sao chốt (grain + luật)

**Grain FACT_TRADE:** `tháng × partner (góc nhìn VN) × HS6 × flow × reporting_perspective` — 1 dòng = một trị giá khai báo.

| Bảng | Vai trò |
|---|---|
| DIM_DATE | date_key YYYYMM → năm/quý/tháng; macro **không** nằm ở đây |
| DIM_PARTNER | partner_key, tên, code Comtrade, `is_aggregate` (World), nhóm khu vực |
| DIM_COMMODITY | hs6, tên, `commodity_group`, HS4/HS2 cha (rollup) |
| DIM_FLOW | X/M + mô tả theo góc nhìn VN |
| DIM_PERSPECTIVE | VN_REPORTED / PARTNER_MIRROR (+ mô tả độ tin cậy) |
| DIM_INDICATOR | cho vĩ mô |
| FACT_TRADE | measures: `primary_value_usd`, `net_wgt` (nullable, chỉ tham khảo), `qty`; audit: source, batch_id, fetched_at |
| FACT_TARIFF_RATE | grain: năm × reporter(=VN) × partner × HS6 × tariff_type; measure `ad_valorem_pct` |
| FACT_MACRO_INDICATOR | grain: thời gian × indicator × quốc gia |
| VW_TRADE_RECONCILIATION | pivot 2 perspective cùng grain: `vn_value`, `mirror_value`, `abs_diff`, `pct_diff_vs_vn`, `discrepancy_level` (LOW ≤10% / MODERATE ≤30% / HIGH >30% / MISSING_VN_REPORTED / MISSING_MIRROR), `reconciliation_note` |

**Luật khóa (không đổi khi triển khai):** `motCode=0`, `customsCode=C00`, `partner2Code=0`; HS6 thuần, không trộn HS4; mirror không thay thế số chính thức; chỉ tiêu tổng luôn filter rõ perspective; World aggregate không cộng vào xếp hạng partner.

---

## 6. Dashboard chốt

| # | Trang | Nội dung | Thuộc phạm vi |
|---|---|---|---|
| D1 | Tổng quan XNK | trend tháng/năm, YoY, switch perspective, slicer partner/HS6/flow | **Chính** |
| D2 | Thị trường & mặt hàng | share theo partner, top commodity, heatmap mùa vụ, độ tập trung (share top-3) | **Chính** |
| D3 | Đối chiếu dữ liệu (mirror reconciliation) | bảng diff % theo kỳ, cờ màu, biểu đồ VN vs mirror song song, danh sách kỳ MISSING_VN_REPORTED | **Chính — điểm mới** |
| D4 | Thuế quan & FTA (tariff gap) | MFN vs PREF theo HS6 × partner, chỉ hiện tổ hợp có dữ liệu | **Phụ/conditional** |
| D5 | Bối cảnh vĩ mô | GDP/tỷ giá đặt cạnh kim ngạch | Bổ trợ |

---

## 7. Điểm mới / điểm khác biệt (câu chữ trình GVHD)

> Điểm khác biệt của đề tài không nằm ở việc có thêm dashboard, mà ở chỗ kho dữ liệu được thiết kế với **hai reporting perspective song song (Việt Nam khai báo và mirror đối tác)** và **lớp reconciliation có gắn cờ chất lượng dữ liệu**. Nhờ đó dashboard không chỉ trả lời "kim ngạch bao nhiêu" mà còn trả lời "con số đó đáng tin đến đâu, kỳ nào Việt Nam chưa có dữ liệu và mirror nói gì" — đúng bài toán thực tế của dữ liệu Comtrade (đã chứng minh: 3/8 kỳ kiểm tra phía Việt Nam thiếu nhưng phía đối tác có dữ liệu, độ lệch phổ biến 0.25%–87%).

Ba lớp khác biệt so với đề tài XNK "đại trà":
1. **Thiết kế**: grain có `reporting_perspective` + fact/view reconciliation (thay vì chỉ một bảng fact trade).
2. **Quy trình**: scope chốt bằng Coverage Matrix + profile số liệu thật trước extract (tài liệu này + `scope_profile_results.md`), thể hiện đúng tư duy ETL "source-first".
3. **Phân tích**: cờ `discrepancy_level` trở thành một chỉ tiêu nghiệp vụ trên dashboard, không phải metadata ẩn.

---

## 8. Ngoài phạm vi (nói rõ để chống phình đề tài)

- Tỷ lệ tận dụng FTA thực tế, số liệu C/O, tờ khai hải quan doanh nghiệp.
- Dữ liệu vi mô: doanh nghiệp, lô hàng, vận tải, giá chi tiết.
- Forecasting/ML, phát hiện bất thường tự động (chỉ để ngỏ 1 slide "hướng phát triển").
- Toàn bộ HS chapters, toàn bộ partner (chỉ 14 HS6 × 5+1 partner).
- Cập nhật near-real-time, pipeline tự động chạy lịch.
- Lakehouse/Delta/Iceberg — không thuộc trọng tâm môn Kho dữ liệu.
- Xuất khẩu/ nhập khẩu của nước thứ hai bất kỳ ngoài cặp (VN ↔ partner).

---

## 9. Rủi ro và phương án

| Rủi ro | Mức | Giảm thiểu (đã thiết kế) |
|---|---|---|
| Preview cap 50 records/query | **Cao, chặn ở bước extract** | Đăng ký API key trước tuần 2; script đã tự đọc `.env` (đã vá), tự chuyển endpoint `data/v1/get` khi có key |
| Comtrade rate limit 429 khi gọi nhiều | Trung | sleep 2.2s + retry backoff trong mọi script; batch theo năm |
| WITS sparse/timeout | Trung | tariff là phụ/conditional; chỉ extract tổ hợp đã xác nhận; cache raw |
| 2024 VN thiếu dữ liệu | Đã xảy ra (bằng chứng count=0) | thiết kế partial + mirror fallback — biến rủi ro thành nội dung phân tích |
| Case chênh mirror quá lớn bị hiểu nhầm "dữ liệu sai" | Trung | mọi trang D3 có note FOB/CIF + `reconciliation_note` |
| Trộn perspective khi tính tổng | Trung | luật khóa ở §5 + view reconciliation; kiểm tra luật ở nhiệm vụ kế tiếp |
| Chiếm dụng thời gian tuần 2–4 (ETL/SSAS) | Cao | grain + schema đã chốt tại đây, transform chỉ còn là việc cơ giới hóa |

## 10. Câu hỏi cần GVHD xác nhận (kèm khuyến nghị của nhóm)

1. **Năm 2024 chỉ đưa vào ở mức partial + mirror minh họa** — đồng ý không? *(Khuyến nghị: đồng ý, vì Comtrade chưa có VN annual 2024.)*
2. **14 mã HS6, 5 partner lõi + World** là vừa tầm 5 tín chỉ? *(Khuyến nghị: giữ nguyên; đồng ý giảm nếu GVHD muốn gọn hơn.)*
3. Nhận **mirror + reconciliation làm điểm mới trung tâm** thay vì phân tích FTA — GVHD xác nhận hướng? *(Khuyến nghị: có — đã chứng minh được bằng dữ liệu.)*
4. Công cụ triển khai: **SQL Server + SSIS + SSAS (cube) + Power BI trình bày** — đúng yêu cầu môn học chưa, hay GVHD chỉ yêu cầu tới SSAS? *(Khuyến nghị: giữ cả hai nếu được.)*

## 11. Ghi chú phản hồi của GVHD

| Ngày | Nội dung GVHD yêu cầu thay đổi | Đã cập nhật mục nào |
|---|---|---|
| (điền sau khi gặp GVHD) | | |

---

## 12. Checklist hoàn thành Nhiệm vụ 6

- [ ] Chạy `python scripts/profiling/scope_validation_profile.py` trên máy local — kỳ vọng: 14/14 KEEP, gap check 2024 = `VAN_CHUA_CO`.
- [ ] So bảng §3.3 với kết quả local; nếu mã nào local ra `REPLACE_OR_DROP` (khác workspace), dùng phương án thay thế §3.3 và ghi chú.
- [ ] Hai thành viên đọc toàn bộ tài liệu, đồng thuận §8 (ngoài phạm vi).
- [ ] Mang §2 + §3 + §6 + §7 + §10 gặp GVHD; ghi phản hồi vào §11.
- [ ] Commit + push tài liệu này + script + `results/week1/scope_profile_results.*`.

## 13. Commit

```bash
git add scripts/profiling/scope_validation_profile.py docs/06_NhiemVu6_ChotPhamViDeTai.md
git add results/week1/scope_profile_results.md results/week1/scope_profile_results.csv results/week1/scope_profile_results.json
git commit -m "add week1 scope validation profile and finalized scope doc"
git push
```
