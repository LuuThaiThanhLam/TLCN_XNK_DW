# HƯỚNG DẪN MỞ RỘNG KHO DỮ LIỆU LÊN TOÀN BỘ QUỐC GIA GIAO DỊCH VỚI VIỆT NAM

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**Phiên bản:** v1.0 — Tài liệu hướng phát triển tương lai  
**Ngày tạo:** 2026-10-15  
**Mục đích:** Hướng dẫn từng bước để nâng cấp hệ thống từ **6 đối tác trọng điểm** lên **toàn bộ ~200 quốc gia/vùng lãnh thổ** có giao dịch xuất nhập khẩu với Việt Nam.

> [!IMPORTANT]
> Tài liệu này là bản thiết kế cho **giai đoạn mở rộng trong tương lai** (ví dụ: Luận văn Thạc sĩ hoặc Dự án doanh nghiệp).
> Kiến trúc Star Schema và Pipeline ETL hiện tại đã được thiết kế theo dạng **module hóa**, nên việc mở rộng chủ yếu là thay đổi cấu hình đầu vào chứ **không cần đập đi xây lại hệ thống**.

---

## Mục lục

1. [Tổng quan phạm vi mở rộng](#1-tổng-quan-phạm-vi-mở-rộng)
2. [Điều kiện tiên quyết](#2-điều-kiện-tiên-quyết)
3. [Giai đoạn 1: Mở rộng tầng Extract](#3-giai-đoạn-1-mở-rộng-tầng-extract-cào-dữ-liệu)
4. [Giai đoạn 2: Mở rộng tầng Transform & Load](#4-giai-đoạn-2-mở-rộng-tầng-transform--load-biến-đổi-và-nạp)
5. [Giai đoạn 3: Xử lý dữ liệu khuyết (Mirror Imputation)](#5-giai-đoạn-3-xử-lý-dữ-liệu-khuyết-mirror-imputation)
6. [Giai đoạn 4: Tối ưu hiệu năng cho dữ liệu lớn](#6-giai-đoạn-4-tối-ưu-hiệu-năng-cho-dữ-liệu-lớn)
7. [Giai đoạn 5: Nâng cấp tầng phân tích và Dashboard](#7-giai-đoạn-5-nâng-cấp-tầng-phân-tích-và-dashboard)
8. [Ước tính khối lượng dữ liệu sau mở rộng](#8-ước-tính-khối-lượng-dữ-liệu-sau-mở-rộng)
9. [Đánh giá rủi ro và phương án giảm thiểu](#9-đánh-giá-rủi-ro-và-phương-án-giảm-thiểu)
10. [Lộ trình triển khai đề xuất](#10-lộ-trình-triển-khai-đề-xuất)

---

## 1. Tổng quan phạm vi mở rộng

### 1.1. So sánh phạm vi hiện tại và phạm vi mở rộng

| Tiêu chí | Hiện tại (v1) | Mở rộng (v2) |
| :--- | :--- | :--- |
| Số đối tác | 5 quốc gia + World | ~200 quốc gia/vùng lãnh thổ + World |
| Số mã hàng HS6 | 14 mã tiêu biểu | 14 mã (giữ nguyên) hoặc mở rộng lên 50–100 mã |
| Thời gian | 2015–2024 | 2015–2024 (giữ nguyên) |
| Số dòng FACT_TRADE | ~28.000 | ~500.000 – 1.000.000 |
| Số dòng FACT_TARIFF_RATE | ~419 | ~5.000 – 15.000 |
| Số dòng FACT_MACRO_INDICATOR | ~300 | ~6.000 – 10.000 |
| Dung lượng CSV staging | ~8.5 MB | ~300 – 500 MB |
| Thời gian cào API | ~30 phút | ~6 – 12 giờ |

### 1.2. Nguyên tắc mở rộng

1. **Không thay đổi cấu trúc Star Schema:** Các bảng `DIM_*` và `FACT_*` giữ nguyên DDL hiện tại. Chỉ thay đổi dữ liệu đầu vào.
2. **Mở rộng theo chiều ngang (Horizontal Scaling):** Thêm đối tác mới chỉ là thêm dòng vào `DIM_PARTNER`, không cần thêm cột hay thêm bảng.
3. **Bảo toàn tính Idempotent:** Lệnh `MERGE` hiện tại vẫn hoạt động đúng cho dù nạp 6 hay 200 quốc gia.
4. **Gắn nhãn minh bạch:** Mọi dữ liệu được điền khuyết từ Mirror phải được đánh dấu rõ ràng, không trộn lẫn.

---

## 2. Điều kiện tiên quyết

### 2.1. Tài khoản API

| Nguồn | Yêu cầu | Ghi chú |
| :--- | :--- | :--- |
| UN Comtrade | **Bắt buộc** có Subscription Key (miễn phí) | Gói miễn phí giới hạn ~100 request/phút. Nếu cào 200 nước, cân nhắc gói Premium ($490/năm) để có quota cao hơn |
| WITS TRAINS | Không cần Key | Máy chủ chậm, cần xử lý timeout |
| World Bank | Không cần Key | Không giới hạn đáng kể |

### 2.2. Hạ tầng phần cứng

| Hạng mục | Yêu cầu tối thiểu | Khuyến nghị |
| :--- | :--- | :--- |
| RAM | 8 GB | 16 GB (SQL Server cần RAM cho các phép `MERGE` lớn) |
| Ổ cứng trống | 2 GB | 5 GB (cho raw JSON + CSV staging + database) |
| Kết nối Internet | Ổn định | Nên có IP tĩnh để tránh bị Comtrade nghi ngờ bot |
| SQL Server | 2017+ (hỗ trợ `FORMAT='CSV'`) | 2019+ (tối ưu `MERGE` tốt hơn) |

### 2.3. Lấy danh sách đối tác đầy đủ

Gọi API Comtrade để lấy danh sách toàn bộ quốc gia đã giao dịch với Việt Nam (reporter=704):

```python
import requests

url = "https://comtradeapi.un.org/data/v1/getDA/C/A/HS"
params = {
    "reporterCode": "704",
    "period": "2023",
    "flowCode": "X,M",
    "partnerCode": "all",
    "cmdCode": "TOTAL",
    "subscription-key": "<YOUR_KEY>"
}
resp = requests.get(url, params=params)
partners = set()
for row in resp.json().get("data", []):
    partners.add((row["partnerCode"], row["partnerDesc"]))

print(f"Tổng số đối tác: {len(partners)}")
for code, name in sorted(partners):
    print(f"  {code}: {name}")
```

> [!NOTE]
> Kết quả thường trả về khoảng **180–220 đối tác** (bao gồm cả các vùng lãnh thổ như Hong Kong, Macau, và các nhóm tổng hợp như EU, ASEAN).
> Nên loại bỏ các nhóm tổng hợp (aggregate) và chỉ giữ quốc gia/vùng lãnh thổ đơn lẻ để tránh cộng trùng.

---

## 3. Giai đoạn 1: Mở rộng tầng Extract (Cào dữ liệu)

### 3.1. Sửa file cấu hình đối tác

Tạo file cấu hình `config/partners.json` để quản lý danh sách đối tác tập trung thay vì hardcode trong script:

```json
{
  "version": "2.0",
  "description": "Danh sách đối tác mở rộng",
  "partners": {
    "tier_1_core": {
      "description": "5 đối tác lõi ban đầu — dữ liệu đã kiểm chứng 100%",
      "codes": ["156", "842", "410", "392", "276"]
    },
    "tier_2_asean": {
      "description": "Khối ASEAN — đối tác khu vực quan trọng",
      "codes": ["764", "702", "360", "458", "608", "104", "116", "418", "096"]
    },
    "tier_3_fta_partners": {
      "description": "Các đối tác FTA khác — EU, CPTPP, RCEP",
      "codes": ["826", "250", "380", "528", "036", "554", "124", "484", "152", "604"]
    },
    "tier_4_emerging": {
      "description": "Thị trường mới nổi — Trung Đông, Châu Phi, Nam Mỹ",
      "codes": ["682", "784", "818", "710", "566", "076", "032", "356"]
    },
    "tier_5_remaining": {
      "description": "Tất cả quốc gia còn lại — cào sau cùng nếu còn quota API",
      "codes": ["auto_discover"]
    },
    "aggregate_control": {
      "description": "Tổng hợp dùng để tính tỷ trọng — KHÔNG xếp hạng",
      "codes": ["0"]
    }
  }
}
```

### 3.2. Sửa script Extract để đọc cấu hình

Thay đổi trong `scripts/extract/extract_comtrade_core.py`:

```python
# TRƯỚC (hardcode):
PARTNER_CODES = ["156", "842", "410", "392", "276", "0"]

# SAU (đọc từ cấu hình):
import json
with open("config/partners.json") as f:
    config = json.load(f)
PARTNER_CODES = []
for tier_name, tier_data in config["partners"].items():
    if tier_data["codes"] != ["auto_discover"]:
        PARTNER_CODES.extend(tier_data["codes"])
```

### 3.3. Chiến lược cào theo Tier (Phân tầng ưu tiên)

Để tránh bị API chặn và quản lý thời gian hiệu quả, cào dữ liệu theo **5 đợt ưu tiên giảm dần**:

```text
Đợt 1: Tier 1 (5 nước lõi)        →  ~30 phút    → Kiểm tra chất lượng ngay
Đợt 2: Tier 2 (9 nước ASEAN)      →  ~1 giờ      → Kiểm tra coverage
Đợt 3: Tier 3 (10 nước FTA)       →  ~1.5 giờ    → Kiểm tra coverage
Đợt 4: Tier 4 (8 thị trường mới)  →  ~1 giờ      → Kiểm tra coverage
Đợt 5: Tier 5 (còn lại)           →  ~4–8 giờ    → Chạy qua đêm
────────────────────────────────────────────────────────────────────────
Tổng cộng:                         →  ~8–12 giờ
```

### 3.4. Tăng cường cơ chế chống lỗi API

Bổ sung vào tất cả các script Extract:

```python
import time
import random

MAX_RETRIES = 5
BASE_SLEEP = 2.5  # giây giữa các request (tăng từ 2.2s lên 2.5s)

def call_api_with_retry(url, params, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                # Rate limited: đợi lâu hơn theo cấp số nhân
                wait = BASE_SLEEP * (2 ** attempt) + random.uniform(0, 1)
                print(f"  ⚠ Rate limited (429). Đợi {wait:.1f}s...")
                time.sleep(wait)
            elif resp.status_code == 404:
                print(f"  ℹ Không có dữ liệu (404). Bỏ qua.")
                return {"data": []}  # Trả về rỗng, không phải lỗi
            else:
                print(f"  ⚠ HTTP {resp.status_code}. Thử lại...")
                time.sleep(BASE_SLEEP * (attempt + 1))
        except requests.exceptions.Timeout:
            print(f"  ⚠ Timeout. Thử lại lần {attempt + 1}...")
            time.sleep(BASE_SLEEP * (attempt + 1))
    
    print(f"  ❌ Thất bại sau {retries} lần thử. Ghi log và tiếp tục.")
    return None  # Ghi log lỗi, không dừng toàn bộ pipeline

# Giữa mỗi request thành công:
time.sleep(BASE_SLEEP + random.uniform(0, 0.5))
```

### 3.5. Script cào Mirror mở rộng

Với Mirror, cần cào từng nước đối tác báo cáo (reporter = mã nước bạn, partner = 704):

```python
# Cào mirror cho từng đối tác
for partner_code in PARTNER_CODES:
    if partner_code == "0":
        continue  # World không có mirror
    
    params = {
        "reporterCode": partner_code,   # Nước bạn là người báo cáo
        "partnerCode": "704",           # Đối tác = Việt Nam
        "flowCode": "X,M",
        "period": "201501:202312",
        "cmdCode": ",".join(HS6_CODES),
        "subscription-key": API_KEY
    }
    data = call_api_with_retry(COMTRADE_URL, params)
    # ... lưu vào raw JSON và staging CSV
```

> [!WARNING]
> **Rủi ro lớn nhất của bước này:** Nhiều quốc gia đang phát triển không nộp dữ liệu theo tháng lên UN Comtrade. Script sẽ nhận về kết quả rỗng (`data: []`) cho các nước này. Đây KHÔNG phải lỗi — mà là thực tế khách quan cần ghi nhận trong `DIM_AUDIT`.

---

## 4. Giai đoạn 2: Mở rộng tầng Transform & Load (Biến đổi và Nạp)

### 4.1. Thay đổi DDL: Không cần!

Điểm mạnh của thiết kế hiện tại là **cấu trúc bảng không cần thay đổi**:
- `DIM_PARTNER`: Lệnh `MERGE` tự động thêm quốc gia mới khi phát hiện mã chưa tồn tại.
- `FACT_TRADE`: Grain `(date_key, partner_key, commodity_key, flow_key, perspective_key)` vẫn đúng cho mọi quốc gia.
- `DIM_AUDIT`: Tự động sinh `batch_id` mới cho từng đợt cào.

### 4.2. Bổ sung bảng tra cứu mã ISO3

Hiện tại `DIM_PARTNER` đang gán cứng mã ISO3 bằng `CASE WHEN`. Khi mở rộng lên 200 nước, cần tạo bảng tra cứu:

```sql
-- Tạo bảng tra cứu mã quốc gia (chạy một lần duy nhất)
CREATE TABLE dbo.REF_COUNTRY_CODES (
    code_comtrade    CHAR(3)      NOT NULL PRIMARY KEY,
    iso3             CHAR(3)      NULL,
    iso2             CHAR(2)      NULL,
    country_name_en  NVARCHAR(200) NOT NULL,
    country_name_vi  NVARCHAR(200) NULL,
    region           NVARCHAR(100) NULL,    -- Châu Á, Châu Âu, ...
    sub_region       NVARCHAR(100) NULL,    -- Đông Nam Á, Tây Âu, ...
    income_group     NVARCHAR(50)  NULL,    -- High, Upper-middle, ...
    is_aggregate     BIT           DEFAULT 0,
    has_fta_with_vn  BIT           DEFAULT 0,
    fta_name         NVARCHAR(200) NULL     -- EVFTA, CPTPP, RCEP, ...
);
```

Và thay đổi logic nạp `DIM_PARTNER`:

```sql
-- TRƯỚC (hardcode 7 nước):
CASE s.code WHEN '704' THEN 'VNM' WHEN '156' THEN 'CHN' ... END

-- SAU (tra bảng tự động):
MERGE dbo.DIM_PARTNER AS t
USING (
    SELECT DISTINCT 
        LTRIM(RTRIM(partner_code)) AS code,
        ref.iso3,
        ref.country_name_en AS partner_name,
        ref.region,
        ref.sub_region,
        ref.income_group,
        ref.has_fta_with_vn,
        ref.fta_name,
        CASE WHEN LTRIM(RTRIM(partner_code)) = '0' THEN 1 ELSE 0 END AS is_aggregate
    FROM lz.vn_reported vr
    LEFT JOIN dbo.REF_COUNTRY_CODES ref 
        ON ref.code_comtrade = LTRIM(RTRIM(vr.partner_code))
) AS s
ON t.code_comtrade = s.code
WHEN MATCHED THEN UPDATE SET partner_name = s.partner_name, iso3 = s.iso3
WHEN NOT MATCHED THEN INSERT (...) VALUES (...);
```

### 4.3. Bổ sung cột phân nhóm khu vực vào DIM_PARTNER

```sql
ALTER TABLE dbo.DIM_PARTNER ADD
    region         NVARCHAR(100) NULL,    -- Châu Á, Châu Âu, Châu Mỹ, ...
    sub_region     NVARCHAR(100) NULL,    -- Đông Nam Á, Đông Bắc Á, Tây Âu, ...
    income_group   NVARCHAR(50)  NULL,    -- High income, Upper-middle income, ...
    has_fta_with_vn BIT          DEFAULT 0,
    fta_name       NVARCHAR(200) NULL;
```

Các cột mới này giúp Dashboard có thể:
- Lọc/Nhóm theo khu vực địa lý (ASEAN, EU, Bắc Mỹ...).
- Phân tích theo nhóm thu nhập quốc gia (nước phát triển vs đang phát triển).
- Lọc riêng các nước có FTA với Việt Nam.

---

## 5. Giai đoạn 3: Xử lý dữ liệu khuyết (Mirror Imputation)

> [!CAUTION]
> Đây là phần phức tạp nhất và nhạy cảm nhất của toàn bộ quá trình mở rộng.
> Việc "lấp đầy" dữ liệu thiếu bằng số liệu gương phải tuân thủ nghiêm ngặt các nguyên tắc dưới đây để không phá hỏng tính toàn vẹn của Kho dữ liệu.

### 5.1. Nguyên tắc vàng: KHÔNG BAO GIỜ TRỘN LẪN

```text
   ╔═══════════════════════════════════════════════════════════════╗
   ║  SỐ LIỆU CHÍNH THỨC (VN_REPORTED)                          ║
   ║  và SỐ LIỆU ƯỚC TÍNH (MIRROR_ESTIMATED)                   ║
   ║  PHẢI LUÔN LUÔN ĐƯỢC LƯU TRỮ TRONG CÁC CỘT/BẢNG RIÊNG   ║
   ║  VÀ ĐƯỢC GẮN NHÃN PHÂN BIỆT RÕ RÀNG.                      ║
   ╚═══════════════════════════════════════════════════════════════╝
```

### 5.2. Tạo bảng hệ số điều chỉnh CIF/FOB

Khi lấy số Mirror để bù, phải quy đổi từ cơ sở tính giá CIF (của nước nhập) sang FOB (của nước xuất):

```sql
CREATE TABLE dbo.REF_CIF_FOB_FACTOR (
    commodity_group  NVARCHAR(50)  NOT NULL,  -- Nông sản, Điện tử, Dệt may, ...
    transport_route  NVARCHAR(50)  NOT NULL,  -- INTRA_ASIA, TRANS_PACIFIC, ...
    factor_pct       DECIMAL(5,2)  NOT NULL,  -- Hệ số ước tính (VD: 7.5 = lệch 7.5%)
    source_reference NVARCHAR(200) NULL,      -- Nguồn tham khảo (IMF, OECD, ...)
    PRIMARY KEY (commodity_group, transport_route)
);

-- Dữ liệu mẫu dựa trên nghiên cứu của IMF và OECD:
INSERT INTO dbo.REF_CIF_FOB_FACTOR VALUES
('Nông sản',                'INTRA_ASIA',      5.0,  'OECD Trade Facilitation 2020'),
('Nông sản',                'TRANS_PACIFIC',   12.0, 'IMF DOTS methodology'),
('Nông sản',                'ASIA_EUROPE',     10.0, 'IMF DOTS methodology'),
('Điện tử & Viễn thông',   'INTRA_ASIA',      2.5,  'OECD Trade Facilitation 2020'),
('Điện tử & Viễn thông',   'TRANS_PACIFIC',    4.0, 'IMF DOTS methodology'),
('Điện tử & Viễn thông',   'ASIA_EUROPE',      3.5, 'IMF DOTS methodology'),
('Dệt may & Da giày',      'INTRA_ASIA',       4.0, 'OECD Trade Facilitation 2020'),
('Dệt may & Da giày',      'TRANS_PACIFIC',    8.0, 'IMF DOTS methodology'),
('Dệt may & Da giày',      'ASIA_EUROPE',      7.0, 'IMF DOTS methodology'),
('Nguyên vật liệu',        'INTRA_ASIA',       8.0, 'OECD Trade Facilitation 2020'),
('Nguyên vật liệu',        'TRANS_PACIFIC',   18.0, 'IMF DOTS methodology'),
('Nguyên vật liệu',        'ASIA_EUROPE',     15.0, 'IMF DOTS methodology'),
('Mặc định',               'UNKNOWN',          6.0, 'IMF global average estimate');
```

### 5.3. Tạo View ước tính có điều chỉnh CIF→FOB

```sql
CREATE OR ALTER VIEW dbo.VW_TRADE_BEST_ESTIMATE AS
WITH base AS (
    SELECT 
        f.date_key, f.partner_key, f.commodity_key, f.flow_key,
        f.primary_value_usd,
        f.perspective_key,
        dc.commodity_group,
        dp.sub_region
    FROM dbo.FACT_TRADE f
    JOIN dbo.DIM_COMMODITY dc ON dc.commodity_key = f.commodity_key
    JOIN dbo.DIM_PARTNER dp ON dp.partner_key = f.partner_key
),
vn AS (
    SELECT date_key, partner_key, commodity_key, flow_key, 
           primary_value_usd AS vn_value
    FROM base WHERE perspective_key = 1
),
mi AS (
    SELECT date_key, partner_key, commodity_key,
           CASE flow_key WHEN 1 THEN 2 ELSE 1 END AS flow_key,
           primary_value_usd AS mirror_value_raw,
           commodity_group, sub_region
    FROM base WHERE perspective_key = 2
)
SELECT
    COALESCE(vn.date_key, mi.date_key)             AS date_key,
    COALESCE(vn.partner_key, mi.partner_key)       AS partner_key,
    COALESCE(vn.commodity_key, mi.commodity_key)   AS commodity_key,
    COALESCE(vn.flow_key, mi.flow_key)             AS flow_key,
    
    -- Số liệu chính thức (có thể NULL)
    vn.vn_value,
    
    -- Số liệu gương thô (có thể NULL)
    mi.mirror_value_raw,
    
    -- Số liệu gương đã điều chỉnh CIF→FOB
    CASE 
        WHEN mi.mirror_value_raw IS NOT NULL THEN
            mi.mirror_value_raw / (1 + COALESCE(cf.factor_pct, 6.0) / 100.0)
        ELSE NULL
    END AS mirror_value_adjusted,
    
    -- SỐ LIỆU "TỐT NHẤT" (Best Estimate):
    -- Ưu tiên VN chính thức, fallback Mirror đã điều chỉnh
    CASE
        WHEN vn.vn_value IS NOT NULL THEN vn.vn_value
        WHEN mi.mirror_value_raw IS NOT NULL THEN
            mi.mirror_value_raw / (1 + COALESCE(cf.factor_pct, 6.0) / 100.0)
        ELSE NULL
    END AS best_estimate_value,
    
    -- CỜ NGUỒN GỐC: Người dùng luôn biết con số đến từ đâu
    CASE
        WHEN vn.vn_value IS NOT NULL AND mi.mirror_value_raw IS NOT NULL 
            THEN 'BOTH_AVAILABLE'
        WHEN vn.vn_value IS NOT NULL 
            THEN 'VN_OFFICIAL_ONLY'
        WHEN mi.mirror_value_raw IS NOT NULL 
            THEN 'MIRROR_ESTIMATED'
        ELSE 'NO_DATA'
    END AS data_source_flag,
    
    -- Hệ số CIF/FOB đã áp dụng (nếu có)
    COALESCE(cf.factor_pct, 6.0) AS cif_fob_adjustment_pct

FROM vn
FULL OUTER JOIN mi
  ON  mi.date_key      = vn.date_key
  AND mi.partner_key   = vn.partner_key
  AND mi.commodity_key = vn.commodity_key
  AND mi.flow_key      = vn.flow_key
LEFT JOIN dbo.REF_CIF_FOB_FACTOR cf
  ON  cf.commodity_group = COALESCE(mi.commodity_group, N'Mặc định')
  AND cf.transport_route = CASE 
        WHEN COALESCE(mi.sub_region, '') 
            IN (N'Đông Nam Á', N'Đông Bắc Á', N'Nam Á') 
            THEN 'INTRA_ASIA'
        WHEN COALESCE(mi.sub_region, '') 
            IN (N'Bắc Mỹ', N'Nam Mỹ') 
            THEN 'TRANS_PACIFIC'
        WHEN COALESCE(mi.sub_region, '') 
            IN (N'Tây Âu', N'Đông Âu', N'Bắc Âu', N'Nam Âu') 
            THEN 'ASIA_EUROPE'
        ELSE 'UNKNOWN'
      END;
```

### 5.4. Quy tắc sử dụng số liệu Best Estimate trên Dashboard

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    QUY TẮC HIỂN THỊ TRÊN DASHBOARD                    │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Mặc định: Dashboard CHỈ hiển thị số liệu VN chính thức (OFFICIAL) │
│                                                                       │
│ 2. Người dùng BẬT Slicer "Bao gồm số ước tính":                     │
│    → Biểu đồ hiển thị thêm vùng số ước tính bằng ĐƯỜNG NÉT ĐỨT     │
│    → Hoặc dùng MÀU NHẠT HƠN để phân biệt                            │
│    → Tooltip ghi rõ: "Số liệu ước tính từ đối tác, đã điều chỉnh    │
│      CIF→FOB với hệ số XX%"                                          │
│                                                                       │
│ 3. Bảng tổng hợp phải có cột data_source_flag để người dùng lọc     │
│                                                                       │
│ 4. NGHIÊM CẤM: Cộng gộp SUM(best_estimate_value) rồi trình bày     │
│    như thể đó là "Tổng kim ngạch chính thức của Việt Nam"             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Giai đoạn 4: Tối ưu hiệu năng cho dữ liệu lớn

### 6.1. Phân vùng bảng Fact theo năm (Table Partitioning)

Khi FACT_TRADE vượt 500.000 dòng, nên phân vùng theo năm:

```sql
-- Tạo Partition Function theo năm (date_key / 100 = năm)
CREATE PARTITION FUNCTION pf_trade_year (INT) AS
RANGE RIGHT FOR VALUES (201600, 201700, 201800, 201900, 202000, 
                         202100, 202200, 202300, 202400);

CREATE PARTITION SCHEME ps_trade_year AS
PARTITION pf_trade_year ALL TO ([PRIMARY]);

-- Lưu ý: Áp dụng khi dữ liệu đã lớn thực sự (> 500K dòng)
```

### 6.2. Thêm Index tối ưu truy vấn

```sql
-- Index phục vụ Dashboard lọc theo khu vực
CREATE NONCLUSTERED INDEX IX_PARTNER_REGION 
ON dbo.DIM_PARTNER (region, sub_region) 
INCLUDE (partner_name, iso3);

-- Index phục vụ View Best Estimate
CREATE NONCLUSTERED INDEX IX_FACT_TRADE_PERSPECTIVE 
ON dbo.FACT_TRADE (perspective_key, partner_key, date_key) 
INCLUDE (primary_value_usd, commodity_key, flow_key);

-- Index phục vụ Reconciliation mở rộng
CREATE NONCLUSTERED INDEX IX_FACT_TRADE_RECON 
ON dbo.FACT_TRADE (date_key, partner_key, commodity_key, flow_key, perspective_key)
INCLUDE (primary_value_usd);
```

### 6.3. Vật chất hóa View (Materialized View)

Khi dữ liệu lớn, View ảo sẽ chạy chậm. Cần tạo bảng vật lý và cập nhật định kỳ:

```sql
-- Tạo bảng vật lý chứa kết quả đối chiếu
SELECT * INTO dbo.MAT_TRADE_RECONCILIATION
FROM dbo.VW_TRADE_RECONCILIATION;

-- Tạo index trên bảng vật lý
CREATE CLUSTERED INDEX IX_MAT_RECON 
ON dbo.MAT_TRADE_RECONCILIATION 
    (date_key, partner_key, commodity_key, flow_key);

-- Script cập nhật (chạy sau mỗi lần nạp dữ liệu mới):
TRUNCATE TABLE dbo.MAT_TRADE_RECONCILIATION;
INSERT INTO dbo.MAT_TRADE_RECONCILIATION
SELECT * FROM dbo.VW_TRADE_RECONCILIATION;
```

### 6.4. Chia nhỏ MERGE theo batch khi dữ liệu lớn

```sql
-- Thay vì MERGE toàn bộ 500K dòng cùng lúc:
-- Chia theo từng năm để giảm áp lực khóa bảng (Lock Escalation)

DECLARE @year INT = 2015;
WHILE @year <= 2024 BEGIN
    MERGE INTO dbo.FACT_TRADE AS Target
    USING (
        SELECT ...
        FROM lz.vn_reported s
        WHERE TRY_CAST(s.year AS INT) = @year
        JOIN ...
    ) AS Source
    ON (Target.date_key = Source.date_key AND ...)
    WHEN MATCHED THEN UPDATE SET ...
    WHEN NOT MATCHED THEN INSERT ...;
    
    PRINT CONCAT(N'FACT_TRADE năm ', @year, N': ', @@ROWCOUNT, N' dòng');
    SET @year = @year + 1;
END
```

---

## 7. Giai đoạn 5: Nâng cấp tầng phân tích và Dashboard

### 7.1. Câu truy vấn OLAP mới cho phạm vi mở rộng

```sql
-- Phân tích theo khu vực địa lý (MỚI)
SELECT 
    dp.region,
    dp.sub_region,
    dd.calendar_year,
    df.flow_desc,
    SUM(ft.primary_value_usd) AS total_value,
    COUNT(DISTINCT dp.partner_key) AS num_partners
FROM dbo.FACT_TRADE ft
JOIN dbo.DIM_PARTNER dp ON dp.partner_key = ft.partner_key
JOIN dbo.DIM_DATE dd ON dd.date_key = ft.date_key
JOIN dbo.DIM_FLOW df ON df.flow_key = ft.flow_key
WHERE ft.perspective_key = 1          -- Chỉ số VN chính thức
  AND dp.is_aggregate = 0             -- Loại World
  AND dd.granularity = 'MONTH'
GROUP BY GROUPING SETS (
    (dp.region, dd.calendar_year, df.flow_desc),
    (dp.region, dp.sub_region, dd.calendar_year, df.flow_desc),
    (dd.calendar_year, df.flow_desc)  -- Tổng toàn cầu
);

-- Phân tích FTA vs Non-FTA (MỚI)
SELECT 
    CASE WHEN dp.has_fta_with_vn = 1 
         THEN N'Có FTA' ELSE N'Không FTA' END AS fta_status,
    dd.calendar_year,
    SUM(ft.primary_value_usd) AS total_value,
    COUNT(DISTINCT dp.partner_key) AS num_partners
FROM dbo.FACT_TRADE ft
JOIN dbo.DIM_PARTNER dp ON dp.partner_key = ft.partner_key
JOIN dbo.DIM_DATE dd ON dd.date_key = ft.date_key
WHERE ft.perspective_key = 1 AND dp.is_aggregate = 0
GROUP BY dp.has_fta_with_vn, dd.calendar_year;

-- Tỷ lệ coverage dữ liệu theo khu vực (MỚI)
SELECT 
    dp.region,
    COUNT(*) AS total_cells,
    SUM(CASE WHEN be.data_source_flag = 'BOTH_AVAILABLE' 
        THEN 1 ELSE 0 END) AS both_available,
    SUM(CASE WHEN be.data_source_flag = 'VN_OFFICIAL_ONLY' 
        THEN 1 ELSE 0 END) AS vn_only,
    SUM(CASE WHEN be.data_source_flag = 'MIRROR_ESTIMATED' 
        THEN 1 ELSE 0 END) AS mirror_only,
    SUM(CASE WHEN be.data_source_flag = 'NO_DATA' 
        THEN 1 ELSE 0 END) AS no_data,
    CAST(100.0 * SUM(CASE WHEN be.data_source_flag 
        IN ('BOTH_AVAILABLE','VN_OFFICIAL_ONLY') 
        THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) 
        AS DECIMAL(5,1)) AS vn_coverage_pct
FROM dbo.VW_TRADE_BEST_ESTIMATE be
JOIN dbo.DIM_PARTNER dp ON dp.partner_key = be.partner_key
GROUP BY dp.region
ORDER BY vn_coverage_pct;
```

### 7.2. Dashboard mới bổ sung

| # | Dashboard mới | Nội dung | Ghi chú |
| :--- | :--- | :--- | :--- |
| D6 | **Bản đồ thương mại toàn cầu** | Bản đồ thế giới (Choropleth Map) tô màu kim ngạch theo quốc gia. Bấm vào nước nào sẽ drill-down chi tiết mặt hàng | Cần file GeoJSON hoặc TopoJSON bản đồ thế giới |
| D7 | **Phân tích theo Khu vực & Khối kinh tế** | So sánh ASEAN vs EU vs Bắc Mỹ. Tỷ trọng FTA vs Non-FTA. Biểu đồ Treemap phân cấp Region → Country → HS6 | Dùng cột `region`, `sub_region` mới |
| D8 | **Bảng điều khiển Chất lượng dữ liệu** | Bản đồ nhiệt hiển thị coverage: ô nào có số VN chính thức (xanh), ô nào phải dùng Mirror (vàng), ô nào hoàn toàn trống (đỏ) | Giúp người dùng biết khu vực nào đáng tin, khu vực nào cần cẩn trọng |

---

## 8. Ước tính khối lượng dữ liệu sau mở rộng

### 8.1. Bảng ước lượng chi tiết

| Layer | Công thức | Ước tính |
| :--- | :--- | :--- |
| **FACT_TRADE (VN_REPORTED)** | 14 HS6 × 200 nước × 2 flow × 108 tháng | ≤ 604.800 dòng (thực tế ~300.000 vì nhiều tổ hợp không có giao dịch) |
| **FACT_TRADE (MIRROR)** | 14 HS6 × 200 nước × 2 flow × 108 tháng | ≤ 604.800 dòng (thực tế ~150.000 vì nhiều nước không nộp Mirror) |
| **FACT_TARIFF_RATE** | 14 HS6 × 200 nước × 2 loại × 8 năm | ≤ 44.800 dòng (thực tế ~5.000–10.000 vì WITS rất thưa) |
| **FACT_MACRO_INDICATOR** | 5 chỉ số × 200 nước × 10 năm | ~10.000 dòng |
| **DIM_PARTNER** | | ~200 dòng |
| **DIM_AUDIT** | | ~500–1.000 dòng |
| **Tổng FACT** | | **~450.000 – 800.000 dòng** |
| **Dung lượng Database** | | ~200 – 400 MB |

### 8.2. So sánh hiệu năng truy vấn

| Loại truy vấn | Hiện tại (28K dòng) | Mở rộng (500K dòng) | Biện pháp |
| :--- | :--- | :--- | :--- |
| SELECT đơn giản | < 1 giây | 1–2 giây | Không cần tối ưu |
| GROUP BY + JOIN 3 bảng | < 1 giây | 2–5 giây | Thêm Index |
| VW_TRADE_RECONCILIATION | 1–2 giây | 10–30 giây | Vật chất hóa |
| Dashboard Power BI refresh | 2–3 giây | 15–30 giây | Import Mode thay vì DirectQuery |

---

## 9. Đánh giá rủi ro và phương án giảm thiểu

| # | Rủi ro | Mức độ | Xác suất | Phương án giảm thiểu |
| :--- | :--- | :--- | :--- | :--- |
| 1 | API Comtrade chặn IP/Key do cào quá nhiều | 🔴 Cao | Trung bình | Cào theo Tier, sleep 2.5s+, dùng cache manifest, phân bổ cào ra nhiều ngày |
| 2 | Dữ liệu nhiều nước nhỏ hoàn toàn rỗng | 🟡 Trung bình | Rất cao | Chấp nhận: ghi `NO_DATA` vào `data_source_flag`, Dashboard hiển thị vùng trống rõ ràng |
| 3 | Hệ số CIF/FOB ước tính không chính xác cho mọi tuyến | 🟡 Trung bình | Cao | Ghi rõ nguồn tham chiếu (IMF, OECD), cho phép người dùng tự điều chỉnh hệ số |
| 4 | SQL Server nghẽn khi MERGE 500K dòng | 🟡 Trung bình | Trung bình | Chia nhỏ MERGE theo từng năm hoặc từng Tier đối tác; thêm Index |
| 5 | Người dùng Dashboard hiểu nhầm số ước tính là số chính thức | 🔴 Cao | Trung bình | Mặc định ẩn số ước tính; bắt buộc bật Slicer mới thấy; dùng màu/nét đứt phân biệt |
| 6 | Mã quốc gia bất đồng nhất giữa Comtrade/WITS/WB | 🟡 Trung bình | Cao | Bảng `REF_COUNTRY_CODES` làm trung tâm tra cứu, hỗ trợ ISO3/ISO2/Comtrade code |

---

## 10. Lộ trình triển khai đề xuất

### Giai đoạn A: Nền tảng (2 tuần)

```text
Tuần 1: - Tạo bảng REF_COUNTRY_CODES (nạp từ UN Statistics Division)
        - Tạo bảng REF_CIF_FOB_FACTOR
        - Sửa DIM_PARTNER: thêm cột region/sub_region/fta
        - Tạo file config/partners.json
        
Tuần 2: - Sửa script Extract để đọc cấu hình
        - Cào Tier 2 (ASEAN) làm pilot test
        - Chạy MERGE, kiểm tra tính toàn vẹn
        - Tạo View VW_TRADE_BEST_ESTIMATE
```

### Giai đoạn B: Mở rộng dần (3 tuần)

```text
Tuần 3: - Cào Tier 3 (FTA partners)
        - Cào Tier 4 (Thị trường mới nổi)
        - Kiểm tra coverage từng Tier
        
Tuần 4: - Cào Tier 5 (tất cả còn lại) — chạy qua đêm
        - Nạp toàn bộ vào SQL Server
        - Thêm Index tối ưu
        
Tuần 5: - Vật chất hóa View đối chiếu
        - Kiểm thử hiệu năng truy vấn
        - Xây Dashboard D6, D7, D8 mới
```

### Giai đoạn C: Kiểm thử và hoàn thiện (1 tuần)

```text
Tuần 6: - Chạy bộ kiểm thử nghiệm thu mở rộng
        - Đánh giá tỷ lệ coverage theo khu vực
        - Viết báo cáo so sánh v1 (6 nước) vs v2 (200 nước)
        - Cập nhật README và tài liệu
```

---

## Phụ lục: Checklist trước khi bắt đầu mở rộng

- [ ] Đã có Comtrade Subscription Key hoạt động
- [ ] Đã backup toàn bộ database `TLCN_XNK` hiện tại
- [ ] Đã tạo bảng `REF_COUNTRY_CODES` và nạp đủ ~250 mã quốc gia
- [ ] Đã tạo bảng `REF_CIF_FOB_FACTOR` với hệ số mặc định
- [ ] Đã tạo file `config/partners.json` với phân Tier
- [ ] Đã sửa script Extract để đọc cấu hình thay vì hardcode
- [ ] Đã test thử cào 1 Tier nhỏ (ASEAN) thành công
- [ ] Đã kiểm tra ổ cứng còn trống ≥ 5 GB
- [ ] Đã xác nhận SQL Server RAM ≥ 8 GB

---

> [!TIP]
> **Lời khuyên cuối:** Hãy mở rộng **từng bước, từng Tier** thay vì cào ồ ạt 200 nước cùng lúc. Sau mỗi Tier, dừng lại kiểm tra coverage và chất lượng dữ liệu. Nếu Tier nào có tỷ lệ rỗng (NO_DATA) quá cao (>80%), cân nhắc loại bỏ khỏi Dashboard chính để tránh làm loãng phân tích.
