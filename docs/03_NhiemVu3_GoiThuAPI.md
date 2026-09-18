# NHIỆM VỤ 3 — GỌI THỬ API

## 1. Mục tiêu

Nhiệm vụ 3 nhằm kiểm tra nhanh các API chính trước khi extract dữ liệu hàng loạt.

Nói dễ hiểu:

> Mình chưa lấy dữ liệu lớn. Mình chỉ “gõ cửa” từng nguồn xem cửa có mở không, bên trong có dữ liệu không, và có vấn đề gì không.

Sau nhiệm vụ này, nhóm phải có bằng chứng rằng dữ liệu của đề tài là dữ liệu thật từ API.

---

## 2. Nguồn sẽ gọi thử

| Nguồn | Mục đích kiểm tra |
|---|---|
| UN Comtrade | Có dữ liệu xuất nhập khẩu, dữ liệu tháng, dữ liệu mirror không |
| WITS/UNCTAD TRAINS | Có dữ liệu thuế MFN/PREF không |
| World Bank Indicators | Có dữ liệu GDP, tỷ giá, lạm phát/tỷ giá tháng ứng viên không |

---

## 3. Script dùng cho nhiệm vụ 3

File script:

```text
scripts/profiling/api_smoke_test.py
```

Script này sẽ:

1. Gọi thử Comtrade annual.
2. Gọi thử Comtrade monthly.
3. Gọi thử Comtrade mirror.
4. Gọi thử WITS MFN/PREF.
5. Gọi thử World Bank GDP/tỷ giá.
6. Lưu raw response vào `data/raw/week1_smoke_test/`.
7. Lưu bảng kết quả vào `results/week1/`.

---

## 4. Cách chạy trên máy Windows bằng Git Bash

Vì bạn đang dùng Git Bash/MINGW64, chạy đúng lệnh sau:

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate
python scripts/profiling/api_smoke_test.py
```

Nếu terminal đã có `(.venv)` rồi thì chỉ cần:

```bash
python scripts/profiling/api_smoke_test.py
```

---

## 5. Nếu có Comtrade API key

Nếu đã có key, chạy:

```bash
export COMTRADE_SUBSCRIPTION_KEY="DAN_KEY_CUA_BAN_VAO_DAY"
python scripts/profiling/api_smoke_test.py
```

Nếu chưa có key vẫn chạy được bằng public preview, nhưng số dòng bị giới hạn hơn.

---

## 6. Kết quả sau khi chạy

Script sẽ tạo:

```text
results/week1/api_smoke_test_results.md
results/week1/api_smoke_test_results.csv
results/week1/api_smoke_test_results.json
```

Và raw response:

```text
data/raw/week1_smoke_test/
```

Trong đó:

| File | Dùng để làm gì? |
|---|---|
| `api_smoke_test_results.md` | Đọc dễ nhất, dùng để báo cáo/trao đổi |
| `api_smoke_test_results.csv` | Mở bằng Excel, điền vào coverage matrix |
| `api_smoke_test_results.json` | Lưu đầy đủ kết quả máy đọc được |
| `data/raw/week1_smoke_test/*` | Bằng chứng response gốc từ API |

---

## 7. Cách đọc kết quả

Trong file `api_smoke_test_results.md`, chú ý các cột:

| Cột | Ý nghĩa |
|---|---|
| `OK` | API có gọi thành công về mặt kỹ thuật không |
| `Status` | HTTP status code, ví dụ 200 là ổn, 429 là rate limit |
| `Count` | Số dòng hoặc số observation API trả về |
| `Note` | Ghi chú lỗi hoặc OK |

Cách hiểu:

| Trường hợp | Ý nghĩa |
|---|---|
| OK = ✅, Count > 0 | API gọi được và có dữ liệu |
| OK = ✅, Count = 0 | API gọi được nhưng tổ hợp đó không có dữ liệu |
| OK = ❌, Status = 429 | Gọi quá nhanh/rate limit, chạy lại sau hoặc dùng key |
| OK = ❌, timeout | API chậm, ghi nhận rủi ro và chạy lại sau |
| WITS không có Obs | Có thể tổ hợp reporter/partner/HS/year đó không có dữ liệu |

---

## 8. Các test có trong script

## 8.1. UN Comtrade

| Test | Mục đích |
|---|---|
| VN export TOTAL to World 2023 | Kiểm tra VN có dữ liệu năm 2023 |
| VN export TOTAL to World 2024 | Kiểm tra khoảng trống dữ liệu năm gần đây |
| VN export HS090111 to Japan 2023M01 | Kiểm tra dữ liệu tháng |
| Japan import HS090111 from VN 2024M01 | Kiểm tra dữ liệu mirror |

## 8.2. WITS

| Test | Mục đích |
|---|---|
| VN tariff on World HS090111 2018 | Kiểm tra MFN baseline |
| VN tariff on Japan-origin goods HS090111 2018 | Kiểm tra PREF chiều nhập khẩu vào VN |
| Japan tariff on Vietnam-origin goods HS090111 2018 | Kiểm tra PREF chiều xuất khẩu VN sang Nhật |

## 8.3. World Bank

| Test | Mục đích |
|---|---|
| GDP current USD Vietnam 2024 | Kiểm tra GDP |
| Official exchange rate annual Vietnam 2024 | Kiểm tra tỷ giá năm |
| Exchange rate monthly candidate 2024M01–2024M12 | Kiểm tra tỷ giá tháng ứng viên |

---

## 9. Luật quan trọng khi gọi Comtrade

Trong script đã tự thêm:

```text
motCode=0
customsCode=C00
partner2Code=0
```

Lý do:

- `motCode=0`: lấy tổng tất cả phương thức vận tải.
- `customsCode=C00`: lấy chế độ hải quan chuẩn/tổng quát.
- `partner2Code=0`: không phân tích partner thứ hai.

Nếu không khóa các tham số này, dữ liệu có thể bị cộng trùng.

---

## 10. Việc bạn cần làm sau khi chạy

Sau khi chạy xong, gửi mình nội dung file:

```text
results/week1/api_smoke_test_results.md
```

Hoặc copy phần bảng kết quả vào chat.

Mình sẽ giúp bạn đọc kết quả và kết luận:

- Nguồn nào dùng được.
- Nguồn nào có rủi ro.
- Test nào cần chạy lại.
- Có cần đổi mã HS/đối tác mẫu không.
- Có nên dùng tỷ giá tháng không.
- Có nên giữ dashboard tariff là dashboard chính không.

---

## 11. Commit lên GitHub sau khi thêm script

Sau khi bạn copy/tạo script `api_smoke_test.py` trên máy local, commit:

```bash
git status
git add scripts/profiling/api_smoke_test.py docs/03_NhiemVu3_GoiThuAPI.md
git commit -m "add API smoke test script"
git push
```

Sau khi chạy script và có kết quả, **không nhất thiết commit raw data lớn**. Nhưng có thể commit file kết quả nhỏ nếu cần:

```bash
git add results/week1/api_smoke_test_results.md results/week1/api_smoke_test_results.csv
_git commit -m "add week1 API smoke test results"
```

Lưu ý: dòng trên có `_git` là sai. Lệnh đúng là:

```bash
git commit -m "add week1 API smoke test results"
git push
```

Nếu raw response trong `data/raw/` lớn, không commit.

---

## 12. Checklist hoàn thành Nhiệm vụ 3

- [ ] Có file `scripts/profiling/api_smoke_test.py`.
- [ ] Chạy script không lỗi Python.
- [ ] Có file `results/week1/api_smoke_test_results.md`.
- [ ] Có file `results/week1/api_smoke_test_results.csv`.
- [ ] Có raw response trong `data/raw/week1_smoke_test/`.
- [ ] Đọc được test nào OK, test nào lỗi.
- [ ] Gửi kết quả cho trợ lý/GVHD để phân tích.

---

## 13. Kết luận

Nhiệm vụ 3 không yêu cầu mọi test đều phải có dữ liệu. Mục tiêu là biết rõ:

```text
API nào gọi được → tổ hợp nào có dữ liệu → tổ hợp nào thiếu → rủi ro nào cần ghi nhận
```

Nếu có test thất bại vì timeout/rate limit, đó cũng là thông tin quan trọng cho báo cáo khả thi.
