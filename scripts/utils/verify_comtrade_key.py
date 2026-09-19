"""
TUAN 2 — NHIEM VU 1: KIEM TRA COMTRADE API KEY (KEY CHECK)
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Mục đích:
- Chính thức hóa việc kiểm tra Comtrade subscription key (Free APIs) trước khi extract hàng loạt.
- 3 kiểm tra: (1) key đọc được từ .env; (2) goi data/v1/get nam 2023 TOTAL; (3) goi monthly
  voi RANGE ky (period=201501:201512) de chung minh batch multi-period hoat dong.
- Cross-check: so giá trị annual 2023 cua mode-key voi bang chung preview đã commit
  ở results/week1/api_smoke_test_results.json.
- Ket qua luu vao results/week2/key_check_results.{json,md}. KHÔNG ghi đè bat ky file nao
  trong results/week1.

Cách chạy Git Bash trên Windows:
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/utils/verify_comtrade_key.py

Exit code: 0 = PASS, 1 = FAIL (xem bang ket qua in ra de biet nguyên nhân).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "results" / "week2"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week2_key_check"
WEEK1_SMOKE_JSON = PROJECT_ROOT / "results" / "week1" / "api_smoke_test_results.json"

RESULT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
VIETNAM_CODE = "704"
WORLD_CODE = "0"
DATA_API_BASE = "https://comtradeapi.un.org/data/v1/get"


# =========================
# 1. Tien ich
# =========================


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:120]


def clean_text(value: object, limit: int = 300) -> str:
    text = "" if value is None else str(value)
    text = text.replace("|", "/").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def mask_key(key: str) -> str:
    """Chi lo 4 ky tu dau de nhan dang, khong bao giờ in key day du."""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + f"(dai {len(key)})"


def parse_env_file(path: Path) -> dict:
    """Doc .env thu cong (phuong an du phong khi python-dotenv chua cai)."""
    data = {}
    if not path.exists():
        return data
    try:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:  # noqa: BLE001
        pass
    return data


def load_subscription_key() -> str | None:
    key = os.getenv("COMTRADE_SUBSCRIPTION_KEY") or os.getenv("COMTRADE_KEY")
    if key:
        return key
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
        key = os.getenv("COMTRADE_SUBSCRIPTION_KEY") or os.getenv("COMTRADE_KEY")
        if key:
            return key
    except ImportError:
        pass
    env_data = parse_env_file(PROJECT_ROOT / ".env")
    key = env_data.get("COMTRADE_SUBSCRIPTION_KEY") or env_data.get("COMTRADE_KEY")
    return key or None


def request_with_retry(url: str, params: dict, timeout: int = 45, tries: int = 3) -> requests.Response:
    """Goi API co retry, xu ly rieng 429 nhu cac script tuan 1."""
    last_error = None
    response = None

    for attempt in range(1, tries + 1):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)
            if response.status_code == 429:
                match = re.search(r"Try again in (\d+)", response.text)
                wait_seconds = int(match.group(1)) + 1 if match else 5 * attempt
                print(f"    [429] Rate limit. Cho {wait_seconds}s... ({attempt}/{tries})")
                time.sleep(wait_seconds)
                continue
            return response
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait_seconds = min(3 * attempt, 10)
            print(f"    [ERROR] {type(exc).__name__}: {exc}. Cho {wait_seconds}s... ({attempt}/{tries})")
            time.sleep(wait_seconds)

    if response is not None:
        return response
    if last_error:
        raise last_error
    raise RuntimeError("Khong nhan duoc response tu API")


def call_data_api(label: str, freq: str, extra_params: dict, key: str) -> dict:
    """Goi data/v1/get (mode key) voi luat khoa motCode/customs/partner2 nhu tuan 1."""
    params = {
        "subscription-key": key,
        "reporterCode": VIETNAM_CODE,
        "motCode": "0",
        "customsCode": "C00",
        "partner2Code": "0",
        "includeDesc": "true",
        "maxrecords": "100",
    }
    params.update(extra_params)

    base_url = f"{DATA_API_BASE}/C/{freq}/HS"
    full_url = base_url + "?" + urlencode(params)

    result = {
        "label": label,
        "url_masked": re.sub(r"(subscription-key=)[^&]+", r"\1***", full_url),
        "tested_at": now_iso(),
        "ok": False,
        "status_code": None,
        "count": None,
        "first_value_usd": None,
        "periods": [],
        "note": "",
    }

    try:
        response = request_with_retry(base_url, params=params, timeout=45, tries=3)
        result["status_code"] = response.status_code
        raw_path = RAW_DIR / f"{safe_name(label)}.json"
        raw_path.write_bytes(response.content)

        if response.status_code != 200:
            result["note"] = clean_text(response.text)
            return result

        data = response.json()
        rows = data.get("data") or []
        result["ok"] = True
        result["count"] = data.get("count", len(rows))
        if rows:
            result["first_value_usd"] = rows[0].get("primaryValue")
            result["periods"] = sorted({str(r.get("period")) for r in rows})
        if not rows:
            result["note"] = "200 nhung khong co duong dan"
    except Exception as exc:  # noqa: BLE001
        result["note"] = clean_text(f"{type(exc).__name__}: {exc}")

    return result


def load_week1_preview_value() -> float | None:
    """Doc gia tri VN export TOTAL 2023 tu bang chung preview tuan 1 (neu co)."""
    if not WEEK1_SMOKE_JSON.exists():
        return None
    try:
        entries = json.loads(WEEK1_SMOKE_JSON.read_text(encoding="utf-8-sig"))
        for entry in entries:
            name = entry.get("test_name") or ""
            if "TOTAL to World 2023" in name and entry.get("sample"):
                value = entry["sample"].get("primaryValue")
                return float(value) if value is not None else None
    except Exception:  # noqa: BLE001
        return None
    return None


# =========================
# 2. Cac kiem tra
# =========================


def run_checks(key: str | None) -> list[dict]:
    checks: list[dict] = []

    check1 = {
        "name": "1. Key duoc doc tu moi truong/.env",
        "passed": key is not None,
        "detail": mask_key(key) if key else "KHONG THAY KEY - kiem tra .env o root project",
    }
    checks.append(check1)

    if not key:
        checks.append({"name": "2. Goi data/v1/get (annual 2023 TOTAL)", "passed": False, "detail": "BO QUA - chua co key"})
        checks.append({"name": "3. Goi monthly voi RANGE period 201501:201512", "passed": False, "detail": "BO QUA - chua co key"})
        checks.append({"name": "4. Cross-check gia tri voi preview tuan 1", "passed": False, "detail": "BO QUA - chua co key"})
        return checks

    annual = call_data_api(
        "key_check_annual_total_2023",
        "A",
        {"cmdCode": "TOTAL", "flowCode": "X", "partnerCode": WORLD_CODE, "period": "2023"},
        key,
    )
    check2 = {
        "name": "2. Goi data/v1/get (annual 2023 TOTAL)",
        "passed": bool(annual["ok"]) and (annual["count"] or 0) >= 1,
        "detail": f"HTTP {annual['status_code']}, count={annual['count']}, value={annual['first_value_usd']}, note={annual['note'] or 'OK'}",
    }
    checks.append(check2)
    time.sleep(2.5)

    monthly = call_data_api(
        "key_check_monthly_range_201501_201512",
        "M",
        {"cmdCode": "090111", "flowCode": "X", "partnerCode": "392", "period": "201501:201512"},
        key,
    )
    periods = monthly["periods"] or []
    check3 = {
        "name": "3. Goi monthly voi RANGE period 201501:201512",
        "passed": bool(monthly["ok"]) and len(periods) >= 2,
        "detail": f"HTTP {monthly['status_code']}, count={monthly['count']}, so ky tra ve={len(periods)} ({periods[:3]}...{periods[-2:] if len(periods) > 3 else ''}), note={monthly['note'] or 'OK'}",
    }
    checks.append(check3)

    preview_value = load_week1_preview_value()
    key_value = annual["first_value_usd"]
    if preview_value is None or key_value is None:
        check4 = {
            "name": "4. Cross-check gia tri voi preview tuan 1",
            "passed": preview_value is None and key_value is None,
            "detail": f"preview={preview_value}, key={key_value} - khong du du lieu de doi chieu (khong chan)",
        }
    else:
        diff = abs(float(key_value) - preview_value)
        check4 = {
            "name": "4. Cross-check gia tri voi preview tuan 1",
            "passed": diff <= 0.01,
            "detail": f"preview={preview_value}, key={key_value}, diff={diff:.3f} USD",
        }
    checks.append(check4)

    return checks


# =========================
# 3. Xuat ket qua
# =========================


def write_outputs(key: str | None, checks: list[dict], all_passed: bool) -> None:
    payload = {
        "ran_at": now_iso(),
        "mode": "verify_comtrade_key",
        "key_present": key is not None,
        "key_masked": mask_key(key) if key else None,
        "all_passed": all_passed,
        "checks": checks,
    }
    (RESULT_DIR / "key_check_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# KEY CHECK RESULTS — TUAN 2 (NHIEM VU 1)",
        "",
        f"- Chay luc: {payload['ran_at']}",
        f"- Key tai duoc: {'CO' if key else 'KHONG'} ({mask_key(key) if key else '—'})",
        f"- Ket luan tong: **{'PASS' if all_passed else 'FAIL'}**",
        "",
        "| # | Kiem tra | Dat | Chi tiet |",
        "|---:|---|:---:|---|",
    ]
    for idx, c in enumerate(checks, start=1):
        mark = "✅" if c["passed"] else "❌"
        lines.append(f"| {idx} | {c['name']} | {mark} | {clean_text(c['detail'], 220)} |")
    lines += [
        "",
        "## Y nghia",
        "",
        "- Kiem tra 2 dat: endpoint day du `data/v1/get` tra duoc du lieu (khong con bi chan preview 500 records).",
        "- Kiem tra 3 dat: 1 query lay duoc nhieu ky (range period) → nen cho thiet ke extract tuan 2 batch theo nam.",
        "- Kiem tra 4 dat: mode key va mode preview tra cung mot so lieu → bang chung tuan 1 van con gia tri doi chieu.",
        "- Raw response cu the nam trong `data/raw/week2_key_check/` (khong commit, .gitignore da chan).",
    ]
    (RESULT_DIR / "key_check_results.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("=== TUAN 2 - NV1: KIEM TRA COMTRADE API KEY ===")
    print(f"Project root: {PROJECT_ROOT}")
    print("")

    key = load_subscription_key()
    checks = run_checks(key)
    all_passed = all(c["passed"] for c in checks)

    for c in checks:
        mark = "PASS" if c["passed"] else "FAIL"
        print(f"[{mark}] {c['name']}")
        print(f"       {c['detail']}")

    write_outputs(key, checks, all_passed)
    print("")
    print("=== DA GHI KET QUA ===")
    print(f"- {RESULT_DIR.relative_to(PROJECT_ROOT)}/key_check_results.md")
    print(f"- {RESULT_DIR.relative_to(PROJECT_ROOT)}/key_check_results.json")
    print("")
    verdict = "PASS — san sang cho W2-NV2 (extract loi)" if all_passed else "FAIL — xu ly nguyen nhan o tren roi chay lai"
    print(f"KET LUAN: {verdict}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
