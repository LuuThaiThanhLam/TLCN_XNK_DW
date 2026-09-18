# API SMOKE TEST RESULTS — TUẦN 1

Mục đích: kiểm tra nhanh API có gọi được không, có dữ liệu không, có rủi ro gì không.

| # | Test | Source | OK | Status | Count | Note |
|---:|---|---|:---:|---:|---:|---|
| 1 | Comtrade annual - VN export TOTAL to World 2023 | Comtrade public preview | ✅ | 200 | 1 | OK |
| 2 | Comtrade annual - VN export TOTAL to World 2024 gap check | Comtrade public preview | ✅ | 200 | 0 | OK |
| 3 | Comtrade monthly - VN export HS090111 to Japan 2023M01 | Comtrade public preview | ✅ | 200 | 1 | OK |
| 4 | Comtrade monthly mirror - Japan import HS090111 from VN 2024M01 | Comtrade public preview | ✅ | 200 | 1 | OK |
| 5 | WITS MFN baseline - VN tariff on World HS090111 2018 | WITS/UNCTAD TRAINS API | ✅ | 200 | 1 | OK |
| 6 | WITS PREF - VN tariff on Japan-origin goods HS090111 2018 | WITS/UNCTAD TRAINS API | ✅ | 200 | 1 | OK |
| 7 | WITS PREF - Japan tariff on Vietnam-origin goods HS090111 2018 | WITS/UNCTAD TRAINS API | ❌ | 404 | None | Not Found - NoRecordsFound
 |
| 8 | WB GDP current USD - Vietnam 2024 | World Bank Indicators API | ✅ | 200 | 1 | OK |
| 9 | WB official exchange rate annual - Vietnam 2024 | World Bank Indicators API | ✅ | 200 | 1 | OK |
| 10 | WB exchange rate monthly candidate - Vietnam 2024M01 to 2024M12 | World Bank Indicators API | ✅ | 200 | 12 | OK |

## Chi tiết sample

### Comtrade annual - VN export TOTAL to World 2023

- URL: `https://comtradeapi.un.org/public/v1/preview/C/A/HS?cmdCode=TOTAL&flowCode=X&reporterCode=704&period=2023&partnerCode=0&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Raw file: `data\raw\week1_smoke_test\comtrade_annual_vn_export_total_to_world_2023.json`

```json
{
  "period": "2023",
  "freqCode": "A",
  "refYear": 2023,
  "refMonth": 52,
  "reporterCode": 704,
  "reporterDesc": "Viet Nam",
  "flowCode": "X",
  "flowDesc": "Export",
  "partnerCode": 0,
  "partnerDesc": "World",
  "cmdCode": "TOTAL",
  "cmdDesc": "All Commodities",
  "motCode": 0,
  "customsCode": "C00",
  "primaryValue": 353077513296.001,
  "fobvalue": 353077513296.001,
  "cifvalue": null,
  "qty": 0.0,
  "netWgt": null,
  "isReported": false,
  "isAggregate": true
}
```

### Comtrade annual - VN export TOTAL to World 2024 gap check

- URL: `https://comtradeapi.un.org/public/v1/preview/C/A/HS?cmdCode=TOTAL&flowCode=X&reporterCode=704&period=2024&partnerCode=0&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Raw file: `data\raw\week1_smoke_test\comtrade_annual_vn_export_total_to_world_2024_gap_check.json`

```json
null
```

### Comtrade monthly - VN export HS090111 to Japan 2023M01

- URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=X&reporterCode=704&period=202301&partnerCode=392&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Raw file: `data\raw\week1_smoke_test\comtrade_monthly_vn_export_hs090111_to_japan_2023m01.json`

```json
{
  "period": "202301",
  "freqCode": "M",
  "refYear": 2023,
  "refMonth": 1,
  "reporterCode": 704,
  "reporterDesc": "Viet Nam",
  "flowCode": "X",
  "flowDesc": "Export",
  "partnerCode": 392,
  "partnerDesc": "Japan",
  "cmdCode": "090111",
  "cmdDesc": "Coffee; not roasted or decaffeinated",
  "motCode": 0,
  "customsCode": "C00",
  "primaryValue": 10127757.599,
  "fobvalue": 10127757.599,
  "cifvalue": null,
  "qty": 5024600.0,
  "netWgt": 5024600.0,
  "isReported": false,
  "isAggregate": true
}
```

### Comtrade monthly mirror - Japan import HS090111 from VN 2024M01

- URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=M&reporterCode=392&period=202401&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Raw file: `data\raw\week1_smoke_test\comtrade_monthly_mirror_japan_import_hs090111_from_vn_2024m01.json`

```json
{
  "period": "202401",
  "freqCode": "M",
  "refYear": 2024,
  "refMonth": 1,
  "reporterCode": 392,
  "reporterDesc": "Japan",
  "flowCode": "M",
  "flowDesc": "Import",
  "partnerCode": 704,
  "partnerDesc": "Viet Nam",
  "cmdCode": "090111",
  "cmdDesc": "Coffee; not roasted or decaffeinated",
  "motCode": 0,
  "customsCode": "C00",
  "primaryValue": 35660719.503,
  "fobvalue": null,
  "cifvalue": 35660719.503,
  "qty": 13296000.0,
  "netWgt": 13296000.0,
  "isReported": true,
  "isAggregate": false
}
```

### WITS MFN baseline - VN tariff on World HS090111 2018

- URL: `https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/704/partner/000/product/090111/year/2018/datatype/reported`
- Raw file: `data\raw\week1_smoke_test\wits_mfn_baseline_vn_tariff_on_world_hs090111_2018.xml`

```json
{
  "series": {
    "FREQ": "A",
    "DATATYPE": "Reported",
    "PRODUCTCODE": "090111",
    "PARTNER": "000",
    "REPORTER": "704"
  },
  "obs": {
    "TIME_PERIOD": "2018",
    "OBS_VALUE": "15",
    "TARIFFTYPE": "MFN",
    "OBS_VALUE_MEASURE": "SimpleAverage",
    "TOTALNOOFLINES": "2",
    "NBR_PREF_LINES": "0",
    "NBR_MFN_LINES": "2",
    "NBR_NA_LINES": "0",
    "SUM_OF_RATES": "30",
    "MIN_RATE": "15",
    "MAX_RATE": "15",
    "NOMENCODE": "H5"
  }
}
```

### WITS PREF - VN tariff on Japan-origin goods HS090111 2018

- URL: `https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/704/partner/392/product/090111/year/2018/datatype/reported`
- Raw file: `data\raw\week1_smoke_test\wits_pref_vn_tariff_on_japan_origin_goods_hs090111_2018.xml`

```json
{
  "series": {
    "FREQ": "A",
    "DATATYPE": "Reported",
    "PRODUCTCODE": "090111",
    "PARTNER": "392",
    "REPORTER": "704"
  },
  "obs": {
    "TIME_PERIOD": "2018",
    "OBS_VALUE": "8",
    "TARIFFTYPE": "PREF",
    "OBS_VALUE_MEASURE": "SimpleAverage",
    "TOTALNOOFLINES": "2",
    "NBR_PREF_LINES": "2",
    "NBR_MFN_LINES": "0",
    "NBR_NA_LINES": "0",
    "SUM_OF_RATES": "16",
    "MIN_RATE": "8",
    "MAX_RATE": "8",
    "NOMENCODE": "H5"
  }
}
```

### WITS PREF - Japan tariff on Vietnam-origin goods HS090111 2018

- URL: `https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/392/partner/704/product/090111/year/2018/datatype/reported`
- Raw file: `data\raw\week1_smoke_test\wits_pref_japan_tariff_on_vietnam_origin_goods_hs090111_2018.xml`

```json
null
```

### WB GDP current USD - Vietnam 2024

- URL: `https://api.worldbank.org/v2/country/VNM/indicator/NY.GDP.MKTP.CD?date=2024&format=json&per_page=1000`
- Raw file: `data\raw\week1_smoke_test\wb_gdp_current_usd_vietnam_2024.json`

```json
{
  "country": "Viet Nam",
  "countryiso3code": "VNM",
  "indicator": "NY.GDP.MKTP.CD",
  "indicator_name": "GDP (current US$)",
  "date": "2024",
  "value": 476324572783.807,
  "unit": "",
  "obs_status": ""
}
```

### WB official exchange rate annual - Vietnam 2024

- URL: `https://api.worldbank.org/v2/country/VNM/indicator/PA.NUS.FCRF?date=2024&format=json&per_page=1000`
- Raw file: `data\raw\week1_smoke_test\wb_official_exchange_rate_annual_vietnam_2024.json`

```json
{
  "country": "Viet Nam",
  "countryiso3code": "VNM",
  "indicator": "PA.NUS.FCRF",
  "indicator_name": "Official exchange rate (LCU per US$, period average)",
  "date": "2024",
  "value": 24164.8858333333,
  "unit": "",
  "obs_status": ""
}
```

### WB exchange rate monthly candidate - Vietnam 2024M01 to 2024M12

- URL: `https://api.worldbank.org/v2/country/VNM/indicator/DPANUSSPB?date=2024M01%3A2024M12&format=json&per_page=1000`
- Raw file: `data\raw\week1_smoke_test\wb_exchange_rate_monthly_candidate_vietnam_2024m01_to_2024m12.json`

```json
{
  "country": "Vietnam",
  "countryiso3code": "",
  "indicator": "DPANUSSPB",
  "indicator_name": "Exchange rate, new LCU per USD extended backward, period average,,",
  "date": "2024M12",
  "value": 25418.7727272727,
  "unit": "",
  "obs_status": ""
}
```

## Cách đọc kết quả

- `OK = ✅`, `Count > 0`: API gọi được và có dữ liệu cho tổ hợp test.
- `OK = ✅`, `Count = 0`: API gọi được nhưng tổ hợp đó không có dữ liệu; cần ghi vào coverage.
- `OK = ❌`, status 429: gọi quá nhanh/rate limit; chạy lại sau hoặc dùng API key.
- `OK = ❌`, timeout: API chậm; chạy lại sau và ghi nhận rủi ro.
- WITS thiếu dữ liệu không có nghĩa bỏ WITS ngay; cần đổi partner/HS6/năm để profiling thêm.