"""
NHIỆM VỤ 4 — KIỂM TRA DỮ LIỆU MIRROR CỦA UN COMTRADE
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Mục đích:
- So sánh dữ liệu Việt Nam báo cáo với dữ liệu mirror do đối tác báo cáo.
- Kiểm tra xem cơ chế VN_REPORTED vs PARTNER_MIRROR có khả thi không.
- Ghi nhận chênh lệch để chuẩn bị thiết kế FACT_TRADE_RECONCILIATION.
- Không extract dữ liệu lớn; chỉ profiling một số tổ hợp partner x HS6 x tháng.

Cách chạy Git Bash trên Windows:
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/profiling/mirror_check.py

Nếu có Comtrade API key:
    export COMTRADE_SUBSCRIPTION_KEY="key_cua_ban"
    python scripts/profiling/mirror_check.py

Nếu chưa có key, script dùng Comtrade public preview.
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
# 1. CẤU HÌNH ĐƯỜNG DẪN
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "results" / "week1"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week1_mirror_check"

RESULT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
VIETNAM_CODE = "704"

# Gọi chậm để giảm rủi ro rate limit khi chưa có Comtrade API key.
SLEEP_SECONDS_BETWEEN_CALLS = 2.2


# =========================
# 2. MA TRẬN TEST NHỎ
# =========================

"""
Hướng dẫn chỉnh CASES:
- direction = "EXPORT": so sánh Việt Nam xuất khẩu sang đối tác với đối tác nhập khẩu từ Việt Nam.
- direction = "IMPORT": so sánh Việt Nam nhập khẩu từ đối tác với đối tác xuất khẩu sang Việt Nam.
- period dùng dạng YYYYMM, ví dụ 202401.
- hs6 là mã HS6.

Không nên thêm quá nhiều case khi chưa có API key. Mỗi case gọi 2 request.
"""

CASES = [
    {
        "case_id": "EXP_JPN_COFFEE_202301",
        "direction": "EXPORT",
        "period": "202301",
        "partner_code": "392",
        "partner_name": "Japan",
        "hs6": "090111",
        "commodity_name": "Coffee; not roasted or decaffeinated",
    },
    {
        "case_id": "EXP_JPN_COFFEE_202401",
        "direction": "EXPORT",
        "period": "202401",
        "partner_code": "392",
        "partner_name": "Japan",
        "hs6": "090111",
        "commodity_name": "Coffee; not roasted or decaffeinated",
    },
    {
        "case_id": "EXP_USA_COFFEE_202301",
        "direction": "EXPORT",
        "period": "202301",
        "partner_code": "842",
        "partner_name": "United States",
        "hs6": "090111",
        "commodity_name": "Coffee; not roasted or decaffeinated",
    },
    {
        "case_id": "EXP_DEU_COFFEE_202301",
        "direction": "EXPORT",
        "period": "202301",
        "partner_code": "276",
        "partner_name": "Germany",
        "hs6": "090111",
        "commodity_name": "Coffee; not roasted or decaffeinated",
    },
    {
        "case_id": "IMP_CHN_NETWORK_EQUIP_202301",
        "direction": "IMPORT",
        "period": "202301",
        "partner_code": "156",
        "partner_name": "China",
        "hs6": "851762",
        "commodity_name": "Machines for reception, conversion and transmission/regeneration of data",
    },
    {
        "case_id": "IMP_KOR_INTEGRATED_CIRCUITS_202301",
        "direction": "IMPORT",
        "period": "202301",
        "partner_code": "410",
        "partner_name": "Rep. of Korea",
        "hs6": "854231",
        "commodity_name": "Electronic integrated circuits; processors and controllers",
    },
    {
        "case_id": "IMP_CHN_NETWORK_EQUIP_202401",
        "direction": "IMPORT",
        "period": "202401",
        "partner_code": "156",
        "partner_name": "China",
        "hs6": "851762",
        "commodity_name": "Machines for reception, conversion and transmission/regeneration of data",
    },
    {
        "case_id": "IMP_KOR_INTEGRATED_CIRCUITS_202401",
        "direction": "IMPORT",
        "period": "202401",
        "partner_code": "410",
        "partner_name": "Rep. of Korea",
        "hs6": "854231",
        "commodity_name": "Electronic integrated circuits; processors and controllers",
    },
]


# =========================
# 3. HÀM TIỆN ÍCH
# =========================


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:120]


def clean_text(value: object, limit: int = 250) -> str:
    text = str(value or "")
    text = text.replace("|", "/").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def redact_url(url: str) -> str:
    """Ẩn subscription key nếu có để không lộ key trong file kết quả."""
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


def request_with_retry(url: str, params: dict | None = None, timeout: int = 45, tries: int = 3) -> requests.Response:
    """Gọi API có retry đơn giản, xử lý riêng lỗi 429 rate limit."""
    last_error: Exception | None = None
    response: requests.Response | None = None

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
            print(f"    [ERROR] {type(exc).__name__}: {exc}. Chờ {wait_seconds}s rồi gọi lại... ({attempt}/{tries})")
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
# 4. GỌI COMTRADE
# =========================


def build_comtrade_params(*, reporter_code: str, partner_code: str, flow_code: str, hs6: str, period: str) -> dict:
    """Luật khóa Comtrade để tránh double counting."""
    return {
        "cmdCode": hs6,
        "flowCode": flow_code,
        "reporterCode": reporter_code,
        "period": period,
        "partnerCode": partner_code,
        "motCode": "0",
        "customsCode": "C00",
        "partner2Code": "0",
        "includeDesc": "true",
    }


def fetch_comtrade_monthly(label: str, params: dict) -> dict:
    key = os.getenv("COMTRADE_SUBSCRIPTION_KEY") or os.getenv("COMTRADE_KEY")

    params = dict(params)
    if key:
        base_url = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
        params.setdefault("maxrecords", "100000")
        params["subscription-key"] = key
        api_mode = "Comtrade data API with subscription key"
    else:
        base_url = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
        params.setdefault("maxrecords", "50")
        api_mode = "Comtrade public preview"

    full_url = base_url + "?" + urlencode(params)

    result = {
        "label": label,
        "source": api_mode,
        "tested_at": now_iso(),
        "url": redact_url(full_url),
        "ok": False,
        "status_code": None,
        "count": None,
        "raw_file_path": None,
        "row": None,
        "note": "",
    }

    try:
        response = request_with_retry(base_url, params=params, timeout=45, tries=3)
        result["status_code"] = response.status_code
        result["raw_file_path"] = save_raw_response(label, response)

        if response.status_code != 200:
            result["note"] = clean_text(response.text, 500)
            return result

        data = response.json()
        rows = data.get("data") or []
        count = data.get("count", len(rows))

        result["ok"] = True
        result["count"] = count
        result["note"] = clean_text(data.get("error") or "OK")

        if rows:
            d = rows[0]
            result["row"] = {
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
        result["note"] = clean_text(f"{type(exc).__name__}: {exc}", 500)

    return result


# =========================
# 5. SO SÁNH MIRROR
# =========================


def classify_discrepancy(pct_vs_vn: float | None, vn_count: int | None, mirror_count: int | None, api_ok: bool) -> str:
    if not api_ok:
        return "API_ERROR"

    vn_has_data = bool(vn_count and vn_count > 0)
    mirror_has_data = bool(mirror_count and mirror_count > 0)

    if not vn_has_data and not mirror_has_data:
        return "NO_DATA_BOTH"
    if not vn_has_data and mirror_has_data:
        return "MISSING_VN_REPORTED"
    if vn_has_data and not mirror_has_data:
        return "MISSING_MIRROR"

    if pct_vs_vn is None:
        return "HAS_DATA_BUT_CANNOT_COMPARE"
    if pct_vs_vn <= 10:
        return "LOW"
    if pct_vs_vn <= 30:
        return "MODERATE"
    return "HIGH"


def build_note(direction: str, vn_value: float | None, mirror_value: float | None, level: str) -> str:
    if level == "API_ERROR":
        return "Có lỗi kỹ thuật khi gọi ít nhất một phía API; cần chạy lại hoặc kiểm tra rate limit."
    if level == "NO_DATA_BOTH":
        return "Cả Việt Nam báo cáo và mirror đều không có dữ liệu cho tổ hợp này."
    if level == "MISSING_VN_REPORTED":
        return "Việt Nam báo cáo thiếu dữ liệu, nhưng partner mirror có dữ liệu; đây là case quan trọng cho cơ chế mirror."
    if level == "MISSING_MIRROR":
        return "Việt Nam báo cáo có dữ liệu, nhưng mirror từ đối tác thiếu; cần ghi nhận rủi ro coverage."

    if vn_value is None or mirror_value is None:
        return "Có dữ liệu nhưng không đủ trị giá để tính chênh lệch."

    if direction == "EXPORT":
        base = "EXPORT: VN thường ghi FOB, đối tác nhập khẩu thường ghi CIF; mirror cao hơn có thể là bình thường."
    else:
        base = "IMPORT: VN nhập khẩu thường ghi CIF, đối tác xuất khẩu thường ghi FOB; mirror thấp hơn có thể là bình thường."

    if mirror_value > vn_value:
        relation = "Mirror cao hơn VN-reported."
    elif mirror_value < vn_value:
        relation = "Mirror thấp hơn VN-reported."
    else:
        relation = "Mirror bằng VN-reported."

    return f"{relation} {base} Mức chênh lệch: {level}."


def compare_case(case: dict) -> dict:
    direction = case["direction"].upper()
    partner_code = case["partner_code"]
    period = case["period"]
    hs6 = case["hs6"]

    if direction == "EXPORT":
        # Việt Nam xuất khẩu sang partner vs partner nhập khẩu từ Việt Nam.
        vn_params = build_comtrade_params(
            reporter_code=VIETNAM_CODE,
            partner_code=partner_code,
            flow_code="X",
            hs6=hs6,
            period=period,
        )
        mirror_params = build_comtrade_params(
            reporter_code=partner_code,
            partner_code=VIETNAM_CODE,
            flow_code="M",
            hs6=hs6,
            period=period,
        )
        vn_label = f"{case['case_id']} - VN_REPORTED_EXPORT"
        mirror_label = f"{case['case_id']} - PARTNER_MIRROR_IMPORT"
        expected_pattern = "VN export FOB vs partner import CIF"
    elif direction == "IMPORT":
        # Việt Nam nhập khẩu từ partner vs partner xuất khẩu sang Việt Nam.
        vn_params = build_comtrade_params(
            reporter_code=VIETNAM_CODE,
            partner_code=partner_code,
            flow_code="M",
            hs6=hs6,
            period=period,
        )
        mirror_params = build_comtrade_params(
            reporter_code=partner_code,
            partner_code=VIETNAM_CODE,
            flow_code="X",
            hs6=hs6,
            period=period,
        )
        vn_label = f"{case['case_id']} - VN_REPORTED_IMPORT"
        mirror_label = f"{case['case_id']} - PARTNER_MIRROR_EXPORT"
        expected_pattern = "VN import CIF vs partner export FOB"
    else:
        raise ValueError(f"direction không hợp lệ: {direction}")

    vn = fetch_comtrade_monthly(vn_label, vn_params)
    time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)
    mirror = fetch_comtrade_monthly(mirror_label, mirror_params)
    time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)

    vn_row = vn.get("row") or {}
    mirror_row = mirror.get("row") or {}

    vn_value = to_float(vn_row.get("primaryValue"))
    mirror_value = to_float(mirror_row.get("primaryValue"))
    vn_net_wgt = to_float(vn_row.get("netWgt"))
    mirror_net_wgt = to_float(mirror_row.get("netWgt"))

    value_diff = None
    abs_value_diff = None
    pct_diff_vs_vn = None
    pct_diff_vs_max = None

    if vn_value is not None and mirror_value is not None:
        value_diff = mirror_value - vn_value
        abs_value_diff = abs(value_diff)
        if vn_value != 0:
            pct_diff_vs_vn = abs_value_diff / abs(vn_value) * 100
        max_value = max(abs(vn_value), abs(mirror_value))
        if max_value != 0:
            pct_diff_vs_max = abs_value_diff / max_value * 100

    net_wgt_diff = None
    pct_net_wgt_diff_vs_vn = None
    if vn_net_wgt is not None and mirror_net_wgt is not None:
        net_wgt_diff = mirror_net_wgt - vn_net_wgt
        if vn_net_wgt != 0:
            pct_net_wgt_diff_vs_vn = abs(net_wgt_diff) / abs(vn_net_wgt) * 100

    api_ok = bool(vn.get("ok")) and bool(mirror.get("ok"))
    level = classify_discrepancy(pct_diff_vs_vn, vn.get("count"), mirror.get("count"), api_ok)
    note = build_note(direction, vn_value, mirror_value, level)

    return {
        "case_id": case["case_id"],
        "direction": direction,
        "period": period,
        "partner_code": partner_code,
        "partner_name": case["partner_name"],
        "hs6": hs6,
        "commodity_name": case["commodity_name"],
        "expected_valuation_pattern": expected_pattern,
        "vn_status_code": vn.get("status_code"),
        "vn_count": vn.get("count"),
        "vn_value_usd": vn_value,
        "vn_fobvalue": to_float(vn_row.get("fobvalue")),
        "vn_cifvalue": to_float(vn_row.get("cifvalue")),
        "vn_qty": to_float(vn_row.get("qty")),
        "vn_net_wgt": vn_net_wgt,
        "vn_is_reported": vn_row.get("isReported"),
        "vn_is_aggregate": vn_row.get("isAggregate"),
        "vn_url": vn.get("url"),
        "vn_raw_file_path": vn.get("raw_file_path"),
        "vn_note": vn.get("note"),
        "mirror_status_code": mirror.get("status_code"),
        "mirror_count": mirror.get("count"),
        "mirror_value_usd": mirror_value,
        "mirror_fobvalue": to_float(mirror_row.get("fobvalue")),
        "mirror_cifvalue": to_float(mirror_row.get("cifvalue")),
        "mirror_qty": to_float(mirror_row.get("qty")),
        "mirror_net_wgt": mirror_net_wgt,
        "mirror_is_reported": mirror_row.get("isReported"),
        "mirror_is_aggregate": mirror_row.get("isAggregate"),
        "mirror_url": mirror.get("url"),
        "mirror_raw_file_path": mirror.get("raw_file_path"),
        "mirror_note": mirror.get("note"),
        "value_diff_mirror_minus_vn_usd": value_diff,
        "abs_value_diff_usd": abs_value_diff,
        "pct_diff_vs_vn": pct_diff_vs_vn,
        "pct_diff_vs_max": pct_diff_vs_max,
        "net_wgt_diff_mirror_minus_vn": net_wgt_diff,
        "pct_net_wgt_diff_vs_vn": pct_net_wgt_diff_vs_vn,
        "discrepancy_level": level,
        "analysis_note": note,
        "tested_at": now_iso(),
    }


# =========================
# 6. GHI KẾT QUẢ
# =========================


def write_json(results: list[dict]) -> None:
    path = RESULT_DIR / "mirror_check_results.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(results: list[dict]) -> None:
    path = RESULT_DIR / "mirror_check_results.csv"
    fieldnames = [
        "case_id",
        "direction",
        "period",
        "partner_name",
        "partner_code",
        "hs6",
        "commodity_name",
        "expected_valuation_pattern",
        "vn_status_code",
        "vn_count",
        "vn_value_usd",
        "mirror_status_code",
        "mirror_count",
        "mirror_value_usd",
        "value_diff_mirror_minus_vn_usd",
        "abs_value_diff_usd",
        "pct_diff_vs_vn",
        "pct_diff_vs_max",
        "vn_net_wgt",
        "mirror_net_wgt",
        "pct_net_wgt_diff_vs_vn",
        "discrepancy_level",
        "analysis_note",
        "vn_raw_file_path",
        "mirror_raw_file_path",
        "vn_url",
        "mirror_url",
        "tested_at",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def write_markdown(results: list[dict]) -> None:
    path = RESULT_DIR / "mirror_check_results.md"
    lines: list[str] = []

    lines.append("# MIRROR CHECK RESULTS — TUẦN 1")
    lines.append("")
    lines.append("Mục đích: so sánh nhanh dữ liệu Việt Nam báo cáo với dữ liệu mirror do đối tác báo cáo trên UN Comtrade.")
    lines.append("")
    lines.append("> Lưu ý: chênh lệch mirror là bình thường do khác biệt FOB/CIF, thời điểm ghi nhận, phương pháp thống kê, phân loại HS và độ trễ báo cáo. Kết quả này dùng để thiết kế cơ chế reconciliation, không dùng để kết luận bên nào sai.")
    lines.append("")
    lines.append("## 1. Bảng tổng hợp")
    lines.append("")
    lines.append("| # | Direction | Period | Partner | HS6 | VN count | Mirror count | VN value USD | Mirror value USD | Diff vs VN | Level | Note |")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---|---|")

    for idx, r in enumerate(results, start=1):
        pct = r.get("pct_diff_vs_vn")
        pct_text = "" if pct is None else f"{pct:.2f}%"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(idx),
                    clean_text(r.get("direction")),
                    clean_text(r.get("period")),
                    clean_text(r.get("partner_name")),
                    clean_text(r.get("hs6")),
                    clean_text(r.get("vn_count")),
                    clean_text(r.get("mirror_count")),
                    fmt_number(r.get("vn_value_usd")),
                    fmt_number(r.get("mirror_value_usd")),
                    pct_text,
                    clean_text(r.get("discrepancy_level")),
                    clean_text(r.get("analysis_note"), 180),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## 2. Cách đọc mức chênh lệch")
    lines.append("")
    lines.append("| Level | Ý nghĩa |")
    lines.append("|---|---|")
    lines.append("| LOW | Hai phía có dữ liệu và chênh lệch trị giá <= 10% so với VN-reported |")
    lines.append("| MODERATE | Hai phía có dữ liệu và chênh lệch > 10% đến <= 30% |")
    lines.append("| HIGH | Hai phía có dữ liệu và chênh lệch > 30%; cần kiểm tra kỹ khi chọn dashboard |")
    lines.append("| MISSING_VN_REPORTED | Việt Nam không có dữ liệu nhưng đối tác có mirror; đây là case hữu ích cho cơ chế mirror |")
    lines.append("| MISSING_MIRROR | Việt Nam có dữ liệu nhưng đối tác không có mirror |")
    lines.append("| NO_DATA_BOTH | Cả hai phía không có dữ liệu cho tổ hợp đó |")
    lines.append("| API_ERROR | Có lỗi kỹ thuật khi gọi API, cần chạy lại trước khi kết luận |")
    lines.append("")
    lines.append("## 3. Chi tiết từng case")
    lines.append("")

    for r in results:
        lines.append(f"### {r['case_id']}")
        lines.append("")
        lines.append(f"- Direction: `{r['direction']}`")
        lines.append(f"- Period: `{r['period']}`")
        lines.append(f"- Partner: `{r['partner_name']}` (`{r['partner_code']}`)")
        lines.append(f"- HS6: `{r['hs6']}` — {r['commodity_name']}")
        lines.append(f"- Expected valuation pattern: {r['expected_valuation_pattern']}")
        lines.append(f"- VN-reported count/value: `{r['vn_count']}` / `{fmt_number(r['vn_value_usd'])}` USD")
        lines.append(f"- Mirror count/value: `{r['mirror_count']}` / `{fmt_number(r['mirror_value_usd'])}` USD")
        lines.append(f"- Difference mirror - VN: `{fmt_number(r['value_diff_mirror_minus_vn_usd'])}` USD")
        pct = r.get("pct_diff_vs_vn")
        pct_text = "" if pct is None else f"{pct:.2f}%"
        lines.append(f"- Difference % vs VN: `{pct_text}`")
        lines.append(f"- Level: `{r['discrepancy_level']}`")
        lines.append(f"- Note: {clean_text(r['analysis_note'])}")
        lines.append(f"- VN raw: `{r['vn_raw_file_path']}`")
        lines.append(f"- Mirror raw: `{r['mirror_raw_file_path']}`")
        lines.append(f"- VN URL: `{r['vn_url']}`")
        lines.append(f"- Mirror URL: `{r['mirror_url']}`")
        lines.append("")

    lines.append("## 4. Kết luận sử dụng cho báo cáo")
    lines.append("")
    lines.append("Nếu có nhiều case hai phía đều có dữ liệu, có thể kết luận dữ liệu mirror khả thi để đưa vào kho dữ liệu. Nếu xuất hiện `MISSING_VN_REPORTED`, đây là bằng chứng cho nhu cầu dùng mirror để bổ sung/đối chiếu khi Việt Nam chưa có dữ liệu cập nhật. Nếu xuất hiện `HIGH`, không loại dữ liệu ngay mà cần lưu cả hai perspective và gắn cờ chất lượng dữ liệu trong `FACT_TRADE_RECONCILIATION`.")
    lines.append("")
    lines.append("## 5. Luật thiết kế rút ra")
    lines.append("")
    lines.append("- Không cộng trực tiếp VN-reported và partner-mirror vào cùng một chỉ tiêu chính nếu chưa chọn perspective.")
    lines.append("- `FACT_TRADE` phải có cột `reporting_perspective`, ví dụ `VN_REPORTED`, `PARTNER_MIRROR`.")
    lines.append("- Reconciliation nên nằm ở fact riêng hoặc view riêng, ví dụ `FACT_TRADE_RECONCILIATION`.")
    lines.append("- Chênh lệch không có nghĩa là dữ liệu sai; cần giải thích FOB/CIF, thời điểm ghi nhận và phương pháp thống kê.")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(results: list[dict]) -> None:
    write_json(results)
    write_csv(results)
    write_markdown(results)

    print("\n=== ĐÃ GHI KẾT QUẢ ===")
    print(f"- {(RESULT_DIR / 'mirror_check_results.json').relative_to(PROJECT_ROOT)}")
    print(f"- {(RESULT_DIR / 'mirror_check_results.csv').relative_to(PROJECT_ROOT)}")
    print(f"- {(RESULT_DIR / 'mirror_check_results.md').relative_to(PROJECT_ROOT)}")
    print(f"- Raw responses: {RAW_DIR.relative_to(PROJECT_ROOT)}")


# =========================
# 7. MAIN
# =========================


def main() -> None:
    print("=== NHIỆM VỤ 4: KIỂM TRA MIRROR DATA ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Kết quả sẽ lưu vào: {RESULT_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Raw response sẽ lưu vào: {RAW_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Số case: {len(CASES)}; mỗi case gọi 2 request Comtrade")
    print("")

    results: list[dict] = []
    for idx, case in enumerate(CASES, start=1):
        print(f"[{idx}/{len(CASES)}] {case['case_id']} | {case['direction']} | {case['partner_name']} | {case['hs6']} | {case['period']}")
        result = compare_case(case)
        results.append(result)
        pct = result.get("pct_diff_vs_vn")
        pct_text = "" if pct is None else f"{pct:.2f}%"
        print(
            "  -> "
            f"VN count={result.get('vn_count')}, mirror count={result.get('mirror_count')}, "
            f"level={result.get('discrepancy_level')}, "
            f"diff_vs_vn={pct_text}"
        )

    write_outputs(results)

    print("\n=== TÓM TẮT NHANH ===")
    for r in results:
        pct = r.get("pct_diff_vs_vn")
        pct_text = "N/A" if pct is None else f"{pct:.2f}%"
        print(
            f"- [{r['discrepancy_level']}] {r['case_id']} | "
            f"VN={fmt_number(r.get('vn_value_usd')) or 'None'} | "
            f"Mirror={fmt_number(r.get('mirror_value_usd')) or 'None'} | "
            f"Diff={pct_text}"
        )

    print("\nXong Nhiệm vụ 4 bước kiểm tra mirror. Hãy mở results/week1/mirror_check_results.md để đọc kết quả.")


if __name__ == "__main__":
    main()
