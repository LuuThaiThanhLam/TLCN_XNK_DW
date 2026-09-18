# PHÂN TÍCH COVERAGE MATRIX — TUẦN 1

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Nguồn kết quả:** `results/week1/Coverage_Matrix.md`, `.csv`, `.json`  
**Input:** `api_smoke_test_results.csv`, `mirror_check_results.csv`

---

## 1. Kết luận nhanh

Coverage Matrix cho thấy đề tài **đủ cơ sở dữ liệu để tiếp tục**, với trọng tâm nên đặt vào:

```text
Trade analytics + Mirror reconciliation
```

Phần WITS/tariff vẫn có thể giữ, nhưng nên xem là phạm vi phụ hoặc có điều kiện vì dữ liệu thuế thưa theo partner/HS/year.

---

## 2. Những gì đã chứng minh được

| Nhóm dữ liệu | Kết luận |
|---|---|
| Comtrade trade | Có dữ liệu trade theo annual và monthly |
| Comtrade mirror | Có dữ liệu hai phía để đối chiếu; có case thấp/vừa/cao |
| Comtrade 2024 | Có dấu hiệu thiếu VN-reported nhưng partner mirror có dữ liệu |
| WITS tariff | Có MFN/PREF ở một số tổ hợp; thiếu ở chiều khác |
| World Bank macro | Có GDP, tỷ giá năm và tỷ giá tháng candidate |

---

## 3. Phạm vi nên ưu tiên

### 3.1. Dashboard chính

Nên ưu tiên ba nhóm dashboard:

1. **Trade overview**  
   Kim ngạch xuất nhập khẩu theo thời gian, đối tác, nhóm hàng.

2. **Partner/commodity analysis**  
   Phân tích nhóm hàng HS6 và thị trường trọng điểm.

3. **Mirror reconciliation**  
   So sánh `VN_REPORTED` và `PARTNER_MIRROR`, hiển thị `LOW`, `MODERATE`, `HIGH`, `MISSING_VN_REPORTED`.

### 3.2. Dashboard phụ

Có thể làm:

```text
Tariff gap MFN/PREF
```

Nhưng chỉ nên làm cho các tổ hợp WITS đã xác nhận có dữ liệu. Không nên biến tariff thành trục chính nếu coverage chưa đủ.

---

## 4. Khuyến nghị scope sơ bộ

| Thành phần | Khuyến nghị |
|---|---|
| Thời gian lõi | 2015–2023 |
| Năm 2024 | Optional/partial, dùng để minh họa gap/mirror nếu coverage đủ |
| Đối tác lõi ban đầu | Japan, United States, Germany, China, Rep. of Korea |
| HS6 đã có bằng chứng | 090111, 851762, 854231 |
| Phần mở rộng | Top 10 partner và 10–15 HS6 sau profiling thêm |
| Không làm | Không phân tích tỷ lệ tận dụng FTA thực tế do thiếu C/O/tờ khai |

---

## 5. Quyết định thiết kế quan trọng

### 5.1. FACT_TRADE

`FACT_TRADE` cần có:

```text
reporting_perspective
```

Giá trị:

```text
VN_REPORTED
PARTNER_MIRROR
```

### 5.2. FACT_TRADE_RECONCILIATION hoặc view reconciliation

Nên có bảng/view:

```text
FACT_TRADE_RECONCILIATION
```

Các chỉ tiêu chính:

```text
vn_reported_value_usd
mirror_value_usd
abs_diff_value_usd
pct_diff_vs_vn
discrepancy_level
reconciliation_note
```

### 5.3. FACT_MACRO_INDICATOR

Dữ liệu GDP/tỷ giá/lạm phát nằm ở:

```text
FACT_MACRO_INDICATOR
```

Không đưa chỉ số vĩ mô vào `DIM_DATE`.

### 5.4. FACT_TARIFF_RATE

WITS nên đi vào:

```text
FACT_TARIFF_RATE
```

Chỉ tính `tariff_gap = MFN - PREF` khi có đủ cả MFN và PREF đúng chiều.

---

## 6. Câu đưa vào báo cáo khả thi dữ liệu

Có thể viết:

> Dựa trên kết quả gọi thử API và kiểm tra dữ liệu mirror, nhóm lập Coverage Matrix để đánh giá mức độ sẵn có của dữ liệu theo nguồn và theo tổ hợp phân tích. Kết quả cho thấy UN Comtrade có dữ liệu trade theo tháng và có thể dùng để đối chiếu giữa Việt Nam báo cáo và dữ liệu mirror của đối tác. Một số tổ hợp năm 2024 thiếu dữ liệu phía Việt Nam nhưng có dữ liệu mirror, giúp củng cố nhu cầu thiết kế reporting perspective và reconciliation layer. World Bank có dữ liệu vĩ mô đủ dùng làm bối cảnh phân tích. WITS/UNCTAD TRAINS có dữ liệu MFN/PREF ở một số tổ hợp nhưng còn rủi ro coverage, vì vậy phần tariff gap nên được triển khai có điều kiện theo các tổ hợp đã xác nhận có dữ liệu.

---

## 7. Kết luận

Nhiệm vụ 5 hoàn thành khi nhóm có:

- `Coverage_Matrix.csv`
- `Coverage_Matrix.md`
- Khuyến nghị scope sơ bộ
- Căn cứ để bước sang Nhiệm vụ 6 — Chốt phạm vi đề tài

Kết luận cuối:

> Đề tài khả thi nếu lấy trade/mirror reconciliation làm lõi, macro làm bối cảnh, và tariff gap làm phân tích bổ trợ có kiểm soát.
