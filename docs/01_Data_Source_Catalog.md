# DATA SOURCE CATALOG — TUẦN 1

| Mã nguồn | Tên nguồn | URL/API | Dữ liệu lấy | Tần suất | Định dạng | Có key? | Giới hạn | Bảng staging dự kiến |
|---|---|---|---|---|---|---|---|---|
| SRC01 | UN Comtrade | https://comtradeapi.un.org/... | Trade value, quantity, weight | Monthly/Annual | JSON/CSV | Có/Không | Rate limit, maxrecords | STG_COMTRADE |
| SRC02 | WITS/UNCTAD TRAINS | https://wits.worldbank.org/API/... | MFN/PREF tariff | Annual | SDMX XML | Không | Coverage thưa, timeout | STG_WITS_TARIFF |
| SRC03 | World Bank Indicators | https://api.worldbank.org/v2/... | GDP, exchange rate, inflation | Annual/Monthly tùy indicator | JSON | Không | Một số chỉ tiêu thiếu năm mới | STG_WORLD_BANK |

---

## Endpoint mẫu cần lưu

### UN Comtrade monthly

```text
/C/M/HS?cmdCode={HS6}&flowCode={X|M}&reporterCode={reporter}&period={YYYYMM}&partnerCode={partner}&motCode=0&customsCode=C00&partner2Code=0
```

### WITS tariff

```text
/API/V1/SDMX/V21/datasource/TRN/reporter/{reporter}/partner/{partner}/product/{HS6}/year/{year}/datatype/reported
```

### World Bank

```text
/v2/country/{country}/indicator/{indicator}?date={date}&format=json
```
