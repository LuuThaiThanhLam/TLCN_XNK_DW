# TLCN_XNK_DW

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

## Mục tiêu hiện tại

- **Tuần 1** — khảo sát dữ liệu, chốt phạm vi, báo cáo khả thi — **đã hoàn thành**; bằng chứng tại `results/week1/`, `reports/`, `docs/00`→`docs/06`.
- **Tuần 2** — NV1 (kiểm API key, gate batch multi-period — PASS 6/6, `docs/07`) và NV2 (extract lõi VN_REPORTED 2015–2024, 13.725 dòng staging, validation 5/5 khớp từng cent với bằng chứng tuần 1 — `docs/08`) — **đã hoàn thành**; bằng chứng tại `results/week2/`.
- NV2b (bridge mã HS2017 `851712` cho 2015–2021, 958 dòng, annual-check đã điều tra tới tận nguồn — `docs/09`) và audit coverage toàn phạm vi (`scripts/profiling/audit_week2_coverage.py`: 249/252 ô 12/12 tháng, 14/14 neo docs/06 MATCH, 3 ô partial minh oan trùng khớp preview API tới từng tháng thiếu).
- NV3 mirror 5 đối tác (13.252 dòng, validation 8/8 khớp từng cent với bằng chứng tuần 1 — `docs/10`) — **đã hoàn thành**.
- NV4 (WITS biểu thuế + WB macro — `docs/11`) và NV5 (QA tuần + coverage + báo cáo) — đang thực hiện.


## Cấu trúc thư mục

```text
TLCN_XNK_DW/
├── docs/                  # Tài liệu phân tích, nguồn dữ liệu, luật thiết kế
├── reports/               # Báo cáo tuần, báo cáo khả thi, báo cáo cuối
├── refs/                  # Tài liệu tham khảo được phép lưu
├── dashboard/             # File Power BI/dashboard sau này
├── notebooks/             # Notebook phân tích thử nếu cần
├── scripts/
│   ├── extract/           # Script gọi API
│   ├── profiling/         # Script kiểm tra coverage/chất lượng dữ liệu
│   ├── transform_load/    # Script transform/load sau này
│   └── utils/             # Hàm dùng chung
├── sql/
│   ├── ddl/               # Script tạo bảng
│   ├── staging/           # Script staging
│   └── olap_queries/      # ROLLUP/CUBE/GROUPING SETS/window functions
├── data/
│   ├── raw/               # JSON/XML gốc từ API, không commit dữ liệu lớn
│   ├── staging/           # Dữ liệu staging xuất tạm
│   └── processed/         # Dữ liệu xử lý tạm
├── results/               # Kết quả chạy script, benchmark, profiling
├── .env.example           # Mẫu biến môi trường, không chứa key thật
├── .gitignore
└── requirements.txt
```

## Luật quan trọng

1. Dữ liệu chính lấy từ API, không dùng CSV/Excel tải sẵn làm nguồn chính.
2. Comtrade lõi phải khóa `motCode=0`, `customsCode=C00`, `partner2Code=0`.
3. Fact thương mại lõi dùng HS6, không trộn HS4 và HS6 trong cùng grain.
4. Không gọi dashboard là “tỷ lệ tận dụng FTA”.
5. Dữ liệu mirror dùng để đối chiếu/đánh dấu độ tin cậy, không thay thế âm thầm số liệu chính thức.
