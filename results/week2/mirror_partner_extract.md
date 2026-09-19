# MIRROR PARTNER — TUAN 2 NV3

- Chat luc: 2026-09-19T04:43:37+00:00
- Goc nhin: PARTNER_MIRROR (reporter = doi tac, partner = 704). Khong bao gio trộn số với VN_REPORTED.
- Nam: 2015–2024. Ma dien thoai tu dong chuyen theo nam (<2022: 851712; tu 2022: 851713).
- Tong dong: **13252** (RECON: 8379 | INFO_EXTRA: 4873) → `data/staging/stg_comtrade_partner_mirror.csv` (khong commit).

## 1. Validation vs mirror tuan 1 (mirror_check_results.json)

| Case tuan 1 | O kiem tra (rep/flow/hs6/period) | Gia tri tuan 1 | Gia tri mirror | Ket qua |
|---|---|---:|---:|---|
| EXP_JPN_COFFEE_202301 | 392/M/090111/202301 | 16,784,397.261 | 16,784,397.261 | ✅ MATCH |
| EXP_JPN_COFFEE_202401 | 392/M/090111/202401 | 35,660,719.503 | 35,660,719.503 | ✅ MATCH |
| EXP_USA_COFFEE_202301 | 842/M/090111/202301 | 37,790,801.000 | 37,790,801.000 | ✅ MATCH |
| EXP_DEU_COFFEE_202301 | 276/M/090111/202301 | 38,271,554.955 | 38,271,554.955 | ✅ MATCH |
| IMP_CHN_NETWORK_EQUIP_202301 | 156/X/851762/202301 | 29,945,226.000 | 29,945,226.000 | ✅ MATCH |
| IMP_KOR_INTEGRATED_CIRCUITS_202301 | 410/X/854231/202301 | 217,401,413.000 | 217,401,413.000 | ✅ MATCH |
| IMP_CHN_NETWORK_EQUIP_202401 | 156/X/851762/202401 | 62,727,085.000 | 62,727,085.000 | ✅ MATCH |
| IMP_KOR_INTEGRATED_CIRCUITS_202401 | 410/X/854231/202401 | 412,589,570.000 | 412,589,570.000 | ✅ MATCH |

- Khop: 8/8 (MISSING_IN_MIRROR o nam 2024 co the xay ra — kiem tra bang 3 truoc khi ket luan).

## 2. Coverage o RECON (so thang co du lieu / 108)

| Reporter | Vai tro | HS6 | So thang |
|---|---|---|---:|
| 156 | RECON_VN_EXPORT | 080132 | 108 |
| 156 | RECON_VN_EXPORT | 090111 | 108 |
| 156 | RECON_VN_EXPORT | 090411 | 104 |
| 156 | RECON_VN_EXPORT | 100630 | 108 |
| 156 | RECON_VN_EXPORT | 610910 | 108 |
| 156 | RECON_VN_EXPORT | 640399 | 108 |
| 156 | RECON_VN_EXPORT | 851712 | 71 |
| 156 | RECON_VN_EXPORT | 851713 | 36 |
| 156 | RECON_VN_EXPORT | 854442 | 108 |
| 156 | RECON_VN_IMPORT | 390120 | 108 |
| 156 | RECON_VN_IMPORT | 540761 | 108 |
| 156 | RECON_VN_IMPORT | 721049 | 108 |
| 156 | RECON_VN_IMPORT | 847330 | 108 |
| 156 | RECON_VN_IMPORT | 851712 | 72 |
| 156 | RECON_VN_IMPORT | 851713 | 36 |
| 156 | RECON_VN_IMPORT | 851762 | 108 |
| 156 | RECON_VN_IMPORT | 854231 | 108 |
| 276 | RECON_VN_EXPORT | 080132 | 120 |
| 276 | RECON_VN_EXPORT | 090111 | 120 |
| 276 | RECON_VN_EXPORT | 090411 | 120 |
| 276 | RECON_VN_EXPORT | 100630 | 120 |
| 276 | RECON_VN_EXPORT | 610910 | 120 |
| 276 | RECON_VN_EXPORT | 640399 | 120 |
| 276 | RECON_VN_EXPORT | 851712 | 84 |
| 276 | RECON_VN_EXPORT | 851713 | 36 |
| 276 | RECON_VN_EXPORT | 854442 | 120 |
| 276 | RECON_VN_IMPORT | 390120 | 89 |
| 276 | RECON_VN_IMPORT | 540761 | 113 |
| 276 | RECON_VN_IMPORT | 721049 | 5 |
| 276 | RECON_VN_IMPORT | 847330 | 120 |
| 276 | RECON_VN_IMPORT | 851712 | 76 |
| 276 | RECON_VN_IMPORT | 851713 | 25 |
| 276 | RECON_VN_IMPORT | 851762 | 120 |
| 276 | RECON_VN_IMPORT | 854231 | 120 |
| 392 | RECON_VN_EXPORT | 080132 | 120 |
| 392 | RECON_VN_EXPORT | 090111 | 120 |
| 392 | RECON_VN_EXPORT | 090411 | 120 |
| 392 | RECON_VN_EXPORT | 100630 | 62 |
| 392 | RECON_VN_EXPORT | 610910 | 120 |
| 392 | RECON_VN_EXPORT | 640399 | 120 |
| 392 | RECON_VN_EXPORT | 851712 | 84 |
| 392 | RECON_VN_EXPORT | 851713 | 36 |
| 392 | RECON_VN_EXPORT | 854442 | 120 |
| 392 | RECON_VN_IMPORT | 390120 | 120 |
| 392 | RECON_VN_IMPORT | 540761 | 120 |
| 392 | RECON_VN_IMPORT | 721049 | 120 |
| 392 | RECON_VN_IMPORT | 847330 | 120 |
| 392 | RECON_VN_IMPORT | 851712 | 30 |
| 392 | RECON_VN_IMPORT | 851713 | 35 |
| 392 | RECON_VN_IMPORT | 851762 | 120 |
| 392 | RECON_VN_IMPORT | 854231 | 120 |
| 410 | RECON_VN_EXPORT | 080132 | 120 |
| 410 | RECON_VN_EXPORT | 090111 | 120 |
| 410 | RECON_VN_EXPORT | 090411 | 120 |
| 410 | RECON_VN_EXPORT | 100630 | 99 |
| 410 | RECON_VN_EXPORT | 610910 | 120 |
| 410 | RECON_VN_EXPORT | 640399 | 120 |
| 410 | RECON_VN_EXPORT | 851712 | 84 |
| 410 | RECON_VN_EXPORT | 851713 | 36 |
| 410 | RECON_VN_EXPORT | 854442 | 120 |
| 410 | RECON_VN_IMPORT | 390120 | 120 |
| 410 | RECON_VN_IMPORT | 540761 | 120 |
| 410 | RECON_VN_IMPORT | 721049 | 120 |
| 410 | RECON_VN_IMPORT | 847330 | 120 |
| 410 | RECON_VN_IMPORT | 851712 | 84 |
| 410 | RECON_VN_IMPORT | 851713 | 36 |
| 410 | RECON_VN_IMPORT | 851762 | 120 |
| 410 | RECON_VN_IMPORT | 854231 | 120 |
| 842 | RECON_VN_EXPORT | 080132 | 120 |
| 842 | RECON_VN_EXPORT | 090111 | 120 |
| 842 | RECON_VN_EXPORT | 090411 | 120 |
| 842 | RECON_VN_EXPORT | 100630 | 120 |
| 842 | RECON_VN_EXPORT | 610910 | 120 |
| 842 | RECON_VN_EXPORT | 640399 | 120 |
| 842 | RECON_VN_EXPORT | 851712 | 84 |
| 842 | RECON_VN_EXPORT | 851713 | 36 |
| 842 | RECON_VN_EXPORT | 854442 | 120 |
| 842 | RECON_VN_IMPORT | 390120 | 118 |
| 842 | RECON_VN_IMPORT | 540761 | 110 |
| 842 | RECON_VN_IMPORT | 721049 | 2 |
| 842 | RECON_VN_IMPORT | 847330 | 120 |
| 842 | RECON_VN_IMPORT | 851712 | 84 |
| 842 | RECON_VN_IMPORT | 851713 | 36 |
| 842 | RECON_VN_IMPORT | 851762 | 120 |
| 842 | RECON_VN_IMPORT | 854231 | 120 |

## 3. Nhat ky batch

- Batch OK/SKIP: 50/50

| Batch | Trang thai | So dong | Mode |
|---|---|---:|---|
| mir_156_2015 | SKIP (cache) | 0 | cache |
| mir_276_2015 | SKIP (cache) | 236 | cache |
| mir_392_2015 | SKIP (cache) | 252 | cache |
| mir_410_2015 | SKIP (cache) | 262 | cache |
| mir_842_2015 | SKIP (cache) | 255 | cache |
| mir_156_2016 | OK | 276 | dual-flow |
| mir_276_2016 | OK | 245 | dual-flow |
| mir_392_2016 | OK | 250 | dual-flow |
| mir_410_2016 | OK | 280 | dual-flow |
| mir_842_2016 | OK | 264 | dual-flow |
| mir_156_2017 | OK | 286 | dual-flow |
| mir_276_2017 | OK | 251 | dual-flow |
| mir_392_2017 | OK | 249 | dual-flow |
| mir_410_2017 | OK | 294 | dual-flow |
| mir_842_2017 | OK | 268 | dual-flow |
| mir_156_2018 | OK | 288 | dual-flow |
| mir_276_2018 | OK | 266 | dual-flow |
| mir_392_2018 | OK | 250 | dual-flow |
| mir_410_2018 | OK | 286 | dual-flow |
| mir_842_2018 | OK | 265 | dual-flow |
| mir_156_2019 | OK | 290 | dual-flow |
| mir_276_2019 | OK | 260 | dual-flow |
| mir_392_2019 | OK | 255 | dual-flow |
| mir_410_2019 | OK | 286 | dual-flow |
| mir_842_2019 | OK | 265 | dual-flow |
| mir_156_2020 | OK | 288 | dual-flow |
| mir_276_2020 | OK | 266 | dual-flow |
| mir_392_2020 | OK | 254 | dual-flow |
| mir_410_2020 | OK | 285 | dual-flow |
| mir_842_2020 | OK | 262 | dual-flow |
| mir_156_2021 | OK | 286 | dual-flow |
| mir_276_2021 | OK | 257 | dual-flow |
| mir_392_2021 | OK | 266 | dual-flow |
| mir_410_2021 | OK | 286 | dual-flow |
| mir_842_2021 | OK | 258 | dual-flow |
| mir_156_2022 | OK | 287 | dual-flow |
| mir_276_2022 | OK | 263 | dual-flow |
| mir_392_2022 | OK | 272 | dual-flow |
| mir_410_2022 | OK | 290 | dual-flow |
| mir_842_2022 | OK | 270 | dual-flow |
| mir_156_2023 | OK | 294 | dual-flow |
| mir_276_2023 | OK | 263 | dual-flow |
| mir_392_2023 | OK | 270 | dual-flow |
| mir_410_2023 | OK | 292 | dual-flow |
| mir_842_2023 | OK | 271 | dual-flow |
| mir_156_2024 | OK | 292 | dual-flow |
| mir_276_2024 | OK | 272 | dual-flow |
| mir_392_2024 | OK | 268 | dual-flow |
| mir_410_2024 | OK | 297 | dual-flow |
| mir_842_2024 | OK | 264 | dual-flow |

## 4. Ghi chu su dung o transform (NV4/tuan 3)

- Join reconciliation: `mirror(period, hs6=maps_to_hs6 or hs6, reporter=p, M)` vs `vn_reported(period, hs6, partner=p, X)` (va nguoc lai cho M/VN-IMPORT).
- Chi so dung primaryValue; lech %abs = |m−v|/max(m,v); co: LOW ≤10%, MODERATE ≤30%, HIGH >30% (docs/06).
- `is_reported=false` (uoc luong cua UN) → khong dung cho so so sanh chinh; dem rieng de minh bach.
- INFO_EXTRA giu nguyen trong staging de phan tich phu, loc khi vao fact.