"""
TUAN 2 — NHIEM VU 1: KIEM TRA COMTRADE API KEY (KEY CHECK, BAN 2)
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Mục đích:
- Kiểm key Free APIs trước khi extract hàng loạt. Ban 2 phat hien tu lan chay dau tien:
  API MOI (comtradeapi.un.org) KHONG nhan range dau hai cham `period=201501:201512`
  (400 "The field period is invalid"); cu phap dung là DANH SÁCH CÁCH NHAU BANG DAU PHAY
  `period=201501,201502,...` (theo docs chính thức). Script nay kiem dung dieu do.
- 6 kiem tra:
  1) Key doc duoc tu .env / bien moi truong (in mask, khong in key du).
  2) data/v1/get annual 2023 TOTAL → 200 + co duong dan.
  3a) data/v1/get monthly 1 ky don (201501) → 200.
  3b) data/v1/get monthly 12 ky cach bang dau phay → 200 + nhieu hon 1 ky → PASSED thi
      NV2 duoc phep batch ca nam trong 1 call.
  3c) (tham khao) colon-range 201501:201512 → ky vong bi tu choi; chi ghi lai hanh vi.
  4) Cross-check gia tri annual 2023 cua mode-key voi bang chung preview tuan 1.
- Ket qua luu results/week2/key_check_results.{json,md}. KHONG ghi de file nao week1.
  (Lan chay dau tien — FAIL 3b vi colon-range — van con trong lich su git 041d8ac, giu
  nhu bang chung phat hien.)

Cách chạy Git Bash trên Windows:
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/utils/verify_comtrade_key.py

Exit code: 0 = PASS (3b la dieu kien can), 1 = FAIL.
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

MONTHS_2015 = [f"2015{m:02d}" for m in range(1, 13)]


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
        for skipped in ("2.", "3a.", "3b.", "3c.", "4."):
            checks.append({"name": skipped.strip() + " BO QUA - chua co key", "passed": False, "detail": "—", "skipped": True})
        return checks

    annual = call_data_api(
        "v2_key_check_annual_total_2023",
        "A",
        {"cmdCode": "TOTAL", "flowCode": "X", "partnerCode": WORLD_CODE, "period": "2023"},
        key,
    )
    checks.append({
        "name": "2. data/v1/get annual 2023 TOTAL",
        "passed": bool(annual["ok"]) and (annual["count"] or 0) >= 1,
        "detail": f"HTTP {annual['status_code']}, count={annual['count']}, value={annual['first_value_usd']}, note={annual['note'] or 'OK'}",
    })
    time.sleep(2.5)

    single = call_data_api(
        "v2_key_check_monthly_single_201501",
        "M",
        {"cmdCode": "090111", "flowCode": "X", "partnerCode": "392", "period": "201501"},
        key,
    )
    checks.append({
        "name": "3a. monthly mot ky don (201501)",
        "passed": bool(single["ok"]),
        "detail": f"HTTP {single['status_code']}, count={single['count']}, note={single['note'] or 'OK'}",
    })
    time.sleep(2.5)

    comma_periods = ",".join(MONTHS_2015)
    multi = call_data_api(
        "v2_key_check_monthly_comma_201501_201512",
        "M",
        {"cmdCode": "090111", "flowCode": "X", "partnerCode": "392", "period": comma_periods},
        key,
    )
    got_periods = multi["periods"] or []
    checks.append({
        "name": "3b. monthly 12 ky cach bang DAU PHAY (dinh dang API moi)",
        "passed": bool(multi["ok"]) and len(got_periods) >= 2,
        "detail": f"HTTP {multi['status_code']}, count={multi['count']}, so ky={len(got_periods)} {got_periods[:3]}...{got_periods[-2:] if len(got_periods) > 3 else ''}, note={multi['note'] or 'OK'}",
    })
    time.sleep(2.5)

    colon = call_data_api(
        "v2_key_check_monthly_colon_range",
        "M",
        {"cmdCode": "090111", "flowCode": "X", "partnerCode": "392", "period": "201501:201512"},
        key,
    )
    checks.append({
        "name": "3c. (tham khao) range dau hai cham 201501:201512",
        "passed": True,
        "informational": True,
        "detail": f"HTTP {colon['status_code']}, count={colon['count']}, note={clean_text(colon['note'], 160) or 'OK'} → API MOI dung dau phay, khong dung dau hai cham",
    })

    preview_value = load_week1_preview_value()
    key_value = annual["first_value_usd"]
    if preview_value is None or key_value is None:
        checks.append({
            "name": "4. Cross-check gia tri annual 2023 voi preview tuan 1",
            "passed": False,
            "detail": f"preview={preview_value}, key={key_value} - khong du du lieu de doi chieu",
        })
    else:
        diff = abs(float(key_value) - preview_value)
        checks.append({
            "name": "4. Cross-check gia tri annual 2023 voi preview tuan 1",
            "passed": diff <= 0.01,
            "detail": f"preview={preview_value}, key={key_value}, diff={diff:.3f} USD",
        })

    return checks


# =========================
# 3. Xuat ket qua
# =========================


def write_outputs(key: str | None, checks: list[dict], all_passed: bool) -> None:
    payload = {
        "ran_at": now_iso(),
        "script_version": 2,
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
        "# KEY CHECK RESULTS — TUAN 2 (NHIEM VU 1, BAN 2)",
        "",
        f"- Chay luc: {payload['ran_at']}",
        f"- Key tai duoc: {'CO' if key else 'KHONG'} ({mask_key(key) if key else '—'})",
        f"- Ket luan tong: **{'PASS' if all_passed else 'FAIL'}**",
        "",
        "| # | Kiem tra | Dat | Chi tiet |",
        "|---:|---|:---:|---|",
    ]
    for idx, c in enumerate(checks, start=1):
        mark = "ℹ️" if c.get("informational") else ("✅" if c["passed"] else "❌")
        lines.append(f"| {idx} | {c['name']} | {mark} | {clean_text(c['detail'], 220)} |")
    lines += [
        "",
        "## Y nghia",
        "",
        "- Kiem tra 2: endpoint day du `data/v1/get` tra du lieu bang key (khong con chan preview 500 records/1 ky).",
        "- Kiem tra 3b: MOT call monthly lay duoc nhieu ky khi dung danh sach `period=YYYYMM,YYYYMM,...` (cu ph chinh thuc cua API moi — docs vi du `period=202301,202302,...`). 3b PASS → W2-NV2 batch theo nam (12 ky/call) duoc phep thuc hien.",
        "- Kiem tra 3c (tham khao): `period=201501:201512` (dau hai cham) la cu phap API cu, bi API moi tu choi 400. Ban 1 cua script dung cu phap nay va FAIL — phat hien da duoc giu trong lich su git (commit 041d8ac).",
        "- Kiem tra 4: mode key va mode preview cung tra mot so lieu → bang chung tuan 1 con nguyen gia tri doi chieu.",
        "- Raw response nam trong `data/raw/week2_key_check/` (khong commit, .gitignore da chan).",
    ]
    (RESULT_DIR / "key_check_results.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("=== TUAN 2 - NV1: KIEM TRA COMTRADE API KEY (BAN 2 - DA SUA CU PHAP PERIOD) ===")
    print(f"Project root: {PROJECT_ROOT}")
    print("")

    key = load_subscription_key()
    checks = run_checks(key)
    all_passed = all(c["passed"] for c in checks)

    for c in checks:
        mark = "INFO" if c.get("informational") else ("PASS" if c["passed"] else "FAIL")
        print(f"[{mark}] {c['name']}")
        print(f"       {c['detail']}")

    write_outputs(key, checks, all_passed)
    print("")
    print("=== DA GHI KET QUA ===")
    print(f"- {RESULT_DIR.relative_to(PROJECT_ROOT)}/key_check_results.md")
    print(f"- {RESULT_DIR.relative_to(PROJECT_ROOT)}/key_check_results.json")
    print("")
    if all_passed:
        print("KET LUAN: PASS — chot thiet ke W2-NV2 batch-theo-nam (comma period).")
        return 0
    print("KET LUAN: FAIL — xem bang o tren; neu 3b FAIL thi NV2 phai goi tung ky (thieu may muon van xong, quota 500 calls/ngay du cho ~168-180 calls/lan chay).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
