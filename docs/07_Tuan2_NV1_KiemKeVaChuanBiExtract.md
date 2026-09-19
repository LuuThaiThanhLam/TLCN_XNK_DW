# TUẦN 2 — NHIỆM VỤ 1: KIỂM KEY VÀ CHUẨN BỊ EXTRACT

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam
**Bối cảnh:** Tuần 1 đã chốt phạm vi (`docs/06_NhiemVu6_ChotPhamViDeTai.md`) với ràng buộc: extract hàng loạt cần subscription key vì preview giới hạn 500 records và 1 kỳ 1 sản phẩm mỗi call.
**Trạng thái tài khoản:** Nhóm đã lấy **Free APIs key** (tự động duyệt) và test nhanh thành công (Status 200, count=1, giá trị khớp bằng chứng preview tuần 1).

---

## 1. Mục tiêu nhiệm vụ

1. Chính thức hóa việc kiểm key bằng script trong repo (không chỉ test tạm trong chat) để có bằng chứng lặp lại được.
2. Xác nhận 3 điều kiện tiền đề của extract hàng loạt:
   - endpoint đầy đủ `data/v1/get` hoạt động với key;
   - một query lấy được **nhiều kỳ** (range `period=YYYYMM:YYYYMM`) — nền cho thiết kế batch theo năm;
   - dữ liệu mode key **trùng khớp** dữ liệu mode preview đã commit tuần 1.
3. Ghi bằng chứng vào `results/week2/key_check_results.*` và đưa lên GitHub.

## 2. Vì sao cần bước này (thay vì extract ngay)

- Key free có thể bị từ chối/không Active, `.env` sai định dạng, dotenv chưa cài — những lỗi này mà phát hiện giữa batch extract 12–16 request thì rất mất thời gian debug.
- Check "range period" quyết định thiết kế W2-NV2: nếu một call lấy được 12 tháng thì toàn bộ VN_REPORTED chỉ cần vài call; nếu không, phải gọi theo từng năm → số request thay đổi (12–16 → ~180), ảnh hưởng quota 500 calls/ngày.
- Cross-check với tuần 1 chứng minh hai chế độ truy cập cùng một nguồn sự thật — đưa vào báo cáo tuần 2 rất mạnh về mặt phương pháp.

## 3. File của nhiệm vụ

| File | Vai trò |
|---|---|
| `scripts/utils/verify_comtrade_key.py` | Script kiểm tra 4 mục, exit code 0/1, không in key đầy đủ |
| `results/week2/key_check_results.md` | Bảng kết quả đọc nhanh (sinh ra sau khi chạy) |
| `results/week2/key_check_results.json` | Kết quả máy đọc |
| `data/raw/week2_key_check/*.json` | Raw response thật (không commit — `.gitignore` chặn) |

Script chỉ đọc key từ: biến môi trường → `python-dotenv` → tự parse `.env` (phương án dự phòng khi chưa cài dotenv). **Không có hành vi ghi đè file tuần 1.**

## 4. Cách chạy (Windows Git Bash)

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate
python scripts/utils/verify_comtrade_key.py
echo $?   # 0 = PASS
```

## 5. Kết quả kỳ vọng

> Phiên bản 2 của script — sửa sau phát hiện ở lần chạy đầu (commit `041d8ac`): API mới **không** nhận range dấu hai chấm `period=201501:201512` (HTTP 400 "The field period is invalid" — cú pháp đó của hệ thống cũ). Cú pháp đúng, theo docs chính thức, là **danh sách phân tách dấu phẩy** `period=201501,201502,...`.

```text
[PASS] 1. Key duoc doc tu moi truong/.env
       4cf9****(dai 32)
[PASS] 2. data/v1/get annual 2023 TOTAL
       HTTP 200, count=1, value=353077513296.001, note=OK
[PASS] 3a. monthly mot ky don (201501)
       HTTP 200, count=1, note=OK
[PASS] 3b. monthly 12 ky cach bang DAU PHAY (dinh dang API moi)
       HTTP 200, count=12, so ky=12 ['201501','201502','201503']...
[INFO] 3c. (tham khao) range dau hai cham 201501:201512
       HTTP 400 ... → API MOI dung dau phay, khong dung dau hai cham
[PASS] 4. Cross-check gia tri annual 2023 voi preview tuan 1
       preview=353077513296.001, key=353077513296.001, diff=0.000 USD

KET LUAN: PASS — chot thiet ke W2-NV2 batch-theo-nam (comma period).
```

Bảng xử lý khi FAIL:

| Triệu chứng | Nguyên nhân hay gặp | Cách xử lý |
|---|---|---|
| Check 1 FAIL: `KHONG THAY KEY` | `.env` sai chỗ/sai tên biến/có nháy kép | `.env` phải ở **root project**, `COMTRADE_SUBSCRIPTION_KEY=<key>` không nháy, không space |
| Check 2: HTTP 401/403 | Key copy thiếu, chưa Active, bị regenerate | Mở profile Developer Portal kiểm tra trạng thái, copy lại Primary Key |
| Check 3a FAIL nhưng 2 PASS | Hy hữu: monthly bị khóa theo tier | Báo mình kèm note lỗi; kiểm tra lại quyền của sản phẩm Free APIs |
| Check 3b: 200 nhưng `so ky=1` | Range comma không được tier free cho phép đầy đủ | NV2 chuyển thiết kế sang **gọi từng kỳ** (~168–180 calls/chu kỳ extract, vẫn < 500 calls/ngày); script NV2 có sẵn chế độ `--single-period` |
| Check 3b: HTTP 400 "too many values" | Giới hạn số kỳ/call | Giảm danh sách period xuống 6 hoặc 3 kỳ/call, ghi lại số học được vào docs này |
| Check 4: diff > 0.01 | Comtrade revision dữ liệu giữa 2 lần gọi | Ghi chú snapshot vào báo cáo tuần 2; không cần sửa gì |
| HTTP 429 các check | Gọi dày | Script tự chờ theo `Try again in N`; chạy lại lần nữa |

Lần chạy **đầu tiên FAIL 3b không phải điều phải giấu** — nó là bằng chứng phương pháp "test trước khi tin cú pháp"; giữ nguyên trong git history (`041d8ac`), lần chạy PASS này sẽ commit đè file kết quả.

## 6. Cam kết an toàn key (áp dụng cho mọi nhiệm vụ còn lại)

- Key chỉ nằm trong `.env` (đã `.gitignore`) — không paste vào chat, commit, issue, báo cáo.
- Script luôn in key dạng mask (4 ký tự đầu + độ dài).
- File kết quả tự động che key trong URL (`subscription-key=***`).

## 7. Checklist hoàn thành W2-NV1

- [ ] `python scripts/utils/verify_comtrade_key.py` in ra 4 dòng PASS, exit code 0.
- [ ] `results/week2/key_check_results.md` + `.json` tồn tại và nội dung khớp console.
- [ ] Không có file nào trong `results/week1/` bị sửa (kiểm tra: `git status` không liệt kê results/week1).
- [ ] `docs/03` bản đã dọn block `_git` (nợ từ cuối tuần 1) đã copy đè và nằm trong commit này.
- [ ] Commit + push (xem mục 8).

## 8. Commit

```bash
git add docs reports scripts results
git commit -m "week2 nv1: comtrade key verification script and results"
git push
```

## 9. Bước tiếp theo

> **W2-NV2 — Extract Comtrade lõi VN_REPORTED**: 14 HS6 × (5 partner + World) × X/M × `201501:202312`, batch theo năm nếu cần, raw JSON cache + resume, gộp ra `results/week2/extract_vn_reported.*` và CSV staging theo đúng grain `docs/06` §5. Thiết kế phụ thuộc kết quả Check 3 (range hay per-year).

Sau khi NV1 xong và báo mình kết quả, mình sẽ hướng dẫn NV2 chi tiết.
