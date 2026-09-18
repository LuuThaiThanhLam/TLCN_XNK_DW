"""
NHIỆM VỤ 3 — API SMOKE TEST
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Mục đích:
- Gọi thử UN Comtrade, WITS/UNCTAD TRAINS và World Bank.
- Chứng minh API có dữ liệu thật trước khi extract hàng loạt.
- Lưu kết quả test vào results/week1/.
- Lưu raw response vào data/raw/week1_smoke_test/ để làm bằng chứng audit.

Cách chạy Git Bash trên Windows:
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/profiling/api_smoke_test.py

Nếu có Comtrade API key:
    export COMTRADE_SUBSCRIPTION_KEY="key_cua_ban"
    python scripts/profiling/api_smoke_test.py
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests


# =========================
# 1. CẤU HÌNH ĐƯỜNG DẪN
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "results" / "week1"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week1_smoke_test"

RESULT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()


# =========================
# 2. HÀM TIỆN ÍCH
# =========================


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:100]


def redact_url(url: str) -> str:
    """Ẩn subscription key nếu có để không lộ key trong file kết quả."""
    return re.sub(r"(subscription-key=)[^&]+", r"\1***", url)


def request_with_retry(url: str, params: dict | None = None, timeout: int = 30, tries: int = 3) -> requests.Response:
    """Gọi API có retry đơn giản, xử lý riêng lỗi 429 rate limit."""
    last_error: Exception | None = None

    for attempt in range(1, tries + 1):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)

            # UN Comtrade preview hay trả 429 nếu gọi quá nhanh.
            if response.status_code == 429:
                match = re.search(r"Try again in (\d+)", response.text)
                wait_seconds = int(match.group(1)) + 1 if match else 4
                print(f"    [429] Rate limit. Chờ {wait_seconds}s rồi gọi lại... ({attempt}/{tries})")
                time.sleep(wait_seconds)
                continue

            return response

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait_seconds = min(2 * attempt, 8)
            print(f"    [ERROR] {type(exc).__name__}: {exc}. Chờ {wait_seconds}s rồi gọi lại... ({attempt}/{tries})")
            time.sleep(wait_seconds)

    if last_error:
        raise last_error

    return response


def save_raw_response(test_name: str, response: requests.Response, extension: str) -> str:
    file_path = RAW_DIR / f"{safe_name(test_name)}.{extension}"
    file_path.write_bytes(response.content)
    return str(file_path.relative_to(PROJECT_ROOT))


# =========================
# 3. TEST UN COMTRADE
# =========================


def test_comtrade(test_name: str, freq: str, params: dict) -> dict:
    """
    freq:
    - A = annual
    - M = monthly
    """
    key = os.getenv("COMTRADE_SUBSCRIPTION_KEY") or os.getenv("COMTRADE_KEY")

    # LUẬT KHÓA: tránh double counting mode/customs/partner2.
    params = dict(params)
    params.setdefault("motCode", "0")
    params.setdefault("customsCode", "C00")
    params.setdefault("partner2Code", "0")
    params.setdefault("includeDesc", "true")

    if key:
        base_url = f"https://comtradeapi.un.org/data/v1/get/C/{freq}/HS"
        params.setdefault("maxrecords", "100000")
        params["subscription-key"] = key
        api_mode = "Comtrade data API with subscription key"
    else:
        base_url = f"https://comtradeapi.un.org/public/v1/preview/C/{freq}/HS"
        params.setdefault("maxrecords", "50")
        api_mode = "Comtrade public preview"

    full_url = base_url + "?" + urlencode(params)

    result = {
        "test_name": test_name,
        "source": api_mode,
        "tested_at": now_iso(),
        "url": redact_url(full_url),
        "ok": False,
        "status_code": None,
        "count": None,
        "raw_file_path": None,
        "sample": None,
        "note": "",
    }

    try:
        response = request_with_retry(base_url, params=params, timeout=45, tries=3)
        result["status_code"] = response.status_code
        result["raw_file_path"] = save_raw_response(test_name, response, "json")

        if response.status_code != 200:
            result["note"] = response.text[:500]
            return result

        data = response.json()
        rows = data.get("data") or []

        result["ok"] = True
        result["count"] = data.get("count", len(rows))
        result["note"] = data.get("error") or "OK"

        if rows:
            d = rows[0]
            result["sample"] = {
                "period": d.get("period"),
                "freqCode": d.get("freqCode"),
                "refYear": d.get("refYear"),
                "refMonth": d.get("refMonth"),
                "reporterCode": d.get("reporterCode"),
                "reporterDesc": d.get("reporterDesc"),
                "flowCode": d.get("flowCode"),
                "flowDesc": d.get("flowDesc"),
                "partnerCode": d.get("partnerCode"),
                "partnerDesc": d.get("partnerDesc"),
                "cmdCode": d.get("cmdCode"),
                "cmdDesc": d.get("cmdDesc"),
                "motCode": d.get("motCode"),
                "customsCode": d.get("customsCode"),
                "primaryValue": d.get("primaryValue"),
                "fobvalue": d.get("fobvalue"),
                "cifvalue": d.get("cifvalue"),
                "qty": d.get("qty"),
                "netWgt": d.get("netWgt"),
                "isReported": d.get("isReported"),
                "isAggregate": d.get("isAggregate"),
            }

    except Exception as exc:  # noqa: BLE001
        result["note"] = f"{type(exc).__name__}: {exc}"

    return result


# =========================
# 4. TEST WITS/TRAINS
# =========================


def test_wits(test_name: str, reporter: str, partner: str, product: str, year: str) -> dict:
    url = (
        "https://wits.worldbank.org/API/V1/SDMX/V21/"
        f"datasource/TRN/reporter/{reporter}/partner/{partner}/product/{product}/year/{year}/datatype/reported"
    )

    result = {
        "test_name": test_name,
        "source": "WITS/UNCTAD TRAINS API",
        "tested_at": now_iso(),
        "url": url,
        "ok": False,
        "status_code": None,
        "count": None,
        "raw_file_path": None,
        "sample": None,
        "note": "",
    }

    try:
        response = request_with_retry(url, timeout=60, tries=2)
        result["status_code"] = response.status_code
        result["raw_file_path"] = save_raw_response(test_name, response, "xml")

        if response.status_code != 200:
            result["note"] = response.text[:500]
            return result

        root = ET.fromstring(response.content)
        series_attrs = None
        obs_rows = []

        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            if tag == "Series" and series_attrs is None:
                series_attrs = dict(elem.attrib)
            elif tag == "Obs":
                obs_rows.append(dict(elem.attrib))

        result["ok"] = True
        result["count"] = len(obs_rows)
        result["note"] = "OK" if obs_rows else "API gọi được nhưng không có Obs"

        if obs_rows:
            result["sample"] = {
                "series": series_attrs,
                "obs": obs_rows[0],
            }

    except Exception as exc:  # noqa: BLE001
        result["note"] = f"{type(exc).__name__}: {exc}"

    return result


# =========================
# 5. TEST WORLD BANK
# =========================


def test_worldbank(test_name: str, country: str, indicator: str, date: str) -> dict:
    base_url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    params = {
        "date": date,
        "format": "json",
        "per_page": "1000",
    }
    full_url = base_url + "?" + urlencode(params)

    result = {
        "test_name": test_name,
        "source": "World Bank Indicators API",
        "tested_at": now_iso(),
        "url": full_url,
        "ok": False,
        "status_code": None,
        "count": None,
        "raw_file_path": None,
        "sample": None,
        "note": "",
    }

    try:
        response = request_with_retry(base_url, params=params, timeout=30, tries=3)
        result["status_code"] = response.status_code
        result["raw_file_path"] = save_raw_response(test_name, response, "json")

        if response.status_code != 200:
            result["note"] = response.text[:500]
            return result

        data = response.json()
        metadata = data[0] if isinstance(data, list) and len(data) > 0 else {}
        rows = data[1] if isinstance(data, list) and len(data) > 1 and data[1] else []

        result["ok"] = True
        result["count"] = metadata.get("total", len(rows))
        result["note"] = "OK" if rows else "API gọi được nhưng không có dữ liệu"

        if rows:
            d = rows[0]
            result["sample"] = {
                "country": (d.get("country") or {}).get("value"),
                "countryiso3code": d.get("countryiso3code"),
                "indicator": (d.get("indicator") or {}).get("id"),
                "indicator_name": (d.get("indicator") or {}).get("value"),
                "date": d.get("date"),
                "value": d.get("value"),
                "unit": d.get("unit"),
                "obs_status": d.get("obs_status"),
            }

    except Exception as exc:  # noqa: BLE001
        result["note"] = f"{type(exc).__name__}: {exc}"

    return result


# =========================
# 6. GHI KẾT QUẢ
# =========================


def write_outputs(results: list[dict]) -> None:
    json_path = RESULT_DIR / "api_smoke_test_results.json"
    csv_path = RESULT_DIR / "api_smoke_test_results.csv"
    md_path = RESULT_DIR / "api_smoke_test_results.md"

    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "test_name",
                "source",
                "tested_at",
                "ok",
                "status_code",
                "count",
                "note",
                "url",
                "raw_file_path",
                "sample",
            ],
        )
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["sample"] = json.dumps(r.get("sample"), ensure_ascii=False)
            writer.writerow(row)

    lines = []
    lines.append("# API SMOKE TEST RESULTS — TUẦN 1")
    lines.append("")
    lines.append("Mục đích: kiểm tra nhanh API có gọi được không, có dữ liệu không, có rủi ro gì không.")
    lines.append("")
    lines.append("| # | Test | Source | OK | Status | Count | Note |")
    lines.append("|---:|---|---|:---:|---:|---:|---|")

    for idx, r in enumerate(results, start=1):
        note = str(r.get("note", "")).replace("|", "/").replace("\r", " ").replace("\n", " ")[:180]
        ok = "✅" if r.get("ok") else "❌"
        lines.append(
            f"| {idx} | {r['test_name']} | {r['source']} | {ok} | {r.get('status_code')} | {r.get('count')} | {note} |"
        )

    lines.append("")
    lines.append("## Chi tiết sample")
    lines.append("")

    for r in results:
        lines.append(f"### {r['test_name']}")
        lines.append("")
        lines.append(f"- URL: `{r['url']}`")
        lines.append(f"- Raw file: `{r.get('raw_file_path')}`")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(r.get("sample"), ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    lines.append("## Cách đọc kết quả")
    lines.append("")
    lines.append("- `OK = ✅`, `Count > 0`: API gọi được và có dữ liệu cho tổ hợp test.")
    lines.append("- `OK = ✅`, `Count = 0`: API gọi được nhưng tổ hợp đó không có dữ liệu; cần ghi vào coverage.")
    lines.append("- `OK = ❌`, status 429: gọi quá nhanh/rate limit; chạy lại sau hoặc dùng API key.")
    lines.append("- `OK = ❌`, timeout: API chậm; chạy lại sau và ghi nhận rủi ro.")
    lines.append("- WITS thiếu dữ liệu không có nghĩa bỏ WITS ngay; cần đổi partner/HS6/năm để profiling thêm.")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== ĐÃ GHI KẾT QUẢ ===")
    print(f"- {json_path.relative_to(PROJECT_ROOT)}")
    print(f"- {csv_path.relative_to(PROJECT_ROOT)}")
    print(f"- {md_path.relative_to(PROJECT_ROOT)}")
    print(f"- Raw responses: {RAW_DIR.relative_to(PROJECT_ROOT)}")


# =========================
# 7. MAIN
# =========================


def main() -> None:
    results: list[dict] = []

    print("=== NHIỆM VỤ 3: GỌI THỬ API ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Kết quả sẽ lưu vào: {RESULT_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Raw response sẽ lưu vào: {RAW_DIR.relative_to(PROJECT_ROOT)}")
    print("")

    # 1) UN Comtrade
    print("[1/3] Test UN Comtrade...")
    comtrade_tests = [
        (
            "Comtrade annual - VN export TOTAL to World 2023",
            "A",
            {"cmdCode": "TOTAL", "flowCode": "X", "reporterCode": "704", "period": "2023", "partnerCode": "0"},
        ),
        (
            "Comtrade annual - VN export TOTAL to World 2024 gap check",
            "A",
            {"cmdCode": "TOTAL", "flowCode": "X", "reporterCode": "704", "period": "2024", "partnerCode": "0"},
        ),
        (
            "Comtrade monthly - VN export HS090111 to Japan 2023M01",
            "M",
            {"cmdCode": "090111", "flowCode": "X", "reporterCode": "704", "period": "202301", "partnerCode": "392"},
        ),
        (
            "Comtrade monthly mirror - Japan import HS090111 from VN 2024M01",
            "M",
            {"cmdCode": "090111", "flowCode": "M", "reporterCode": "392", "period": "202401", "partnerCode": "704"},
        ),
    ]

    for test_name, freq, params in comtrade_tests:
        print(f"  - {test_name}")
        results.append(test_comtrade(test_name, freq, params))
        time.sleep(2)

    # 2) WITS/TRAINS
    print("\n[2/3] Test WITS/UNCTAD TRAINS...")
    wits_tests = [
        # MFN baseline: Việt Nam áp thuế lên hàng từ World
        ("WITS MFN baseline - VN tariff on World HS090111 2018", "704", "000", "090111", "2018"),
        # PREF: Việt Nam áp thuế ưu đãi lên hàng Nhật
        ("WITS PREF - VN tariff on Japan-origin goods HS090111 2018", "704", "392", "090111", "2018"),
        # Chiều xuất khẩu: Nhật áp thuế lên hàng Việt Nam
        ("WITS PREF - Japan tariff on Vietnam-origin goods HS090111 2018", "392", "704", "090111", "2018"),
    ]

    for test in wits_tests:
        print(f"  - {test[0]}")
        results.append(test_wits(*test))
        time.sleep(2)

    # 3) World Bank
    print("\n[3/3] Test World Bank Indicators...")
    wb_tests = [
        ("WB GDP current USD - Vietnam 2024", "VNM", "NY.GDP.MKTP.CD", "2024"),
        ("WB official exchange rate annual - Vietnam 2024", "VNM", "PA.NUS.FCRF", "2024"),
        ("WB exchange rate monthly candidate - Vietnam 2024M01 to 2024M12", "VNM", "DPANUSSPB", "2024M01:2024M12"),
    ]

    for test in wb_tests:
        print(f"  - {test[0]}")
        results.append(test_worldbank(*test))
        time.sleep(1)

    write_outputs(results)

    print("\n=== TÓM TẮT NHANH ===")
    for r in results:
        ok = "OK" if r.get("ok") else "FAIL"
        print(f"- [{ok}] {r['test_name']} | status={r.get('status_code')} | count={r.get('count')} | note={r.get('note')}")

    print("\nXong Nhiệm vụ 3 bước chạy thử. Hãy mở results/week1/api_smoke_test_results.md để đọc kết quả.")


if __name__ == "__main__":
    main()
