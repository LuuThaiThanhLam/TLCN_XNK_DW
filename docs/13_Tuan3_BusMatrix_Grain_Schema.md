# docs/13 — Tuần 3: Bus matrix, khai báo grain và schema sao chi tiết

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

> **Vị trí tài liệu:** Triển khai chi tiết phần "Lược đồ sao chốt" của `docs/06 §5` —
> docs/06 vẫn là văn bản phạm vi có hiệu lực; tài liệu này **không sửa hồi tố** docs/06,
> mọi điểm chi tiết hóa khác bản phác đều đánh số Q và nêu lý do ở §8.
> **Đầu vào:** 5 file staging Tuần 2 trên máy (cột thật của chúng, không phải trí nhớ).
> **Người review:** bạn Dương — mục tiêu duyệt ở góc nghiệp vụ trước khi viết DDL (mục 9).

---

## 1. Business process (4 quy trình nghiệp vụ được mô hình hóa)

| BP | Quy trình | Nguồn | Bảng staging | Sản lượng đã kiểm chứng |
|---|---|---|---|---:|
| BP1 | Việt Nam khai báo kim ngạch XNK theo tháng (VN_REPORTED) | UN Comtrade `data/v1/get` | `stg_comtrade_vn_reported.csv` + `stg_comtrade_vn_reported_bridge.csv` | 13.725 + 958 dòng |
| BP2 | Đối tác khai báo kim ngạch với Việt Nam theo tháng (PARTNER_MIRROR) | cùng API, reporter = đối tác | `stg_comtrade_partner_mirror.csv` | 13.252 dòng (RECON 8.379 / INFO_EXTRA 4.873) |
| BP3 | Việt Nam/đối tác áp chế độ thuế quan cho mã hàng theo năm | WITS/TRAINS | `stg_wits_tariff.csv` | 419 dòng |
| BP4 | Bối cảnh vĩ mô theo nước theo năm | World Bank WDI | `stg_wb_macro.csv` | 300 dòng |

*Lớp đối chiếu (reconciliation) **không phải business process** — là dẫn xuất từ BP1+BP2,
nên không có dòng riêng trong bus matrix; nó là view (§6), tuần 9 mới materialize thành
`FACT_TRADE_RECONCILIATION` theo đúng kế hoạch 13 tuần.*

## 2. Bus matrix

Dấu ● = chiều tham gia khóa ngoài thật; ô trống = không áp dụng cho BP đó.

| | DIM_DATE | DIM_PARTNER | DIM_COMMODITY | DIM_FLOW | DIM_PERSPECTIVE | DIM_TARIFF_TYPE | DIM_INDICATOR | DIM_AUDIT |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **BP1** FACT_TRADE | ● | ● | ● | ● | ● | | | ● |
| **BP2** FACT_TRADE (perspective=PARTNER_MIRROR) | ● | ● | ● | ● | ● | | | ● |
| **BP3** FACT_TARIFF_RATE | ●(năm) | ● | ● | | | ● | | ● |
| **BP4** FACT_MACRO_INDICATOR | ●(năm) | ● | | | | | ● | ● |
| **VW** TRADE_RECONCILIATION (dẫn xuất) | ● | ● | ● | ● | — (pivot) | | | |

Điểm conformed cần giữ nghiêm: `DIM_PARTNER`, `DIM_COMMODITY`, `DIM_DATE` dùng chung
cho cả 4 BP — BP3/BP4 cùng granularity năm và cùng hệ mã nước (iso3 — xem Q4), nên dashboard
D4/D5 join thẳng vào D1 không cần cầu.

## 3. Khai báo grain (từng câu là một hợp đồng — không dịch lại khi code)

1. **FACT_TRADE:** *một dòng = một cam kết khai báo của một nước cho UN Comtrade về trị giá thương mại tháng (YYYYMM) giữa Việt Nam và đúng một đối tác, cho đúng một mã HS6, theo đúng một chiều (X/M), dưới đúng một góc nhìn khai báo (VN_REPORTED hoặc PARTNER_MIRROR)*. Đơn vị measure: USD. `0` là giá trị hợp lệ; thiếu kỳ là **không có dòng**, không phải dòng 0.
2. **FACT_TARIFF_RATE:** *một dòng = mức thuế áp dụng (ad valorem %) của một nước reporter đối với hàng từ một nước partner, cho một mã HS6, một loại thuế (MFN/PREF), trong một năm.*
3. **FACT_MACRO_INDICATOR:** *một dòng = giá trị một chỉ số vĩ mô của một nước trong một năm.*
4. **VW_TRADE_RECONCILIATION:** *một dòng = một ô thương mại tháng (YYYYMM × đối tác × HS6 × chiều **nhìn từ phía Việt Nam**), kèm số liệu phía VN, phía mirror và trạng thái đối chiếu.* Thế giới World không vào view (không có mirror của World).

Luậtgranularity dùng chung: grain của fact tháng **không bao giờ** được trộn với dònggranularity năm
(BP3/BP4) trong một phép cộng; năm của ta = Σ 12 tháng (luật đã chốt docs/09 §2b — số
năm UN công bố chỉ dùng QA).

## 4. Nhóm chiều — đặc tả và seed

### 4.1 DIM_DATE
| Cột | Kiểu | Nguồn |
|---|---|---|
| date_key (PK) | INT | `period` staging — dạng `YYYYMM`; dòng năm sentinel = `YYYY00` (Q2) |
| calendar_year | SMALLINT | `year` |
| quarter | TINYINT NULL | suy ra từ month; NULL ở dòng sentinel |
| month | TINYINT NULL | `month`; NULL ở dòng sentinel |
| granularity | CHAR(5) | `'MONTH'` / `'YEAR'` |
| date_label | CHAR(7) | `2023-01` / `2023` — dùng cho slicer |

Seed: `SELECT DISTINCT TRY_CAST(period AS INT) FROM 3 bảng trade` + bảng năm của BP3/BP4. Kiểm tra sau load: dải `201501–202412`, số month-key = 120.

### 4.2 DIM_PARTNER
| Cột | Kiểu | Nguồn / quy tắc |
|---|---|---|
| partner_key (PK) | INT IDENTITY | — |
| code_comtrade (UQ) | CHAR(3) | `partner_code` phía VN_REPORTED; mirror: `reporter_code` (Q1); VN tự = `'704'`; World = `'0'` |
| partner_name | NVARCHAR(120) | `partner_name` từ dòng VN_REPORTED — **cấm** lấy từ dòng mirror (cột đó luôn mang giá trị "Vietnam") |
| iso3 | CHAR(3) NULL | map tay 7 mã: VNM/CHN/JPN/KOR/DEU/USA (+VNM cho 704), theo `stg_wb_macro` (Q4) |
| is_aggregate | BIT | `is_aggregate_partner` — chỉ World = 1 |
| is_vietnam | BIT | code='704' |
| display_order_note | NVARCHAR(60) | "World chỉ dùng kiểm tra chéo, không vào xếp hạng" (luật docs/06) |

Seed hiện có: `0` World, `156` China, `276` Germany, `392` Japan, `410` Korea, `704` Vietnam, `842` United States. (Nguồn tên: `partnerDesc` từ API — chính là `partner_name` đã commit; nếu bật universe 160×20 thì seed mở rộng, **schema giữ nguyên**.)

### 4.3 DIM_COMMODITY
| Cột | Kiểu | Nguồn / quy tắc |
|---|---|---|
| commodity_key (PK) | INT IDENTITY | — |
| hs6 (UQ) | CHAR(6) | `maps_to_hs6` nếu không rỗng, ngược lại `hs6` (Q3 — quy tắc đã ghi docs/10: bridge vào fact theo mã HS2022) |
| hs6_original | CHAR(6) | `hs6` nguyên văn từ staging — để truy vết về raw |
| hs4 | CHAR(4) | `LEFT(hs6,4)` |
| hs2 | CHAR(2) | `LEFT(hs6,2)` |
| name_en | NVARCHAR(200) | `commodity_desc` của kỳ lớn nhất có dòng (tie-break: `period DESC`, rồi `batch_id`) |
| commodity_group | NVARCHAR(60) | bảng tay 14 mã — đề xuất ở §7.1, **chờ B duyệt** |
| bridge_flag | BIT | 1 cho `851713`; 0 còn lại |
| bridge_note | NVARCHAR(160) | cho 851713: "2015–2021 theo mã cũ 851712, gồm cả điện thoại thường — xấp xỉ có chủ đích" (nguyên văn docs/09); cho `851714`: "series bắt đầu 2022 (HS2022 revision), không bridge — thiếu tuyệt đối 2015–21" |

Không có dòng HS4/HS2 riêng — roll-up bằng cột cha, đúng chỉnh sửa #6 của kế hoạch.

### 4.4 DIM_FLOW
1 = `X` "Xuất khẩu", 2 = `M` "Nhập khẩu", kèm `vn_side_meaning` / `mirror_side_meaning` NVARCHAR(120) — vì flow code luôn đọc **theo reporter của dòng đó**; ý nghĩa phía Việt Nam suy qua DIM_PERSPECTIVE (đã cảnh báo docs/04: đừng dán nhãn cứng "X = VN xuất" trên dashboard mirror).

### 4.5 DIM_PERSPECTIVE
| perspective_key | code | label_vi | reliability_note |
|---|---|---|---|
| 1 | VN_REPORTED | Việt Nam khai | "Nguồn chính thức của VN; 2024 chưa có số (độ trễ nguồn, đã chứng minh 2 lần)" |
| 2 | PARTNER_MIRROR | Đối tác khai về VN | "Đi trước VN ~3 năm ở kỳ kiểm; bù ước lượng cao hơn ở một số reporter — phân phối thật trong `results/week3/is_reported_check.md` (B chạy)" |

*(kế hoạch 13 tuần gọi `DIM_REPORTING_PERSPECTIVE` — giữ tên docs/06 `DIM_PERSPECTIVE` làm chuẩn, alias ghi ở đây.)*

### 4.6 DIM_TARIFF_TYPE
1 = MFN ("rộng nhất, không phân biệt nguồn gốc"), 2 = PREF ("ưu đãi có điều kiện theo nguồn gốc"). Coverage note (docs/11): "PREF song phương VN–đối tác dừng ở 2021; chiều đối tác không có PREF trên endpoint miễn phí".

### 4.7 DIM_INDICATOR (seed 5 dòng — đúng mã đã extract)
| indicator_key | code_wb | name_en | unit |
|---|---|---|---|
| 1 | NY.GDP.MKTP.CD | GDP (current US$) | USD |
| 2 | NY.GDP.PCAP.CD | GDP per capita (current US$) | USD |
| 3 | FP.CPI.TOTL.ZG | Inflation, CPI (annual %) | % |
| 4 | PA.NUS.FCRF | Official exchange rate (LCU per US$, period average) | LCU/USD |
| 5 | NE.TRD.GNFS.ZS | Trade (% of GDP) | % |

Ghi chú chống quay lại lỗi cũ: `BN.TOTL.GD.ZS` là mã chết (WB error 120) — đã thay bằng `NE.TRD.GNFS.ZS` và test lại (ghi trong `results/week2/wb_macro.md`).

### 4.8 DIM_AUDIT (Q5 — docs/06 để 3 cột audit trong fact; chính thức hóa thành chiều thứ 7)
| Cột | Kiểu | Nguồn |
|---|---|---|
| audit_key (PK) | INT IDENTITY | — |
| batch_id (UQ) | VARCHAR(32) | `batch_id` staging (`w2_X_2015`, `mir_156_2023`, `br_…`…) |
| source_system | VARCHAR(80) | `source_system` staging |
| extracted_at | DATETIME2(0) | `MAX(extracted_at)` của batch |
| staging_file | VARCHAR(120) | tên file csv nguồn |
| raw_dir | VARCHAR(120) | `data/raw/week2_extract/` — nơi response thô của batch |

Mọi fact đều mang `audit_key` → mọi con số trên dashboard click được về batch + response thô.

## 5. Nhóm fact — source-to-target mapping

### 5.1 FACT_TRADE (BP1 + BP2 — hai perspective trong MỘT bảng, không bao giờ cộng chéo perspective chưa lọc)

| Cột | Kiểu | Nguồn staging | Ghi chú |
|---|---|---|---|
| trade_key | INT IDENTITY PK | — | |
| date_key | INT | `CAST(period AS INT)` | |
| partner_key | INT FK | Q1: VN→`partner_code`; MIRROR→`reporter_code` | DIM_PARTNER |
| commodity_key | INT FK | `COALESCE(NULLIF(maps_to_hs6,''), hs6)` | Q3 |
| flow_key | TINYINT FK | X→1, M→2 | |
| perspective_key | TINYINT FK | `reporting_perspective` | |
| audit_key | INT FK | `batch_id` | |
| primary_value_usd | DECIMAL(18,3) NOT NULL | cùng tên | measure chính |
| net_wgt_kg | DECIMAL(18,3) NULL | `net_wgt_kg` | tham khảo — đơn vị kg, nhiều dòng null |
| qty | DECIMAL(18,3) NULL | `qty` | **không cộng khác đơn vị** — chỉ hiện khi lọc 1 mã (kế hoạch #6) |
| fob_value_usd / cif_value_usd | DECIMAL(18,3) NULL | cùng tên | Comtrade trả không đều; chỉ khi có |
| hs6_reported | CHAR(6) | `hs6` | mã nguyên văn (traceability) |
| reporter_code / partner_code_src | CHAR(3) ×2 | cùng tên | khóa thật khi đối chiếu về raw |
| is_aggregate_partner | BIT | cùng tên | bộ lọc bắt buộc khi xếp hạng |
| mirror_role | VARCHAR(20) NULL | mirror: RECON_VN_EXPORT/RECON_VN_IMPORT/INFO_EXTRA; VN: NULL | |
| is_reported | BIT NULL | cột staging mirror; VN: NULL | chờ Q6 (§9) |
| year / month | SMALLINT/TINYINT | `year`,`month` | denormalize hiệu năng |

**Unique index** `UQ_FT_GRAIN (date_key, partner_key, commodity_key, flow_key, perspective_key)`.
Điều kiện nạp (đã chứng minh được trên dữ liệu): bridge 851712→851713 (2015–2021) và core 851713 (2022+) **không chồng năm** — query V2 phải trả 0; nếu trả >0 là universe/bridge đổi, DỪNG không nạp.

### 5.2 FACT_TARIFF_RATE (BP3)

| Cột | Kiểu | Nguồn | Ghi chú |
|---|---|---|---|
| tariff_key | INT IDENTITY PK | — | |
| date_key | INT FK | `year*100` sentinel | Q2 |
| partner_key | INT FK | đối tác của dòng (VN_IMPORT_*: `partner_code`; MKT_EXPORT_*: `reporter_code`) | chiều luôn là "đối tác thương mại" |
| commodity_key | INT FK | `hs6` | |
| tariff_type_key | TINYINT FK | `tariff_type` MFN/PREF | |
| audit_key | INT FK | `batch_id` | |
| combo_code | VARCHAR(20) | `combo_type` (VN_IMPORT_MFN / VN_IMPORT_PREF / MKT_EXPORT_MFN) | hướng dẫn dùng: đọc §4 của `results/week2/wits_tariff_extract.md` — MKT_EXPORT_MFN là xấp xỉ "MFN thị trường áp lên hàng VN", không phải thuế song phương |
| ad_valorem_pct | DECIMAL(9,4) NULL | `rate_pct` | **measure không cộng được** — tổng/mean trần là lỗi; aggregation chuẩn = trung bình có quyền theo `total_lines` (chủ ý để tuần 10) |
| measure_label | VARCHAR(60) | `measure` | "SimpleAverage"… |
| min_rate / max_rate / total_lines / mfn_lines / pref_lines | INT NULL | cùng tên | nguyên liệu trọng số |
| datatype | VARCHAR(10) | cùng tên | |

Unique: `(date_key, partner_key, commodity_key, tariff_type_key, combo_code)`.

### 5.3 FACT_MACRO_INDICATOR (BP4)

| Cột | Kiểu | Nguồn | Ghi chú |
|---|---|---|---|
| macro_key | INT IDENTITY PK | — | |
| date_key | INT FK | `year*100` | Q2 |
| partner_key | INT FK | map `country_iso3` → DIM_PARTNER.iso3 | Q4 |
| indicator_key | TINYINT FK | `indicator` → DIM_INDICATOR | |
| audit_key | INT FK | `batch_id` | |
| value | DECIMAL(18,2) NULL | `value` | NULL = WB không có số (khác 0) |

Unique: `(date_key, partner_key, indicator_key)`.

## 6. Lớp đối chiếu — `VW_TRADE_RECONCILIATION` (tuần 3) → materialize tuần 9

Phối cảnh theo **ô nhìn từ phía Việt Nam**; flow mirror đọc ngược chiều (đối tác nhập = ta xuất):

```sql
CREATE OR ALTER VIEW dbo.VW_TRADE_RECONCILIATION AS
WITH vn AS (
    SELECT f.date_key, f.partner_key, f.commodity_key, f.flow_key,
           f.primary_value_usd AS vn_value
    FROM dbo.FACT_TRADE f
    WHERE f.perspective_key = 1 AND f.partner_code_src <> '0'      -- bỏ World
), mi AS (
    SELECT f.date_key, f.partner_key, f.commodity_key,
           CASE f.flow_key WHEN 1 THEN 2 ELSE 1 END AS flow_key,   -- ngược chiều
           f.primary_value_usd AS mirror_value, f.is_reported AS mirror_is_reported,
           f.mirror_role
    FROM dbo.FACT_TRADE f
    WHERE f.perspective_key = 2
)
SELECT
    COALESCE(vn.date_key, mi.date_key)         AS date_key,
    COALESCE(vn.partner_key, mi.partner_key)   AS partner_key,
    COALESCE(vn.commodity_key, mi.commodity_key) AS commodity_key,
    COALESCE(vn.flow_key, mi.flow_key)         AS flow_key,
    vn.vn_value, mi.mirror_value, mi.mirror_is_reported, mi.mirror_role,
    ABS(COALESCE(mi.mirror_value,0) - COALESCE(vn.vn_value,0)) AS abs_diff_usd,
    CASE WHEN vn.vn_value IS NULL OR vn.vn_value = 0 THEN NULL
         ELSE 100.0 * (mi.mirror_value - vn.vn_value) / vn.vn_value END AS pct_diff_vs_vn,
    CASE
        WHEN vn.vn_value IS NULL THEN 'MISSING_VN_REPORTED'
        WHEN mi.mirror_value IS NULL THEN 'MISSING_MIRROR'
        WHEN vn.vn_value = 0 THEN 'HIGH'                    -- VN khai 0, đối tác có số
        WHEN ABS(100.0*(mi.mirror_value - vn.vn_value)/vn.vn_value) <= 10 THEN 'LOW'
        WHEN ABS(100.0*(mi.mirror_value - vn.vn_value)/vn.vn_value) <= 30 THEN 'MODERATE'
        ELSE 'HIGH'
    END AS discrepancy_level,
    CASE
        WHEN vn.vn_value IS NULL THEN N'Kỳ này Việt Nam chưa công bố — số tham chiếu từ đối tác'
        WHEN mi.mirror_value IS NULL THEN N'Dữ liệu Việt Nam là nguồn duy nhất cho ô này'
        WHEN vn.vn_value = 0 THEN N'VN khai 0, đối tác khai dương — kiểm tra chiều/đơn vị trước khi dùng'
        ELSE NULL
    END AS reconciliation_note
FROM vn
FULL OUTER JOIN mi
  ON  mi.date_key = vn.date_key
  AND mi.partner_key = vn.partner_key
  AND mi.commodity_key = vn.commodity_key
  AND mi.flow_key = vn.flow_key;
```

Ràng buộc thiết kế:
- **view** không sinh số mới — chỉ ghép; **không** cộng `vn_value` với `mirror_value` ở bất kỳ đâu (kế hoạch chỉnh sửa #1).
- 5 nhãn mức khớp hệ thống nhãn Tuần 1 (`results/week1/mirror_check_results.md`) và khớp luật đã chốt docs/06: LOW ≤10% / MODERATE ≤30% / HIGH >30%.
- Tuần 9: `dbo.FACT_TRADE_RECONCILIATION` = materialize view + `reconciliation_batch`; quy tắc CASE chỉ được định nghĩa MỘT nơi (view), tuần 9 dùng `SELECT INTO` từ view — chống hai phiên bản luật lệch nhau.
- Cờ `is_reported`: hiện là cột thông tin; quyết định "filter mặc định hay không" chờ số liệu từ `check_is_reported.py` (Q6).

## 7. Phụ lục seed & mapping tay

### 7.1 `commodity_group` đề xuất cho 14 mã (chờ B duyệt — chỉ phục vụ slicer D2)
Nhóm 1 Điện tử–viễn thông: 851713, 851714, 854231, 851762, 847330, 854442 — Nhóm 2 Dệt may–giày dép: 610910, 640399, 540761 — Nhóm 3 Nông sản–thực phẩm: 090111, 090411, 100630, 080132 — Nhóm 4 Nhựa–công nghiệp nặng: 390120, 721049. *(Mã nào B muốn đổi nhóm cứ đổi; không ảnh hưởng grain/fact.)*

### 7.2 Map iso3 (DIM_PARTNER ↔ `stg_wb_macro.country_iso3`)
VNM→704, CHN→156, JPN→392, KOR→410, DEU→276, USA→842. Sáu mã — đúng số nước WB đã extract.

## 8. Năm quyết định thiết kế (Q) so với bản phác docs/06 §5 — có lý do, có thể đảo

| # | Quyết định | Lý do |
|---|---|---|
| Q1 | Dòng MIRROR: DIM_PARTNER lấy theo `reporter_code` (nước bạn tình), không tạo DIM_REPORTER riêng | grain docs/06 định nghĩa "partner = đối tác của VN" cho cả hai perspective → cùng một chiều, đối chiếu join 1 điều kiện; mã gốc vẫn còn ở `reporter_code/partner_code_src` |
| Q2 | Fact granularity năm (BP3/BP4) dùng `DIM_DATE` với sentinel `YYYY00` + cột `granularity` | một chiều thời gian conformed duy nhất (kế hoạch #4: macro không nằm ở DIM_DATE theo ngày); chặn join năm×tháng bằng `granularity` chặn ngay ở view |
| Q3 | `commodity_key` nạp theo `COALESCE(maps_to_hs6, hs6)` — mã HS2022 làm chuẩn, `hs6_reported` giữ mã gốc | đã chốt docs/10; bridge tự nhiên cho mọi cặp mã-cũ, không phải logic riêng cho điện thoại |
| Q4 | Vĩ mô dùng lại DIM_PARTNER (thêm cột `iso3`), không lập DIM_COUNTRY riêng | 6 nước trùng hệ đối tác; hai bảng chiều cùng khái niệm = bus matrix hỏng (chỉnh sửa #7 của kế hoạch: chống phình) |
| Q5 | DIM_AUDIT thành chiều thứ 7 | docs/06 để 3 cột audit trần trong fact; tách bảng thì batch_id có chỗ mang metadata (file nguồn, raw_dir) và mọi drill-through đi qua một cửa |

*Bất đồng tên đã ghi nhận, không sửa hồi tố docs/11:* docs/11 và md WITS gọi `FACT_TARIFF_ANNUAL` — **chuẩn là `FACT_TARIFF_RATE`** theo docs/06 §5 (đúng cùng một bảnggranularity năm; "ANNUAL" chỉ mô tảgranularity). Ghi chú này là nơi duy nhất hóa giải hai tên.

## 9. Việc B review + cổng bước tiếp

Câu hỏi chờ duyệt (trả lời vào mục cuối file này):
1. §7.1 nhóm ngành 14 mã — giữ hay sửa?
2. Q2 sentinel `YYYY00` — đồng ý, hay muốn tách `DIM_YEAR`?
3. Q4 một chiều quốc gia — đồng ý?
4. `qty` giữ trong fact (nullable) hay bỏ hẳn? (đơn vị không chuẩn hóa giữa mã — em nghiêng giữ làm thuộc tính, cấm SUM khi >1 mã, luật đã ghi §5.1)

Cổng kỹ thuật trước khi viết DDL (`sql/01_star_ddl.sql` + `02_load_dims.sql` + `03_load_facts.sql`, lệnh BULK INSERT/BCP):
- B chạy xong `check_is_reported.py` (việc 4, docs bàn giao) → kết quả quyết định Q6 (có filter `is_reported` trong view không) — **không chặn** DDL, chỉ chặn câu lệnh WHERE của view tuần 9.
- Chạy 6 query nghiệm thu V1–V6 (đính trong file DDL tuần sau) trên DB vừa load, kỳ vọng: V1 đúng 5 số §1; V2 trùng-grain = 0; V3 khóa mồ côi = 0; V4 neo 14/14; V5 ô validation 5+8 MATCH; V6 tổng theo perspective tách bạch.

Nếu bật universe 160×20 (chờ thầy): **schema này giữ nguyên 100%** — chỉ seed DIM to ra và dòng fact nhiều lên; đó là lý do thiết kế Tuần 3 không phụ thuộc quyết định phạm vi.
