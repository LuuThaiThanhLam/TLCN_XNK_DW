# Báo cáo tuần 2 — Extract dữ liệu đa nguồn, QA bằng validation chéo

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam
**Sinh lúc:** 2026-09-19T05:14:45+00:00 — bởi `scripts/profiling/gen_week2_report.py` (mọi số liệu đọc tự động từ `results/week2/*.json` đã commit; file nào thiếu báo MISSING, không điền tay).

## 1. Bảng hoàn thành

| Nhiệm vụ | Trạng thái | Số liệu chốt |
|---|---|---|
| NV1 — kiểm key + gate batch | PASS | checks=6, all_passed=True |
| NV2 — extract lõi VN_REPORTED | PASS | staging=13725 dong; 13/14 ma du 108/108 thang (2015-2023); validation vs tuần 1: **5/5 MATCH** |
| NV2b — bridge 851712 (HS2017) | PASS | staging=958 dong; batch OK=14/14; annual-check MATCH=4/14 (WARN con lại = đặc tính nguồn A-vs-ΣM, xem muc 5) |
| NV2-audit — coverage toàn phạm vi | PASS | 249/252 o 12/12 thang; neo 2023: MATCH 14/14; fails=0, warns=3 |
| NV3 — mirror 5 đối tác | PASS | staging=13252 dong (RECON=8379, INFO_EXTRA=4873); batch dat=50/50; validation vs mirror tuần 1: **8/8 MATCH** |
| NV4a — WITS biểu thuế | PASS | staging=419 dong; combo OK/SKIP/REBUILT=55/83, NO_DATA=28 (my + vai cap song phuong); anchors MFN/PREF 2018: **2/2 MATCH** |
| NV4b — WB macro 6 nước × 5 chỉ số | PASS | staging=300 dong; anchors WB 2024: **2/2 MATCH** |

**QA tổng tuần: PASS** — đủ 7/7 nguồn bằng chứng.

## 2. Sản lượng dữ liệu vào tầng staging (input trực tiếp cho mô hình sao)

| Bảng staging | Grain | Dòng | Perspective / phạm vi |
|---|---|---:|---|
| `stg_comtrade_vn_reported.csv` | tháng × partner × HS6 × flow | 13725 | VN_REPORTED, 2015–2024, 14 mã |
| `stg_comtrade_vn_reported_bridge.csv` | như trên | 958 | VN_REPORTED, 851712 2015–2021 (bridge HS2017 → 851713) |
| `stg_comtrade_partner_mirror.csv` | tháng × reporter × HS6 × flow | 13252 | PARTNER_MIRROR, 5 nước, 2015–2024 |
| `stg_wits_tariff.csv` | năm × reporter × partner × HS6 × loại thuế | 419 | 2015–2023 (WITS lag; PREF song phương dừng 2021) |
| `stg_wb_macro.csv` | nước × năm × chỉ số | 300 | 6 nước × 5 chỉ số 2015–2024 |

Quy tắc đã chốt (docs/06, tiếp tục hiệu lực ở transform): hai perspective không bao giờ trộn; World (partner 0) giữ trong dữ liệu nhưng loại khi xếp hạng; giá trị năm của ta = Σ tháng; `OK 0 dòng` ≡ no-data.

## 3. Bảng độ trễ nguồn (số thật từ kỳ chạy này — liệu trực tiếp cho D3)

| Nguồn | Kỳ mới nhất có dữ liệu (phạm vi đã chốt) | Hệ quả |
|---|---|---|
| Comtrade — VN tự báo cáo | 2023 (2024: 0 dòng) | D3 hiển thị khoảng trắng 2024 + lý do |
| Comtrade — mirror 5 đối tác | 2024 (đủ tháng, validation 2024 khớp tuần trước) | 'mirror đi trước VN' = chức năng D3, không phải lỗi |
| WITS TRAINS | 2023 (MFN); PREF song phương dừng 2021; Mỹ không có trên endpoint miễn phí | D4 = 4/5 thị trường + chú thích |
| World Bank WDI | 2024 | macro làm trục tham chiếu đến 2024 |

## 4. Validation — nguyên tắc 'số mới phải khớp bằng chứng cũ'

Mỗi bước extract đều đối chiếu với bằng chứng đã lưu từ **thời điểm khác** (tuần 1) hoặc **nguồn thứ hai** (preview API, không key):

- NV2 ↔ 5 ô mirror tuần 1 (202301): **5/5 MATCH**
- NV3 ↔ 8 ô mirror tuần 1 (202301+202401): **8/8 MATCH**
- NV4a ↔ 2 ô smoke test tuần 1 (090111/2018): **2/2 MATCH**
- NV4b ↔ 2 ô WB smoke test tuần 1 (VNM 2024): **2/2 MATCH**
- Audit coverage: ô nào thiếu tháng, dùng preview API kiểm lại **từng tháng thiếu trùng khớp** (3/3 ô cảnh báo đều do nguồn, chứng minh ở docs/09 §2b và log điều tra tuần này).
- Tính xác định: WB/WITS chạy trên 2 máy độc lập cho **cùng từng con số** (300/300, 61/61) — pipeline tất định, không phụ thuộc phiên gọi.

## 5. Năm 'case study' kỹ thuật trong tuần (đưa vào slide bảo vệ được)

1. **Cú pháp API đổi theo phiên bản**: colon-range (`period=a:b`) bị API mới từ chối 400 → chuyển comma-list theo docs chính thức; gate bằng check 3b trước khi thiết kế batch (docs/07).
2. **Revision mã HS 2022** phát hiện qua *audit coverage* (851713 chỉ 24/108 tháng): xử lý bằng bridge 851712 + cột `maps_to_hs6` + ghi chú 'xấp xỉ có chủ đích' — không im lặng, không đổi phạm vi hồi tố (docs/09).
3. **Bug thật do selftest bắt được trước production**: `partnerCode=0` (World) là số nguyên falsy bị `or ''` nuốt → staging sai 2 cột; vá + regression test; dữ liệu đã cache rebuild bằng `--rebuild-only` **0 call API**.
4. **Annual ≠ Σ tháng là đặc tính của UN Comtrade** (lưu trữ cũ gộp ước định): điều tra bằng nguồn thứ hai tới 3 số thập phân, đặt luật 'năm của ta = Σ tháng; số A chỉ dùng QA ngưỡng tương đối' (docs/09 §2b).
5. **Khung kiểm chứng 2 nguồn**: validation cùng thời điểm (key vs preview — NV1 check 4), khác thời điểm (5+8 ô khớp từng cent), khác máy (WB/WITS determinism). Hội đồng hỏi 'sao tin dữ liệu API?' → đưa đúng mục này.

## 6. Vấn đề ghi nhận — KHÔNG xử lý trong tuần 2 (có lý do)

- Monthly của TQ trên Comtrade bắt đầu 2016 → VN–TQ không đối soát monthly được 2015; annual A/2015 có dữ liệu (đã probe 47,9M USD cà phê) — D3 ghi chú, không bịa bridge.
- WITS PREF dừng 2021 & Mỹ NO_DATA: D4 thiết kế 4 thị trường MFN (2015–2023); PREF chỉ vẽ khi đủ chuỗi, chú thích năm cắt.
- 2024 VN: giữ 0 dòng làm bằng chứng; **trước bảo vệ chạy lại** `extract_comtrade_core.py --years 2024 --force` (2 call) để húp dữ liệu nếu nguồn nhả thêm.

## 7. Kế hoạch tuần 3 (theo kế hoạch 12 tuần đã nộp)

- Thiết kế mô hình chiều theo **4 bước Kimball**: ma trận Bus cho 5 bảng staging trên; grain đã chốt (tháng × partner × HS6 × flow × perspective) — chỉ còn chọn chiều (calendar, commodity có cầu `hs6_original/maps_to_hs6`, partner có cờ aggregate, macro).
- DDL Star Schema + view reconciliation (cờ LOW/MOD/HIGH ≤10/≤30/>30% trên primaryValue) — chạy trực tiếp trên staging CSV tuần này, không cần gọi lại API.
- SSIS package đầu tiên: load staging → fact (bước công cụ song song với thiết kế).

## 8. Phụ lục — tái lập mọi con số trong báo cáo

```bash
python scripts/utils/verify_comtrade_key.py           # NV1
python scripts/extract/extract_comtrade_core.py --rebuild-only   # NV2 (0 call API, dung raw da cache)
python scripts/extract/extract_comtrade_bridge_hs2017.py --rebuild-only  # NV2b
python scripts/profiling/audit_week2_coverage.py       # audit
python scripts/extract/extract_comtrade_mirror.py --rebuild-only  # NV3
python scripts/extract/extract_wits_tariff.py --rebuild-only      # NV4a
python scripts/extract/extract_wb_macro.py --rebuild-only         # NV4b
python scripts/profiling/gen_week2_report.py           # bao cao nay
```
Mọi `--rebuild-only` chỉ cần file `data/raw/week2_*` trên máy — không cần key, không cần mạng.