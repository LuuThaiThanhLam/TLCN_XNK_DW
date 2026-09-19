# TUẦN 2 — NHIỆM VỤ 4: WITS BIỂU THUẾ + WORLD BANK MACRO

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam
**Đặc điểm NV4:** cả hai nguồn **không cần key**. Điểm duy nhất cần nhớ: WITS chặn User-Agent lạ (Cloudflare) — script đã tự đặt UA trình duyệt.

## 1. Hai script

| Script | Nguồn | Calls | Output |
|---|---|---:|---|
| `scripts/extract/extract_wb_macro.py` | WB WDI API v2, 5 chỉ số × 6 nước × 2015–2024 | **5** | `stg_wb_macro.csv` (~300 dòng) + `results/week2/wb_macro.{md,json}` |
| `scripts/extract/extract_wits_tariff.py` | WITS TRAINS SDMX, 83 combo `year/all`, lọc năm ≥2015 | **83** | `stg_wits_tariff.csv` (~1,5–2k dòng) + `results/week2/wits_tariff_extract.{md,json}` |

Hai bài học nguồn đã được kiểm bằng probe trước khi viết (không đoán):
1. WB phân tách nhiều nước bằng **dấu chấm phẩy** (`country/VNM;CHN;...`) — dấu phẩy trả error 120; và `BN.TOTL.GD.ZS` là mã chết → đã đổi `NE.TRD.GNFS.ZS` (Trade % of GDP), có test bắt lỗi im lặng (API msg → FAIL, không 0-dòng-không-giải-thích).
2. WITS: chiều đối tác báo cáo về VN (`reporter=partner, partner=704`) **404 trên miền phí** — reproduce đúng như tuần 1 → thiết kế MKT dùng **MFN-World** (xấp xỉ một chiều, có ghi chú pháp lý trong report, không overclaim FTA). `year/all` trả trọn chuỗi (test thật: VN-coffee có 1994→2023) → 1 call/combo thay vì 9.

## 2. Chạy

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW && source .venv/Scripts/activate

python scripts/extract/extract_wb_macro.py --selftest      # PASS (doc 2 anchor tuan 1)
python scripts/extract/extract_wb_macro.py                 # ~15 giay
python scripts/extract/extract_wits_tariff.py --selftest   # PASS (parse XML + 81+2 combo)
python scripts/extract/extract_wits_tariff.py --scope VN --limit 8   # rehearsal ~20 giay
python scripts/extract/extract_wits_tariff.py              # full, ~4-6 phut, resume duoc
echo $?   # 0
```

## 3. Kết quả kỳ vọng (mình đã chạy THẬT trong sandbox — số này là đo, không phải ước)

| Hạng mục | Kỳ vọng |
|---|---|
| WB | 300 dòng staging (5×60); validation **2/2 MATCH** (VNM GDP 2024 = 476.324.572.783,807; FX 24.164,886); exit 0 |
| WITS rehearsal 8 combo | 7-8 combo OK (mỗi combo 9 dòng, 2015–2023); 0-2 `NO_DATA` (vd PREF TQ cho 854231) = bình thường; §2 validation **⚠️ MISSING là đúng** (anchor 090111 chưa nằm trong 8 combo đầu) |
| WITS full | 83 combo: phần lớn OK, một ít NO_DATA (nhật ký §3 ghi hết); nam tối đa **2023** (WITS lag ~2 năm — vào ghi chú D4); validation **2/2 MATCH** (090111/2018: MFN 15,000 & PREF 8,000) |
| Staging files | `data/staging/stg_wb_macro.csv` + `stg_wits_tariff.csv` — gitignore chặn, không commit |

## 4. Sự cố

| Triệu chứng | Xử lý |
|---|---|
| WITS `HTTP 403` hàng loạt | Cloudflare đổi chính sách UA — gửi mình log, mình đổi chuỗi UA (1 dòng) |
| `API msg: Invalid value` phía WB | Indicator/nước sai — script đã FAIL thay vì im lặng; báo mình mã lỗi |
| Vài combo WITS `FAIL` (mạng) | Chạy lại lệnh — resume chỉ gọi thiếu |
| `NO_DATA` > 15 combo | Bất thường (kỳ vọng ≤ ~6); dán bảng §3 cho mình |
| Muốn tạo lại report không gọi API | `--rebuild-only` (cả 2 script đều có) |

## 5. Ý nghĩa cho D4 + báo cáo tuần (NV5 sẽ dùng trực tiếp)

- `FACT_TARIFF_ANNUAL` grain năm — không bao giờ join vào fact monthly (ghi trong md WITS §4).
- Cột `nomenclature` (H5/H6/HS2022...) phải được filter khi join theo (hs6, year) — đã ghi trong ghi chú transform.
- Chuỗi macro 6 nước 10 năm → bubble D2 "GDP × tốc độ tăng trưởng × XK VN" đủ dữ liệu, **không cần thêm chỉ số**.
- WITS mới nhất 2023 + WB 2024 + Comtrade-VN trống 2024 → bảng "độ trễ từng nguồn" cho D3 (tự động có số từ 3 report tuần này).

## 6. Commit (kèm lần cuối 2 nợ docs — check `git diff --stat` phải ra ĐÚNG 2 file docs/03+docs/09 trước khi add)

```bash
git status
git add scripts/extract docs results/week2
git commit -m "week2 nv4: WITS tariff (83 combos, MFN+PREF VN, MKT MFN approx) + WB macro 6x5x10y, anchors vs week1 verified"
git push
```

## 7. Checklist

- [ ] 2 selftest PASS; WB 300 dòng + 2/2 MATCH.
- [ ] WITS rehearsal OK → full: exit 0, §2 validation 2/2, năm max 2023.
- [ ] `git diff --stat` trước add có `docs/03_NhiemVu3_GoiThuAPI.md` + `docs/09_Tuan2_NV2b_BridgeMaHS.md` (bản copy MỚI — có mục "2b.").
- [ ] Sau push: mở 2 file md trên GitHub kiểm nhanh.

Xong NV4 thì **NV5** là bước cuối tuần: QA tổng + báo cáo tuần — mình sẽ dựng sẵn `reports/tuan2_bao_cao.md` từ chính các file results.
