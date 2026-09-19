# TUẦN 2 — NV2b: BRIDGE MÃ HS2017 (851712) CHO DÂY CHUYỀN ĐIỆN THOẠI

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam
**Vì sao tồn tại tài liệu này:** audit coverage cuối NV2 (bảng §2 của `results/week2/extract_vn_reported.md`) cho thấy 13/14 mã đạt 108/108 tháng, riêng `851713` chỉ **24/108**. Nguyên nhân không phải pipeline: **HS revision 2022** thay 8517.12 (toàn bộ điện thoại di động, HS2017) bằng 8517.13 (smartphone, HS2022). Comtrade không hồi mã tự động. Nếu bỏ qua, chart mặt hàng chủ lực (~26,5 tỷ USD năm 2023) trên dashboard D1 sẽ đứt 7 năm 2015–2021.

**Phạm vi sửa:** extract thêm `851712` cho **2015–2021** (đúng các năm trống), X + M, 6 partner, cùng grain tháng, cùng luật khóa. Không gọi lại API cho dữ liệu NV2 đã có — mọi thứ là layer mới (`vnbr_*`).

**Kèm theo — bản vá normalize:** selftest của bridge bắt được bug thật trong `normalize_rows` của core: `partnerCode = 0` (World, số nguyên) bị `or ""` nuốt thành rỗng → staging CSV sai cột `partner_code`/`is_aggregate_partner` cho các dòng World (số dòng và validation không ảnh hưởng). Core script đã vá + có regression test; phải `--rebuild-only` lại NV2 để staging CSV đúng (không tốn API call nào).

## 1. Chạy (theo đúng thứ tự)

```bash
cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
source .venv/Scripts/activate

# Buoc A — tai tao NV2 tu raw da cache (0 call API), tinh ca bug fix World:
python scripts/extract/extract_comtrade_core.py --rebuild-only
python scripts/extract/extract_comtrade_core.py --selftest        # 6 nhom, PASS

# Buoc B — bridge:
python scripts/extract/extract_comtrade_bridge_hs2017.py --selftest   # PASS
python scripts/extract/extract_comtrade_bridge_hs2017.py              # 14 batch + 2 annual-check
```

Cả hai script đều có resume; bridge dùng manifest riêng `data/raw/week2_extract/manifest_bridge.json`. Bridge cũng hỗ trợ `--rebuild-only`.

## 2. Kết quả kỳ vọng

| Hạng mục | Kỳ vọng |
|---|---|
| NV2 rebuild | `Dong staging: 13725` (y hệt lần trước), validation 5/5 khop; mở `stg_comtrade_vn_reported.csv` lọc `partner_code=0` sẽ thấy các dòng World với `is_aggregate_partner=True` |
| Bridge batch | 14/14 OK; exit code 0 |
| Bridge dòng | X dày (thời kỳ Samsung cực đại), M thưa hơn; tổng vài trăm dòng là bình thường |
| Annual-check §3 | Mục tiêu 14/14 `MATCH`. **Kết quả thật (đã xác minh cuối Tuần 2): 4/14 MATCH, 10 WARN** — điều tra tới tận nguồn cho thấy WARN là ĐẶC TÍNH NGUỒN (số World ≠ Σ partner trên cùng năm, do cơ chế khai báo khác nhau), KHÔNG phải revision giữa 2 lần gọi như ghi chú ban đầu; pipeline đúng, không sửa gì. Diễn giải đầy đủ: `reports/tuan2_bao_cao.md` §5 case 4 |
| Output | `data/staging/stg_comtrade_vn_reported_bridge.csv` (không commit) + `results/week2/extract_bridge_hs2017.{md,json}` (commit) |

### 2b. KẾT LUẬN CHÍNH THỨC về các WARN của annual-check (run 2026-09-19: 4/14 MATCH, 10 WARN)

Điều tra độc lập bằng preview API công khai (không key) trên 2 ô lệch lớn nhất (M/2017 lệch 20,6%; X/2015 lệch 1,2%):

| Bằng chứng | Giá trị | Ý nghĩa |
|---|---:|---|
| Preview annual M/2017 | 1.850.351.130,800 | khớp annual của `data/v1/get` **từng chữ số** |
| Preview Σ 12 tháng M/2017 | 1.468.976.306,027 | khớp tổng World trong staging của **chính pipeline bạn** tới 3 số thập phân |
| 12/12 tháng của chuỗi monthly M/2017 | đều có dòng, mang `isReported=false` | phần lệch A − ΣM **không** đến từ tháng thiếu |

**Kết luận:** extract trung thực 100% với nguồn; A − ΣM là **đặc tính của lưu trữ UN Comtrade** (mode năm cho năm cũ gộp thêm phần ước tính chưa từng xuất hiện ở mode tháng — năm càng cũ lệch càng lớn; 2020–2021 khớp 0,001, còn 2018–2019 lệch <1 USD thuần làm tròn float). **Không phải bug, không chạy lại gì cả.** Hai luật rút ra:
1. Trong DW của ta, giá trị năm luôn = Σ tháng (tự nhất quán); số annual A của UN chỉ dùng để cross-check QA với **ngưỡng tương đối** (cờ khi >1%), không bao giờ cộng thẳng vào fact.
2. Check NV3 viết lại thành 3 lớp: `ROUNDING` (≤1 USD) / `MATCH` / `SOURCE_LEVEL_DIFF` (báo %, không tính là fail).

## 3. Hợp nhất ở tầng transform (tuần 3 — ghi vào backlog transform)

1. Khi load fact: dòng bridge được gán `hs6 = maps_to_hs6 = 851713`, giữ `hs6_original = 851712`, `hs_nomenclature = HS2017`, `batch_id LIKE 'vnbr_%'`.
2. Bridge là **xấp xỉ có chủ đích** (8517.12 gồm cả điện thoại thường, 8517.13 thiên smartphone): ghi chú cố định trên D1 — "2015–2021 theo mã cũ 8517.12 (gồm mọi điện thoại di động)"; tuyệt đối không tuyên bố đây là chuỗi smartphone thuần.
3. Reconciliation NV3 (mirror): đối tác cũng đổi mã tương tự → mirror script sẽ extract **cả** 851712 (2015–2021) và 851713 (2022+) cùng lúc; so khớp theo cặp năm–đối tác.
4. docs/06 không bị sửa hồi tố; phạm vi thay đổi được ghi nhận tại đây + báo cáo tuần NV5 ("phát hiện qua audit coverage → xử lý bằng bridge có kiểm chứng") — đúng trình tự bằng chứng.

## 4. Sự cố

| Triệu chứng | Xử lý |
|---|---|
| 401/403 | Key bị regenerate — portal, rồi `verify_comtrade_key.py` (docs/07) |
| Batch FAIL | Chạy lại lệnh — resume; vẫn fail → gửi mình log |
| WARN_MISMATCH hàng loạt (≥4 năm) | Không commit số lệch; nhắn mình kèm bảng §3 (thường = nguồn vừa revision, cần chạy lại validation NV2) |
| Staging CSV lộ trong `git status` | Sai — `data/staging/*` phải bị ignore; dừng và báo |

## 5. Commit

```bash
git status   # thay: docs/09*, results/week2/* (2 file moi + 2 file rebuild), scripts/extract/* (2 file), README.md, docs/03
git add docs scripts/extract results/week2 README.md docs/03_NhiemVu3_GoiThuAPI.md
git commit -m "week2 nv2b: HS2017 bridge for 851713 series gap + World partner_code normalize fix"
git push
```

(Kèm 2 file nợ mỹ phẩm `README.md` + `docs/03` — copy từ workspace trước khi add, nếu chưa.)
