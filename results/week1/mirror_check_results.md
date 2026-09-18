# MIRROR CHECK RESULTS — TUẦN 1

Mục đích: so sánh nhanh dữ liệu Việt Nam báo cáo với dữ liệu mirror do đối tác báo cáo trên UN Comtrade.

> Lưu ý: chênh lệch mirror là bình thường do khác biệt FOB/CIF, thời điểm ghi nhận, phương pháp thống kê, phân loại HS và độ trễ báo cáo. Kết quả này dùng để thiết kế cơ chế reconciliation, không dùng để kết luận bên nào sai.

## 1. Bảng tổng hợp

| # | Direction | Period | Partner | HS6 | VN count | Mirror count | VN value USD | Mirror value USD | Diff vs VN | Level | Note |
|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | EXPORT | 202301 | Japan | 090111 | 1 | 1 | 10,127,757.60 | 16,784,397.26 | 65.73% | HIGH | Mirror cao hơn VN-reported. EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường. Mức chênh lệch: HIGH. |
| 2 | EXPORT | 202401 | Japan | 090111 |  | 1 |  | 35,660,719.50 |  | MISSING_VN_REPORTED | Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror. |
| 3 | EXPORT | 202301 | United States | 090111 | 1 | 1 | 20,201,618.07 | 37,790,801.00 | 87.07% | HIGH | Mirror cao hơn VN-reported. EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường. Mức chênh lệch: HIGH. |
| 4 | EXPORT | 202301 | Germany | 090111 | 1 | 1 | 41,199,796.46 | 38,271,554.95 | 7.11% | LOW | Mirror thấp hơn VN-reported. EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường. Mức chênh lệch: LOW. |
| 5 | IMPORT | 202301 | China | 851762 | 1 | 1 | 29,869,079.44 | 29,945,226.00 | 0.25% | LOW | Mirror cao hơn VN-reported. IMPORT: VN nhập khẩu thường ghi CIF, đối tác xuất khẩu thường ghi FOB; mirror thấp hơn có thể là bình thường. Mức chênh lệch: LOW. |
| 6 | IMPORT | 202301 | Rep. of Korea | 854231 | 1 | 1 | 252,083,766.17 | 217,401,413.00 | 13.76% | MODERATE | Mirror thấp hơn VN-reported. IMPORT: VN nhập khẩu thường ghi CIF, đối tác xuất khẩu thường ghi FOB; mirror thấp hơn có thể là bình thường. Mức chênh lệch: MODERATE. |
| 7 | IMPORT | 202401 | China | 851762 |  | 1 |  | 62,727,085.00 |  | MISSING_VN_REPORTED | Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror. |
| 8 | IMPORT | 202401 | Rep. of Korea | 854231 |  | 1 |  | 412,589,570.00 |  | MISSING_VN_REPORTED | Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror. |

## 2. Cách đọc mức chênh lệch

| Level | Ý nghĩa |
|---|---|
| LOW | Hai phía có dữ liệu và chênh lệch trị giá <= 10% so với VN-reported |
| MODERATE | Hai phía có dữ liệu và chênh lệch > 10% đến <= 30% |
| HIGH | Hai phía có dữ liệu và chênh lệch > 30%; cần kiểm tra kỹ khi chọn dashboard |
| MISSING_VN_REPORTED | Việt Nam không có dữ liệu nhưng đối tác có mirror; đây là case hữu ích cho cơ chế mirror |
| MISSING_MIRROR | Việt Nam có dữ liệu nhưng đối tác không có mirror |
| NO_DATA_BOTH | Cả hai phía không có dữ liệu cho tổ hợp đó |
| API_ERROR | Có lỗi kỹ thuật khi gọi API, cần chạy lại trước khi kết luận |

## 3. Chi tiết từng case

### EXP_JPN_COFFEE_202301

- Direction: `EXPORT`
- Period: `202301`
- Partner: `Japan` (`392`)
- HS6: `090111` — Coffee; not roasted or decaffeinated
- Expected valuation pattern: VN export FOB vs partner import CIF
- VN-reported count/value: `1` / `10,127,757.60` USD
- Mirror count/value: `1` / `16,784,397.26` USD
- Difference mirror - VN: `6,656,639.66` USD
- Difference % vs VN: `65.73%`
- Level: `HIGH`
- Note: Mirror cao hơn VN-reported. EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường. Mức chênh lệch: HIGH.
- VN raw: `data\raw\week1_mirror_check\exp_jpn_coffee_202301_vn_reported_export.json`
- Mirror raw: `data\raw\week1_mirror_check\exp_jpn_coffee_202301_partner_mirror_import.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=X&reporterCode=704&period=202301&partnerCode=392&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=M&reporterCode=392&period=202301&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### EXP_JPN_COFFEE_202401

- Direction: `EXPORT`
- Period: `202401`
- Partner: `Japan` (`392`)
- HS6: `090111` — Coffee; not roasted or decaffeinated
- Expected valuation pattern: VN export FOB vs partner import CIF
- VN-reported count/value: `0` / `` USD
- Mirror count/value: `1` / `35,660,719.50` USD
- Difference mirror - VN: `` USD
- Difference % vs VN: ``
- Level: `MISSING_VN_REPORTED`
- Note: Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror.
- VN raw: `data\raw\week1_mirror_check\exp_jpn_coffee_202401_vn_reported_export.json`
- Mirror raw: `data\raw\week1_mirror_check\exp_jpn_coffee_202401_partner_mirror_import.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=X&reporterCode=704&period=202401&partnerCode=392&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=M&reporterCode=392&period=202401&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### EXP_USA_COFFEE_202301

- Direction: `EXPORT`
- Period: `202301`
- Partner: `United States` (`842`)
- HS6: `090111` — Coffee; not roasted or decaffeinated
- Expected valuation pattern: VN export FOB vs partner import CIF
- VN-reported count/value: `1` / `20,201,618.07` USD
- Mirror count/value: `1` / `37,790,801.00` USD
- Difference mirror - VN: `17,589,182.93` USD
- Difference % vs VN: `87.07%`
- Level: `HIGH`
- Note: Mirror cao hơn VN-reported. EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường. Mức chênh lệch: HIGH.
- VN raw: `data\raw\week1_mirror_check\exp_usa_coffee_202301_vn_reported_export.json`
- Mirror raw: `data\raw\week1_mirror_check\exp_usa_coffee_202301_partner_mirror_import.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=X&reporterCode=704&period=202301&partnerCode=842&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=M&reporterCode=842&period=202301&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### EXP_DEU_COFFEE_202301

- Direction: `EXPORT`
- Period: `202301`
- Partner: `Germany` (`276`)
- HS6: `090111` — Coffee; not roasted or decaffeinated
- Expected valuation pattern: VN export FOB vs partner import CIF
- VN-reported count/value: `1` / `41,199,796.46` USD
- Mirror count/value: `1` / `38,271,554.95` USD
- Difference mirror - VN: `-2,928,241.51` USD
- Difference % vs VN: `7.11%`
- Level: `LOW`
- Note: Mirror thấp hơn VN-reported. EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường. Mức chênh lệch: LOW.
- VN raw: `data\raw\week1_mirror_check\exp_deu_coffee_202301_vn_reported_export.json`
- Mirror raw: `data\raw\week1_mirror_check\exp_deu_coffee_202301_partner_mirror_import.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=X&reporterCode=704&period=202301&partnerCode=276&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=090111&flowCode=M&reporterCode=276&period=202301&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### IMP_CHN_NETWORK_EQUIP_202301

- Direction: `IMPORT`
- Period: `202301`
- Partner: `China` (`156`)
- HS6: `851762` — Machines for reception, conversion and transmission/regeneration of data
- Expected valuation pattern: VN import CIF vs partner export FOB
- VN-reported count/value: `1` / `29,869,079.44` USD
- Mirror count/value: `1` / `29,945,226.00` USD
- Difference mirror - VN: `76,146.56` USD
- Difference % vs VN: `0.25%`
- Level: `LOW`
- Note: Mirror cao hơn VN-reported. IMPORT: VN nhập khẩu thường ghi CIF, đối tác xuất khẩu thường ghi FOB; mirror thấp hơn có thể là bình thường. Mức chênh lệch: LOW.
- VN raw: `data\raw\week1_mirror_check\imp_chn_network_equip_202301_vn_reported_import.json`
- Mirror raw: `data\raw\week1_mirror_check\imp_chn_network_equip_202301_partner_mirror_export.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=851762&flowCode=M&reporterCode=704&period=202301&partnerCode=156&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=851762&flowCode=X&reporterCode=156&period=202301&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### IMP_KOR_INTEGRATED_CIRCUITS_202301

- Direction: `IMPORT`
- Period: `202301`
- Partner: `Rep. of Korea` (`410`)
- HS6: `854231` — Electronic integrated circuits; processors and controllers
- Expected valuation pattern: VN import CIF vs partner export FOB
- VN-reported count/value: `1` / `252,083,766.17` USD
- Mirror count/value: `1` / `217,401,413.00` USD
- Difference mirror - VN: `-34,682,353.17` USD
- Difference % vs VN: `13.76%`
- Level: `MODERATE`
- Note: Mirror thấp hơn VN-reported. IMPORT: VN nhập khẩu thường ghi CIF, đối tác xuất khẩu thường ghi FOB; mirror thấp hơn có thể là bình thường. Mức chênh lệch: MODERATE.
- VN raw: `data\raw\week1_mirror_check\imp_kor_integrated_circuits_202301_vn_reported_import.json`
- Mirror raw: `data\raw\week1_mirror_check\imp_kor_integrated_circuits_202301_partner_mirror_export.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=854231&flowCode=M&reporterCode=704&period=202301&partnerCode=410&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=854231&flowCode=X&reporterCode=410&period=202301&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### IMP_CHN_NETWORK_EQUIP_202401

- Direction: `IMPORT`
- Period: `202401`
- Partner: `China` (`156`)
- HS6: `851762` — Machines for reception, conversion and transmission/regeneration of data
- Expected valuation pattern: VN import CIF vs partner export FOB
- VN-reported count/value: `0` / `` USD
- Mirror count/value: `1` / `62,727,085.00` USD
- Difference mirror - VN: `` USD
- Difference % vs VN: ``
- Level: `MISSING_VN_REPORTED`
- Note: Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror.
- VN raw: `data\raw\week1_mirror_check\imp_chn_network_equip_202401_vn_reported_import.json`
- Mirror raw: `data\raw\week1_mirror_check\imp_chn_network_equip_202401_partner_mirror_export.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=851762&flowCode=M&reporterCode=704&period=202401&partnerCode=156&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=851762&flowCode=X&reporterCode=156&period=202401&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

### IMP_KOR_INTEGRATED_CIRCUITS_202401

- Direction: `IMPORT`
- Period: `202401`
- Partner: `Rep. of Korea` (`410`)
- HS6: `854231` — Electronic integrated circuits; processors and controllers
- Expected valuation pattern: VN import CIF vs partner export FOB
- VN-reported count/value: `0` / `` USD
- Mirror count/value: `1` / `412,589,570.00` USD
- Difference mirror - VN: `` USD
- Difference % vs VN: ``
- Level: `MISSING_VN_REPORTED`
- Note: Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror.
- VN raw: `data\raw\week1_mirror_check\imp_kor_integrated_circuits_202401_vn_reported_import.json`
- Mirror raw: `data\raw\week1_mirror_check\imp_kor_integrated_circuits_202401_partner_mirror_export.json`
- VN URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=854231&flowCode=M&reporterCode=704&period=202401&partnerCode=410&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`
- Mirror URL: `https://comtradeapi.un.org/public/v1/preview/C/M/HS?cmdCode=854231&flowCode=X&reporterCode=410&period=202401&partnerCode=704&motCode=0&customsCode=C00&partner2Code=0&includeDesc=true&maxrecords=50`

## 4. Kết luận sử dụng cho báo cáo

Nếu có nhiều case hai phía đều có dữ liệu, có thể kết luận dữ liệu mirror khả thi để đưa vào kho dữ liệu. Nếu xuất hiện `MISSING_VN_REPORTED`, đây là bằng chứng cho nhu cầu dùng mirror để bổ sung/đối chiếu khi Việt Nam chưa có dữ liệu cập nhật. Nếu xuất hiện `HIGH`, không loại dữ liệu ngay mà cần lưu cả hai perspective và gắn cờ chất lượng dữ liệu trong `FACT_TRADE_RECONCILIATION`.

## 5. Luật thiết kế rút ra

- Không cộng trực tiếp VN-reported và partner-mirror vào cùng một chỉ tiêu chính nếu chưa chọn perspective.
- `FACT_TRADE` phải có cột `reporting_perspective`, ví dụ `VN_REPORTED`, `PARTNER_MIRROR`.
- Reconciliation nên nằm ở fact riêng hoặc view riêng, ví dụ `FACT_TRADE_RECONCILIATION`.
- Chênh lệch không có nghĩa là dữ liệu sai; cần giải thích FOB/CIF, thời điểm ghi nhận và phương pháp thống kê.