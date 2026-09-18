# PHÂN TÍCH KẾT QUẢ API SMOKE TEST — TUẦN 1

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Nguồn kết quả:** `results/week1/api_smoke_test_results.md`, `.csv`, `.json`  
**Ghi chú:** Nhóm chưa có Comtrade API key, nên Comtrade đang chạy bằng public preview. Điều này vẫn hợp lệ cho smoke test, nhưng khi extract dữ liệu lớn cần đăng ký key hoặc giảm phạm vi.

---

## 1. Kết luận nhanh

Kết quả smoke test **đạt yêu cầu để chuyển sang bước profiling/coverage**.

| Nhóm nguồn | Kết quả | Kết luận |
|---|---|---|
| UN Comtrade | 4/4 test gọi được; 3 test có dữ liệu, 1 test count = 0 cho VN 2024 | Dùng được cho trade, monthly và mirror; xác nhận có khoảng trống VN-reported 2024 |
| WITS/UNCTAD TRAINS | 2/3 test có dữ liệu, 1 test NoRecordsFound | Dùng được nhưng coverage thưa; cần profiling thêm theo partner/HS/year |
| World Bank | 3/3 test có dữ liệu | Dùng được cho vĩ mô; tỷ giá tháng ứng viên có 12 tháng năm 2024 |

---

## 2. Phân tích chi tiết UN Comtrade

### 2.1. VN export TOTAL to World 2023

Kết quả:

- Status: 200
- Count: 1
- Value: `353,077,513,296.001 USD`
- Flow: Export
- Reporter: Viet Nam
- Partner: World
- `motCode = 0`, `customsCode = C00`

**Ý nghĩa:** Comtrade có dữ liệu xuất khẩu tổng của Việt Nam năm 2023. Việc khóa `motCode=0` và `customsCode=C00` giúp tránh lấy trùng dòng tổng và dòng chi tiết theo phương thức vận tải/chế độ hải quan.

### 2.2. VN export TOTAL to World 2024

Kết quả:

- Status: 200
- Count: 0

**Ý nghĩa:** API gọi được nhưng không có dữ liệu cho tổ hợp Việt Nam báo cáo xuất khẩu năm 2024. Đây là bằng chứng ban đầu cho rủi ro/khoảng trống dữ liệu VN-reported ở năm gần đây.

**Kết luận thiết kế:** Cần giữ `PARTNER_MIRROR` và `FACT_TRADE_RECONCILIATION` để xử lý/đánh dấu khoảng trống này. Không được âm thầm thay thế dữ liệu chính thức bằng mirror.

### 2.3. VN export HS090111 to Japan 2023M01

Kết quả:

- Status: 200
- Count: 1
- Value: `10,127,757.599 USD`
- Quantity/net weight: `5,024,600 kg`
- Flow: Export
- Period: 202301

**Ý nghĩa:** Dữ liệu tháng có tồn tại. Có thể xây dashboard mùa vụ nếu coverage theo các tháng/năm khác đủ.

### 2.4. Japan import HS090111 from VN 2024M01 — mirror

Kết quả:

- Status: 200
- Count: 1
- Value: `35,660,719.503 USD`
- Quantity/net weight: `13,296,000 kg`
- Reporter: Japan
- Partner: Viet Nam
- Flow: Import

**Ý nghĩa:** Dữ liệu mirror có tồn tại cho năm 2024 khi VN-reported có thể thiếu. Đây là bằng chứng ban đầu hỗ trợ điểm mới **Mirror-Reconciled Trade Data Warehouse**.

---

## 3. Phân tích WITS/UNCTAD TRAINS

### 3.1. VN tariff on World HS090111 2018 — MFN baseline

Kết quả:

- Status: 200
- Count: 1
- Tariff type: MFN
- OBS_VALUE: `15`
- Measure: SimpleAverage

**Ý nghĩa:** Có dữ liệu MFN baseline cho Việt Nam áp thuế lên hàng HS090111 từ World năm 2018.

### 3.2. VN tariff on Japan-origin goods HS090111 2018 — PREF

Kết quả:

- Status: 200
- Count: 1
- Tariff type: PREF
- OBS_VALUE: `8`
- Measure: SimpleAverage

**Ý nghĩa:** Có dữ liệu thuế ưu đãi cho hàng HS090111 xuất xứ Nhật vào Việt Nam năm 2018.

Có thể tính ví dụ:

```text
Tariff gap = MFN - PREF = 15 - 8 = 7 điểm phần trăm
```

**Lưu ý:** Đây là phân tích lợi thế thuế quan, không phải tỷ lệ tận dụng FTA thực tế.

### 3.3. Japan tariff on Vietnam-origin goods HS090111 2018

Kết quả:

- Status: 404
- Note: NoRecordsFound

**Ý nghĩa:** Tổ hợp Nhật áp thuế lên cà phê HS090111 xuất xứ Việt Nam năm 2018 không có record trong WITS với endpoint này. Đây không phải lỗi code; đây là vấn đề coverage dữ liệu.

**Cần làm tiếp:** Không loại WITS ngay. Phải profiling thêm:

- Thử năm khác: 2015–2024 hoặc `year/all`.
- Thử mã HS khác.
- Thử đối tác khác.
- Thử MFN baseline của Nhật với partner `000`.

---

## 4. Phân tích World Bank

### 4.1. GDP current USD Vietnam 2024

Kết quả:

- GDP 2024: `476,324,572,783.807 USD`

**Ý nghĩa:** World Bank có dữ liệu GDP Việt Nam 2024, dùng được làm bối cảnh vĩ mô.

### 4.2. Official exchange rate annual Vietnam 2024

Kết quả:

- `PA.NUS.FCRF` năm 2024: `24,164.8858333333 VND/USD`

**Ý nghĩa:** Có tỷ giá chính thức bình quân năm.

### 4.3. Exchange rate monthly candidate 2024M01–2024M12

Kết quả:

- Count: 12
- Có dữ liệu đủ 12 tháng năm 2024
- Mẫu 2024M12: `25,418.7727272727 VND/USD`

**Ý nghĩa:** Có thể cân nhắc dùng chỉ tiêu tỷ giá tháng `DPANUSSPB` như dữ liệu bổ trợ nếu GVHD đồng ý. Tuy nhiên cần ghi rõ đây là monthly candidate, không nhét vào `DIM_DATE`; phải lưu ở `FACT_MACRO_INDICATOR`.

---

## 5. Những điều rút ra cho thiết kế đề tài

| Vấn đề | Kết luận thiết kế |
|---|---|
| Không có Comtrade API key | Smoke test vẫn OK bằng public preview; extract lớn cần đăng ký key hoặc giảm scope |
| VN 2024 count = 0 | Củng cố lý do cần mirror reconciliation |
| Monthly trade có dữ liệu | Có cơ sở làm dashboard mùa vụ |
| Mirror Japan 2024 có dữ liệu | Có cơ sở làm điểm mới mirror-reconciled DW |
| WITS có MFN/PREF cho chiều VN nhập | Dashboard tariff có thể làm được với các tổ hợp có coverage |
| WITS thiếu chiều Japan import from VN | Cần profiling coverage trước khi chọn partner/HS |
| World Bank ổn | Dùng được cho `FACT_MACRO_INDICATOR` |
| Tỷ giá tháng có dữ liệu | Có thể dùng nếu GVHD đồng ý và ghi rõ định nghĩa |

---

## 6. Việc cần làm tiếp theo

Sau smoke test, bước tiếp theo không phải extract toàn bộ ngay. Cần làm **coverage profiling**:

1. Chọn danh sách partner ứng viên: Japan, United States, China, Korea, Germany, Thailand, Singapore, Netherlands, India, Australia...
2. Chọn danh sách HS6 ứng viên: cà phê, gạo, thủy sản, dệt may, giày dép, gỗ, điện tử...
3. Gọi thử theo ma trận nhỏ partner × HS6 × năm/tháng.
4. Ghi `Có/Không` cho Comtrade VN-reported, Comtrade mirror, WITS MFN, WITS PREF.
5. Từ coverage đó mới chốt scope chính thức.

---

## 7. Kết luận đưa vào báo cáo tuần 1

Có thể viết ngắn gọn:

> Nhóm đã kiểm chứng ba nguồn API chính. UN Comtrade public preview trả dữ liệu xuất khẩu Việt Nam năm 2023, dữ liệu tháng cho mã HS090111 sang Nhật và dữ liệu mirror từ Nhật năm 2024. Truy vấn Việt Nam báo cáo năm 2024 trả về 0 dòng, cho thấy tồn tại khoảng trống dữ liệu và củng cố nhu cầu thiết kế cơ chế đối chiếu dữ liệu gương. WITS/UNCTAD TRAINS trả dữ liệu MFN và PREF cho chiều Việt Nam áp thuế lên hàng Nhật, nhưng thiếu một số tổ hợp theo chiều ngược, do đó cần profiling coverage trước khi chốt mã HS/đối tác. World Bank Indicators trả dữ liệu GDP, tỷ giá năm và tỷ giá tháng ứng viên cho Việt Nam năm 2024, có thể dùng làm dữ liệu bối cảnh vĩ mô.
