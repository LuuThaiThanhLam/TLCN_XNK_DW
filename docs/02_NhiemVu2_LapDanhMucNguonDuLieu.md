# NHIỆM VỤ 2 — LẬP DANH MỤC NGUỒN DỮ LIỆU

## 1. Mục tiêu

Nhiệm vụ 2 nhằm trả lời câu hỏi:

> Đề tài sẽ lấy dữ liệu từ đâu, lấy cái gì, bằng cách nào, lưu vào đâu, dùng để trả lời câu hỏi nào?

Ở nhiệm vụ này **chưa cần gọi API hàng loạt**. Mình chỉ lập bản đồ nguồn dữ liệu trước để tránh làm bừa.

---

## 2. Vì sao cần làm nhiệm vụ này?

Nếu bỏ qua bước này, nhóm rất dễ gặp lỗi:

- Thấy API nào cũng lấy, nhưng không biết dữ liệu đó dùng cho câu hỏi nào.
- Lấy dữ liệu xong mới phát hiện không có cột mình cần.
- Dùng nhầm nguồn để kết luận sai, ví dụ nói “tỷ lệ tận dụng FTA” dù không có dữ liệu C/O.
- Trộn dữ liệu chính với dữ liệu tham chiếu.
- Không biết dữ liệu lấy về sẽ vào staging table nào.

Nhiệm vụ này giống như lập “bản đồ nguyên liệu” trước khi nấu ăn.

---

## 3. Các nguồn dữ liệu chính

Đề tài hiện có 3 nguồn API chính và 3 nhóm bảng tham chiếu nội bộ.

## 3.1. Nguồn API chính

| Nguồn | Dùng để làm gì? | Bắt buộc không? |
|---|---|---|
| UN Comtrade | Kim ngạch, số lượng, trọng lượng, partner, flow, mã HS | Bắt buộc |
| WITS/UNCTAD TRAINS | Thuế MFN/PREF, tariff gap | Bắt buộc cho phần thuế, nhưng có thể giảm nếu coverage thưa |
| World Bank Indicators | GDP, tỷ giá, lạm phát, trade/GDP | Phụ trợ/bối cảnh |

## 3.2. Bảng tham chiếu nội bộ

| Bảng tham chiếu | Dùng để làm gì? |
|---|---|
| Partner selection | Chốt danh sách đối tác được phân tích |
| Commodity grouping | Phân nhóm HS6 thành ngành/nhóm mùa vụ |
| Trade agreement reference | Lưu bối cảnh FTA nếu làm bridge |

Lưu ý: các bảng tham chiếu này không phải dữ liệu giao dịch chính. Chúng chỉ giúp hệ thống quản lý phạm vi và hiển thị dashboard dễ hiểu hơn.

---

## 4. File cần hoàn thiện

File chính của nhiệm vụ 2 là:

```text
docs/01_Data_Source_Catalog.md
```

Trong workspace, file này đã được cập nhật bản đầy đủ.

---

## 5. Cách hiểu file `01_Data_Source_Catalog.md`

File này gồm các phần:

1. Nguyên tắc lập danh mục nguồn dữ liệu.
2. Bảng tổng quan nguồn dữ liệu.
3. Chi tiết nguồn UN Comtrade.
4. Chi tiết nguồn WITS/UNCTAD TRAINS.
5. Chi tiết nguồn World Bank Indicators.
6. Các bảng tham chiếu nội bộ.
7. Mapping nguồn → staging → fact/dimension.
8. Ma trận nguồn dữ liệu và câu hỏi nghiệp vụ.
9. Câu hỏi cần xác nhận với GVHD.
10. Checklist hoàn thành.

---

## 6. Những điều bắt buộc phải nhớ

## 6.1. Comtrade là nguồn chính cho trade

Comtrade dùng để trả lời:

- Việt Nam xuất/nhập bao nhiêu?
- Theo tháng/năm như thế nào?
- Theo đối tác nào?
- Theo mã hàng nào?
- Có mùa vụ không?
- Có rủi ro tập trung thị trường không?
- Số liệu VN-reported và mirror khác nhau ra sao?

Nhưng Comtrade **không** trả lời được:

- Doanh nghiệp nào xuất khẩu?
- Lô hàng nào dùng FTA?
- Tờ khai nào dùng C/O?

---

## 6.2. WITS là nguồn chính cho thuế

WITS dùng để trả lời:

- Thuế MFN là bao nhiêu?
- Thuế ưu đãi PREF là bao nhiêu?
- Chênh lệch MFN/PREF là bao nhiêu?
- Kim ngạch biến động thế nào trong bối cảnh thuế ưu đãi?

Nhưng WITS **không** trả lời được:

- Giao dịch thực tế có dùng FTA không?
- Tỷ lệ tận dụng FTA là bao nhiêu?

---

## 6.3. World Bank là nguồn bối cảnh vĩ mô

World Bank dùng để thêm bối cảnh:

- GDP.
- Tăng trưởng GDP.
- Lạm phát.
- Trade/GDP.
- Tỷ giá.

Nhưng World Bank không phải nguồn chính để tính kim ngạch XNK trong kho dữ liệu.

---

## 7. Kết quả cần có sau Nhiệm vụ 2

Sau nhiệm vụ 2, nhóm phải có thể nói rõ:

```text
Nguồn nào → lấy dữ liệu gì → endpoint nào → staging nào → fact/dimension nào → trả lời câu hỏi nào → rủi ro gì
```

Ví dụ:

```text
UN Comtrade → trade value, quantity, weight → STG_COMTRADE_TRADE → FACT_TRADE → phân tích kim ngạch/mùa vụ/rủi ro/mirror
```

```text
WITS → MFN/PREF tariff → STG_WITS_TARIFF → FACT_TARIFF_RATE → phân tích tariff gap
```

```text
World Bank → GDP/tỷ giá/lạm phát → STG_WORLD_BANK_INDICATOR → FACT_MACRO_INDICATOR → bối cảnh vĩ mô
```

---

## 8. Checklist hoàn thành nhiệm vụ 2

- [ ] Đã đọc file `docs/01_Data_Source_Catalog.md`.
- [ ] Hiểu Comtrade dùng cho trade, không dùng cho tỷ lệ tận dụng FTA.
- [ ] Hiểu WITS dùng cho tariff gap, không dùng cho tỷ lệ tận dụng FTA.
- [ ] Hiểu World Bank dùng cho bối cảnh vĩ mô.
- [ ] Hiểu bảng seed/reference chỉ là bảng tham chiếu nội bộ.
- [ ] Hiểu Comtrade phải khóa `motCode=0`, `customsCode=C00`, `partner2Code=0`.
- [ ] Hiểu fact trade lõi dùng HS6, không trộn HS4/HS6.
- [ ] Hiểu perspective do ETL tự gán, không dùng trực tiếp `isReported`.
- [ ] Có thể giải thích được mapping nguồn → staging → DW.

---

## 9. Việc cần làm trên GitHub/local

Sau khi cập nhật hoặc copy nội dung file `docs/01_Data_Source_Catalog.md`, commit lên GitHub:

```bash
git status
git add docs/01_Data_Source_Catalog.md docs/02_NhiemVu2_LapDanhMucNguonDuLieu.md
git commit -m "add data source catalog"
git push
```

Nếu chưa có file `docs/02_NhiemVu2_LapDanhMucNguonDuLieu.md` trên máy local, bạn có thể tạo file này hoặc chỉ commit `docs/01_Data_Source_Catalog.md` trước.

---

## 10. Bước tiếp theo

Sau khi nhiệm vụ 2 xong, chuyển sang:

> Nhiệm vụ 3 — Gọi thử API.

Nhiệm vụ 3 sẽ dùng catalog này để viết/chạy script smoke test cho Comtrade, WITS và World Bank.
