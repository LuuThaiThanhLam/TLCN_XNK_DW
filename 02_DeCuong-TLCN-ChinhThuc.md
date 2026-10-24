Trường ĐH Sư Phạm Kỹ Thuật TP.HCM
Khoa : CNTT

# ĐỀ CƯƠNG TIỂU LUẬN CHUYÊN NGÀNH

**Họ và Tên SV thực hiện 1 :** Nguyễn Khắc Dương  **Mã Số SV :** 23110199  
**Họ và Tên SV thực hiện 2 :** Lưu Thái Thanh Lâm  **Mã Số SV :** 23110249  

**Thời gian làm tiểu luận :** từ : 01/09/2026  Đến : 30/11/2026 (13 tuần)  
**Chuyên ngành :** Hệ thống thông tin  
**Tên tiểu luận :** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam  
**GV hướng dẫn :** ………………………………………  

---

## NHIỆM VỤ CỦA TIỂU LUẬN

1. **Khảo sát nghiệp vụ và nguồn dữ liệu xuất nhập khẩu (XNK) Việt Nam:** Phân tích thực trạng thương mại quốc tế, hệ thống hài hòa mô tả và mã hóa hàng hóa (Mã HS qua các phiên bản HS2012, HS2017, HS2022), các hiệp định thương mại tự do (FTA) trọng điểm (EVFTA, CPTPP, RCEP, ATIGA). Kiểm chứng thực nghiệm tính khả dụng, độ trễ và giới hạn kỹ thuật của các nguồn dữ liệu mở truy cập qua API (UN Comtrade API v1, WITS/UNCTAD TRAINS API, World Bank Open Data API).

2. **Phân tích yêu cầu và đặc tả bộ chỉ số nghiệp vụ:** Xác định bài toán nghiệp vụ phục vụ quản lý vĩ mô và doanh nghiệp; chuyển hóa thành bộ chỉ số KPI (Kim ngạch, Cán cân thương mại, Tỷ trọng thị trường, Chỉ số tập trung thị trường Herfindahl-Hirschman HHI, Tỷ lệ tập trung CR-n, Tác động thuế quan ưu đãi). Ánh xạ vết yêu cầu nghiệp vụ về dữ liệu nguồn.

3. **Thiết kế Kho dữ liệu đa chiều theo phương pháp Kimball:**
   - Xây dựng ma trận Bus chuẩn hóa và xác định các chiều đồng nhất (Conformed Dimensions: Date, Partner, Commodity).
   - Thiết kế lược đồ hình sao (Star Schema) với grain được khai báo tường minh.
   - Xử lý vấn đề biến động mã phân loại hàng hóa bằng kỹ thuật ánh xạ đa phiên bản (HS Revision: As-Is vs As-Mapped).
   - Thiết lập bảng tra cứu chuẩn hóa quốc tế `REF_COUNTRY_CODES` ánh xạ mã Comtrade M49 sang ISO-Alpha-3 và phân cấp địa lý (Region, Sub-region, Income Group).
   - Ứng dụng Khóa Sentinel (`YYYY00`) để giải quyết bất đồng nhất về độ mịn thời gian giữa Fact tháng và Fact năm.

4. **Đề xuất và hiện thực cơ chế đối chiếu gương (Mirror Reconciliation) và điền khuyết có kiểm soát (Mirror Imputation):**
   - Xử lý tình trạng gián đoạn nguồn dữ liệu chính thức của Việt Nam từ năm 2024 bằng cách đối chiếu với số liệu do các nước đối tác tự báo cáo (Partner Mirror Data).
   - Mở rộng Grain của bảng Fact thương mại theo Chiều góc nhìn báo cáo (`DIM_PERSPECTIVE`).
   - Xây dựng bảng hệ số chi phí vận tải và bảo hiểm quốc tế `REF_CIF_FOB_FACTOR` nhằm quy đổi chênh lệch cơ sở tính giá CIF sang FOB khi sử dụng dữ liệu đối tác để ước tính.
   - Hiện thực tầng Fact phái sinh `VW_TRADE_RECONCILIATION` và View ước tính tối ưu `VW_TRADE_BEST_ESTIMATE` kèm nhãn cờ nguồn gốc dữ liệu (`data_source_flag`), đảm bảo tuyệt đối không trộn lẫn số liệu làm sai lệch tính toàn vẹn dữ liệu.

5. **Thiết lập cơ chế quản trị tính cộng gộp (Summarizability Governance):**
   - Nhúng trực tiếp bảng nội quy `DW_USAGE_RULE` vào cơ sở dữ liệu để khóa và hướng dẫn các ràng buộc cộng gộp (Cấm SUM cột số lượng `qty` chéo đơn vị tính; cấm tính trung bình giản đơn cho thuế suất `ad_valorem_pct`; cấm cộng gộp dòng tổng hợp World).
   - Ràng buộc thực thi chặt chẽ ở tầng Semantic Layer và Power BI.

6. **Xây dựng quy trình ETL tự động và nạp Idempotent:**
   - Viết pipeline trích xuất tự động 100% từ API bằng Python với cơ chế xử lý Rate Limiting, Exponential Backoff và Retry.
   - Xây dựng vùng đệm dữ liệu (Landing Zone `lz.*` và Staging CSV).
   - Hiện thực hóa nạp dữ liệu bằng câu lệnh `MERGE` (Idempotent Load) trong SQL Server, hỗ trợ nạp lại mà không gây trùng lặp bản ghi, gắn tem nhật ký kiểm toán từ `DIM_AUDIT`.

7. **Hiện thực tầng phân tích OLAP, Khối đa chiều SSAS và Trực quan hóa:**
   - Xây dựng khối đa chiều SSAS OLAP Cubes (Measure Groups, Hierarchies, KPI) trên SQL Server Analysis Services.
   - Xây dựng bộ truy vấn phân tích nâng cao sử dụng các phép mở rộng SQL (`CUBE`, `ROLLUP`, `GROUPING SETS`) và hàm cửa sổ phân tích (`Window Functions`).
   - Thiết kế 5 Dashboard chuyên sâu trên Microsoft Power BI Desktop phục vụ 5 kịch bản ra quyết định chiến lược.

8. **Kiểm thử, đánh giá hiệu năng và hoàn thiện báo cáo:** Kiểm thử toàn vẹn dữ liệu end-to-end, đánh giá độ phủ (coverage) theo khu vực, đo lường hiệu năng truy vấn có index/materialized view và viết báo cáo luận văn hoàn chỉnh theo quy định Khoa CNTT - ĐH Sư Phạm Kỹ Thuật TP.HCM.

---

## ĐỀ CƯƠNG VIẾT TIỂU LUẬN

# MỤC LỤC

## 1. PHẦN MỞ ĐẦU

### 1.1. Tính cấp thiết của đề tài
- Hoạt động xuất nhập khẩu hàng hóa là động lực tăng trưởng cốt lõi của nền kinh tế Việt Nam với độ mở thương mại vượt 180% GDP. Nhu cầu phân tích dữ liệu đa chiều, kịp thời để hỗ trợ hoạch định chính sách và chiến lược thị trường của doanh nghiệp là vô cùng cấp thiết.
- **Thực trạng phân tán và dị thể của dữ liệu thương mại:** Dữ liệu nằm rải rác trên các hệ thống quốc tế (UN Comtrade, WITS/UNCTAD, World Bank) với cấu trúc phân loại khác nhau, kỳ báo cáo khác nhau, đơn vị đo không đồng nhất và sự khác biệt về quy tắc định giá (FOB đối với hàng xuất và CIF đối với hàng nhập).
- **Khoảng trống dữ liệu thời sự:** Phía Việt Nam gián đoạn công bố báo cáo chi tiết lên hệ sinh thái UN Comtrade từ năm 2024, gây ra sự đứt gãy chuỗi thời gian phân tích đối với các nghiên cứu kinh tế thương mại truyền thống.
- **Sự cần thiết của Kho dữ liệu (Data Warehouse):** Nhu cầu cấp bách xây dựng một hệ thống hướng chủ đề, tích hợp, biến đổi theo thời gian và bất biến (theo định nghĩa Inmon & Kimball) nhằm thống nhất các nguồn dữ liệu mở, đồng thời giải quyết bài toán bù đắp và hòa giải dữ liệu gián đoạn thông qua số liệu đối tác (Mirror Data).

### 1.2. Mục đích của đề tài
- Thiết kế và cài đặt một Kho dữ liệu XNK hàng hóa Việt Nam hoàn chỉnh, vận hành tự động theo kiến trúc luồng dữ liệu chuẩn từ Open APIs $\rightarrow$ Staging $\rightarrow$ Data Warehouse $\rightarrow$ OLAP Cubes $\rightarrow$ Power BI Dashboard.
- Đề xuất và chứng minh tính đúng đắn của mô hình dữ liệu đa góc nhìn báo cáo (Multi-Perspective Dimensional Model), tích hợp cơ chế đối chiếu gương và điền khuyết có kiểm soát thông qua hệ số điều chỉnh CIF/FOB.
- Hiện thực hóa 5 kịch bản phân tích hỗ trợ ra quyết định:
  1. Đánh giá tác động và lợi thế thuế quan ưu đãi theo các cam kết FTA.
  2. Nhận diện quy luật chu kỳ mùa vụ của các nhóm hàng chủ lực (Nông sản, Thủy sản).
  3. Giám sát rủi ro tập trung thị trường và mặt hàng (Chỉ số HHI, CR-n).
  4. Trực quan hóa dòng chảy thương mại toàn cầu của Việt Nam theo phân cấp địa lý (Choropleth Map).
  5. Đánh giá chất lượng và độ phủ dữ liệu thống kê thương mại theo vùng lãnh thổ.

### 1.3. Cách tiếp cận và phương pháp nghiên cứu

**Cách tiếp cận:**
- Tiếp cận từ trên xuống (Top-down) theo phương pháp luận mô hình hóa đa chiều của Ralph Kimball: Bắt đầu từ câu hỏi nghiệp vụ của người ra quyết định $\rightarrow$ Xác định quy trình nghiệp vụ $\rightarrow$ Khai báo Grain tường minh $\rightarrow$ Thiết kế các Chiều (Dimensions) $\rightarrow$ Xác định Độ đo (Measures) $\rightarrow$ Hiện thực lược đồ vật lý.
- Tiếp cận kiểm soát nghiêm ngặt tính cộng gộp (Summarizability) theo lý thuyết của Vaisman & Zimányi (2022).

**Phương pháp nghiên cứu:**
- *Phương pháp nghiên cứu tài liệu:* Hệ thống hóa lý thuyết kho dữ liệu hiện đại, mô hình khối đa chiều, kỹ thuật SCD, quy trình ETL từ giáo trình quốc tế của Kimball & Ross (2013) và Vaisman & Zimányi (2022).
- *Phương pháp thực nghiệm kỹ thuật:* Kiểm chứng thực tế các điểm cuối (endpoints) của UN Comtrade API v1, WITS API (định dạng SDMX-XML) và World Bank API; đo lường độ trễ, giới hạn quota và tỷ lệ phản hồi rỗng.
- *Phương pháp mô hình hóa và triển khai hệ thống:* Thiết kế cơ sở dữ liệu trên Microsoft SQL Server, xây dựng khối đa chiều SSAS, viết pipeline ETL bằng Python và thiết kế Semantic Layer trên Microsoft Power BI.
- *Phương pháp kiểm chứng chéo và đánh giá:* So sánh số liệu nạp với các niên giám thống kê chính thức; đo lường thời gian đáp ứng của truy vấn phân tích (Execution Time & I/O Cost) trước và sau khi tối ưu hóa Index/Materialized Views.

**Đối tượng và Phạm vi nghiên cứu:**

| Tiêu chí | Giới hạn và Phạm vi triển khai |
|---|---|
| **Thời gian dữ liệu** | Giai đoạn 2015 – 2024 (10 năm), độ mịn theo **Tháng** đối với dữ liệu thương mại; theo **Năm** đối với dữ liệu thuế quan và vĩ mô |
| **Phạm vi không gian (Quốc gia)** | **Toàn cầu (~200 quốc gia và vùng lãnh thổ)** có giao dịch XNK với Việt Nam theo mô hình phân tầng Đa cấp (Hybrid Multi-Tier):<br>• *Tầng lõi (Tier 1):* 6 đối tác lớn nhất (Hoa Kỳ, Trung Quốc, Hàn Quốc, Nhật Bản, Đức và dòng tổng hợp World).<br>• *Tầng khu vực (Tier 2):* 9 quốc gia khối ASEAN.<br>• *Tầng hiệp định (Tier 3):* 10 đối tác FTA lớn (EU, CPTPP, RCEP).<br>• *Tầng mở rộng (Tier 4 & 5):* Các thị trường mới nổi và các quốc gia còn lại. |
| **Phân loại hàng hóa** | Hệ thống mã hài hòa HS cấp 6 chữ số (HS6 - phân nhóm tiêu biểu thuộc các ngành xuất nhập khẩu mũi nhọn: Điện tử, Dệt may, Da giày, Thủy sản, Nông sản, Nhiên liệu); roll-up lên cấp HS4 và HS2. Ánh xạ đồng nhất về phiên bản HS2022. |
| **Loại hình thương mại** | Thương mại hàng hóa quốc tế chính ngạch (Merchandise Trade); **không** bao gồm thương mại dịch vụ |
| **Phạm vi thuế quan** | Thuế suất tối huệ quốc (MFN Applied) và thuế suất ưu đãi bình quân (Effectively Handled / Preferential AHS) từ hệ thống WITS |
| **Chỉ số kinh tế vĩ mô** | GDP, Tốc độ tăng trưởng GDP, Lạm phát (CPI), Vốn đầu tư trực tiếp nước ngoài (FDI), Tỷ giá hối đoái thực tế từ World Bank |
| **Ngoài phạm vi** | Dữ liệu định danh cấp doanh nghiệp cụ thể, thông tin tờ khai hải quan chi tiết từng chuyến hàng, các mô hình dự báo học máy (Machine Learning) chuyên sâu |

### 1.4. Phân tích các công trình liên quan & Khoảng trống nghiên cứu
- **Nhóm nghiên cứu phương pháp luận DWH:** Các công trình kinh điển của Kimball & Ross (2013) và Vaisman & Zimányi (2022) đặt nền móng cho việc thiết kế mô hình đa chiều, ma trận Bus, kỹ thuật xử lý dữ liệu thay đổi chậm (SCD) và các điều kiện đảm bảo Summarizability.
- **Nhóm hệ thống kho dữ liệu thương mại quốc tế:** Hệ thống WITS (World Bank), UN Comtrade Analytics, Trade Map (ITC) cung cấp số liệu tổng hợp nhưng hoạt động dưới dạng hệ thống đóng, không công khai kiến trúc mô hình chiều bên dưới và không cung cấp giải pháp xử lý tự động sự bất đối xứng song phương cho các hệ thống BI độc lập.
- **Nhóm nghiên cứu kinh tế về bất đối xứng số liệu (Mirror Statistics):** Các nghiên cứu của IMF, OECD và UNCTAD chỉ ra nguyên nhân sai lệch số liệu thương mại song phương do định giá CIF/FOB, thời điểm ghi nhận và chuyển tải hàng hóa, nhưng dừng lại ở phân tích định tính hoặc mô hình hồi quy kinh tế lượng, **chưa từng được đưa vào thành một thành phần kiến trúc cốt lõi trong mô hình Kho dữ liệu**.

> **Khoảng trống nghiên cứu được đề tài giải quyết:**  
> Đề tài giải quyết khoảng trống trong việc: **"Thiết kế và hiện thực hóa một Kho dữ liệu thương mại có khả năng tự động đối chiếu, đánh giá độ tin cậy và bù đắp khoảng trống dữ liệu bị gián đoạn bằng dữ liệu gương (Mirror Data) có điều chỉnh CIF/FOB, mà vẫn bảo toàn tuyệt đối tính toàn vẹn và quy tắc Summarizability của Kho dữ liệu."**

### 1.5. Kết quả dự kiến đạt được
1. **Sản phẩm hệ thống:**
   - Cơ sở dữ liệu Kho dữ liệu `TLCN_XNK` hoàn chỉnh trên Microsoft SQL Server theo Star Schema, tích hợp hơn **500.000 – 1.000.000 bản ghi Fact**.
   - Khối lập phương đa chiều SSAS OLAP Cubes hoàn chỉnh với các chiều thời gian, địa lý, hàng hóa và nhóm đo lường thương mại.
   - Pipeline ETL viết bằng Python vận hành tự động, có khả năng phục hồi lỗi, chống trùng lặp dữ liệu và ghi vết kiểm toán.
   - 05 Dashboard tương tác trực quan hóa trên Microsoft Power BI Desktop phục vụ 5 kịch bản phân tích chiến lược.
2. **Bộ tài liệu thiết kế học thuật chuẩn mực:**
   - Ma trận Bus kiến trúc Kho dữ liệu (Bus Matrix).
   - Lược đồ hình sao chi tiết kèm ràng buộc toàn vẹn và Grain contract.
   - Bảng quy tắc nghiệp vụ nhúng trong CSDL (`DW_USAGE_RULE`).
   - Từ điển dữ liệu (Data Dictionary) và Ma trận ánh xạ nguồn - đích (Source-to-Target Mapping).
   - Bảng tra cứu chuẩn hóa quốc gia `REF_COUNTRY_CODES` và bảng hệ số chuyển đổi vận tải quốc tế `REF_CIF_FOB_FACTOR`.
3. **Báo cáo tiểu luận:** Hoàn chỉnh theo quy định Mẫu 5 của Khoa CNTT - HCMUTE.

---

## 2. PHẦN NỘI DUNG

### CHƯƠNG 1: TỔNG QUAN VỀ ĐỀ TÀI VÀ NGHIỆP VỤ XUẤT NHẬP KHẨU

1.1. Bối cảnh kinh tế và tầm quan trọng của hoạt động xuất nhập khẩu Việt Nam  
1.2. Thực trạng dữ liệu thương mại và thách thức khi phân tích trên các nguồn dữ liệu rời rạc  
 1.2.1. Vấn đề không đồng nhất về hệ thống mã hóa và độ trễ công bố  
 1.2.2. Hiện tượng gián đoạn số liệu báo cáo của Việt Nam từ năm 2024  
 1.2.3. Bất đối xứng thống kê song phương do cơ chế định giá FOB/CIF  
1.3. Phát biểu bài toán và các câu hỏi nghiệp vụ hỗ trợ ra quyết định  
 1.3.1. Nhóm câu hỏi về tận dụng lợi thế thuế quan theo hiệp định thương mại  
 1.3.2. Nhóm câu hỏi về nhận diện chu kỳ và tính mùa vụ của mặt hàng chủ lực  
 1.3.3. Nhóm câu hỏi về giám sát rủi ro phụ thuộc và mức độ tập trung thị trường  
 1.3.4. Nhóm câu hỏi về phân tích dòng chảy thương mại toàn cầu và bù đắp dữ liệu khuyết tật  
1.4. Mục tiêu, phạm vi và phương pháp nghiên cứu của đề tài  
1.5. Đóng góp kỹ thuật và học thuật của đề tài  
1.6. Cấu trúc của báo cáo tiểu luận  

### CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VỀ KHO DỮ LIỆU VÀ MÔ HÌNH HÓA ĐA CHIỀU

2.1. Tổng quan về Kho dữ liệu (Data Warehouse)  
 2.1.1. Khái niệm và bốn đặc trưng cốt lõi theo W. H. Inmon  
 2.1.2. So sánh chuyên sâu giữa hệ thống xử lý giao dịch (OLTP) và hệ thống phân tích (OLAP)  
 2.1.3. Kiến trúc tổng thể 4 tầng: Source, Staging, Enterprise Warehouse / Data Mart, BI Layer  
2.2. Phương pháp luận mô hình hóa đa chiều (Dimensional Modeling) theo Ralph Kimball  
 2.2.1. Quy trình thiết kế 4 bước của Kimball: Business Process $\rightarrow$ Grain $\rightarrow$ Dimensions $\rightarrow$ Facts  
 2.2.2. Ma trận Bus doanh nghiệp (Enterprise Data Warehouse Bus Matrix)  
 2.2.3. Chiều đồng nhất (Conformed Dimensions) và vai trò gắn kết các quy trình nghiệp vụ  
 2.2.4. Phân loại Fact Tables: Transaction Fact, Periodic Snapshot Fact, Accumulating Fact, Derived Fact  
 2.2.5. Phân loại Dimension Tables: Role-Playing, Degenerate, Junk, Outrigger và Audit Dimension  
 2.2.6. Khóa tự nhiên (Business Key) và Khóa thay thế (Surrogate Key): Cơ sở lý thuyết và ưu thế hiệu năng  
 2.2.7. Xử lý chiều thay đổi chậm (Slowly Changing Dimensions - SCD Type 1, Type 2, Type 3)  
2.3. Lý thuyết về tính cộng gộp được (Summarizability) theo Vaisman & Zimányi  
 2.3.1. Các điều kiện bảo đảm Summarizability: Disjointness, Completeness, Consistency  
 2.3.2. Phân loại độ đo: Cộng gộp toàn phần (Additive), Bán cộng gộp (Semi-additive), Phi cộng gộp (Non-additive)  
 2.3.3. Tác hại của việc cộng gộp sai nghiệp vụ và giải pháp kiểm soát ở tầng Semantic  
2.4. Lý thuyết về phân tích khối đa chiều (OLAP)  
 2.4.1. Các thao tác trên khối dữ liệu: Roll-up, Drill-down, Slice, Dice, Pivot  
 2.4.2. Các phần mở rộng SQL hỗ trợ phân tích: CUBE, ROLLUP, GROUPING SETS và Window Functions  
 2.4.3. Kiến trúc khối lập phương đa chiều SSAS (Cubes, Dimensions, Hierarchies, Measure Groups)  
2.5. Cơ sở nghiệp vụ chuyên ngành thương mại quốc tế  
 2.5.1. Hệ thống mã hài hòa mô tả hàng hóa (HS Nomenclature) và sự dịch chuyển mã qua các phiên bản  
 2.5.2. Biểu thuế quan tối huệ quốc (MFN) và thuế quan ưu đãi theo FTA  
 2.5.3. Cơ chế định giá FOB (Free On Board) và CIF (Cost, Insurance, and Freight)  
 2.5.4. Các chỉ số đo lường mức độ tập trung thị trường: Herfindahl-Hirschman Index (HHI) và Tỷ lệ tập trung (CR-n)  

### CHƯƠNG 3: KHẢO SÁT NGUỒN DỮ LIỆU VÀ PHÂN TÍCH YÊU CẦU

3.1. Khảo sát và đánh giá thực nghiệm các nguồn dữ liệu mở  
 3.1.1. UN Comtrade API v1: Giao thức, Subscription Key, cấu trúc dữ liệu thương mại song phương và dữ liệu Mirror  
 3.1.2. WITS / UNCTAD TRAINS API: Cấu trúc dữ liệu thuế quan, định dạng SDMX-XML, độ trễ cập nhật  
 3.1.3. World Bank Open Data API: Cấu trúc chỉ số vĩ mô và phương thức truy xuất  
 3.1.4. Đánh giá tính khả thi, giới hạn tốc độ (Rate Limit), độ trễ và độ phủ dữ liệu  
3.2. Phân tích yêu cầu chức năng theo 5 kịch bản nghiệp vụ  
 3.2.1. Kịch bản 1: Phân tích lợi thế và tác động cắt giảm thuế quan theo các cam kết FTA  
 3.2.2. Kịch bản 2: Nhận diện biến động chu kỳ và tính mùa vụ của các mặt hàng xuất khẩu chủ lực  
 3.2.3. Kịch bản 3: Giám sát rủi ro tập trung thị trường và đối tác thông qua chỉ số HHI và CR-4  
 3.2.4. Kịch bản 4: Phân tích phân bổ kim ngạch và dòng chảy thương mại toàn cầu của Việt Nam  
 3.2.5. Kịch bản 5: Giám sát chất lượng dữ liệu, đo lường độ bất đối xứng song phương và độ phủ thông tin  
3.3. Đặc tả bộ chỉ số đo lường nghiệp vụ (Metrics & KPIs)  
3.4. Ma trận truy vết yêu cầu nghiệp vụ về dữ liệu nguồn (Requirements Traceability Matrix)  
3.5. Yêu cầu phi chức năng: Tính toàn vẹn, tính khả truy, hiệu năng truy vấn và bảo mật  

### CHƯƠNG 4: THIẾT KẾ KHO DỮ LIỆU ĐA CHIỀU

4.1. Kiến trúc tổng thể hệ sinh thái Kho dữ liệu  
4.2. Xây dựng Ma trận Bus doanh nghiệp (Bus Matrix)  
4.3. Khai báo Grain tường minh cho từng bảng Fact  
4.4. Thiết kế các bảng chiều (Dimension Tables)  
 4.4.1. `DIM_DATE`: Chiều thời gian hỗ trợ phân cấp Lịch, tích hợp Khóa Sentinel (`YYYY00`) cho độ mịn Năm  
 4.4.2. `DIM_PARTNER`: Chiều đối tác thương mại mở rộng, tích hợp phân cấp địa lý (Region, Sub-region) và khối FTA  
 4.4.3. `DIM_COMMODITY`: Chiều hàng hóa HS6, giải quyết vấn đề phiên bản mã HS (HS2017 $\rightarrow$ HS2022)  
 4.4.4. `DIM_FLOW`: Chiều luồng thương mại (Xuất khẩu, Nhập khẩu) theo góc nhìn chuẩn hóa  
 4.4.5. `DIM_PERSPECTIVE`: Chiều góc nhìn báo cáo (Việt Nam tự báo cáo vs Đối tác báo cáo)  
 4.4.6. `DIM_TARIFF_TYPE`: Chiều phân loại thuế quan (MFN vs Ưu đãi Preferential)  
 4.4.7. `DIM_INDICATOR`: Chiều chỉ số kinh tế vĩ mô World Bank  
 4.4.8. `DIM_AUDIT`: Chiều kiểm toán dòng dõi dữ liệu (Data Lineage, Batch ID, Timestamp)  
4.5. Thiết kế các bảng hỗ trợ và tham chiếu chuẩn hóa  
 4.5.1. `REF_COUNTRY_CODES`: Bảng chuẩn hóa mã định danh quốc tế (M49, ISO3, ISO2) và thông tin khu vực  
 4.5.2. `REF_CIF_FOB_FACTOR`: Bảng hệ số chuyển đổi vận tải quốc tế CIF $\rightarrow$ FOB theo nhóm hàng và tuyến hải trình  
4.6. Thiết kế các bảng sự kiện (Fact Tables)  
 4.6.1. `FACT_TRADE`: Bảng Fact thương mại hàng hóa (Grain: Tháng $\times$ Đối tác $\times$ HS6 $\times$ Luồng $\times$ Góc nhìn)  
 4.6.2. `FACT_TARIFF_RATE`: Bảng Fact snapshot mức thuế suất (Grain: Năm $\times$ Đối tác $\times$ HS6 $\times$ Loại thuế $\times$ Combo)  
 4.6.3. `FACT_MACRO_INDICATOR`: Bảng Fact snapshot chỉ số vĩ mô (Grain: Năm $\times$ Quốc gia $\times$ Chỉ số)  
4.7. Thiết kế bảng nội quy kiểm soát tính cộng gộp trong CSDL (`DW_USAGE_RULE`)  
4.8. Thiết kế tầng hòa giải và ước tính dữ liệu (Derived Fact Views)  
 4.8.1. `VW_TRADE_RECONCILIATION`: View đối chiếu bất đối xứng song phương, phân loại mức độ chênh lệch  
 4.8.2. `VW_TRADE_BEST_ESTIMATE`: View ước tính tối ưu, kết hợp số liệu chính thức và Mirror đã quy đổi CIF/FOB  
4.9. Lược đồ hình sao tổng thể (Star Schema ERD) và kiểm tra tính Summarizability  
4.10. Từ điển dữ liệu (Data Dictionary) và Thiết kế vùng Landing/Staging  

### CHƯƠNG 5: HIỆN THỰC HÓA HỆ THỐNG VÀ QUY TRÌNH ETL

5.1. Môi trường triển khai và hạ tầng công nghệ  
 5.1.1. Microsoft SQL Server (Instance SQLEXPRESS1) và công cụ quản trị SSMS  
 5.1.2. SQL Server Analysis Services (Instance MSSQLSERVER1)  
 5.1.3. Môi trường lập trình Python (.venv) và Visual Studio Code  
 5.1.4. Microsoft Power BI Desktop cho tầng Semantic và Trực quan hóa  
5.2. Hiện thực tầng trích xuất dữ liệu tự động (Extract Pipeline)  
 5.2.1. Pipeline trích xuất dữ liệu UN Comtrade đa tầng (Multi-tier extraction) bằng Python  
 5.2.2. Cơ chế xử lý Rate Limiting, Exponential Backoff và Retry tự động  
 5.2.3. Pipeline trích xuất và phân tích cú pháp dữ liệu thuế quan SDMX từ WITS  
 5.2.4. Pipeline trích xuất chỉ số vĩ mô từ World Bank API  
 5.2.5. Tạo lập các tệp dữ liệu trung gian Staging CSV  
5.3. Hiện thực tầng chuyển đổi và nạp dữ liệu (Transform & Load)  
 5.3.1. BULK INSERT từ Staging CSV vào schema Landing Zone (`lz.*`)  
 5.3.2. Chuẩn hóa và làm sạch mã đối tác thông qua `REF_COUNTRY_CODES`  
 5.3.3. Ánh xạ mã hàng hóa đa phiên bản (HS2017 $\rightarrow$ HS2022) và sinh khóa thay thế  
 5.3.4. Hiện thực hóa câu lệnh `MERGE` (Idempotent Load) nạp các bảng Dimension và Fact  
 5.3.5. Ghi nhận thông tin kiểm toán và cập nhật trạng thái lô nạp vào `DIM_AUDIT`  
5.4. Hiện thực khối đa chiều SSAS OLAP Cubes  
 5.4.1. Thiết lập Data Source View và cấu hình quan hệ giữa các bảng  
 5.4.2. Xây dựng Measure Groups và cấu hình Aggregate Function phù hợp  
 5.4.3. Thiết kế phân cấp chiều (Hierarchies): Thời gian (Năm $\rightarrow$ Quý $\rightarrow$ Tháng), Địa lý (Khu vực $\rightarrow$ Quốc gia), Hàng hóa (HS2 $\rightarrow$ HS4 $\rightarrow$ HS6)  
 5.4.4. Xây dựng các Calculated Measures và KPI bằng ngôn ngữ MDX/DAX  
5.5. Hiện thực bộ truy vấn phân tích nâng cao trên SQL Server  
 5.5.1. Bộ truy vấn sử dụng CUBE, ROLLUP và GROUPING SETS  
 5.5.2. Bộ truy vấn sử dụng Window Functions (Xếp hạng, Tăng trưởng MoM/YoY, Tỷ trọng Running Total)  
 5.5.3. Bộ truy vấn phân tích chỉ số tập trung thị trường HHI và CR-4  
5.6. Xây dựng hệ thống Dashboard tương tác trên Microsoft Power BI Desktop  
 5.6.1. Thiết lập mô hình dữ liệu Semantic Layer và khóa tính năng SUM của `qty` theo luật R1  
 5.6.2. Dashboard D1: Đánh giá hiệu quả tận dụng lợi thế thuế quan FTA  
 5.6.3. Dashboard D2: Phân tích chu kỳ và nhận diện tính mùa vụ của mặt hàng xuất khẩu  
 5.6.4. Dashboard D3: Giám sát rủi ro tập trung thị trường và đối tác  
 5.6.5. Dashboard D4: Bản đồ luồng thương mại toàn cầu (Choropleth Map) và phân tích vùng kinh tế  
 5.6.6. Dashboard D5: Giám sát chất lượng dữ liệu và ma trận độ phủ thông tin đối chiếu  

### CHƯƠNG 6: KIỂM THỬ, ĐÁNH GIÁ KẾT QUẢ VÀ THỰC NGHIỆM

6.1. Kiểm thử tính toàn vẹn và chất lượng dữ liệu (Data Integrity Testing)  
 6.1.1. Kiểm tra tính duy nhất của Grain thông qua chỉ mục `UQ_FT_GRAIN`  
 6.1.2. Kiểm tra tính toàn vẹn tham chiếu khóa ngoại giữa Fact và các Dim  
 6.1.3. Kiểm thử tính bất biến và khả năng nạp lại (Idempotency) của lệnh `MERGE`  
6.2. Kiểm thử và đánh giá cơ chế đối chiếu gương và điền khuyết  
 6.2.1. Đánh giá mức độ bù đắp khoảng trống dữ liệu giai đoạn gián đoạn (2024–2025)  
 6.2.2. Phân tích định lượng mức độ bất đối xứng thống kê (FOB vs CIF) giữa các nhóm hàng  
 6.2.3. Đánh giá độ phủ dữ liệu (Data Coverage) trên 5 phân tầng quốc gia (Tier 1 đến Tier 5)  
6.3. Thực nghiệm 5 kịch bản nghiệp vụ và phân tích các phát hiện thực tế (Insights)  
6.4. Đánh giá hiệu năng truy vấn Kho dữ liệu (Query Performance Benchmark)  
 6.4.1. So sánh chi phí thực thi (Execution Plan, Logical Reads, Duration) trước và sau khi đánh chỉ mục chuyên biệt  
 6.4.2. Đánh giá hiệu năng giữa View thông thường và View vật chất hóa (Materialized/Indexed View)  
6.5. Rà soát kết quả đạt được so với mục tiêu và chuẩn đầu ra môn học  

---

## 3. PHẦN KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

- **Tổng kết các kết quả đạt được:** Hoàn thành toàn diện một hệ sinh thái Kho dữ liệu XNK từ API đến Dashboard; giải quyết thành công bài toán gián đoạn số liệu bằng kỹ thuật đối chiếu gương có điều chỉnh CIF/FOB; bảo đảm tuyệt đối tính toàn vẹn và tính cộng gộp của dữ liệu.
- **Những đóng góp nổi bật về mặt kỹ thuật và học thuật:**
  + Mô hình hóa đa chiều giải quyết hài hòa bài toán bất đối xứng thống kê quốc tế.
  + Cơ chế nhúng luật nghiệp vụ `DW_USAGE_RULE` trực tiếp vào cơ sở dữ liệu.
  + Giải pháp tích hợp mượt mà giữa SQL Server quan hệ và khối đa chiều SSAS Analysis Services.
- **Hạn chế của đề tài:**
  + Độ chi tiết của hàng hóa dừng ở cấp 6 chữ số (HS6), chưa đi sâu vào cấp 8 chữ số và 10 chữ số của biểu thuế quan chi tiết từng quốc gia.
  + Dữ liệu thuế quan WITS chỉ dừng ở độ mịn theo năm, chưa ghi nhận chính xác ngày biến động thuế suất giữa năm.
  + Chưa mở rộng sang lĩnh vực thương mại dịch vụ quốc tế.
- **Hướng phát triển trong tương lai (Mở rộng cho Khóa luận tốt nghiệp hoặc Luận văn thạc sĩ):**
  + Triển khai kỹ thuật học máy (Machine Learning) để dự báo kim ngạch xuất nhập khẩu theo chuỗi thời gian (ARIMA, Prophet, LSTM).
  + Nâng cấp kiến trúc lên mô hình Data Lakehouse trên nền tảng đám mây (Azure Synapse / Databricks / Snowflake).
  + Xây dựng cơ chế phát hiện bất thường tự động (Anomaly Detection) trong dòng chảy thương mại nhằm cảnh báo gian lận xuất xứ hàng hóa.

---

## 4. TÀI LIỆU THAM KHẢO

[1] R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd Edition, Wiley, Indianapolis, 2013.  
[2] A. Vaisman and E. Zimányi, *Data Warehouse Systems: Design and Implementation*, 2nd Edition, Springer, Berlin, 2022.  
[3] C. S. Jensen, T. B. Pedersen, and C. Thomsen, *Multidimensional Databases and Data Warehousing*, Morgan & Claypool, San Rafael, 2010.  
[4] W. H. Inmon, *Building the Data Warehouse*, 4th Edition, John Wiley & Sons, New York, 2005.  
[5] United Nations Statistics Division, *UN Comtrade Database API Reference Guide (v1)*, https://comtradeplus.un.org, 2026.  
[6] World Bank, *World Integrated Trade Solution (WITS) — User Manual and API Documentation*, https://wits.worldbank.org, 2026.  
[7] World Bank, *World Development Indicators API Documentation*, https://datahelpdesk.worldbank.org, 2026.  
[8] International Monetary Fund (IMF), *Direction of Trade Statistics (DOTS) Methodology and Bilateral Asymmetries Guide*, IMF Publications, Washington D.C., 2020.  
[9] OECD, *Measuring Bilateral Trade in Goods: The Role of CIF/FOB Adjustments and Statistical Reconciliations*, OECD Publishing, Paris, 2021.  
[10] Microsoft Corporation, *SQL Server Analysis Services (SSAS) Multidimensional Modeling Documentation*, Microsoft Learn, 2026.  
[11] Bộ Công Thương Việt Nam, *Báo cáo Xuất nhập khẩu Việt Nam các năm 2020 – 2024*, NXB Công Thương, Hà Nội.  
[12] Tổng cục Hải quan Việt Nam, *Cơ sở dữ liệu thống kê thương mại hàng hóa xuất nhập khẩu*, https://tongcuc.customs.gov.vn.  

---

## KẾ HOẠCH THỰC HIỆN 13 TUẦN CHI TIẾT

| Tuần | Công việc chi tiết | Sản phẩm bàn giao (Deliverables) | Phân công |
|:---:|---|---|:---:|
| **Tuần 1** | • Khảo sát quy trình nghiệp vụ XNK, hệ thống mã HS, các FTA.<br>• Đăng ký Subscription Key UN Comtrade, kiểm chứng thực nghiệm các API (Comtrade, WITS, World Bank).<br>• Thiết lập môi trường phát triển: Git repo, Python `.venv`, SQL Server, SSMS, VS Code. | • Báo cáo khảo sát nghiệp vụ và tính khả thi của các nguồn dữ liệu.<br>• Kho mã nguồn Git và môi trường hoạt động. | **Cả nhóm** |
| **Tuần 2** | • Phân tích yêu cầu và đặc tả 5 kịch bản nghiệp vụ.<br>• Xác định bộ chỉ số KPIs (Kim ngạch, Cán cân, Tỷ trọng, HHI, CR-4).<br>• Lập ma trận truy vết yêu cầu - dữ liệu.<br>• Thiết kế kiến trúc tổng thể hệ thống 4 tầng. | • Tài liệu đặc tả yêu cầu và bộ chỉ số.<br>• Sơ đồ kiến trúc tổng thể hệ thống.<br>• Ma trận truy vết yêu cầu nguồn. | SV1: Kịch bản & KPI<br>SV2: Kiến trúc & Nguồn |
| **Tuần 3** | • Thiết kế mô hình đa chiều Kimball: Bus Matrix, khai báo Grain contract.<br>• Thiết kế các bảng Dimension, Fact và Bảng tra cứu `REF_COUNTRY_CODES`, `REF_CIF_FOB_FACTOR`.<br>• Thiết lập bảng nội quy `DW_USAGE_RULE` nhúng trong CSDL.<br>• Soạn thảo script DDL hoàn chỉnh (`01_star_ddl.sql`). Bắt đầu viết bản thảo Chương 2. | • Script DDL `01_star_ddl.sql` tạo schema `TLCN_XNK`.<br>• Sơ đồ thiết kế Star Schema ERD.<br>• Bản thảo Chương 2 (Cơ sở lý thuyết). | SV2: DDL & Schema<br>SV1: Bus Matrix & Dim |
| **Tuần 4** | • Thiết kế chi tiết cơ chế đối chiếu gương và điền khuyết có kiểm soát CIF/FOB.<br>• Thiết kế tầng View: `VW_TRADE_RECONCILIATION` và `VW_TRADE_BEST_ESTIMATE`.<br>• Hoàn thiện Từ điển dữ liệu (Data Dictionary) và Ma trận ánh xạ nguồn - đích (Source-to-Target Mapping). | • Tài liệu Từ điển dữ liệu chi tiết.<br>• Tài liệu Ma trận ánh xạ Source-to-Target.<br>• Thiết kế logic của các View hòa giải. | **Cả nhóm** |
| **Tuần 5** | • Hiện thực hóa script Python trích xuất dữ liệu thương mại UN Comtrade (cả VN-reported và Partner-reported) theo mô hình phân tầng Đa cấp (Tier 1 đến Tier 5).<br>• Lập trình thuật toán chống Rate Limit, xử lý mã lỗi 429 và thử lại Exponential Backoff.<br>• Lưu trữ Raw JSON và xuất dữ liệu ra Staging CSV. | • Bộ script Python trích xuất Comtrade.<br>• Tệp Staging: `stg_comtrade_vn_reported.csv`, `stg_comtrade_partner_mirror.csv`. | SV1: Script Comtrade<br>SV2: Xử lý Retry & Tier |
| **Tuần 6** | • Hiện thực hóa script Python trích xuất biểu thuế quan SDMX từ WITS và chỉ số vĩ mô từ World Bank API.<br>• Lập trình bộ phân tích cú pháp XML/SDMX chuyển đổi sang định dạng bảng.<br>• Hoàn thành trọn bộ 5 tệp dữ liệu Staging. Bắt đầu viết bản thảo Chương 3. | • Bộ script Python trích xuất WITS và World Bank.<br>• Tệp Staging: `stg_wits_tariff.csv`, `stg_wb_macro.csv`.<br>• Bản thảo Chương 3 (Khảo sát yêu cầu). | SV2: Script WITS & WB<br>SV1: Kiểm tra Staging |
| **Tuần 7** | • Xây dựng quy trình nạp Landing Zone (`lz.*`) thông qua `BULK INSERT`.<br>• Viết lệnh T-SQL `MERGE` nạp các bảng Dimension: `DIM_DATE` (kèm Sentinel Key), `DIM_PARTNER` (qua bảng `REF_COUNTRY_CODES`), `DIM_COMMODITY` (ánh xạ HS2017 $\rightarrow$ HS2022).<br>• Sinh khóa thay thế tự tăng và kiểm soát lỗi trùng lặp. | • Script SQL `02_load_dims.sql` nạp thành công 8 bảng chiều.<br>• Nhật ký kiểm tra dữ liệu các bảng chiều. | SV1: Nạp Date, Partner<br>SV2: Nạp Commodity, Audit |
| **Tuần 8** | • Viết lệnh T-SQL `MERGE` nạp các bảng Fact: `FACT_TRADE`, `FACT_TARIFF_RATE`, `FACT_MACRO_INDICATOR`.<br>• Tra cứu khóa thay thế từ các bảng chiều, bảo toàn Grain bằng `UQ_FT_GRAIN`.<br>• Tích hợp ghi vết kiểm toán vào `DIM_AUDIT` cho từng đợt nạp. | • Script SQL `03_load_facts.sql` nạp thành công hơn 500.000 dòng Fact.<br>• Báo cáo kiểm tra toàn vẹn Grain Fact. | **Cả nhóm** |
| **Tuần 9** | • Hiện thực và kiểm thử các View hòa giải: `VW_TRADE_RECONCILIATION` và `VW_TRADE_BEST_ESTIMATE`.<br>• Kiểm tra tính chính xác của thuật toán quy đổi CIF $\rightarrow$ FOB qua `REF_CIF_FOB_FACTOR`.<br>• Tự động hóa toàn bộ luồng ETL từ Python đến SQL Server. Bắt đầu viết bản thảo Chương 4. | • Bộ View đối chiếu hoạt động chính xác.<br>• Pipeline nạp dữ liệu Idempotent hoàn chỉnh.<br>• Bản thảo Chương 4 (Thiết kế Kho dữ liệu). | SV2: Hoàn thiện View<br>SV1: Tự động hóa Pipeline |
| **Tuần 10** | • Cài đặt và cấu hình dự án SSAS trên Visual Studio (SSDT).<br>• Xây dựng khối lập phương đa chiều SSAS OLAP Cubes (Measure Groups, Hierarchies).<br>• Viết bộ truy vấn SQL phân tích nâng cao (CUBE, ROLLUP, GROUPING SETS, Window Functions). Bắt đầu viết bản thảo Chương 5. | • Project SSAS deploy thành công lên instance `MSSQLSERVER1`.<br>• Bộ script truy vấn SQL phân tích nâng cao.<br>• Bản thảo Chương 5 (Hiện thực hệ thống). | SV2: SSAS Cubes & MDX<br>SV1: Bộ truy vấn SQL OLAP |
| **Tuần 11** | • Cài đặt Microsoft Power BI Desktop, kết nối trực tiếp vào SQL Server và SSAS Cubes.<br>• Cấu hình Semantic Model và thiết lập ràng buộc luật `DW_USAGE_RULE` (khóa SUM cột `qty`).<br>• Thiết kế trọn bộ 5 Dashboard tương tác: D1 (FTA), D2 (Mùa vụ), D3 (Tập trung thị trường HHI), D4 (Bản đồ thương mại toàn cầu), D5 (Giám sát chất lượng dữ liệu). | • Tệp báo cáo Power BI (`.pbix`) với 5 Dashboard tương tác hoàn chỉnh.<br>• Video/Ảnh chụp minh họa các kịch bản phân tích. | SV1: Thiết kế Dashboard<br>SV2: Semantic & DAX Rules |
| **Tuần 12** | • Kiểm thử toàn diện tính toàn vẹn dữ liệu, kiểm thử hiệu năng truy vấn có index/materialized view.<br>• Thực nghiệm các kịch bản nghiệp vụ và phân tích các phát hiện insight.<br>• Đánh giá mức độ bù đắp khoảng trống dữ liệu gián đoạn. Hoàn thành toàn bộ bản thảo Chương 6. | • Báo cáo kết quả kiểm thử toàn vẹn và Benchmark hiệu năng truy vấn.<br>• Toàn bộ bản thảo báo cáo 6 chương. | **Cả nhóm** |
| **Tuần 13** | • Rà soát định dạng báo cáo theo Mẫu 5 HCMUTE, kiểm tra chính tả, tài liệu tham khảo.<br>• Chuẩn bị slide thuyết trình, quay video demo hệ thống.<br>• Gặp GVHD rà soát lần cuối, đóng tập báo cáo, ghi đĩa CD mã nguồn và nộp tiểu luận. Tổ chức bảo vệ thử. | • Báo cáo tiểu luận hoàn chỉnh (bản in và file PDF).<br>• Slide thuyết trình bảo vệ.<br>• Đĩa CD nộp lưu chiểu và mã nguồn trên Git. | **Cả nhóm** |

---

TP. Hồ Chí Minh, ngày 15 tháng 10 năm 2026

| **Sinh viên thực hiện 1** | **Sinh viên thực hiện 2** | **Ý kiến của Giáo viên hướng dẫn** |
|:---:|:---:|---|
| *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* |
| <br><br><br>**Nguyễn Khắc Dương** | <br><br><br>**Lưu Thái Thanh Lâm** | |
