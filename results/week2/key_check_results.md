# KEY CHECK RESULTS — TUAN 2 (NHIEM VU 1, BAN 2)

- Chay luc: 2026-09-19T03:43:35+00:00
- Key tai duoc: CO (4cf9****(dai 32))
- Ket luan tong: **PASS**

| # | Kiem tra | Dat | Chi tiet |
|---:|---|:---:|---|
| 1 | 1. Key duoc doc tu moi truong/.env | ✅ | 4cf9****(dai 32) |
| 2 | 2. data/v1/get annual 2023 TOTAL | ✅ | HTTP 200, count=1, value=353077513296.001, note=OK |
| 3 | 3a. monthly mot ky don (201501) | ✅ | HTTP 200, count=1, note=OK |
| 4 | 3b. monthly 12 ky cach bang DAU PHAY (dinh dang API moi) | ✅ | HTTP 200, count=12, so ky=12 ['201501', '201502', '201503']...['201511', '201512'], note=OK |
| 5 | 3c. (tham khao) range dau hai cham 201501:201512 | ℹ️ | HTTP 400, count=None, note={"error":"Invalid parameter value","details":[{"memberNames":["period"],"errorMessage":"The field period is invalid"}]} → API MOI dung dau phay, khong dung dau hai cham |
| 6 | 4. Cross-check gia tri annual 2023 voi preview tuan 1 | ✅ | preview=353077513296.001, key=353077513296.001, diff=0.000 USD |

## Y nghia

- Kiem tra 2: endpoint day du `data/v1/get` tra du lieu bang key (khong con chan preview 500 records/1 ky).
- Kiem tra 3b: MOT call monthly lay duoc nhieu ky khi dung danh sach `period=YYYYMM,YYYYMM,...` (cu ph chinh thuc cua API moi — docs vi du `period=202301,202302,...`). 3b PASS → W2-NV2 batch theo nam (12 ky/call) duoc phep thuc hien.
- Kiem tra 3c (tham khao): `period=201501:201512` (dau hai cham) la cu phap API cu, bi API moi tu choi 400. Ban 1 cua script dung cu phap nay va FAIL — phat hien da duoc giu trong lich su git (commit 041d8ac).
- Kiem tra 4: mode key va mode preview cung tra mot so lieu → bang chung tuan 1 con nguyen gia tri doi chieu.
- Raw response nam trong `data/raw/week2_key_check/` (khong commit, .gitignore da chan).