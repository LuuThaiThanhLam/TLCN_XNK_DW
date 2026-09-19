# BRIDGE HS2017 851712 → 851713 — TUAN 2 NV2b

- Chat luc: 2026-09-19T04:11:59+00:00
- Ly do: audit coverage NV2 phat hien 851713 chi co 24/108 thang (revision HS 2022).
- Extract 851712 cho 2015–2021, X+M, 6 partner, grain thang.
- Tong dong staging: **958** → `data/staging/stg_comtrade_vn_reported_bridge.csv` (khong commit).

## 1. Dong theo flow x nam

| Flow | Nam | So dong |
|---|---:|---:|
| M | 2015 | 56 |
| M | 2016 | 64 |
| M | 2017 | 69 |
| M | 2018 | 66 |
| M | 2019 | 63 |
| M | 2020 | 72 |
| M | 2021 | 71 |
| X | 2015 | 65 |
| X | 2016 | 72 |
| X | 2017 | 72 |
| X | 2018 | 72 |
| X | 2019 | 72 |
| X | 2020 | 72 |
| X | 2021 | 72 |

## 2. Nhat ky batch

| Batch | Trang thai | So dong |
|---|---|---:|
| vnbr_X_2015 | OK | 65 |
| vnbr_X_2016 | OK | 72 |
| vnbr_X_2017 | OK | 72 |
| vnbr_X_2018 | OK | 72 |
| vnbr_X_2019 | OK | 72 |
| vnbr_X_2020 | OK | 72 |
| vnbr_X_2021 | OK | 72 |
| vnbr_M_2015 | OK | 56 |
| vnbr_M_2016 | OK | 64 |
| vnbr_M_2017 | OK | 69 |
| vnbr_M_2018 | OK | 66 |
| vnbr_M_2019 | OK | 63 |
| vnbr_M_2020 | OK | 72 |
| vnbr_M_2021 | OK | 71 |

## 3. Annual-vs-monthly (tu kiem chung noi bo)

- MATCH: 4/14 — WARN: 10. Monthly sum lay tu dong World (partner 0) cua bridge; annual tu query A cung key.

| Flow | Nam | Annual | Sum 12 thang | Ket qua |
|---|---|---:|---:|---|
| X | 2015 | 25,088,231,933.000 | 24,784,107,781.915 | ⚠️ WARN_MISMATCH |
| X | 2016 | 27,155,261,576.670 | 26,907,158,032.210 | ⚠️ WARN_MISMATCH |
| X | 2017 | 29,646,866,365.400 | 29,437,898,035.622 | ⚠️ WARN_MISMATCH |
| X | 2018 | 31,125,419,011.920 | 31,125,419,012.058 | ⚠️ WARN_MISMATCH |
| X | 2019 | 34,151,089,860.530 | 34,151,089,861.473 | ⚠️ WARN_MISMATCH |
| X | 2020 | 31,090,301,706.337 | 31,090,301,706.336 | ✅ MATCH |
| X | 2021 | 33,620,820,860.368 | 33,620,820,860.367 | ✅ MATCH |
| M | 2015 | 1,397,672,650.000 | 1,316,780,831.891 | ⚠️ WARN_MISMATCH |
| M | 2016 | 1,587,314,859.930 | 1,381,740,287.240 | ⚠️ WARN_MISMATCH |
| M | 2017 | 1,850,351,130.800 | 1,468,976,306.027 | ⚠️ WARN_MISMATCH |
| M | 2018 | 1,671,646,315.420 | 1,671,646,315.584 | ⚠️ WARN_MISMATCH |
| M | 2019 | 1,760,806,612.430 | 1,760,806,612.971 | ⚠️ WARN_MISMATCH |
| M | 2020 | 1,498,777,488.076 | 1,498,777,488.075 | ✅ MATCH |
| M | 2021 | 2,590,326,874.283 | 2,590,326,874.284 | ✅ MATCH |

## 4. Cach su dung o tang transform (tuan 3)

- Noi bridge vao bang fact: `hs6 = maps_to_hs6 (851713)` khi load, giu nguyen `hs6_original=851712` + cot `hs_nomenclature`.
- Dashboard D1 hien ghi chu: `giai doan 2015–2021 theo ma cu 8517.12 (gom ca dien thoai thuong) — bridge gan dung, kh phai map 1-1`.
- Khong trộn vao batch NV2 goc; moi layer tai liệu hóa nguồn riêng (batch_id vnbr_*).
*(Bao cao nay sinh sau khi audit NV2; fetched=True)*