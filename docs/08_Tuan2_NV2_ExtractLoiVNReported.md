# TUẦN 2 — NHIỆM VỤ 2: EXTRACT COMTRADE LÕI (VN_REPORTED)

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam
**Tiền đề:** W2-NV1 PASS — key hoạt động, check 3b chứng minh 1 call lấy được 12 kỳ (comma-period).
**Phạm vi extract:** đúng `docs/06` §3 — 14 HS6 × 6 partner (China, Germany, Japan, Korea, USA + World) × 2 flow × 2015–2023 (lõi) + 2024 (partial).

---

## 1. Thiết kế (tóm tắt)

| Yếu tố | Quyết định |
|---|---|
| Batch | 1 call = 1 flow × 1 năm (12 kỳ comma-list, 14 mã, 6 partner). Tổng **20 call** cho trọn NV2 |
| Endpoint | `data/v1/get/C/M/HS` với `subscription-key` (bắt buộc key — preview không đủ sức) |
| Luật khóa | `motCode=0, customsCode=C00, partner2Code=0` đặt ngay trong hàm gọi (không thể quên) |
| Fallback 400 | Nếu API từ chối danh sách 14 mã, script **tự chia đôi cmdCode** gọi lại (2 sub-call/năm) |
| Resume | `data/raw/week2_extract/manifest.json` ghi sha1 logical-params; chạy lại chỉ gọi batch thiếu. `--force` để gọi lại tất cả |
| Output đầy đủ | `data/staging/stg_comtrade_vn_reported.csv` — **không commit** (gitignore), là input trực tiếp cho staging/SSIS tuần 3 |
| Output bằng chứng | `results/week2/extract_vn_reported.{md,json}` — thống kê + validation, **có commit** |
| Validation | So 5 ô số liệu (X/M × Japan/China/Germany/USA/Korea × 090111/851762/854231 × 202301) với `results/week1/mirror_check_results.json` — cùng query, 2 thời điểm khác nhau, giá trị phải khớp từng cent |

Kỳ vọng sản lượng (không phải cam kết chính xác từng dòng): mỗi batch ≤ 1008 dòng (đầy đủ 14×6×12); thực tế các năm đầu thưa hơn → toàn bộ core dự kiến **~12.000–19.000 dòng**; 2024 có thể gần 0 (gap cấu trúc đã chứng minh tuần 1 — đó là nội dung D3, không phải lỗi extract).

## 2. Chạy từng bước

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate

# Buoc 0 (khuyen nghi): test logic offline, khong call API
python scripts/extract/extract_comtrade_core.py --selftest      # ky vong: SELFTEST: PASS

# Buoc 1: rehearsal 1 nam (2 call, ~15 giay) de yen tam ve auth + hoi dap
python scripts/extract/extract_comtrade_core.py --years 2015
#   -> moi thay "Dong staging: <vài trăm tới ~2000>" la OK.
#   -> Validation se bao MISSING_IN_EXTRACT cho ca 5 case: DUNG KY, vi
#      o so lieu tuan 1 nam 202301 con nam ngoai pham vi 2015. Dung lo.

# Buoc 2: chay tron (tich luy them 18 call; batch 2015 da cache se duoc SKIP)
python scripts/extract/extract_comtrade_core.py
#   -> toan bo ~2-3 phut (tieng nghi giua call). Co the dat may chay,
#      neu gian doan giua chung cu lenh Ctrl+C -> chay lai lenh tren, no resume.
```

## 3. Đọc kết quả

Mở `results/week2/extract_vn_reported.md`:

- **Mục 1** — dòng theo flow×năm: các năm 2015–2023 phải > 0 cho cả hai flow (trừ ô hiếm); 2024 X có thể = 0 (gap — đúng dự kiến), 2024 M có thể đã có một phần.
- **Mục 2** — độ phủ tháng theo mã: `số tháng có dữ liệu` tối đa 120 (10 năm × 12). Mã nào < ~100 là ứng viên ghi chú coverage (không bắt buộc loại — mirror/D3 giải thích sau).
- **Mục 3** — validation: **5/5 MATCH** là chuẩn (lệch cho phép 0.01 USD).
- **Mục 4** — nhật ký gọi: mọi batch `OK`/`SKIP (cache)`; batch `FAIL` in ra kèm hướng dẫn resume.

## 4. Bảng xử lý sự cố

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `[FAIL] Khong tim thay COMTRADE_SUBSCRIPTION_KEY` | `.env` mất/sai | Xem docs/07 mục 6; chạy `verify_comtrade_key.py` |
| 401/403 hàng loạt | Key bị regenerate | Portal Developer → copy key mới vào `.env` |
| 400 vẫn fail sau "tach 2 nua" | Danh sách partner/period vượt kiểu gì đó | Tạm chạy `--years 2015-2019` để cô lập + gửi mình log |
| 429 lặp | Gọi dày quá mức free tier | Script đã tự chờ; nếu vẫn dày, tăng `SLEEP_SECONDS_BETWEEN_CALLS` lên 2.5 và resume |
| Validation `MISMATCH` (không phải MISSING) | Comtrade đã revision dữ liệu giữa 2 tuần | Không sửa gì; ghi 1 dòng vào §5 notes report khi commit — dashboard D3 sẽ hiển thị cả revision story |
| Staging CSV không thấy trên GitHub | Đúng — `data/staging/*` bị gitignore có chủ đích | Repo chỉ cần report; file dữ liệu nằm máy bạn + `data/raw` đủ để rebuild (`--rebuild-only`) |
| Muốn tạo lại bảng/staging mà không gọi API |  | `python scripts/extract/extract_comtrade_core.py --rebuild-only` |

## 5. Kỷ luật dữ liệu (kiểm lần cuối trước khi commit)

```bash
git status   # KHONG duoc thay: stg_comtrade_vn_reported.csv, data/raw/week2_extract/*, .env
```

Nếu `git status` liệt kê bất kỳ file nào trong 3 loại trên → **dừng, báo mình**, đừng commit.

## 6. Commit

```bash
git add results/week2 scripts/extract docs
git add README.md docs/03_NhiemVu3_GoiThuAPI.md   # 2 no my pham cu (neu chua copy)
git commit -m "week2 nv2: core VN_REPORTED extraction pipeline, staging csv (local), evidence report"
git push
```

## 7. Checklist hoàn thành W2-NV2

- [ ] `--selftest` in `SELFTEST: PASS`.
- [ ] Rehearsal `--years 2015` chạy OK, xem được `stg_comtrade_vn_reported.csv` mở bằng Excel không lỗi font.
- [ ] Full run: 20/20 batch OK hoặc SKIP (cache), exit code 0.
- [ ] `extract_vn_reported.md`: validation 5/5 MATCH (trường hợp MISMATCH do revision thì đã ghi chú).
- [ ] `git status` sạch trước commit (mục 5).
- [ ] Push xong, GitHub có `results/week2/extract_vn_reported.*`.

## 8. Bước tiếp theo

> **W2-NV3 — Extract mirror (PARTNER_MIRROR)** cho 5 partner lõi: 5 reporter × 9–10 năm × 2 chiều = ~100 call, dùng lại 80% code NV2 (thêm chiều đảo flow + normalize partner về góc nhìn VN). Sau đó NV4 (WITS + macro) là phần nhỏ.

Báo mình kết quả mục 3 (dán nguyên khối `=== TONG KET ===`), mình xác nhận số rồi bật NV3.
