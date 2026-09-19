# KEY CHECK RESULTS — TUAN 2 (NHIEM VU 1)

- Chay luc: 2026-09-19T03:39:02+00:00
- Key tai duoc: CO (4cf9****(dai 32))
- Ket luan tong: **FAIL**

| # | Kiem tra | Dat | Chi tiet |
|---:|---|:---:|---|
| 1 | 1. Key duoc doc tu moi truong/.env | ✅ | 4cf9****(dai 32) |
| 2 | 2. Goi data/v1/get (annual 2023 TOTAL) | ✅ | HTTP 200, count=1, value=353077513296.001, note=OK |
| 3 | 3. Goi monthly voi RANGE period 201501:201512 | ❌ | HTTP 400, count=None, so ky tra ve=0 ([]...), note={"error":"Invalid parameter value","details":[{"memberNames":["period"],"errorMessage":"The field period is invalid"}]} |
| 4 | 4. Cross-check gia tri voi preview tuan 1 | ✅ | preview=353077513296.001, key=353077513296.001, diff=0.000 USD |

## Y nghia

- Kiem tra 2 dat: endpoint day du `data/v1/get` tra duoc du lieu (khong con bi chan preview 500 records).
- Kiem tra 3 dat: 1 query lay duoc nhieu ky (range period) → nen cho thiet ke extract tuan 2 batch theo nam.
- Kiem tra 4 dat: mode key va mode preview tra cung mot so lieu → bang chung tuan 1 van con gia tri doi chieu.
- Raw response cu the nam trong `data/raw/week2_key_check/` (khong commit, .gitignore da chan).