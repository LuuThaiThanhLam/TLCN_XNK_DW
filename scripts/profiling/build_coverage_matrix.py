"""
NHIỆM VỤ 5 — LẬP COVERAGE MATRIX
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Mục đích:
- Gom kết quả từ Nhiệm vụ 3 API smoke test và Nhiệm vụ 4 mirror check.
- Chuẩn hóa thành ma trận coverage để biết tổ hợp nào có dữ liệu, tổ hợp nào thiếu.
- Tạo bằng chứng cho việc chốt phạm vi đề tài ở Nhiệm vụ 6.

Script này KHÔNG gọi API mới.
Nó chỉ đọc các file kết quả đã có:
- results/week1/api_smoke_test_results.csv
- results/week1/mirror_check_results.csv

Cách chạy Git Bash trên Windows:
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/profiling/build_coverage_matrix.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "results" / "week1"

API_SMOKE_CSV = RESULT_DIR / "api_smoke_test_results.csv"
MIRROR_CHECK_CSV = RESULT_DIR / "mirror_check_results.csv"

OUT_CSV = RESULT_DIR / "Coverage_Matrix.csv"
OUT_JSON = RESULT_DIR / "Coverage_Matrix.json"
OUT_MD = RESULT_DIR / "Coverage_Matrix.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clean(value: object) -> str:
    text = str(value or "")
    text = text.replace("|", "/").replace("\r", " ").replace("\n", " ")
    return " ".join(text.split())


def to_int(value: object) -> int | None:
    text = clean(value)
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def to_float(value: object) -> float | None:
    text = clean(value)
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def is_true(value: object) -> bool:
    return clean(value).lower() in {"true", "1", "yes", "y", "ok", "✅"}


def availability_from_count(count: object, ok: object = True) -> str:
    if ok is not True and not is_true(ok):
        return "NO"
    c = to_int(count)
    if c is None:
        return "UNKNOWN"
    return "YES" if c > 0 else "NO"


def fmt_num(value: object, digits: int = 2) -> str:
    num = to_float(value)
    if num is None:
        return ""
    return f"{num:,.{digits}f}"


def fmt_pct(value: object) -> str:
    num = to_float(value)
    if num is None:
        return ""
    return f"{num:.2f}%"


def base_matrix_row() -> dict:
    return {
        "row_id": "",
        "coverage_area": "",
        "business_question": "",
        "source_evidence": "",
        "direction": "",
        "partner_name": "",
        "partner_code": "",
        "hs6": "",
        "commodity_name": "",
        "period_grain": "",
        "year_or_month": "",
        "comtrade_vn_reported_available": "UNKNOWN",
        "comtrade_vn_reported_count": "",
        "comtrade_mirror_available": "UNKNOWN",
        "comtrade_mirror_count": "",
        "wits_mfn_available": "UNKNOWN",
        "wits_mfn_count": "",
        "wits_pref_available": "UNKNOWN",
        "wits_pref_count": "",
        "worldbank_available": "UNKNOWN",
        "observed_value_usd_vn": "",
        "observed_value_usd_mirror": "",
        "pct_diff_vs_vn": "",
        "coverage_status": "",
        "scope_recommendation": "",
        "note": "",
        "evidence_file": "",
        "built_at": now_iso(),
    }


def recommendation_from_mirror_level(level: str) -> str:
    level = level.upper()
    if level == "LOW":
        return "CORE_CANDIDATE"
    if level == "MODERATE":
        return "CORE_CANDIDATE_WITH_FLAG"
    if level == "HIGH":
        return "RECONCILIATION_DEMO"
    if level == "MISSING_VN_REPORTED":
        return "MIRROR_FALLBACK_DEMO"
    if level == "MISSING_MIRROR":
        return "VN_REPORTED_ONLY_RISK"
    if level == "NO_DATA_BOTH":
        return "EXCLUDE_OR_RETEST"
    if level == "API_ERROR":
        return "RETRY_REQUIRED"
    return "NEEDS_REVIEW"


def build_rows_from_mirror(mirror_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for idx, src in enumerate(mirror_rows, start=1):
        direction = clean(src.get("direction"))
        partner = clean(src.get("partner_name"))
        hs6 = clean(src.get("hs6"))
        period = clean(src.get("period"))

        row = base_matrix_row()
        row.update(
            {
                "row_id": f"TRADE-{idx:03d}",
                "coverage_area": "TRADE_MIRROR",
                "source_evidence": "UN Comtrade monthly; from mirror_check_results.csv",
                "direction": direction,
                "partner_name": partner,
                "partner_code": clean(src.get("partner_code")),
                "hs6": hs6,
                "commodity_name": clean(src.get("commodity_name")),
                "period_grain": "MONTH",
                "year_or_month": period,
                "comtrade_vn_reported_count": clean(src.get("vn_count")),
                "comtrade_mirror_count": clean(src.get("mirror_count")),
                "comtrade_vn_reported_available": availability_from_count(src.get("vn_count"), True),
                "comtrade_mirror_available": availability_from_count(src.get("mirror_count"), True),
                "observed_value_usd_vn": clean(src.get("vn_value_usd")),
                "observed_value_usd_mirror": clean(src.get("mirror_value_usd")),
                "pct_diff_vs_vn": clean(src.get("pct_diff_vs_vn")),
                "coverage_status": clean(src.get("discrepancy_level")),
                "scope_recommendation": recommendation_from_mirror_level(clean(src.get("discrepancy_level"))),
                "note": clean(src.get("analysis_note")),
                "evidence_file": "results/week1/mirror_check_results.csv",
            }
        )

        if direction == "EXPORT":
            row["business_question"] = f"Đối chiếu Việt Nam xuất khẩu HS{hs6} sang {partner} với mirror nhập khẩu của {partner}"
        elif direction == "IMPORT":
            row["business_question"] = f"Đối chiếu Việt Nam nhập khẩu HS{hs6} từ {partner} với mirror xuất khẩu của {partner}"
        else:
            row["business_question"] = "Đối chiếu VN-reported và partner-mirror"

        rows.append(row)

    return rows


def parse_wits_test_name(test_name: str) -> dict:
    """Rút thông tin cơ bản từ tên test WITS đã chuẩn hóa ở Nhiệm vụ 3."""
    name = clean(test_name)

    if "MFN baseline - VN tariff on World HS090111 2018" in name:
        return {
            "area": "TARIFF_MFN",
            "business_question": "Có MFN baseline cho Việt Nam áp thuế lên HS090111 không?",
            "direction": "IMPORT_TARIFF",
            "partner_name": "World",
            "partner_code": "000",
            "hs6": "090111",
            "commodity_name": "Coffee; not roasted or decaffeinated",
            "year": "2018",
            "mfn_or_pref": "MFN",
        }

    if "PREF - VN tariff on Japan-origin goods HS090111 2018" in name:
        return {
            "area": "TARIFF_PREF",
            "business_question": "Có thuế ưu đãi cho hàng HS090111 xuất xứ Nhật nhập vào Việt Nam không?",
            "direction": "IMPORT_TARIFF",
            "partner_name": "Japan",
            "partner_code": "392",
            "hs6": "090111",
            "commodity_name": "Coffee; not roasted or decaffeinated",
            "year": "2018",
            "mfn_or_pref": "PREF",
        }

    if "PREF - Japan tariff on Vietnam-origin goods HS090111 2018" in name:
        return {
            "area": "TARIFF_PREF",
            "business_question": "Có thuế ưu đãi của Nhật cho hàng HS090111 xuất xứ Việt Nam không?",
            "direction": "EXPORT_TARIFF",
            "partner_name": "Japan",
            "partner_code": "392",
            "hs6": "090111",
            "commodity_name": "Coffee; not roasted or decaffeinated",
            "year": "2018",
            "mfn_or_pref": "PREF",
        }

    return {
        "area": "TARIFF_OTHER",
        "business_question": name,
        "direction": "",
        "partner_name": "",
        "partner_code": "",
        "hs6": "",
        "commodity_name": "",
        "year": "",
        "mfn_or_pref": "",
    }


def parse_worldbank_test_name(test_name: str) -> dict:
    name = clean(test_name)
    if "GDP current USD" in name:
        return {
            "indicator": "NY.GDP.MKTP.CD",
            "business_question": "Có dữ liệu GDP để làm bối cảnh vĩ mô không?",
            "grain": "YEAR",
            "period": "2024",
        }
    if "official exchange rate annual" in name:
        return {
            "indicator": "PA.NUS.FCRF",
            "business_question": "Có tỷ giá chính thức bình quân năm không?",
            "grain": "YEAR",
            "period": "2024",
        }
    if "exchange rate monthly candidate" in name:
        return {
            "indicator": "DPANUSSPB",
            "business_question": "Có tỷ giá tháng ứng viên để làm dữ liệu bổ trợ không?",
            "grain": "MONTH",
            "period": "2024M01:2024M12",
        }
    return {
        "indicator": "",
        "business_question": name,
        "grain": "",
        "period": "",
    }


def build_rows_from_api_smoke(smoke_rows: list[dict], start_idx: int) -> list[dict]:
    rows: list[dict] = []
    row_no = start_idx

    for src in smoke_rows:
        test_name = clean(src.get("test_name"))
        source = clean(src.get("source"))
        ok = is_true(src.get("ok"))
        count = to_int(src.get("count"))
        available = availability_from_count(count, ok)
        note = clean(src.get("note"))

        if "WITS" in source:
            info = parse_wits_test_name(test_name)
            row = base_matrix_row()
            row_no += 1
            row.update(
                {
                    "row_id": f"TARIFF-{row_no:03d}",
                    "coverage_area": info["area"],
                    "business_question": info["business_question"],
                    "source_evidence": "WITS/UNCTAD TRAINS API; from api_smoke_test_results.csv",
                    "direction": info["direction"],
                    "partner_name": info["partner_name"],
                    "partner_code": info["partner_code"],
                    "hs6": info["hs6"],
                    "commodity_name": info["commodity_name"],
                    "period_grain": "YEAR",
                    "year_or_month": info["year"],
                    "coverage_status": "AVAILABLE" if available == "YES" else "MISSING_OR_FAILED",
                    "note": note,
                    "evidence_file": "results/week1/api_smoke_test_results.csv",
                }
            )
            if info["mfn_or_pref"] == "MFN":
                row["wits_mfn_available"] = available
                row["wits_mfn_count"] = "" if count is None else str(count)
                row["scope_recommendation"] = "TARIFF_BASELINE_AVAILABLE" if available == "YES" else "TARIFF_BASELINE_RISK"
            elif info["mfn_or_pref"] == "PREF":
                row["wits_pref_available"] = available
                row["wits_pref_count"] = "" if count is None else str(count)
                row["scope_recommendation"] = "TARIFF_PREF_AVAILABLE" if available == "YES" else "TARIFF_PREF_COVERAGE_RISK"
            else:
                row["scope_recommendation"] = "NEEDS_REVIEW"
            rows.append(row)

        elif "World Bank" in source:
            info = parse_worldbank_test_name(test_name)
            row = base_matrix_row()
            row_no += 1
            row.update(
                {
                    "row_id": f"MACRO-{row_no:03d}",
                    "coverage_area": "MACRO_INDICATOR",
                    "business_question": info["business_question"],
                    "source_evidence": "World Bank Indicators API; from api_smoke_test_results.csv",
                    "direction": "MACRO",
                    "partner_name": "Viet Nam",
                    "partner_code": "VNM",
                    "hs6": "",
                    "commodity_name": info["indicator"],
                    "period_grain": info["grain"],
                    "year_or_month": info["period"],
                    "worldbank_available": available,
                    "coverage_status": "AVAILABLE" if available == "YES" else "MISSING_OR_FAILED",
                    "scope_recommendation": "MACRO_CONTEXT_AVAILABLE" if available == "YES" else "MACRO_CONTEXT_RISK",
                    "note": note,
                    "evidence_file": "results/week1/api_smoke_test_results.csv",
                }
            )
            rows.append(row)

        elif "Comtrade" in source:
            # Giữ lại các smoke test Comtrade quan trọng như evidence tổng quan.
            if "annual" in test_name.lower() or "monthly" in test_name.lower():
                row = base_matrix_row()
                row_no += 1
                area = "TRADE_SMOKE"
                direction = "EXPORT" if "export" in test_name.lower() else "IMPORT" if "import" in test_name.lower() else ""
                row.update(
                    {
                        "row_id": f"SMOKE-{row_no:03d}",
                        "coverage_area": area,
                        "business_question": test_name,
                        "source_evidence": "UN Comtrade API; from api_smoke_test_results.csv",
                        "direction": direction,
                        "period_grain": "MONTH" if "monthly" in test_name.lower() else "YEAR",
                        "year_or_month": "2024" if "2024" in test_name else "2023" if "2023" in test_name else "",
                        "comtrade_vn_reported_available": available if "mirror" not in test_name.lower() else "UNKNOWN",
                        "comtrade_vn_reported_count": "" if "mirror" in test_name.lower() or count is None else str(count),
                        "comtrade_mirror_available": available if "mirror" in test_name.lower() else "UNKNOWN",
                        "comtrade_mirror_count": "" if "mirror" not in test_name.lower() or count is None else str(count),
                        "coverage_status": "AVAILABLE" if available == "YES" else "NO_DATA_BUT_API_OK" if ok and count == 0 else "MISSING_OR_FAILED",
                        "scope_recommendation": "TRADE_SOURCE_AVAILABLE" if available == "YES" else "TRADE_RECENT_YEAR_GAP" if ok and count == 0 else "RETRY_REQUIRED",
                        "note": note,
                        "evidence_file": "results/week1/api_smoke_test_results.csv",
                    }
                )
                rows.append(row)

    return rows


def write_csv_output(rows: list[dict]) -> None:
    fieldnames = list(base_matrix_row().keys())
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json_output(rows: list[dict]) -> None:
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def build_summary(rows: list[dict]) -> dict:
    coverage_status = Counter(clean(r.get("coverage_status")) for r in rows)
    recommendations = Counter(clean(r.get("scope_recommendation")) for r in rows)
    areas = Counter(clean(r.get("coverage_area")) for r in rows)

    trade_rows = [r for r in rows if clean(r.get("coverage_area")) in {"TRADE_MIRROR", "TRADE_SMOKE"}]
    mirror_rows = [r for r in rows if clean(r.get("coverage_area")) == "TRADE_MIRROR"]
    tariff_rows = [r for r in rows if clean(r.get("coverage_area")).startswith("TARIFF")]
    macro_rows = [r for r in rows if clean(r.get("coverage_area")) == "MACRO_INDICATOR"]

    return {
        "total_rows": len(rows),
        "areas": dict(areas),
        "coverage_status": dict(coverage_status),
        "recommendations": dict(recommendations),
        "trade_rows": len(trade_rows),
        "mirror_rows": len(mirror_rows),
        "tariff_rows": len(tariff_rows),
        "macro_rows": len(macro_rows),
        "built_at": now_iso(),
    }


def write_markdown_output(rows: list[dict]) -> None:
    summary = build_summary(rows)
    lines: list[str] = []

    lines.append("# COVERAGE MATRIX — TUẦN 1")
    lines.append("")
    lines.append("Mục đích: gom kết quả smoke test và mirror check để xác định nguồn/tổ hợp nào có dữ liệu, nguồn/tổ hợp nào thiếu, từ đó chuẩn bị chốt scope đề tài.")
    lines.append("")
    lines.append("## 1. Input")
    lines.append("")
    lines.append("| File | Vai trò |")
    lines.append("|---|---|")
    lines.append("| `results/week1/api_smoke_test_results.csv` | Bằng chứng gọi thử Comtrade, WITS, World Bank |")
    lines.append("| `results/week1/mirror_check_results.csv` | Bằng chứng đối chiếu VN-reported và partner-mirror |")
    lines.append("")
    lines.append("Script `build_coverage_matrix.py` không gọi API mới; chỉ gom và chuẩn hóa hai file trên.")
    lines.append("")

    lines.append("## 2. Tóm tắt coverage")
    lines.append("")
    lines.append(f"- Tổng số dòng coverage: `{summary['total_rows']}`")
    lines.append(f"- Dòng trade/mirror: `{summary['mirror_rows']}`")
    lines.append(f"- Dòng tariff/WITS: `{summary['tariff_rows']}`")
    lines.append(f"- Dòng macro/World Bank: `{summary['macro_rows']}`")
    lines.append("")
    lines.append("### 2.1. Theo coverage status")
    lines.append("")
    lines.append("| Status | Số dòng |")
    lines.append("|---|---:|")
    for key, value in sorted(summary["coverage_status"].items()):
        lines.append(f"| {key or 'BLANK'} | {value} |")
    lines.append("")
    lines.append("### 2.2. Theo khuyến nghị scope")
    lines.append("")
    lines.append("| Recommendation | Số dòng |")
    lines.append("|---|---:|")
    for key, value in sorted(summary["recommendations"].items()):
        lines.append(f"| {key or 'BLANK'} | {value} |")
    lines.append("")

    lines.append("## 3. Ma trận coverage rút gọn")
    lines.append("")
    lines.append("| Row | Area | Direction | Partner | HS6/Indicator | Period | VN | Mirror | WITS MFN | WITS PREF | WB | Status | Recommendation |")
    lines.append("|---|---|---|---|---|---:|:---:|:---:|:---:|:---:|:---:|---|---|")

    for r in rows:
        hs_or_indicator = clean(r.get("hs6")) or clean(r.get("commodity_name"))
        lines.append(
            "| "
            + " | ".join(
                [
                    clean(r.get("row_id")),
                    clean(r.get("coverage_area")),
                    clean(r.get("direction")),
                    clean(r.get("partner_name")),
                    hs_or_indicator,
                    clean(r.get("year_or_month")),
                    clean(r.get("comtrade_vn_reported_available")),
                    clean(r.get("comtrade_mirror_available")),
                    clean(r.get("wits_mfn_available")),
                    clean(r.get("wits_pref_available")),
                    clean(r.get("worldbank_available")),
                    clean(r.get("coverage_status")),
                    clean(r.get("scope_recommendation")),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## 4. Diễn giải quan trọng")
    lines.append("")
    lines.append("### 4.1. Trade và mirror")
    lines.append("")
    lines.append("- Có nhiều tổ hợp hai phía đều có dữ liệu, ví dụ Germany/coffee 202301 và China/network equipment 202301.")
    lines.append("- Có tổ hợp chênh lệch thấp, vừa và cao; do đó dashboard nên có cờ `discrepancy_level`.")
    lines.append("- Có nhiều case năm 2024 bị `MISSING_VN_REPORTED` nhưng partner mirror có dữ liệu; đây là bằng chứng cho nhu cầu mirror fallback/reference.")
    lines.append("")
    lines.append("### 4.2. WITS/tariff")
    lines.append("")
    lines.append("- WITS có MFN và PREF cho chiều Việt Nam nhập khẩu hàng xuất xứ Nhật HS090111 năm 2018.")
    lines.append("- WITS thiếu một case chiều Nhật áp thuế lên hàng Việt Nam HS090111 năm 2018, nên tariff dashboard cần được xem là phạm vi phụ/conditional cho tới khi profiling thêm.")
    lines.append("- Không dùng dữ liệu WITS để kết luận tỷ lệ tận dụng FTA; chỉ dùng để phân tích MFN/PREF/tariff gap ở nơi có dữ liệu.")
    lines.append("")
    lines.append("### 4.3. World Bank")
    lines.append("")
    lines.append("- World Bank có GDP 2024, tỷ giá năm 2024 và tỷ giá tháng candidate 2024M01–2024M12.")
    lines.append("- Dữ liệu vĩ mô nên đưa vào `FACT_MACRO_INDICATOR`, không đưa vào `DIM_DATE`.")
    lines.append("")

    lines.append("## 5. Khuyến nghị scope sơ bộ cho Nhiệm vụ 6")
    lines.append("")
    lines.append("| Thành phần | Khuyến nghị |")
    lines.append("|---|---|")
    lines.append("| Thời gian lõi | 2015–2023 cho VN-reported monthly; 2024 dùng như năm kiểm tra gap/mirror hoặc partial nếu coverage đủ |")
    lines.append("| Partner lõi ban đầu | Japan, United States, Germany, China, Rep. of Korea; sau profiling có thể mở rộng top 10 |")
    lines.append("| HS6 đã có bằng chứng | 090111, 851762, 854231 |")
    lines.append("| Dashboard chính | Trade trend, partner/commodity analysis, mirror reconciliation |")
    lines.append("| Dashboard phụ/conditional | Tariff gap MFN/PREF nếu WITS coverage đủ |")
    lines.append("| Điểm mới | Mirror-reconciled trade data warehouse với perspective và discrepancy flag |")
    lines.append("")

    lines.append("## 6. Kết luận")
    lines.append("")
    lines.append("> Coverage Matrix cho thấy dữ liệu trade/mirror và macro đủ cơ sở để tiếp tục đề tài. WITS có dữ liệu nhưng thưa theo chiều partner/HS/year, nên phần tariff nên được giữ có điều kiện. Phạm vi nên ưu tiên dashboard trade + mirror reconciliation, sau đó bổ sung tariff gap ở các tổ hợp đã xác nhận có dữ liệu.")
    lines.append("")
    lines.append("## 7. Output")
    lines.append("")
    lines.append("| File | Nội dung |")
    lines.append("|---|---|")
    lines.append("| `results/week1/Coverage_Matrix.csv` | Ma trận coverage chính dạng bảng |")
    lines.append("| `results/week1/Coverage_Matrix.json` | Ma trận coverage dạng JSON |")
    lines.append("| `results/week1/Coverage_Matrix.md` | Bản đọc nhanh và diễn giải |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("=== NHIỆM VỤ 5: LẬP COVERAGE MATRIX ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Input 1: {API_SMOKE_CSV.relative_to(PROJECT_ROOT)}")
    print(f"Input 2: {MIRROR_CHECK_CSV.relative_to(PROJECT_ROOT)}")
    print("")

    smoke_rows = read_csv(API_SMOKE_CSV)
    mirror_rows = read_csv(MIRROR_CHECK_CSV)

    if not smoke_rows:
        print("[CẢNH BÁO] Chưa đọc được api_smoke_test_results.csv. Hãy chạy Nhiệm vụ 3 trước.")
    if not mirror_rows:
        print("[CẢNH BÁO] Chưa đọc được mirror_check_results.csv. Hãy chạy Nhiệm vụ 4 trước.")

    rows: list[dict] = []
    rows.extend(build_rows_from_mirror(mirror_rows))
    rows.extend(build_rows_from_api_smoke(smoke_rows, start_idx=len(rows)))

    write_csv_output(rows)
    write_json_output(rows)
    write_markdown_output(rows)

    summary = build_summary(rows)

    print("=== ĐÃ GHI KẾT QUẢ ===")
    print(f"- {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"- {OUT_JSON.relative_to(PROJECT_ROOT)}")
    print(f"- {OUT_MD.relative_to(PROJECT_ROOT)}")
    print("")
    print("=== TÓM TẮT NHANH ===")
    print(f"- Tổng dòng coverage: {summary['total_rows']}")
    print(f"- Trade mirror rows: {summary['mirror_rows']}")
    print(f"- Tariff/WITS rows: {summary['tariff_rows']}")
    print(f"- Macro/WB rows: {summary['macro_rows']}")
    print("- Coverage status:")
    for key, value in sorted(summary["coverage_status"].items()):
        print(f"  + {key or 'BLANK'}: {value}")
    print("")
    print("Xong Nhiệm vụ 5 bước lập coverage matrix. Hãy mở results/week1/Coverage_Matrix.md để đọc kết quả.")


if __name__ == "__main__":
    main()
