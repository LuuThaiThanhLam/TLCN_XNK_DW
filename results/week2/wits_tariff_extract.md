# WITS THU QUAN — TUAN 2 NV4a

- Chat luc: 2026-09-19T05:04:05+00:00 | WITS/UNCTAD TRAINS, mien phi, khong key (UA trinh duyet bat buoc — Cloudflare).
- Combo dat: 55 | NO_DATA (nuoc khong bao cao TRAINS cho cap do): 28
- Tong dong staging: **419** (nam >= 2015) → `data/staging/stg_wits_tariff.csv` (khong commit)
- Nam toi da co du lieu: 2023 — WITS lag ~1-2 nam → D4 dung thu theo nam (khong monthly), khong doi 2024.

## 1. Theo nhom combo

| Nhom | Combos | Dat | Dong | Y nghia |
|---|---:|---:|---:|---|
| VN_IMPORT_MFN | 6 | 6 | 125 | thue MFN VN ap len dau vao san xuat |
| VN_IMPORT_PREF | 30 | 11 | 65 | MFN/PREF VN ap theo goc xu xu (song phuong phia VN bao cao) |
| MKT_EXPORT_MFN | 45 | 36 | 288 | MFN cua thi truong ap len hang VN (xap xi — khong phai bilatral) |
| ANCHOR | 2 | 2 | 16 | 2 o kiem chung vs tuan 1 |

## 2. Validation vs smoke test tuan 1 (HS 090111/2018)

| O (rep|partner|hs6|nam|loai) | Tuan 1 | Bay gio | Ket qua |
|---|---:|---:|---|
| 704|000|090111|2018|MFN | 15.000 | 15.000 | ✅ MATCH |
| 704|392|090111|2018|PREF | 8.000 | 8.000 | ✅ MATCH |

## 3. Nhat ky combo (chi in 12 dong dau — day du trong json)

| Combo | Nhom | Trang thai | Dong | Nam |
|---|---|---|---:|---|
| 704_000_851762 | VN_IMPORT_MFN | SKIP | 15 |  |
| 704_000_854231 | VN_IMPORT_MFN | SKIP | 15 |  |
| 704_000_847330 | VN_IMPORT_MFN | SKIP | 24 |  |
| 704_000_721049 | VN_IMPORT_MFN | SKIP | 24 |  |
| 704_000_540761 | VN_IMPORT_MFN | SKIP | 23 |  |
| 704_000_390120 | VN_IMPORT_MFN | SKIP | 24 |  |
| 704_156_851762 | VN_IMPORT_PREF | SKIP | 11 |  |
| 704_156_854231 | VN_IMPORT_PREF | SKIP | 0 |  |
| 704_156_847330 | VN_IMPORT_PREF | NO_DATA | 0 | — |
| 704_156_721049 | VN_IMPORT_PREF | OK | 7 | 2015-2021 |
| 704_156_540761 | VN_IMPORT_PREF | OK | 7 | 2015-2021 |
| 704_156_390120 | VN_IMPORT_PREF | NO_DATA | 0 | — |

## 4. Ghi chu phap ly du lieu (dung nguyen khi bao cao / dashboard D4)

- MKT_EXPORT_MFN la **MFN ap dung cho World** — thu VN phai tra khi vao thi truong co the THAP HON (FTA), khong the cao hon; tuyet doi khong dien thanh 'VN dang huong uu dai'.
- Chieu doi tac bao cao ve VN (reporter=partner, partner=704) tra 404 tren mien phi — da tai hien 2 lan (tuan 1 + hom nay) → bo qua co chu dich, khong phai that bai.
- Kiem tra `nomenclature` (H5=HS1996, H6=HS2007...) khi join voi fact: WITS nam cu co the dung HS cu; transform tuan 3 join theo (hs6, year) va loc nomenclature thich ung.
- Thu la du lieu **nam** (grain A) — khong bao gio join vao fact monthly; vao bang `FACT_TARIFF_ANNUAL` rieng nhu docs/06.