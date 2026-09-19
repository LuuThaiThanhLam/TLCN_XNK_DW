# SCOPE VALIDATION PROFILE — TUẦN 1 (NHIỆM VỤ 6)

Mục đích: xác nhận từng HS6 ứng viên có số liệu thật (VN-reported, đối tác World, năm 2022-2023) trước khi chốt phạm vi.

## 1. Bảng kết quả

| HS6 | Nhóm hàng | Chiều | Kim ngạch 2022 (USD) | Kim ngạch 2023 (USD) | Comtrade mô tả | Tên khớp | Quyết định |
|---|---|---|---:|---:|---|---|---|
| 090111 | Cà phê nhân xanh | EXPORT | 2,822,756,074.49 | 2,977,954,667.30 | Coffee; not roasted or decaffeinated | TRUNG_KHOP | KEEP |
| 100630 | Gạo xát/xay | EXPORT | 2,917,660,366.35 | 4,060,727,367.80 | Cereals; rice, semi-milled or wholly milled, whether or not  | TRUNG_KHOP | KEEP |
| 080132 | Hạt điều đã chế biến | EXPORT | 2,512,621,083.23 | 2,916,825,905.16 | Nuts, edible; cashew nuts, fresh or dried, shelled | TRUNG_KHOP | KEEP |
| 090411 | Hồ tiêu chưa xay | EXPORT | 710,828,275.63 | 683,211,712.93 | Spices; pepper (of the genus piper), neither crushed nor gro | TRUNG_KHOP | KEEP |
| 610910 | Áo thun cotton (knit) | EXPORT | 1,535,067,559.48 | 1,401,669,879.95 | T-shirts, singlets and other vests; of cotton, knitted or cr | TRUNG_KHOP | KEEP |
| 640399 | Giày da các loại | EXPORT | 4,745,371,652.35 | 4,991,396,908.06 | Footwear; n.e.c. in heading no. 6403, (not covering the ankl | TRUNG_KHOP | KEEP |
| 851713 | Điện thoại thông minh | EXPORT | 33,335,762,793.83 | 26,460,317,776.13 | Telephone sets; smartphones for cellular or other wireless n | TRUNG_KHOP | KEEP |
| 854442 | Dây điện có đầu nối | EXPORT | 2,109,778,071.31 | 2,062,142,409.28 | Insulated electric conductors; for a voltage not exceeding 1 | TRUNG_KHOP | KEEP |
| 851762 | Thiết bị truyền dẫn dữ liệu | IMPORT | 978,371,029.53 | 841,528,134.71 | Communication apparatus (excluding telephone sets or base st | TRUNG_KHOP | KEEP |
| 854231 | Vi mạch xử lý (IC) | IMPORT | 19,198,456,061.53 | 17,797,673,473.56 | Electronic integrated circuits; processors and controllers,  | TRUNG_KHOP | KEEP |
| 847330 | Linh kiện máy vi tính | IMPORT | 1,295,641,754.31 | 928,122,689.03 | Machinery; parts and accessories (other than covers, carryin | TRUNG_KHOP | KEEP |
| 721049 | Thép cán dẹt mạ kẽm | IMPORT | 155,021,516.99 | 137,743,539.00 | Iron or non-alloy steel; flat-rolled, width 600mm or more, ( | TRUNG_KHOP | KEEP |
| 540761 | Vải sợi tổng hợp | IMPORT | 461,686,493.47 | 484,289,054.31 | Fabrics, woven; containing 85% or more by weight of non-text | TRUNG_KHOP | KEEP |
| 390120 | Polyethylene dạng thô | IMPORT | 1,015,224,910.33 | 827,368,947.42 | Ethylene polymers; in primary forms, polyethylene having a s | TRUNG_KHOP | KEEP |

## 2. Tổng kết

- Đủ điều kiện giữ (KEEP): 14
- Giữ nhưng có cờ thiếu năm gần (KEEP_FLAG_RECENT_GAP): 0
- Cần thay/loại (REPLACE_OR_DROP): 0
- Lỗi API (API_ERROR) — chạy lại trước khi kết luận: 0

Quy tắc: KEEP = có dữ liệu 2023; KEEP_FLAG_RECENT_GAP = có 2022 nhưng 2023 trống; REPLACE_OR_DROP = cả hai năm trống.

## 3. Gap check năm 2024

- VN export TOTAL sang World, năm 2024: count=0, value=-, trạng thái=VAN_CHUA_CO
- Ý nghĩa: xác nhận dữ liệu năm 2024 phía Việt Nam trên Comtrade chưa cập nhật đầy đủ. Phạm vi 2024 chỉ nên là phụ/partial.

## 4. Việc tiếp theo

- Điền cột Quyết định vào bảng mục 3.3 của `docs/06_NhiemVu6_ChotPhamViDeTai.md`.
- Các mã REPLACE_OR_DROP: chọn mã thay thế trong danh sách phương án (030617, 720839, 640299, 441239) hoặc hỏi GVHD.