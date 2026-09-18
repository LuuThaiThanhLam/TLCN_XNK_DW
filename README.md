# TLCN_XNK_DW

**Đề tài:** Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

## Mục tiêu hiện tại

Dự án đang ở **Tuần 1 — Phần 1: Khảo sát dữ liệu và chốt phạm vi**.

Tuần 1 tập trung kiểm chứng dữ liệu từ API, chưa xây Data Warehouse đầy đủ.

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
