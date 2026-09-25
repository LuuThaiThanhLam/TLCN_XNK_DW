# Source-to-Target Mapping v1 — TLCN Kho dữ liệu XNK Việt Nam

**Phiên bản:** v1 (Tuần 4)  
**Cập nhật:** 2026-09-25  
**Nguồn tham chiếu:** Header thực tế của 5 file staging đã có trong `data/staging/`

> **Quy ước:**  
> - **Nguồn (Source):** Tên cột CSV staging, lấy trực tiếp từ `data/staging/*.csv`  
> - **Đích (Target):** Tên cột SQL trong database `TLCN_XNK`  
> - 🔑 = thành phần Grain (có trong UQ_INDEX)  
> - 🔄 = cần tra bảng Dimension để lấy Surrogate Key (SK lookup)  
> - ⚙️ = giá trị do script ETL tự tính/sinh ra, không lấy trực tiếp từ staging  
> - ⚠️ = có luật đặc biệt từ `DW_USAGE_RULE`

---

## 1. FACT_TRADE ← `stg_comtrade_vn_reported.csv`

**Staging file:** `data/staging/stg_comtrade_vn_reported.csv`  
**Header thực tế (19 cột):**  
`batch_id, period, year, month, flow_code, reporter_code, partner_code, partner_name, is_aggregate_partner, hs6, commodity_desc, primary_value_usd, fob_value_usd, cif_value_usd, net_wgt_kg, qty, source_system, reporting_perspective, extracted_at`

| # | Cột Đích (SQL) | Cột Nguồn (Staging CSV) | Kiểu biến đổi | Ghi chú |
|:---:|---|---|:---:|---|
| 1 | `date_key` 🔑 | `period` | Cast | `CAST(period AS INT)` → đã là YYYYMM |
| 2 | `partner_key` 🔑🔄 | `partner_code` | SK Lookup | Lookup `DIM_PARTNER` WHERE `code_comtrade = partner_code` |
| 3 | `commodity_key` 🔑🔄 | `hs6` | SK Lookup | Lookup `DIM_COMMODITY` WHERE `hs6 = staging.hs6` (hs6 VN_REPORTED đã là HS2022) |
| 4 | `flow_key` 🔑🔄 | `flow_code` | SK Lookup | Lookup `DIM_FLOW` WHERE `flow_code = staging.flow_code` (`'X'`→1, `'M'`→2) |
| 5 | `perspective_key` 🔑🔄 | `reporting_perspective` | SK Lookup | Lookup `DIM_PERSPECTIVE` WHERE `code = staging.reporting_perspective` |
| 6 | `audit_key` 🔄 | `batch_id` | SK Lookup | Lookup `DIM_AUDIT` WHERE `batch_id = staging.batch_id` (INSERT trước nếu chưa có) |
| 7 | `primary_value_usd` | `primary_value_usd` | Cast | `CAST(primary_value_usd AS DECIMAL(18,3))` |
| 8 | `net_wgt_kg` | `net_wgt_kg` | Cast | `CAST(net_wgt_kg AS DECIMAL(18,3))`; NULL nếu = 0.0 và không có ý nghĩa |
| 9 | `qty` ⚠️ | `qty` | Cast | `CAST(qty AS DECIMAL(18,3))`; NULL nếu trống. **Luật R1: Cấm SUM chéo HS** |
| 10 | `fob_value_usd` | `fob_value_usd` | Cast | `CAST(fob_value_usd AS DECIMAL(18,3))`; NULL nếu = 0.0 |
| 11 | `cif_value_usd` | `cif_value_usd` | Cast | `CAST(cif_value_usd AS DECIMAL(18,3))`; NULL nếu = 0.0 |
| 12 | `hs6_reported` | `hs6` | Direct | Lưu nguyên bản — KHÔNG quy đổi về HS2022 (As-Is) |
| 13 | `reporter_code` | `reporter_code` | Direct | CHAR(3) |
| 14 | `partner_code_src` | `partner_code` | Direct | CHAR(3); dùng lọc World (`'0'`) trong View |
| 15 | `is_aggregate_partner` | `is_aggregate_partner` | Cast | `CASE WHEN is_aggregate_partner='True' THEN 1 ELSE 0 END` |
| 16 | `year` | `year` | Cast | `CAST(year AS SMALLINT)` |
| 17 | `month` | `month` | Cast | `CAST(month AS TINYINT)` |
| 18 | `mirror_role` | *(không có)* | ⚙️ Gán cứng | `NULL` — dòng VN_REPORTED không có mirror_role |
| 19 | `is_reported` | *(không có)* | ⚙️ Gán cứng | `NULL` — chờ kết quả `check_is_reported.py` (Q6) |

**Lệnh nạp:** `MERGE` (UPSERT) theo `UQ_FT_GRAIN (date_key, partner_key, commodity_key, flow_key, perspective_key)`.  
**Kiểm tra trùng Grain trước khi nạp:**
```sql
-- Chạy trước khi MERGE; nếu > 0 → DỪNG, kiểm tra staging
SELECT period, partner_code, hs6, flow_code, COUNT(*)
FROM staging.stg_comtrade_vn_reported
GROUP BY period, partner_code, hs6, flow_code
HAVING COUNT(*) > 1;
```

---

## 2. FACT_TRADE ← `stg_comtrade_partner_mirror.csv`

**Staging file:** `data/staging/stg_comtrade_partner_mirror.csv`  
**Header thực tế (24 cột):**  
`batch_id, period, year, month, flow_code, reporter_code, partner_code, partner_name, is_aggregate_partner, hs6, commodity_desc, primary_value_usd, fob_value_usd, cif_value_usd, net_wgt_kg, qty, source_system, reporting_perspective, extracted_at, is_reported, mirror_role, hs6_original, maps_to_hs6, hs_nomenclature`

> **Lưu ý quan trọng:** Staging mirror có `reporter_code` = mã đối tác (người đang báo cáo), `partner_code` = '704' (Việt Nam). Khi nạp vào `FACT_TRADE`, cần **đổi chiều** để `partner_key` luôn trỏ về đối tác TM của VN.

| # | Cột Đích (SQL) | Cột Nguồn (Staging CSV) | Kiểu biến đổi | Ghi chú |
|:---:|---|---|:---:|---|
| 1 | `date_key` 🔑 | `period` | Cast | `CAST(period AS INT)` |
| 2 | `partner_key` 🔑🔄 | `reporter_code` | SK Lookup | **DÙNG `reporter_code`** (đối tác đang báo về VN) → Lookup `DIM_PARTNER.code_comtrade` |
| 3 | `commodity_key` 🔑🔄 | `maps_to_hs6` hoặc `hs6` | SK Lookup | `COALESCE(NULLIF(maps_to_hs6,''), hs6)` → Lookup `DIM_COMMODITY.hs6` |
| 4 | `flow_key` 🔑🔄 | `flow_code` | SK Lookup | Lookup `DIM_FLOW` WHERE `flow_code = staging.flow_code` |
| 5 | `perspective_key` 🔑🔄 | `reporting_perspective` | SK Lookup | Lookup `DIM_PERSPECTIVE` WHERE `code = 'PARTNER_MIRROR'` |
| 6 | `audit_key` 🔄 | `batch_id` | SK Lookup | Lookup `DIM_AUDIT.batch_id` |
| 7 | `primary_value_usd` | `primary_value_usd` | Cast | `CAST(primary_value_usd AS DECIMAL(18,3))` |
| 8 | `net_wgt_kg` | `net_wgt_kg` | Cast | `CAST(net_wgt_kg AS DECIMAL(18,3))`; NULL nếu = 0 |
| 9 | `qty` ⚠️ | `qty` | Cast | `CAST(qty AS DECIMAL(18,3))`; **Luật R1** |
| 10 | `fob_value_usd` | `fob_value_usd` | Cast | NULL nếu = 0 |
| 11 | `cif_value_usd` | `cif_value_usd` | Cast | NULL nếu = 0 |
| 12 | `hs6_reported` | `hs6_original` | Direct | Mã gốc nguyên bản trước khi ánh xạ (As-Is) |
| 13 | `reporter_code` | `reporter_code` | Direct | Mã đối tác đang báo cáo |
| 14 | `partner_code_src` | `partner_code` | Direct | = '704' (VN) — vì mirror báo về VN |
| 15 | `is_aggregate_partner` | `is_aggregate_partner` | Cast | `CASE WHEN is_aggregate_partner='FALSE' THEN 0 ELSE 1 END` |
| 16 | `year` | `year` | Cast | `CAST(year AS SMALLINT)` |
| 17 | `month` | `month` | Cast | `CAST(month AS TINYINT)` |
| 18 | `mirror_role` | `mirror_role` | Direct | Giữ nguyên: `RECON_VN_EXPORT`, `RECON_VN_IMPORT`, `INFO_EXTRA` |
| 19 | `is_reported` | `is_reported` | Cast | `CASE WHEN is_reported='TRUE' THEN 1 WHEN is_reported='FALSE' THEN 0 ELSE NULL END` |

---

## 3. FACT_TRADE ← `stg_comtrade_vn_reported_bridge.csv`

**Staging file:** `data/staging/stg_comtrade_vn_reported_bridge.csv`  
**Header thực tế (21 cột):**  
`batch_id, period, year, month, flow_code, reporter_code, partner_code, partner_name, is_aggregate_partner, hs6, commodity_desc, primary_value_usd, fob_value_usd, cif_value_usd, net_wgt_kg, qty, source_system, reporting_perspective, extracted_at, hs_nomenclature, maps_to_hs6`

> **Mục đích file này:** Chứa dữ liệu VN_REPORTED cho mã `851712` (HS2017) từ 2015–2021, được bridge sang `851713` (HS2022). Nạp vào **cùng bảng `FACT_TRADE`** với `stg_comtrade_vn_reported.csv`.

| # | Cột Đích (SQL) | Cột Nguồn (Staging CSV) | Kiểu biến đổi | Ghi chú |
|:---:|---|---|:---:|---|
| 1–17 | *(giống Mapping 1)* | *(giống Mapping 1)* | *(giống)* | Áp dụng y hệt mapping VN_REPORTED |
| 3 | `commodity_key` 🔑🔄 | `maps_to_hs6` | SK Lookup | **DÙNG `maps_to_hs6`** (= '851713') thay vì `hs6` (= '851712') |
| 12 | `hs6_reported` | `hs6` | Direct | Lưu nguyên bản '851712' (As-Is) |

**Kiểm tra quan trọng TRƯỚC khi nạp bridge:**
```sql
-- Đảm bảo không chồng lấp năm: 851712 (2015-2021) và 851713 (2022+) không cùng năm
-- Nếu query sau trả > 0 → DỪNG, dữ liệu bị trùng grain
SELECT ft.date_key, ft.partner_key, ft.flow_key, ft.perspective_key, COUNT(*)
FROM FACT_TRADE ft
JOIN DIM_COMMODITY dc ON ft.commodity_key = dc.commodity_key
WHERE dc.hs6 = '851713'
GROUP BY ft.date_key, ft.partner_key, ft.flow_key, ft.perspective_key
HAVING COUNT(*) > 1;
```

---

## 4. FACT_TARIFF_RATE ← `stg_wits_tariff.csv`

**Staging file:** `data/staging/stg_wits_tariff.csv`  
**Header thực tế (17 cột):**  
`combo_type, reporter_code, partner_code, hs6, year, tariff_type, rate_pct, measure, min_rate, max_rate, total_lines, pref_lines, mfn_lines, nomenclature, datatype, source_system, extracted_at`

| # | Cột Đích (SQL) | Cột Nguồn (Staging CSV) | Kiểu biến đổi | Ghi chú |
|:---:|---|---|:---:|---|
| 1 | `date_key` 🔑 | `year` | Tính toán ⚙️ | `CAST(year AS INT) * 100 + 0` → **YYYY00** (Year Sentinel). VD: 2023 → 202300 |
| 2 | `partner_key` 🔑🔄 | `partner_code` | SK Lookup | Lookup `DIM_PARTNER.code_comtrade = partner_code`. Với `combo_type='MKT_EXPORT_MFN'` dùng `reporter_code` |
| 3 | `commodity_key` 🔑🔄 | `hs6` | SK Lookup | Lookup `DIM_COMMODITY.hs6 = staging.hs6` |
| 4 | `tariff_type_key` 🔑🔄 | `tariff_type` | SK Lookup | Lookup `DIM_TARIFF_TYPE.code = staging.tariff_type` (`'MFN'`→1, `'PREF'`→2) |
| 5 | `audit_key` 🔄 | `batch_id` *(tự tạo)* | SK Lookup ⚙️ | Sinh `batch_id` từ `source_system + ngày extract` → INSERT vào `DIM_AUDIT` trước |
| 6 | `combo_code` 🔑 | `combo_type` | Direct | Giữ nguyên: `VN_IMPORT_MFN`, `VN_IMPORT_PREF`, `MKT_EXPORT_MFN` |
| 7 | `ad_valorem_pct` ⚠️ | `rate_pct` | Cast | `CAST(rate_pct AS DECIMAL(9,4))`. **Luật R2: Cấm SUM/AVG trần** |
| 8 | `measure_label` | `measure` | Direct | VD: `'SimpleAverage'` |
| 9 | `min_rate` | `min_rate` | Cast | `CAST(min_rate AS DECIMAL(9,4))` |
| 10 | `max_rate` | `max_rate` | Cast | `CAST(max_rate AS DECIMAL(9,4))` |
| 11 | `total_lines` | `total_lines` | Cast | `CAST(total_lines AS INT)` |
| 12 | `mfn_lines` | `mfn_lines` | Cast | `CAST(mfn_lines AS INT)` |
| 13 | `pref_lines` | `pref_lines` | Cast | `CAST(pref_lines AS INT)` |
| 14 | `datatype` | `datatype` | Direct | `'Reported'` hoặc `'Estimated'` |

> **⚠️ Lỗi phổ biến cần tránh:** Staging lưu `year = 2023` (INT). Nếu ETL nạp `date_key = 2023` thay vì `202300` → vi phạm `CK_TR_YEAR_SENTINEL` → SQL Server báo lỗi constraint ngay lập tức.

---

## 5. FACT_MACRO_INDICATOR ← `stg_wb_macro.csv`

**Staging file:** `data/staging/stg_wb_macro.csv`  
**Header thực tế (8 cột):**  
`country_iso3, country_name, indicator, indicator_name, year, value, source_system, extracted_at`

| # | Cột Đích (SQL) | Cột Nguồn (Staging CSV) | Kiểu biến đổi | Ghi chú |
|:---:|---|---|:---:|---|
| 1 | `date_key` 🔑 | `year` | Tính toán ⚙️ | `CAST(year AS INT) * 100 + 0` → **YYYY00** (Year Sentinel). VD: 2024 → 202400 |
| 2 | `partner_key` 🔑🔄 | `country_iso3` | SK Lookup | Lookup `DIM_PARTNER.iso3 = staging.country_iso3` (World Bank trả iso3, không phải code Comtrade) |
| 3 | `indicator_key` 🔑🔄 | `indicator` | SK Lookup | Lookup `DIM_INDICATOR.code_wb = staging.indicator` |
| 4 | `audit_key` 🔄 | `batch_id` *(tự tạo)* | SK Lookup ⚙️ | Sinh từ `source_system + ngày extract` → INSERT vào `DIM_AUDIT` |
| 5 | `value` | `value` | Cast | `CAST(value AS DECIMAL(18,2))`. **NULL nếu WB trả về null** — phân biệt rõ NULL ≠ 0 |

> **⚠️ Lỗi phổ biến cần tránh:** Tương tự tariff, `year` trong staging là số nguyên (VD: `2024`). Phải nhân 100 rồi cộng 0 → `202400`. Nếu quên → vi phạm `CK_MC_YEAR_SENTINEL`.

---

## 6. DIM_AUDIT ← Script ETL (INSERT trước khi nạp Fact)

`DIM_AUDIT` không có file staging riêng. Script ETL phải **tự INSERT** vào bảng này trước mỗi lần nạp Fact.

| # | Cột Đích (SQL) | Nguồn | Ghi chú |
|:---:|---|---|---|
| 1 | `batch_id` | Tham số script ETL | Quy tắc đặt tên: `{source}_{scope}_{year}`. VD: `'vn_X_2015'`, `'mir_156_2023'`, `'wits_MFN_2022'`, `'wb_macro_2024'` |
| 2 | `source_system` | Cột `source_system` trong staging | Lấy `MAX(source_system)` của batch |
| 3 | `staging_file` | Tham số script ETL | Tên file CSV. VD: `'stg_comtrade_vn_reported.csv'` |
| 4 | `raw_dir` | Tham số script ETL | Thư mục raw. VD: `'data/raw/week2_extract/'` |
| 5 | `extracted_at` | Cột `extracted_at` trong staging | `MAX(CAST(extracted_at AS DATETIME2))` của batch |
| 6 | `row_count` | Đếm dòng staging | `COUNT(*)` trước khi MERGE |

**Pattern Python mẫu:**
```python
batch_id = f"vn_X_{year}"
cursor.execute("""
    MERGE DIM_AUDIT AS t
    USING (VALUES (?, ?, ?, ?, ?, ?)) AS s(batch_id, source_system, staging_file, raw_dir, extracted_at, row_count)
    ON t.batch_id = s.batch_id
    WHEN NOT MATCHED THEN INSERT VALUES (s.batch_id, s.source_system, s.staging_file, s.raw_dir, s.extracted_at, s.row_count);
""", batch_id, source_system, staging_file, raw_dir, extracted_at, row_count)
audit_key = cursor.execute("SELECT audit_key FROM DIM_AUDIT WHERE batch_id = ?", batch_id).fetchone()[0]
```

---

## 7. Bảng Dimension nhỏ — Seed tĩnh (không có staging file)

Các bảng sau được nạp bằng script `INSERT` cứng một lần duy nhất:

### DIM_DATE — Sinh tự động

```sql
-- Sinh dòng tháng (2015-01 → 2024-12): 120 dòng
-- Sinh dòng năm sentinel (2015 → 2025): 11 dòng
-- Tổng: 131 dòng
DECLARE @y INT = 2015;
WHILE @y <= 2025 BEGIN
    -- Năm sentinel
    INSERT INTO DIM_DATE VALUES (@y*100, @y, NULL, NULL, 'YEAR', CAST(@y AS VARCHAR));
    -- 12 tháng (trừ năm 2025 nếu chưa có dữ liệu)
    IF @y <= 2024 BEGIN
        DECLARE @m INT = 1;
        WHILE @m <= 12 BEGIN
            INSERT INTO DIM_DATE VALUES (@y*100+@m, @y, (@m-1)/3+1, @m, 'MONTH', CAST(@y AS VARCHAR)+'-'+RIGHT('0'+CAST(@m AS VARCHAR),2));
            SET @m += 1;
        END
    END
    SET @y += 1;
END
```

### DIM_FLOW — 2 dòng

| flow_key | flow_code | name_vi | vn_side_meaning | mirror_side_meaning |
|:---:|:---:|---|---|---|
| 1 | X | Xuất khẩu | VN xuất hàng sang đối tác | Đối tác nhập hàng từ VN |
| 2 | M | Nhập khẩu | VN nhập hàng từ đối tác | Đối tác xuất hàng sang VN |

### DIM_PERSPECTIVE — 2 dòng

| perspective_key | code | label_vi | reliability_note |
|:---:|---|---|---|
| 1 | VN_REPORTED | Việt Nam khai | Nguồn chính thức của VN; độ trễ ~1 năm so với thời điểm giao dịch |
| 2 | PARTNER_MIRROR | Đối tác khai về VN | Thường đi trước VN ~3 năm ở kỳ kiểm; đo theo chuẩn khác (FOB/CIF) |

### DIM_TARIFF_TYPE — 2 dòng

| tariff_type_key | code | label_vi | coverage_note |
|:---:|---|---|---|
| 1 | MFN | Thuế MFN (không phân biệt nguồn gốc) | Áp dụng chung cho mọi đối tác WTO |
| 2 | PREF | Thuế ưu đãi (PREF - theo FTA) | Song phương VN dừng 2021 trên WITS miễn phí; MKT_EXPORT không có PREF |

### DIM_INDICATOR — 5 dòng

| indicator_key | code_wb | name_en | unit |
|:---:|---|---|---|
| 1 | NY.GDP.MKTP.CD | GDP (current US$) | USD |
| 2 | NY.GDP.PCAP.CD | GDP per capita (current US$) | USD |
| 3 | FP.CPI.TOTL.ZG | Inflation, consumer prices (annual %) | % |
| 4 | PA.NUS.FCRF | Official exchange rate (LCU per US$) | LCU/USD |
| 5 | NE.TRD.GNFS.ZS | Trade (% of GDP) | % |

---

## 8. Thứ tự nạp dữ liệu (Load Order)

```
Bước 1 — Seed tĩnh (chạy 1 lần):
  ├── DIM_DATE       (sinh tự động)
  ├── DIM_FLOW       (2 dòng INSERT cứng)
  ├── DIM_PERSPECTIVE (2 dòng INSERT cứng)
  ├── DIM_TARIFF_TYPE (2 dòng INSERT cứng)
  └── DIM_INDICATOR  (5 dòng INSERT cứng)

Bước 2 — Seed từ staging (Tuần 7):
  ├── DIM_PARTNER    (từ unique(partner_code) trong stg_comtrade_vn_reported)
  └── DIM_COMMODITY  (từ unique(hs6) + bridge mapping)

Bước 3 — DIM_AUDIT:
  └── INSERT batch_id trước MỖI lần nạp Fact

Bước 4 — Facts (Tuần 8):
  ├── FACT_TRADE     ← stg_comtrade_vn_reported (MERGE)
  ├── FACT_TRADE     ← stg_comtrade_vn_reported_bridge (MERGE)
  ├── FACT_TRADE     ← stg_comtrade_partner_mirror (MERGE)
  ├── FACT_TARIFF_RATE ← stg_wits_tariff (MERGE)
  └── FACT_MACRO_INDICATOR ← stg_wb_macro (MERGE)
```

> **Quy tắc vàng:** **LUÔN dùng MERGE, không dùng INSERT**. Khi re-run ETL, MERGE sẽ UPDATE dòng đã có (ghi đè `audit_key` mới) thay vì sinh lỗi vi phạm `UNIQUE INDEX`.
