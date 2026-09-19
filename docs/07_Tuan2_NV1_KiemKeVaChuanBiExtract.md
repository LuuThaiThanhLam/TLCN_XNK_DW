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

```text
[PASS] 1. Key duoc doc tu moi truong/.env
[PASS] 2. Goi data/v1/get (annual 2023 TOTAL)
       HTTP 200, count=1, value=353077513296.001, note=OK
[PASS] 3. Goi monthly voi RANGE period 201501:201512
       HTTP 200, count=12, so ky tra ve=12 ...
[PASS] 4. Cross-check gia tri voi preview tuan 1
       preview=353077513296.001, key=353077513296.001, diff=0.000 USD
KET LUAN: PASS — san sang cho W2-NV2 (extract loi)
```

Bảng xử lý khi FAIL:

| Triệu chứng | Nguyên nhân hay gặp | Cách xử lý |
|---|---|---|
| Check 1 FAIL: `KHONG THAY KEY` | `.env` đặt sai chỗ / sai tên biến / có nháy kép | File `.env` phải nằm **root project**, dòng `COMTRADE_SUBSCRIPTION_KEY=<key>` không nháy, không space |
| Check 2: HTTP 401/403 | Key copy thiếu, chưa Active, hoặc bị regenerate | Mở profile trên Developer Portal xem trạng thái; copy lại Primary Key |
| Check 3: count=1 dù xin range | Portal free tier không cho range | Ghi nhận, báo lại — W2-NV2 chuyển thiết kế sang gọi theo từng năm (~180 calls, vẫn dưới 500/ngày) |
| Check 3: count=0 | Kỳ 2015 cà phê sang Nhật không có dữ liệu tháng | Không chặn; đổi range thử `201801:201812` trong script và chạy lại |
| Check 4: diff > 0.01 | Hy hữu — Comtrade revision dữ liệu | Không panic: ghi chú "preview snapshot 18/09, key snapshot <ngày>" vào báo cáo; không cần sửa gì |
| HTTP 429 các check | Gọi dày | Script đã tự chờ theo `Try again in N`; chạy lại lần nữa là đủ |

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
