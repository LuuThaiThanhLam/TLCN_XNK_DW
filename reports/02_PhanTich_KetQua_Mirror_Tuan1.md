# PHÂN TÍCH KẾT QUẢ MIRROR CHECK — TUẦN 1

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Nguồn kết quả:** `results/week1/mirror_check_results.md`, `.csv`, `.json`  
**Ghi chú:** Nhóm chưa có Comtrade API key, nên kết quả hiện tại dùng `Comtrade public preview`. Đây là đủ cho kiểm tra khả thi, nhưng khi extract lớn cần API key hoặc giảm phạm vi.

---

## 1. Kết luận nhanh

Kết quả mirror check **đạt yêu cầu** cho Nhiệm vụ 4.

Script đã kiểm tra 8 case mẫu:

| Nhóm kết quả | Số case | Ý nghĩa |
|---|---:|---|
| Hai phía đều có dữ liệu | 5 | Có thể so sánh VN-reported và partner-mirror |
| LOW | 2 | Chênh lệch thấp, case khá ổn để demo reconciliation |
| MODERATE | 1 | Chênh lệch vừa, cần gắn cờ nhưng vẫn dùng được |
| HIGH | 2 | Chênh lệch cao, rất hữu ích để chứng minh cần reconciliation |
| MISSING_VN_REPORTED | 3 | Việt Nam thiếu dữ liệu kỳ 2024 nhưng partner mirror có dữ liệu |

Kết luận chính:

> Cơ chế dữ liệu mirror là khả thi và nên được giữ làm điểm khác biệt của đề tài. Kho dữ liệu cần lưu riêng `VN_REPORTED` và `PARTNER_MIRROR`, sau đó xây lớp reconciliation để so sánh, gắn cờ và giải thích chênh lệch.

---

## 2. Bảng kết quả đáng chú ý

| Case | Direction | VN value USD | Mirror value USD | Diff vs VN | Level |
|---|---|---:|---:|---:|---|
| Japan coffee 202301 | EXPORT | 10,127,757.60 | 16,784,397.26 | 65.73% | HIGH |
| Japan coffee 202401 | EXPORT | Không có | 35,660,719.50 | N/A | MISSING_VN_REPORTED |
| USA coffee 202301 | EXPORT | 20,201,618.07 | 37,790,801.00 | 87.07% | HIGH |
| Germany coffee 202301 | EXPORT | 41,199,796.46 | 38,271,554.95 | 7.11% | LOW |
| China network equipment 202301 | IMPORT | 29,869,079.44 | 29,945,226.00 | 0.25% | LOW |
| Korea integrated circuits 202301 | IMPORT | 252,083,766.17 | 217,401,413.00 | 13.76% | MODERATE |
| China network equipment 202401 | IMPORT | Không có | 62,727,085.00 | N/A | MISSING_VN_REPORTED |
| Korea integrated circuits 202401 | IMPORT | Không có | 412,589,570.00 | N/A | MISSING_VN_REPORTED |

---

## 3. Phân tích xuất khẩu

### 3.1. Cà phê sang Nhật — 202301

- Việt Nam báo cáo: `10,127,757.60 USD`
- Nhật mirror nhập khẩu từ Việt Nam: `16,784,397.26 USD`
- Chênh lệch: `65.73%`
- Mức: `HIGH`

Ý nghĩa:

> Có dữ liệu hai phía nhưng chênh lệch cao. Case này phù hợp để chứng minh rằng nếu chỉ dùng một nguồn thì dashboard có thể cho kết luận khác nhau; vì vậy cần lớp đối chiếu mirror.

### 3.2. Cà phê sang Nhật — 202401

- Việt Nam báo cáo: không có dữ liệu
- Nhật mirror: `35,660,719.50 USD`
- Mức: `MISSING_VN_REPORTED`

Ý nghĩa:

> Đây là bằng chứng rất mạnh cho khoảng trống dữ liệu năm gần đây. Mirror không thay thế dữ liệu Việt Nam, nhưng có thể dùng làm nguồn tham chiếu có gắn nhãn.

### 3.3. Cà phê sang Mỹ — 202301

- Việt Nam báo cáo: `20,201,618.07 USD`
- Mỹ mirror: `37,790,801.00 USD`
- Chênh lệch: `87.07%`
- Mức: `HIGH`

Ý nghĩa:

> Chênh lệch rất cao. Nếu chọn Mỹ/cà phê làm case dashboard, cần giải thích rõ FOB/CIF, timing và thống kê mirror.

### 3.4. Cà phê sang Đức — 202301

- Việt Nam báo cáo: `41,199,796.46 USD`
- Đức mirror: `38,271,554.95 USD`
- Chênh lệch: `7.11%`
- Mức: `LOW`

Ý nghĩa:

> Đây là case tốt để demo rằng có những dòng dữ liệu hai phía khá gần nhau. Có thể dùng làm ví dụ đối chiếu ít lệch.

---

## 4. Phân tích nhập khẩu

### 4.1. Việt Nam nhập thiết bị truyền dẫn dữ liệu từ Trung Quốc — 202301

- Việt Nam báo cáo: `29,869,079.44 USD`
- Trung Quốc mirror xuất khẩu sang Việt Nam: `29,945,226.00 USD`
- Chênh lệch: `0.25%`
- Mức: `LOW`

Ý nghĩa:

> Đây là case rất tốt để demo reconciliation vì hai phía gần như khớp.

### 4.2. Việt Nam nhập IC/bộ xử lý từ Hàn Quốc — 202301

- Việt Nam báo cáo: `252,083,766.17 USD`
- Hàn Quốc mirror: `217,401,413.00 USD`
- Chênh lệch: `13.76%`
- Mức: `MODERATE`

Ý nghĩa:

> Chênh lệch vừa phải, phù hợp làm ví dụ gắn cờ `MODERATE`.

### 4.3. Case nhập khẩu 202401

- Việt Nam báo cáo: không có dữ liệu
- Trung Quốc/Hàn Quốc mirror: có dữ liệu

Ý nghĩa:

> Một lần nữa xác nhận kỳ 2024 có thể thiếu dữ liệu phía Việt Nam nhưng đối tác vẫn có mirror. Đây là cơ sở để dashboard có tùy chọn xem dữ liệu theo perspective.

---

## 5. Hàm ý cho thiết kế Data Warehouse

### 5.1. Không được cộng trộn perspective

Sai:

```text
Tổng thương mại = VN_REPORTED + PARTNER_MIRROR
```

Đúng:

```text
Tổng thương mại theo perspective đã chọn
```

Ví dụ:

```text
WHERE reporting_perspective = 'VN_REPORTED'
```

hoặc:

```text
WHERE reporting_perspective = 'PARTNER_MIRROR'
```

### 5.2. FACT_TRADE cần có reporting perspective

`FACT_TRADE` nên có cột:

```text
reporting_perspective
```

Giá trị:

```text
VN_REPORTED
PARTNER_MIRROR
```

### 5.3. Cần bảng/view reconciliation

Nên có bảng hoặc view:

```text
FACT_TRADE_RECONCILIATION
```

Các cột nên có:

| Cột | Ý nghĩa |
|---|---|
| `date_key` | Tháng/năm |
| `partner_key` | Đối tác chuẩn hóa theo góc nhìn Việt Nam |
| `commodity_key` | Mã HS6 |
| `flow_key` | Export/Import theo góc nhìn Việt Nam |
| `vn_reported_value_usd` | Trị giá Việt Nam báo cáo |
| `mirror_value_usd` | Trị giá mirror |
| `abs_diff_value_usd` | Chênh lệch tuyệt đối |
| `pct_diff_vs_vn` | Chênh lệch % so với VN-reported |
| `discrepancy_level` | LOW/MODERATE/HIGH/MISSING... |
| `reconciliation_note` | Ghi chú diễn giải |

---

## 6. Câu đưa vào báo cáo khả thi dữ liệu

Có thể viết:

> Nhóm đã kiểm tra dữ liệu mirror trên UN Comtrade bằng cách so sánh các cặp truy vấn Việt Nam báo cáo và đối tác báo cáo. Kết quả cho thấy nhiều tổ hợp có dữ liệu ở cả hai phía, ví dụ Việt Nam nhập thiết bị truyền dẫn dữ liệu từ Trung Quốc tháng 01/2023 có chênh lệch chỉ 0.25%, trong khi một số tổ hợp xuất khẩu cà phê sang Nhật/Mỹ có chênh lệch cao. Đồng thời, một số kỳ năm 2024 thiếu dữ liệu phía Việt Nam nhưng có dữ liệu mirror từ đối tác. Do đó, đề tài cần thiết kế kho dữ liệu theo hướng lưu riêng từng reporting perspective và xây lớp reconciliation để gắn cờ mức chênh lệch, thay vì cộng trộn hoặc thay thế dữ liệu một cách trực tiếp.

---

## 7. Kết luận

Nhiệm vụ 4 đã chứng minh được ba điểm quan trọng:

1. Mirror data có tồn tại và gọi được qua API.
2. Có chênh lệch thực tế giữa VN-reported và partner-mirror.
3. Có tình huống Việt Nam thiếu dữ liệu kỳ gần đây nhưng mirror có dữ liệu.

Vì vậy, hướng thiết kế **Mirror-Reconciled Trade Data Warehouse** là có cơ sở dữ liệu thực tế, phù hợp để làm điểm khác biệt của đề tài.
