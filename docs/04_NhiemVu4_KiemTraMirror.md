# NHIỆM VỤ 4 — KIỂM TRA DỮ LIỆU MIRROR

## 1. Mục tiêu

Nhiệm vụ 4 dùng để kiểm tra kỹ hơn điểm mới của đề tài:

> Kho dữ liệu không chỉ lấy dữ liệu Việt Nam tự báo cáo, mà còn lưu dữ liệu mirror do đối tác thương mại báo cáo để đối chiếu, phát hiện thiếu dữ liệu và gắn cờ chênh lệch.

Ở nhiệm vụ này, nhóm **chưa extract dữ liệu lớn**. Nhóm chỉ gọi một số tổ hợp mẫu để kiểm tra:

- Việt Nam báo cáo có dữ liệu không?
- Đối tác báo cáo mirror có dữ liệu không?
- Hai phía chênh nhau nhiều hay ít?
- Năm/tháng gần đây có bị thiếu phía Việt Nam không?
- Có đủ cơ sở thiết kế `reporting_perspective` và bảng reconciliation không?

---

## 2. Mirror data là gì?

Ví dụ chiều xuất khẩu:

| Góc nhìn | Query Comtrade | Ý nghĩa |
|---|---|---|
| VN_REPORTED_EXPORT | Reporter = Viet Nam, Flow = Export, Partner = Japan | Việt Nam báo cáo xuất khẩu sang Nhật |
| PARTNER_MIRROR_IMPORT | Reporter = Japan, Flow = Import, Partner = Viet Nam | Nhật báo cáo nhập khẩu từ Việt Nam |

Hai con số này **không nhất thiết bằng nhau**.

Lý do thường gặp:

- Xuất khẩu thường ghi theo FOB, nhập khẩu thường ghi theo CIF.
- Thời điểm ghi nhận khác nhau.
- Phân loại HS khác nhau.
- Độ trễ cập nhật dữ liệu khác nhau.
- Sai khác phương pháp thống kê giữa hai nước.

Vì vậy, mục tiêu không phải chứng minh ai đúng ai sai, mà là thiết kế kho dữ liệu có khả năng:

```text
Lưu cả hai perspective → so sánh → gắn cờ → giải thích cho dashboard
```

---

## 3. Script dùng cho nhiệm vụ 4

File script:

```text
scripts/profiling/mirror_check.py
```

Script này sẽ:

1. Gọi UN Comtrade monthly cho phía Việt Nam báo cáo.
2. Gọi UN Comtrade monthly cho phía partner mirror.
3. So sánh trị giá `primaryValue`.
4. Tính chênh lệch tuyệt đối.
5. Tính phần trăm chênh lệch so với VN-reported.
6. Gắn nhãn mức chênh lệch.
7. Lưu kết quả vào `results/week1/`.
8. Lưu raw response vào `data/raw/week1_mirror_check/`.

---

## 4. Các case test trong script

Script đang test 8 case mẫu:

| # | Direction | Partner | HS6 | Period | Mục đích |
|---:|---|---|---:|---:|---|
| 1 | EXPORT | Japan | 090111 | 202301 | VN xuất cà phê sang Nhật, kỳ có dữ liệu hai phía |
| 2 | EXPORT | Japan | 090111 | 202401 | Kiểm tra năm gần đây, kỳ có khả năng thiếu VN-reported |
| 3 | EXPORT | United States | 090111 | 202301 | VN xuất cà phê sang Mỹ |
| 4 | EXPORT | Germany | 090111 | 202301 | VN xuất cà phê sang Đức |
| 5 | IMPORT | China | 851762 | 202301 | VN nhập thiết bị truyền dẫn dữ liệu từ Trung Quốc |
| 6 | IMPORT | Rep. of Korea | 854231 | 202301 | VN nhập IC/bộ xử lý từ Hàn Quốc |
| 7 | IMPORT | China | 851762 | 202401 | Kiểm tra mirror năm gần đây cho nhập khẩu từ Trung Quốc |
| 8 | IMPORT | Rep. of Korea | 854231 | 202401 | Kiểm tra mirror năm gần đây cho nhập khẩu từ Hàn Quốc |

Có thể chỉnh danh sách này trong biến `CASES` của file script.

---

## 5. Cách chạy trên Windows Git Bash

Chạy:

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate
python scripts/profiling/mirror_check.py
```

Nếu terminal đã có `(.venv)` thì chỉ cần:

```bash
python scripts/profiling/mirror_check.py
```

---

## 6. Nếu chưa có Comtrade API key

Không sao. Script sẽ tự dùng:

```text
Comtrade public preview
```

Nhưng vì chưa có key, cần lưu ý:

- Không thêm quá nhiều case một lần.
- Script đã có sleep giữa các request để giảm rate limit.
- Nếu gặp `429`, chờ vài phút rồi chạy lại.
- Nếu muốn profiling lớn hơn ở các nhiệm vụ sau, nên đăng ký API key.

---

## 7. File kết quả sau khi chạy

Script sẽ tạo:

```text
results/week1/mirror_check_results.md
results/week1/mirror_check_results.csv
results/week1/mirror_check_results.json
```

Và raw response:

```text
data/raw/week1_mirror_check/
```

Ý nghĩa:

| File/thư mục | Ý nghĩa |
|---|---|
| `mirror_check_results.md` | Đọc dễ nhất, dùng để báo cáo/trao đổi |
| `mirror_check_results.csv` | Dùng cho coverage matrix hoặc mở Excel |
| `mirror_check_results.json` | Lưu kết quả đầy đủ dạng máy đọc |
| `data/raw/week1_mirror_check/` | Bằng chứng response gốc từ Comtrade |

---

## 8. Cách đọc mức chênh lệch

| Level | Ý nghĩa |
|---|---|
| `LOW` | Hai phía có dữ liệu và chênh lệch trị giá <= 10% so với VN-reported |
| `MODERATE` | Hai phía có dữ liệu và chênh lệch > 10% đến <= 30% |
| `HIGH` | Hai phía có dữ liệu và chênh lệch > 30%; cần kiểm tra kỹ khi chọn dashboard |
| `MISSING_VN_REPORTED` | Việt Nam không có dữ liệu nhưng partner mirror có dữ liệu |
| `MISSING_MIRROR` | Việt Nam có dữ liệu nhưng partner mirror không có dữ liệu |
| `NO_DATA_BOTH` | Cả hai phía không có dữ liệu |
| `API_ERROR` | Có lỗi kỹ thuật khi gọi API |

Lưu ý:

> `HIGH` không có nghĩa là dữ liệu sai. Nó chỉ có nghĩa là case này cần được gắn cờ, giải thích và không nên cộng/trộn hai perspective một cách tùy tiện.

---

## 9. Kết quả workspace đã chạy thử

Trong workspace, script chạy thành công và tạo kết quả mẫu:

| Case | Kết quả |
|---|---|
| Japan coffee 202301 | Có cả VN-reported và mirror, chênh lệch HIGH |
| Japan coffee 202401 | Thiếu VN-reported, mirror có dữ liệu |
| USA coffee 202301 | Có cả VN-reported và mirror, chênh lệch HIGH |
| Germany coffee 202301 | Có cả VN-reported và mirror, chênh lệch LOW |
| China network equipment 202301 | Có cả VN-reported và mirror, chênh lệch LOW |
| Korea integrated circuits 202301 | Có cả VN-reported và mirror, chênh lệch MODERATE |
| China network equipment 202401 | Thiếu VN-reported, mirror có dữ liệu |
| Korea integrated circuits 202401 | Thiếu VN-reported, mirror có dữ liệu |

Kết quả này rất có ích vì chứng minh cả hai tình huống:

1. Có case hai phía đều có dữ liệu để so sánh.
2. Có case Việt Nam thiếu dữ liệu nhưng mirror có dữ liệu.

---

## 10. Kết luận thiết kế rút ra

Sau nhiệm vụ 4, nhóm có cơ sở giữ các quyết định thiết kế sau:

```text
FACT_TRADE.reporting_perspective
```

Ví dụ giá trị:

```text
VN_REPORTED
PARTNER_MIRROR
```

Và nên có bảng/view reconciliation:

```text
FACT_TRADE_RECONCILIATION
```

Một số chỉ tiêu reconciliation nên có:

| Chỉ tiêu | Ý nghĩa |
|---|---|
| `vn_reported_value_usd` | Trị giá phía Việt Nam báo cáo |
| `mirror_value_usd` | Trị giá phía đối tác mirror |
| `abs_diff_value_usd` | Chênh lệch tuyệt đối |
| `pct_diff_vs_vn` | Chênh lệch % so với VN-reported |
| `discrepancy_level` | LOW/MODERATE/HIGH/MISSING... |
| `reconciliation_note` | Ghi chú lý do/diễn giải |

---

## 11. Câu cần nhớ khi trình bày với GVHD

Nói đúng:

> Nhóm không cộng trộn dữ liệu Việt Nam báo cáo và dữ liệu mirror. Kho dữ liệu lưu riêng từng reporting perspective, sau đó xây lớp reconciliation để đối chiếu và gắn cờ độ lệch.

Không nói:

> Nhóm dùng mirror để thay thế dữ liệu chính thức của Việt Nam.

Cách nói an toàn hơn:

> Khi dữ liệu Việt Nam báo cáo bị thiếu ở một số kỳ gần đây, dữ liệu mirror được dùng như nguồn tham chiếu/đối chiếu, có gắn nhãn nguồn và mức độ tin cậy.

---

## 12. Checklist hoàn thành Nhiệm vụ 4

- [ ] Có file `scripts/profiling/mirror_check.py`.
- [ ] Chạy script không lỗi Python.
- [ ] Có file `results/week1/mirror_check_results.md`.
- [ ] Có file `results/week1/mirror_check_results.csv`.
- [ ] Có file `results/week1/mirror_check_results.json`.
- [ ] Có raw response trong `data/raw/week1_mirror_check/`.
- [ ] Đọc được case nào `LOW`, `MODERATE`, `HIGH`, `MISSING_VN_REPORTED`.
- [ ] Rút ra được kết luận cho thiết kế `FACT_TRADE` và `FACT_TRADE_RECONCILIATION`.

---

## 13. Commit lên GitHub

Sau khi chạy xong trên máy local, nên commit script và kết quả nhỏ:

```bash
git status
git add scripts/profiling/mirror_check.py docs/04_NhiemVu4_KiemTraMirror.md
git add results/week1/mirror_check_results.md results/week1/mirror_check_results.csv results/week1/mirror_check_results.json
git commit -m "add week1 mirror data check"
git push
```

Không cần commit raw response nếu thư mục `data/raw/` lớn hoặc đã bị `.gitignore` chặn.

---

## 14. Chuẩn bị cho nhiệm vụ tiếp theo

Kết quả Nhiệm vụ 4 sẽ dùng làm đầu vào cho:

> **Nhiệm vụ 5 — Lập Coverage Matrix**

Ở Nhiệm vụ 5, nhóm sẽ gom thông tin từ:

```text
api_smoke_test_results.csv
mirror_check_results.csv
```

để xác định tổ hợp nào đủ dữ liệu, tổ hợp nào thiếu, và cuối cùng chốt phạm vi partner/HS6/year/month cho đề tài.
