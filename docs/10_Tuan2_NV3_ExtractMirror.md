# TUẦN 2 — NHIỆM VỤ 3: EXTRACT MIRROR (PARTNER_MIRROR) — 5 ĐỐI TÁC

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam
**Tiền đề:** NV2 + NV2b đóng (13.725 + 958 dòng, audit coverage 249/252, neo 14/14, 3 ô partial đã minh oan trùng khớp nguồn tới từng tháng).

## 1. Mirror là gì trong DW của ta (nhắc lại luật, đừng bỏ qua)

| Quy tắc | Nội dung |
|---|---|
| Perspective | `reporter = đối tác, partnerCode = 704` — **bao giờ cũng là hàng xóm song song** của bảng VN_REPORTED trong fact, không trộn số liệu hai bên (docs/06) |
| Đảo chiều | p IMPORT từ VN (`M`) ⇄ bằng chứng cho **VN EXPORT**; p EXPORT sang VN (`X`) ⇄ bằng chứng cho **VN IMPORT** |
| Vai tro gắn ngay khi extract | `RECON_VN_EXPORT` / `RECON_VN_IMPORT` (đúng cặp cần đối soát) / `INFO_EXTRA` (tổ hợp khác cùng 14 mã — giữ lại, transform lọc) |
| Điện thoại | tự động theo năm: `851712` cho 2015–2021, `851713` cho 2022+ (thủ tục bridge y hệt NV2b; cột `maps_to_hs6` đã ghi sẵn) |
| 2024 | **có thể mirror đã có dữ liệu trong khi VN chưa báo** — đó là tính năng cho D3, không phải lỗi; giữ nguyên, đừng lọc |
| `is_reported=false` | dòng ước lượng của UN: vẫn lưu, transform đánh dấu và không dùng làm số đối chiếu chính |

Batch: 1 call = 1 reporter × 1 năm, `flowCode=X,M`, 14 mã, `partnerCode=704`, 12 kỳ comma-list. **50 call** cho trọn NV3 (5 reporter × 10 năm). Nếu API từ chối dual-flow → script **tự tach** X/M (mode per-flow-fallback, có ghi trong log). Resume qua `manifest_mirror.json` như NV2.

## 2. Chạy

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate

python scripts/extract/extract_comtrade_mirror.py --selftest    # PASS offline
python scripts/extract/extract_comtrade_mirror.py --years 2015  # rehearsal 5 call
python scripts/extract/extract_comtrade_mirror.py               # 50 call, ~6-8 phut, Ctrl+C an toan
echo $?   # 0
```

## 3. Kết quả kỳ vọng

| Hạng mục | Kỳ vọng |
|---|---|
| Rehearsal 2015 | 5 batch OK, mỗi batch vài trăm dòng (China/Korea dày, Germany thưa hơn) |
| Full | 50/50 batch OK/SKIP; tổng staging mirror ~10.000–16.000 dòng |
| Validation §1 | 8/8 MATCH là lý tưởng (đủ 8 case có `mirror_value_usd`, gồm cả 3 case 2024M01 — mirror đi trước VN). `MISMATCH` lẻ tẻ ở case 2024 = nguồn revision sau 3 tuần → ghi chú §4 docs/09-style, không sửa số |
| Coverage §2 | Các cặp RECON của Japan/China/Korea 2015–2023 dày (~108); USA/Đức có thể mỏng hơn vài chục — **đây chính là nguyên liệu bảng discrepancy tuần 3, không phải lỗi extract** |
| Output | `data/staging/stg_comtrade_partner_mirror.csv` (không commit) + `results/week2/mirror_partner_extract.{md,json}` (commit) |

## 4. Sự cố

| Triệu chứng | Xử lý |
|---|---|
| `MISSING_IN_MIRROR` hàng loạt ở case 2024 | Kiểm tra lại đã chạy full 2015–2024 chưa (`--years 2024` có trong manifest?); preview 3 tuần trước thấy có, giờ API key không thấy → gửi mình log, đừng tự kết luận |
| 400 mà log không tự fallback | Có khả năng `partnerCode=704` + dual-flow vướng gì đó — chạy `--reporters 392 --years 2015` cô lập và gửi mình 6 dòng log |
| 429 | Script tự chờ; chạy lại lệnh — resume |
| Batch FAIL | Chạy lại lệnh — resume; còn fail → gửi log |
| Muốn tạo lại report/staging không gọi API | `--rebuild-only` |

## 5. Commit (gộp nốt nợ docs/09 §2b + docs/03 — **copy 2 file này TRƯỚC** rồi mới add)

```bash
git status   # phai thay: mirror script + docs/10 moi, results/week2 mirror 2 file,
             # docs/09 + docs/03 modified (NO CU); KHONG thay file staging/raw/.env
git add docs scripts/extract results/week2
git commit -m "week2 nv3: partner mirror extract (5 reporters x 2015-2024, flow inversion + phone code bridge) + docs cleanup"
git push
```

## 6. Checklist

- [ ] Selftest PASS; rehearsal 5/5 OK.
- [ ] Full: 50/50 batch, exit 0.
- [ ] §1 validation: giải trình được từng ô (MATCH, hoặc MISMATCH-2024-do-revision đã ghi chú).
- [ ] `git status` không lộ file lớn; 4+2 file vào commit.
- [ ] Push xong đối chiếu được `results/week2/mirror_partner_extract.md` trên GitHub.

## 7. Tiếp theo — NV4 (hẹp hơn nhiều)

WITS tariff cho 14 mã × các năm (đã có URL pattern từ smoke test; combo 404 nào skip mã đó, không đổi thiết kế) + WB macro `FACT_MACRO_INDICATOR` (GDP/FX đã verify). Kịch bản chạy ngắn hơn NV3 vì mỗi nguồn 1 script nhỏ, resume tương tự.
