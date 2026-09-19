# EXTRACT VN_REPORTED — TUAN 2 NV2

- Chat luc: 2026-09-19T04:10:18+00:00
- Nam: 2015–2024 (2015–2023 = loi theo docs/06; 2024 = partial)
- Pham vi: 14 HS6 x 6 partner x 2 flow, grain thang, mode key `data/v1/get`
- Tong so dong staging: **13725**

## 1. So dong theo flow x nam

| Flow | Nam | So dong |
|---|---:|---:|
| M | 2015 | 638 |
| M | 2016 | 662 |
| M | 2017 | 668 |
| M | 2018 | 669 |
| M | 2019 | 678 |
| M | 2020 | 683 |
| M | 2021 | 670 |
| M | 2022 | 753 |
| M | 2023 | 740 |
| X | 2015 | 798 |
| X | 2016 | 812 |
| X | 2017 | 816 |
| X | 2018 | 824 |
| X | 2019 | 840 |
| X | 2020 | 814 |
| X | 2021 | 841 |
| X | 2022 | 913 |
| X | 2023 | 906 |

## 2. Do phu theo ma HS6 (so thang co du lieu, toi da = 12 x so nam)

| HS6 | So thang co du lieu |
|---|---:|
| 080132 | 108 |
| 090111 | 108 |
| 090411 | 108 |
| 100630 | 108 |
| 390120 | 108 |
| 540761 | 108 |
| 610910 | 108 |
| 640399 | 108 |
| 721049 | 108 |
| 847330 | 108 |
| 851713 | 24 |
| 851762 | 108 |
| 854231 | 108 |
| 854442 | 108 |

## 3. Validation voi bang chung tuan 1 (mirror_check_results.json)

Cung query (bao gom luat khong motCode/customs/partner2), 2 thoi diem khac nhau → gia tri phai khop.

| Case tuan 1 | O kiem tra | Gia tri tuan 1 | Gia tri extract | Ket qua |
|---|---|---:|---:|---|
| EXP_JPN_COFFEE_202301 | X/392/090111/202301 | 10,127,757.599 | 10,127,757.599 | ✅ MATCH |
| EXP_USA_COFFEE_202301 | X/842/090111/202301 | 20,201,618.072 | 20,201,618.072 | ✅ MATCH |
| EXP_DEU_COFFEE_202301 | X/276/090111/202301 | 41,199,796.464 | 41,199,796.464 | ✅ MATCH |
| IMP_CHN_NETWORK_EQUIP_202301 | M/156/851762/202301 | 29,869,079.442 | 29,869,079.442 | ✅ MATCH |
| IMP_KOR_INTEGRATED_CIRCUITS_202301 | M/410/854231/202301 | 252,083,766.166 | 252,083,766.166 | ✅ MATCH |

- Khop: 5/5

## 4. Nhat ky goi API

| Batch | Trang thai | So dong | Mode | Ghi chu |
|---|---|---:|---|---|
| vn_M_2015 | REBUILT | 638 | cache |  |
| vn_M_2016 | REBUILT | 662 | cache |  |
| vn_M_2017 | REBUILT | 668 | cache |  |
| vn_M_2018 | REBUILT | 669 | cache |  |
| vn_M_2019 | REBUILT | 678 | cache |  |
| vn_M_2020 | REBUILT | 683 | cache |  |
| vn_M_2021 | REBUILT | 670 | cache |  |
| vn_M_2022 | REBUILT | 753 | cache |  |
| vn_M_2023 | REBUILT | 740 | cache |  |
| vn_M_2024 | REBUILT | 0 | cache |  |
| vn_X_2015 | REBUILT | 798 | cache |  |
| vn_X_2016 | REBUILT | 812 | cache |  |
| vn_X_2017 | REBUILT | 816 | cache |  |
| vn_X_2018 | REBUILT | 824 | cache |  |
| vn_X_2019 | REBUILT | 840 | cache |  |
| vn_X_2020 | REBUILT | 814 | cache |  |
| vn_X_2021 | REBUILT | 841 | cache |  |
| vn_X_2022 | REBUILT | 913 | cache |  |
| vn_X_2023 | REBUILT | 906 | cache |  |
| vn_X_2024 | REBUILT | 0 | cache |  |

## 5. Ghi chu

- File day du nam o `data/staging/stg_comtrade_vn_reported.csv` (khong commit — `.gitignore` chan, dung cho staging SSIS tuan 3).
- Raw tung batch: `data/raw/week2_extract/` (khong commit). Resume tu dong qua `manifest.json`.
- 2024 phia VN du kien trong/le te (gap structural da bang chung o tuan 1) — giu lai nhu bang chung cho dashboard D3.
- Khong bao gio loc bo `is_aggregate_partner` khoi tap du lieu; chi loai khi xep hang partner (doc o transform).