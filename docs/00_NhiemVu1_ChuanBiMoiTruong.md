# NHIỆM VỤ 1 — CHUẨN BỊ MÔI TRƯỜNG VÀ THƯ MỤC DỰ ÁN

## 1. Mục tiêu

Tạo một không gian làm việc gọn gàng để các tuần sau không bị rối. Nhiệm vụ này chưa cần gọi API và chưa cần xây kho dữ liệu.

## 2. Đầu ra cần có

- Thư mục dự án `TLCN_XNK_DW/`.
- Cấu trúc thư mục rõ ràng cho docs, scripts, sql, data, reports, dashboard.
- File `.gitignore` để không đẩy dữ liệu lớn/key bí mật lên GitHub.
- File `.env.example` để ghi mẫu biến môi trường.
- File `requirements.txt` để cài thư viện Python.
- File `README.md` giải thích dự án.

## 3. Cấu trúc đã tạo

```text
TLCN_XNK_DW/
├── docs/
├── reports/
├── refs/
├── dashboard/
├── notebooks/
├── scripts/
│   ├── extract/
│   ├── profiling/
│   ├── transform_load/
│   └── utils/
├── sql/
│   ├── ddl/
│   ├── staging/
│   └── olap_queries/
├── data/
│   ├── raw/
│   ├── staging/
│   └── processed/
└── results/
```

## 4. Việc nhóm cần tự làm trên máy cá nhân

### 4.1. Cài Python

Kiểm tra:

```bash
python --version
```

Hoặc:

```bash
python3 --version
```

Nên dùng Python 3.10 trở lên.

### 4.2. Tạo môi trường ảo

Windows PowerShell:

```powershell
cd TLCN_XNK_DW
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
cd TLCN_XNK_DW
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.3. Tạo file `.env`

Copy `.env.example` thành `.env`, sau đó điền key nếu có:

```text
COMTRADE_SUBSCRIPTION_KEY=your_key_here
```

**Không gửi file `.env` lên GitHub.**

### 4.4. Git repo

Nếu nhóm dùng Git:

```bash
cd TLCN_XNK_DW
git init
git add .
git commit -m "init project structure"
```

Nếu đẩy GitHub, nhớ kiểm tra không có `.env` và dữ liệu lớn trong commit.

## 5. Checklist hoàn thành nhiệm vụ 1

- [ ] Có thư mục `TLCN_XNK_DW`.
- [ ] Có các thư mục `docs`, `scripts`, `sql`, `data`, `reports`, `dashboard`.
- [ ] Cài được Python.
- [ ] Cài được thư viện trong `requirements.txt`.
- [ ] Có `.env.example`.
- [ ] Nếu có API key, đã tạo `.env` riêng và không commit.
- [ ] Nếu dùng Git, đã commit cấu trúc ban đầu.

## 6. Kết luận

Khi nhiệm vụ 1 hoàn tất, nhóm đã có “bàn làm việc” chuẩn để bước sang nhiệm vụ 2: lập danh mục nguồn dữ liệu.
