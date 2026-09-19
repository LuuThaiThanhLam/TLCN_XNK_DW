# WB MACRO — TUAN 2 NV4b

- Chat luc: 2026-09-19T05:01:17+00:00 | Pham vi: 5 chi so x 6 nuoc x 2015:2024
- Tong dong staging: **300** → `data/staging/stg_wb_macro.csv` (khong commit)

| Country | So dong |
|---|---:|
| CHN | 50 |
| DEU | 50 |
| JPN | 50 |
| KOR | 50 |
| USA | 50 |
| VNM | 50 |

## Validation vs smoke test tuan 1 (VNM 2024)

| Case | Tuan 1 | Bay gio | Lech | Ket qua |
|---|---:|---:|---:|---|
| VNM NY.GDP.MKTP.CD 2024 | 476,324,572,783.8070 | 476,324,572,783.8070 | 0.000% | ✅ MATCH |
| VNM PA.NUS.FCRF 2024 | 24,164.8858 | 24,164.8858 | 0.000% | ✅ MATCH |

## Nhat ky goi

| Indicator | HTTP/OK | So dong | Ghi chu |
|---|---|---:|---|
| NY.GDP.MKTP.CD | OK | 60 | API total=60 |
| NY.GDP.PCAP.CD | OK | 60 | API total=60 |
| FP.CPI.TOTL.ZG | OK | 60 | API total=60 |
| PA.NUS.FCRF | OK | 60 | API total=60 |
| NE.TRD.GNFS.ZS | OK | 60 | API total=60 |

## Ghi chu
- Gia tri null cua WB (nam chua phat hanh) duoc loai — vi du nam 2024 co the thieu o vai nuoc/vai chi so: day la coverage thuc cua nguon, ghi nguyen trong bao cao NV5. Neu mot indicator tra 0 dong, do la API_ERROR (log FAIL), khong im lang.
- Khong dung macro de suy nguyen nhan; chi la truc tham chieu (docs/06).