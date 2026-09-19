"""
NHIỆM VỤ 6 — PROFILE BẰNG CHỨNG SỐ LIỆU CHO DANH SÁCH HS6 ỨNG VIÊN
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Mục đích:
- Trước khi chốt phạm vi HS6, kiểm tra nhanh từng mã ứng viên có số liệu thật không
  (VN-reported, chiều đúng theo nhóm xuất/nhập, đối tác World, năm 2022 và 2023).
- Kết quả dùng để điền vào bảng 3.3 của docs/06_NhiemVu6_ChotPhamViDeTai.md.
- Script này CHỈ gọi Comtrade annual cho từng mã (14 request x 2 năm), không extract hàng loạt.

Cách chạy Git Bash trên Windows:
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/profiling/scope_validation_profile.py

Không cần Comtrade API key (dùng public preview). Nếu có key trong .env, script tự chuyển endpoint.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests


# =========================
# 1. CẤU HÌNH
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "results" / "week1"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week1_scope_profile"

RESULT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Doc .env neu co de COMTRADE_SUBSCRIPTION_KEY tu .env duoc nhan ma khong can export.
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

SESSION = requests.Session()
VIETNAM_CODE = "704"
WORLD_CODE = "0"
SLEEP_SECONDS_BETWEEN_CALLS = 2.2
YEARS = ["2022", "2023"]

# Danh sách HS6 ứng viên cho phạm vi (side = chiều theo góc nhìn Việt Nam).
CANDIDATES = [
    {"hs6": "090111", "name": "Cà phê nhân xanh", "side": "EXPORT", "expect_kw": "coffee"},
    {"hs6": "100630", "name": "Gạo xát/xay", "side": "EXPORT", "expect_kw": "rice"},
    {"hs6": "080132", "name": "Hạt điều đã chế biến", "side": "EXPORT", "expect_kw": "cashew"},
    {"hs6": "090411", "name": "Hồ tiêu chưa xay", "side": "EXPORT", "expect_kw": "pepper"},
    {"hs6": "610910", "name": "Áo thun cotton (knit)", "side": "EXPORT", "expect_kw": "t-shirt"},
    {"hs6": "640399", "name": "Giày da các loại", "side": "EXPORT", "expect_kw": "footwear"},
    {"hs6": "851713", "name": "Điện thoại thông minh", "side": "EXPORT", "expect_kw": "smartphon"},
    {"hs6": "854442", "name": "Dây điện có đầu nối", "side": "EXPORT", "expect_kw": "conductor"},
    {"hs6": "851762", "name": "Thiết bị truyền dẫn dữ liệu", "side": "IMPORT", "expect_kw": "transmission"},
    {"hs6": "854231", "name": "Vi mạch xử lý (IC)", "side": "IMPORT", "expect_kw": "integrated circuit"},
    {"hs6": "847330", "name": "Linh kiện máy vi tính", "side": "IMPORT", "expect_kw": "parts 8471"},
    {"hs6": "721049", "name": "Thép cán dẹt mạ kẽm", "side": "IMPORT", "expect_kw": "iron or steel"},
    {"hs6": "540761", "name": "Vải sợi tổng hợp", "side": "IMPORT", "expect_kw": "polyester filaments"},
    {"hs6": "390120", "name": "Polyethylene dạng thô", "side": "IMPORT", "expect_kw": "polymer"},
]


# =========================
# 2. HÀM TIỆN ÍCH
# =========================


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:120]


def clean_text(value: object, limit: int = 250) -> str:
    text = "" if value is None else str(value)
    text = text.replace("|", "/").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def redact_url(url: str) -> str:
    return re.sub(r"(subscription-key=)[^&]+", r"\1***", url)


def to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_number(value: object, digits: int = 2) -> str:
    num = to_float(value)
    if num is None:
        return ""
    return f"{num:,.{digits}f}"


def request_with_retry(url: str, params: dict, timeout: int = 45, tries: int = 3) -> requests.Response:
    last_error = None
    response = None

    for attempt in range(1, tries + 1):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)

            if response.status_code == 429:
                match = re.search(r"Try again in (\d+)", response.text)
                wait_seconds = int(match.group(1)) + 1 if match else 5 * attempt
                print(f"    [429] Rate limit. Chờ {wait_seconds}s rồi gọi lại... ({attempt}/{tries})")
                time.sleep(wait_seconds)
                continue

            return response

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait_seconds = min(3 * attempt, 10)
            print(f"    [ERROR] {type(exc).__name__}: {exc}. Chờ {wait_seconds}s... ({attempt}/{tries})")
            time.sleep(wait_seconds)

    if response is not None:
        return response
    if last_error:
        raise last_error
    raise RuntimeError("Không nhận được response từ API")


def save_raw_response(file_stem: str, response: requests.Response) -> str:
    file_path = RAW_DIR / f"{safe_name(file_stem)}.json"
    file_path.write_bytes(response.content)
    return str(file_path.relative_to(PROJECT_ROOT))


# =========================
# 3. GỌI COMTRADE ANNUAL
# =========================


def fetch_annual_total(label: str, hs6: str, flow_code: str, period: str) -> dict:
    key = os.getenv("COMTRADE_SUBSCRIPTION_KEY") or os.getenv("COMTRADE_KEY")

    params = {
        "cmdCode": hs6,
        "flowCode": flow_code,
        "reporterCode": VIETNAM_CODE,
        "period": period,
        "partnerCode": WORLD_CODE,
        "motCode": "0",
        "customsCode": "C00",
        "partner2Code": "0",
        "includeDesc": "true",
    }

    if key:
        base_url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
        params["maxrecords"] = "500"
        params["subscription-key"] = key
        api_mode = "Comtrade data API with subscription key"
    else:
        base_url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
        params["maxrecords"] = "50"
        api_mode = "Comtrade public preview"

    full_url = base_url + "?" + urlencode(params)
    result = {
        "label": label,
        "source": api_mode,
        "url": redact_url(full_url),
        "tested_at": now_iso(),
        "ok": False,
        "status_code": None,
        "count": None,
        "value_usd": None,
        "cmd_desc": None,
        "raw_file_path": None,
        "note": "",
    }

    try:
        response = request_with_retry(base_url, params, timeout=45, tries=3)
        result["status_code"] = response.status_code
        result["raw_file_path"] = save_raw_response(label, response)

        if response.status_code != 200:
            result["note"] = clean_text(response.text, 300)
            return result

        data = response.json()
        rows = data.get("data") or []
        result["ok"] = True
        result["count"] = data.get("count", len(rows))
        result["note"] = clean_text(data.get("error") or "OK")

        if rows:
            d = rows[0]
            result["value_usd"] = to_float(d.get("primaryValue"))
            result["cmd_desc"] = clean_text(d.get("cmdDesc"), 160)

    except Exception as exc:  # noqa: BLE001
        result["note"] = clean_text(f"{type(exc).__name__}: {exc}", 300)

    return result


# =========================
# 4. PROFILE TỪNG ỨNG VIÊN
# =========================


def classify_row(r2022: dict, r2023: dict) -> str:
    v2023 = r2023.get("value_usd") if r2023.get("ok") else None
    v2022 = r2022.get("value_usd") if r2022.get("ok") else None

    if not r2022.get("ok") or not r2023.get("ok"):
        return "API_ERROR"
    if v2023 is not None and v2023 > 0:
        return "KEEP"
    if v2022 is not None and v2022 > 0:
        return "KEEP_FLAG_RECENT_GAP"
    return "REPLACE_OR_DROP"


def describe_name_match(cmd_desc: str | None, expect_kw: str) -> str:
    if not cmd_desc:
        return "KHONG_CO_CMD_DESC"
    low = cmd_desc.lower()
    keywords = [k.strip() for k in expect_kw.split() if k.strip()]
    matched = all(k in low for k in keywords)
    return "TRUNG_KHOP" if matched else "KIEM_TRA_LAI_TEN"


def profile_candidate(cand: dict, idx: int, total: int) -> dict:
    hs6 = cand["hs6"]
    flow = "X" if cand["side"] == "EXPORT" else "M"

    print(f"[{idx}/{total}] {hs6} {cand['name']} ({cand['side']})")

    by_year = {}
    for year in YEARS:
        label = f"scope_{hs6}_{flow}_{year}"
        by_year[year] = fetch_annual_total(label, hs6, flow, year)
        time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)

    r2022 = by_year["2022"]
    r2023 = by_year["2023"]
    status = classify_row(r2022, r2023)
    name_match = describe_name_match(r2023.get("cmd_desc") or r2022.get("cmd_desc"), cand["expect_kw"])

    v2022 = fmt_number(r2022.get("value_usd"))
    v2023 = fmt_number(r2023.get("value_usd"))
    desc = r2023.get("cmd_desc") or r2022.get("cmd_desc") or ""
    note = r2023.get("note") if not r2023.get("ok") else r2022.get("note")

    print(f"    2022 value={v2022 or '-'} | 2023 value={v2023 or '-'} | {status} | {name_match}")

    return {
        "hs6": hs6,
        "candidate_name": cand["name"],
        "side": cand["side"],
        "flow_code": flow,
        "period_2022_count": r2022.get("count"),
        "period_2022_value_usd": r2022.get("value_usd"),
        "period_2023_count": r2023.get("count"),
        "period_2023_value_usd": r2023.get("value_usd"),
        "comtrade_cmd_desc": desc,
        "name_match_check": name_match,
        "decision": status,
        "note": note or "",
        "url_2023": r2023.get("url"),
        "profiled_at": now_iso(),
    }


def profile_gap_check() -> dict:
    """Kiểm tra nhanh: VN export TOTAL sang World năm 2024 (bằng chứng gap cho phần 2024)."""
    print("[gap] VN export TOTAL to World 2024")
    res = fetch_annual_total("scope_gap_check_total_2024", "TOTAL", "X", "2024")
    time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)
    count = res.get("count")
    status = "CO_DATA" if res.get("ok") and count else "VAN_CHUA_CO" if res.get("ok") else "API_ERROR"
    print(f"    gap check 2024: count={count} -> {status}")
    return {
        "check": "VN_export_TOTAL_World_2024",
        "ok": res.get("ok"),
        "count": count,
        "value_usd": res.get("value_usd"),
        "status": status,
        "url": res.get("url"),
        "profiled_at": now_iso(),
    }


# =========================
# 5. GHI KẾT QUẢ
# =========================


def write_csv(results: list[dict]) -> None:
    path = RESULT_DIR / "scope_profile_results.csv"
    fieldnames = [
        "hs6",
        "candidate_name",
        "side",
        "flow_code",
        "period_2022_count",
        "period_2022_value_usd",
        "period_2023_count",
        "period_2023_value_usd",
        "comtrade_cmd_desc",
        "name_match_check",
        "decision",
        "note",
        "url_2023",
        "profiled_at",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def write_json(results: list[dict], gap: dict) -> None:
    path = RESULT_DIR / "scope_profile_results.json"
    payload = {"rows": results, "gap_check_2024": gap}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(results: list[dict], gap: dict) -> None:
    path = RESULT_DIR / "scope_profile_results.md"
    keep = [r for r in results if r["decision"] == "KEEP"]
    flag = [r for r in results if r["decision"] == "KEEP_FLAG_RECENT_GAP"]
    drop = [r for r in results if r["decision"] == "REPLACE_OR_DROP"]
    error = [r for r in results if r["decision"] == "API_ERROR"]

    lines = []
    lines.append("# SCOPE VALIDATION PROFILE — TUẦN 1 (NHIỆM VỤ 6)")
    lines.append("")
    lines.append("Mục đích: xác nhận từng HS6 ứng viên có số liệu thật (VN-reported, đối tác World, năm 2022-2023) trước khi chốt phạm vi.")
    lines.append("")
    lines.append("## 1. Bảng kết quả")
    lines.append("")
    lines.append("| HS6 | Nhóm hàng | Chiều | Kim ngạch 2022 (USD) | Kim ngạch 2023 (USD) | Comtrade mô tả | Tên khớp | Quyết định |")
    lines.append("|---|---|---|---:|---:|---|---|---|")
    for r in results:
        desc = clean_text(r["comtrade_cmd_desc"], 60)
        v22 = fmt_number(r["period_2022_value_usd"]) or "-"
        v23 = fmt_number(r["period_2023_value_usd"]) or "-"
        lines.append(
            f"| {r['hs6']} | {r['candidate_name']} | {r['side']} | {v22} | {v23} | {desc} | {r['name_match_check']} | {r['decision']} |"
        )
    lines.append("")
    lines.append("## 2. Tổng kết")
    lines.append("")
    lines.append(f"- Đủ điều kiện giữ (KEEP): {len(keep)}")
    lines.append(f"- Giữ nhưng có cờ thiếu năm gần (KEEP_FLAG_RECENT_GAP): {len(flag)}")
    lines.append(f"- Cần thay/loại (REPLACE_OR_DROP): {len(drop)}")
    lines.append(f"- Lỗi API (API_ERROR) — chạy lại trước khi kết luận: {len(error)}")
    lines.append("")
    lines.append("Quy tắc: KEEP = có dữ liệu 2023; KEEP_FLAG_RECENT_GAP = có 2022 nhưng 2023 trống; REPLACE_OR_DROP = cả hai năm trống.")
    lines.append("")
    lines.append("## 3. Gap check năm 2024")
    lines.append("")
    gap_status = gap.get("status")
    gap_count = gap.get("count")
    gap_value = fmt_number(gap.get("value_usd")) or "-"
    lines.append(f"- VN export TOTAL sang World, năm 2024: count={gap_count}, value={gap_value}, trạng thái={gap_status}")
    if gap_status == "VAN_CHUA_CO":
        lines.append("- Ý nghĩa: xác nhận dữ liệu năm 2024 phía Việt Nam trên Comtrade chưa cập nhật đầy đủ. Phạm vi 2024 chỉ nên là phụ/partial.")
    elif gap_status == "CO_DATA":
        lines.append("- Ý nghĩa: dữ liệu năm 2024 phía Việt Nam đã có thêm. Cân nhắc nâng 2024 lên phạm vi chính (ghi chú khi trình GVHD).")
    else:
        lines.append("- Ý nghĩa: lỗi kỹ thuật, chạy lại trước khi kết luận.")
    lines.append("")
    lines.append("## 4. Việc tiếp theo")
    lines.append("")
    lines.append("- Điền cột Quyết định vào bảng mục 3.3 của `docs/06_NhiemVu6_ChotPhamViDeTai.md`.")
    lines.append("- Các mã REPLACE_OR_DROP: chọn mã thay thế trong danh sách phương án (030617, 720839, 640299, 441239) hoặc hỏi GVHD.")

    path.write_text("\n".join(lines), encoding="utf-8")


# =========================
# 6. MAIN
# =========================


def main() -> None:
    print("=== NHIỆM VỤ 6: PROFILE HS6 ỨNG VIÊN CHO CHỐT PHẠM VI ===")
    print(f"Project root: {PROJECT_ROOT}")
    total = len(CANDIDATES)
    print(f"Số ứng viên: {total}; mỗi ứng viên gọi 2 request (2022, 2023). Chờ khoảng {int(total * 2 * (SLEEP_SECONDS_BETWEEN_CALLS + 2))} giây.")
    print("")

    results = []
    for idx, cand in enumerate(CANDIDATES, start=1):
        results.append(profile_candidate(cand, idx, total))

    gap = profile_gap_check()

    write_csv(results)
    write_json(results, gap)
    write_markdown(results, gap)

    print("")
    print("=== ĐÃ GHI KẾT QUẢ ===")
    for name in ("scope_profile_results.md", "scope_profile_results.csv", "scope_profile_results.json"):
        print(f"- {(RESULT_DIR / name).relative_to(PROJECT_ROOT)}")
    print("")
    print("=== TÓM TẮT QUYẾT ĐỊNH ===")
    for r in results:
        v2023 = fmt_number(r["period_2023_value_usd"]) or "-"
        print(f"- [{r['decision']}] {r['hs6']} {r['candidate_name']} ({r['side']}) 2023={v2023}")
    print("")
    print("Xong bước bằng chứng số liệu. Đưa bảng này vào docs/06_NhiemVu6_ChotPhamViDeTai.md mục 3.3 rồi chốt phạm vi.")


if __name__ == "__main__":
    main()
