# BÁO CÁO KHẢ THI DỮ LIỆU — TUẦN 1

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Nhóm:** Nguyễn Khắc Dương — Lưu Thái Thanh Lâm  
**Tuần:** 1  
**Ngày cập nhật:** ....../....../2026

---

## 1. Mục tiêu kiểm chứng

Tuần 1 không nhằm xây kho dữ liệu ngay, mà nhằm trả lời 4 câu hỏi:

1. Các API chính có gọi được không?
2. Dữ liệu có đủ để trả lời các câu hỏi nghiệp vụ không?
3. Phạm vi đối tác/mã HS/năm nào là khả thi?
4. Rủi ro dữ liệu lớn nhất là gì và cần giảm phạm vi ra sao?

---

## 2. Nguồn dữ liệu kiểm chứng

| Nguồn | Mục đích | Trạng thái | Ghi chú |
|---|---|---|---|
| UN Comtrade | Kim ngạch, số lượng, trọng lượng theo tháng/năm | Chưa/Kết quả |  |
| WITS/UNCTAD TRAINS | Thuế MFN/PREF | Chưa/Kết quả |  |
| World Bank Indicators | GDP, tỷ giá, lạm phát, thương mại/GDP | Chưa/Kết quả |  |

---

## 3. Kết quả smoke test API

Đính kèm/chèn kết quả từ:

- `results/api_smoke_test_results.md`
- `results/api_smoke_test_results.csv`
- Screenshot nếu chạy trên trình duyệt/Postman

| Test | Kết quả | Nhận xét |
|---|---|---|
| Comtrade VN annual 2023 |  |  |
| Comtrade VN annual 2024 |  |  |
| Comtrade monthly VN → Japan |  |  |
| Comtrade mirror Japan ← VN |  |  |
| WITS MFN |  |  |
| WITS PREF |  |  |
| World Bank GDP |  |  |
| World Bank tỷ giá năm/tháng |  |  |

---

## 4. Ma trận coverage sơ bộ

| Partner | Mã nước | HS6 | Comtrade VN-reported | Comtrade mirror | WITS MFN | WITS PREF | Ghi chú |
|---|---:|---|---|---|---|---|---|
| Japan | 392 | 090111 | Có/Không | Có/Không | Có/Không | Có/Không |  |
| United States | 842 | ... |  |  |  |  |  |
| China | 156 | ... |  |  |  |  |  |
| Korea | 410 | ... |  |  |  |  |  |

---

## 5. Câu hỏi nghiệp vụ có/không trả lời được

| Câu hỏi | Trả lời được? | Nguồn dữ liệu | Ghi chú giới hạn |
|---|---|---|---|
| Kim ngạch theo tháng/năm/đối tác/HS | Có/Không/Một phần | Comtrade |  |
| Mùa vụ nhóm hàng | Có/Không/Một phần | Comtrade monthly |  |
| Rủi ro tập trung thị trường | Có/Không/Một phần | Comtrade |  |
| Tariff gap MFN/PREF | Có/Không/Một phần | WITS |  |
| Tỷ lệ tận dụng FTA thực tế | Không | Cần C/O/tờ khai | Ngoài phạm vi |
| Đối chiếu VN-reported và mirror | Có/Không/Một phần | Comtrade |  |

---

## 6. Phạm vi đề xuất sau tuần 1

| Thành phần | Đề xuất |
|---|---|
| Giai đoạn lõi | 2015–2024 |
| 2025 | Dùng/Không dùng/Dùng với cờ partial |
| Đối tác | Top ... đối tác: ... |
| Mã HS6 | ... mã: ... |
| Dashboard chính | ... |
| Dashboard phụ/mở rộng | ... |

---

## 7. Rủi ro và phương án xử lý

| Rủi ro | Mức độ | Cách xử lý |
|---|---|---|
| API rate limit | Cao/Trung bình/Thấp | Retry, sleep, API key, giảm scope |
| WITS thiếu dữ liệu |  | Chọn HS có coverage tốt |
| 2025 chưa đủ dữ liệu |  | Gắn cờ partial hoặc loại khỏi phân tích chính |
| Double counting Comtrade mode/customs |  | Khóa `motCode=0`, `customsCode=C00`, `partner2Code=0` |
| Nhầm chiều tariff |  | Test case xuất/nhập riêng |

---

## 8. Kết luận tuần 1

- Nguồn dữ liệu nào dùng được: ...
- Nguồn nào có rủi ro: ...
- Phạm vi nên chốt với GVHD: ...
- Việc cần làm ở tuần 2: ...
