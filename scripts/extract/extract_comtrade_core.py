"""
TUAN 2 — NHIEM VU 2: EXTRACT COMTRADE LOI VN_REPORTED
Đề tài: Xây dựng Kho dữ liệu hỗ trợ phân tích và ra quyết định xuất nhập khẩu hàng hóa Việt Nam

Pham vi (docs/06 §3, da chot):
- 14 ma HS6 x 6 partner (China 156, USA 842, Korea 410, Japan 392, Germany 276, World 0)
- 2 flow X/M theo goc nhin Viet Nam
- Nam 2015–2023 (loi) + 2024 (partial, ky vong count=0 phan lon — gap structural)
- reporter = 704, mode VN_REPORTED (mirror la NV3, script khac)
- Lua chon query theo ket qua W2-NV1 check 3b: period = danh sach 12 ky cach dau phay →
  1 call lay ca nam. Neu API tu choi (400), script tu dong tach doi danh sach cmdCode.

Che do cache/resume:
- Moi batch (flow, nam) luu raw vao data/raw/week2_extract/vn_{flow}_{nam}.json
  + manifest.json ghi sha1 cua logical params.
- Chay lai: batch nao da co trong manifest voi cung sha1 → BO QUA (goi lai duoc khi
  chay voi --force). Doi pham vi (nam/codes) → sha1 khac → tu dong goi lai batch do.
- --rebuild-only: khong goi API, chi doc raw da cache de tai tao bang/staging/report.

Output:
- data/staging/stg_comtrade_vn_reported.csv  (FILE DAY DU — khong commit, gitignore chan;
  day la input truc tiep cho staging/SSIS tuan 3)
- results/week2/extract_vn_reported.md / .json  (tom tat + validation, commit duoc)
- Validation: doi chieu 5 o so lieu (X/M, partner, HS6, 2023/2024M01) voi
  results/week1/mirror_check_results.json — cung 1 query, 2 thoi diem khac nhau phai trung.

Cach chay (Git Bash, Windows):
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW
    source .venv/Scripts/activate
    python scripts/extract/extract_comtrade_core.py --years 2015      # rehearsal 2 call
    python scripts/extract/extract_comtrade_core.py                    # toan bo 20 call
    python scripts/extract/extract_comtrade_core.py --selftest         # test logic offline

Yeu cau COMTRADE_SUBSCRIPTION_KEY trong .env (khong chay bang preview — preview khong ho
trtro multi-period va bi chan 500 records/call).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week2_extract"
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
RESULT_DIR = PROJECT_ROOT / "results" / "week2"
MANIFEST_PATH = RAW_DIR / "manifest.json"
WEEK1_MIRROR_JSON = PROJECT_ROOT / "results" / "week1" / "mirror_check_results.json"

DATA_API_URL = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
VIETNAM_CODE = "704"
SLEEP_SECONDS_BETWEEN_CALLS = 1.6

PARTNERS = [
    ("0", "World"),
    ("156", "China"),
    ("276", "Germany"),
    ("392", "Japan"),
    ("410", "Rep. of Korea"),
    ("842", "United States"),
]

HS6_CODES = [
    "090111", "100630", "080132", "090411", "610910", "640399", "854442", "851713",
    "851762", "854231", "847330", "721049", "540761", "390120",
]

DEFAULT_YEARS = list(range(2015, 2025))  # 2015–2023 loi + 2024 partial
FLOWS = ["X", "M"]

SESSION = requests.Session()


# =========================
# 1. Tien ich
# =========================


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value: object, limit: int = 300) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mask_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "****"
    return key[:4] + "****" + f"(dai {len(key)})"


def parse_env_file(path: Path) -> dict:
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


def periods_for_year(year: int) -> list[str]:
    return [f"{year}{m:02d}" for m in range(1, 13)]


def logical_params_sha(flow: str, year: int, codes: list[str]) -> str:
    payload = {
        "flow": flow,
        "year": year,
        "codes": sorted(codes),
        "partners": sorted(p[0] for p in PARTNERS),
        "reporter": VIETNAM_CODE,
        "locks": {"motCode": "0", "customsCode": "C00", "partner2Code": "0"},
        "scope": "vn_reported_w2nv2_v1",
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


# =========================
# 2. Goi API (mode key)
# =========================


def request_with_retry(url: str, params: dict, timeout: int = 60, tries: int = 3) -> requests.Response:
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


def call_once(key: str, flow: str, periods: list[str], codes: list[str]) -> tuple[bool, list[dict], str, int]:
    """Tra ve (ok, rows, note, status_code)."""
    params = {
        "subscription-key": key,
        "cmdCode": ",".join(codes),
        "flowCode": flow,
        "reporterCode": VIETNAM_CODE,
        "partnerCode": ",".join(p[0] for p in PARTNERS),
        "period": ",".join(periods),
        "motCode": "0",
        "customsCode": "C00",
        "partner2Code": "0",
        "includeDesc": "true",
        "maxrecords": "100000",
    }
    try:
        response = request_with_retry(DATA_API_URL, params=params, timeout=60, tries=3)
        if response.status_code != 200:
            note = clean_text(response.text, 400)
            is_param_error = response.status_code == 400 and "invalid" in note.lower()
            return (False, [], f"HTTP {response.status_code}: {note}", response.status_code)
        data = response.json()
        rows = data.get("data") or []
        return (True, rows, clean_text(data.get("error") or "OK", 200), response.status_code)
    except Exception as exc:  # noqa: BLE001
        return (False, [], f"{type(exc).__name__}: {clean_text(exc, 200)}", 0)


def fetch_batch(key: str, flow: str, year: int, codes: list[str]) -> tuple[list[dict], dict]:
    """Goi 1 batch theo nam; tu dong tach doi cmdCode neu bi 400 invalid parameter."""
    periods = periods_for_year(year)
    ok, rows, note, status = call_once(key, flow, periods, codes)

    chunk_note = ""
    if not ok and status == 400 and "invalid" in note.lower() and len(codes) > 3:
        half = len(codes) // 2
        print(f"    [400] API tu choi danh sach {len(codes)} ma → tach 2 nua va thu lai...")
        rows_all = []
        ok_all = True
        notes = []
        for chunk_idx, chunk in enumerate([codes[:half], codes[half:]]):
            time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)
            ok2, rows2, note2, _status2 = call_once(key, flow, periods, chunk)
            rows_all.extend(rows2)
            ok_all = ok_all and ok2
            notes.append(f"chunk{chunk_idx}:{note2}")
        chunk_note = "split2 " + "; ".join(notes)
        if ok_all:
            return rows_all, {"mode": "split2", "note": chunk_note}
        note = chunk_note + " | " + note
    if not ok:
        raise RuntimeError(f"Batch {flow}{year} that bai: {note}")
    return rows, {"mode": "single" if not chunk_note else "split2", "note": chunk_note or note}


# =========================
# 3. Chuan hoa + merge
# =========================


def normalize_rows(batch_rows: list[dict], flow: str, year: int, batch_id: str) -> list[dict]:
    out = []
    for d in batch_rows:
        period = str(d.get("period") or "")
        partner_code = str(d.get("partnerCode") or "")
        hs6 = str(d.get("cmdCode") or "")
        if not re.fullmatch(r"\d{6}", period) or not re.fullmatch(r"\d{6}", hs6):
            continue
        out.append(
            {
                "batch_id": batch_id,
                "period": period,
                "year": int(period[:4]),
                "month": int(period[4:6]),
                "flow_code": flow,
                "reporter_code": str(d.get("reporterCode") or VIETNAM_CODE),
                "partner_code": partner_code,
                "partner_name": clean_text(d.get("partnerDesc"), 120),
                "is_aggregate_partner": partner_code == "0",
                "hs6": hs6,
                "commodity_desc": clean_text(d.get("cmdDesc"), 200),
                "primary_value_usd": to_float(d.get("primaryValue")),
                "fob_value_usd": to_float(d.get("fobvalue")),
                "cif_value_usd": to_float(d.get("cifvalue")),
                "net_wgt_kg": to_float(d.get("netWgt")),
                "qty": to_float(d.get("qty")),
                "source_system": "UN Comtrade data/v1/get (subscription key)",
                "reporting_perspective": "VN_REPORTED",
                "extracted_at": now_iso(),
            }
        )
    return out


def build_cell_index(rows: list[dict]) -> dict:
    index = {}
    for r in rows:
        key = (r["flow_code"], r["partner_code"], r["hs6"], r["period"])
        index[key] = r["primary_value_usd"]
    return index


def load_week1_validation_cells() -> list[dict]:
    """Lay cac case mirror tuan 1 ma phia VN co du lieu → thanh bang doi chieu."""
    if not WEEK1_MIRROR_JSON.exists():
        return []
    try:
        cases = json.loads(WEEK1_MIRROR_JSON.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return []
    wanted = []
    for c in cases:
        if c.get("vn_value_usd") is None:
            continue
        flow = "X" if c.get("direction") == "EXPORT" else "M"
        wanted.append(
            {
                "case_id": c.get("case_id"),
                "cell": (flow, str(c.get("partner_code")), str(c.get("hs6")), str(c.get("period"))),
                "week1_value": float(c["vn_value_usd"]),
            }
        )
    return wanted


def run_validations(index: dict, wanted: list[dict]) -> list[dict]:
    results = []
    for w in wanted:
        got = index.get(w["cell"])
        if got is None:
            status = "MISSING_IN_EXTRACT"
        elif abs(got - w["week1_value"]) <= 0.01:
            status = "MATCH"
        else:
            status = "MISMATCH"
        results.append({**w, "extract_value": got, "status": status})
    return results


# =========================
# 4. Ghi output
# =========================

STAGING_FIELDS = [
    "batch_id", "period", "year", "month", "flow_code", "reporter_code",
    "partner_code", "partner_name", "is_aggregate_partner", "hs6", "commodity_desc",
    "primary_value_usd", "fob_value_usd", "cif_value_usd", "net_wgt_kg", "qty",
    "source_system", "reporting_perspective", "extracted_at",
]


def write_staging_csv(rows: list[dict]) -> int:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    path = STAGING_DIR / "stg_comtrade_vn_reported.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STAGING_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return len(rows)


def coverage_stats(rows: list[dict]) -> dict:
    by_year_flow: dict = {}
    by_code: dict = {}
    for r in rows:
        key = f"{r['flow_code']}|{r['year']}"
        by_year_flow[key] = by_year_flow.get(key, 0) + 1
        by_code.setdefault(r["hs6"], set()).add(r["period"])
    return {
        "rows_by_year_flow": dict(sorted(by_year_flow.items())),
        "months_by_code": {k: len(v) for k, v in sorted(by_code.items())},
        "total_rows": len(rows),
    }


def write_report(stats: dict, validations: list[dict], fetch_log: list[dict], years: list[int]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    matched = sum(1 for v in validations if v["status"] == "MATCH")
    lines = [
        "# EXTRACT VN_REPORTED — TUAN 2 NV2",
        "",
        f"- Chat luc: {now_iso()}",
        f"- Nam: {years[0]}–{years[-1]} (2015–2023 = loi theo docs/06; 2024 = partial)",
        f"- Pham vi: 14 HS6 x 6 partner x 2 flow, grain thang, mode key `data/v1/get`",
        f"- Tong so dong staging: **{stats['total_rows']}**",
        "",
        "## 1. So dong theo flow x nam",
        "",
        "| Flow | Nam | So dong |",
        "|---|---:|---:|",
    ]
    for key, n in stats["rows_by_year_flow"].items():
        flow, year = key.split("|")
        lines.append(f"| {flow} | {year} | {n} |")
    lines += [
        "",
        "## 2. Do phu theo ma HS6 (so thang co du lieu, toi da = 12 x so nam)",
        "",
        "| HS6 | So thang co du lieu |",
        "|---|---:|",
    ]
    for code, months in stats["months_by_code"].items():
        lines.append(f"| {code} | {months} |")
    lines += [
        "",
        "## 3. Validation voi bang chung tuan 1 (mirror_check_results.json)",
        "",
        "Cung query (bao gom luat khong motCode/customs/partner2), 2 thoi diem khac nhau → gia tri phai khop.",
        "",
        "| Case tuan 1 | O kiem tra | Gia tri tuan 1 | Gia tri extract | Ket qua |",
        "|---|---|---:|---:|---|",
    ]
    for v in validations:
        flow, partner, hs6, period = v["cell"]
        extract_val = "—" if v["extract_value"] is None else f"{v['extract_value']:,.3f}"
        mark = {"MATCH": "✅", "MISMATCH": "❌", "MISSING_IN_EXTRACT": "⚠️"}.get(v["status"], "")
        lines.append(
            f"| {v['case_id']} | {flow}/{partner}/{hs6}/{period} | {v['week1_value']:,.3f} | {extract_val} | {mark} {v['status']} |"
        )
    lines += [
        "",
        f"- Khop: {matched}/{len(validations)}",
        "",
        "## 4. Nhat ky goi API",
        "",
        "| Batch | Trang thai | So dong | Mode | Ghi chu |",
        "|---|---|---:|---|---|",
    ]
    for f in fetch_log:
        lines.append(
            f"| {f['batch_id']} | {f['status']} | {f.get('rows', '—')} | {f.get('mode', '—')} | {clean_text(f.get('note', ''), 80)} |"
        )
    lines += [
        "",
        "## 5. Ghi chu",
        "",
        "- File day du nam o `data/staging/stg_comtrade_vn_reported.csv` (khong commit — `.gitignore` chan, dung cho staging SSIS tuan 3).",
        "- Raw tung batch: `data/raw/week2_extract/` (khong commit). Resume tu dong qua `manifest.json`.",
        "- 2024 phia VN du kien trong/le te (gap structural da bang chung o tuan 1) — giu lai nhu bang chung cho dashboard D3.",
        "- Khong bao gio loc bo `is_aggregate_partner` khoi tap du lieu; chi loai khi xep hang partner (doc o transform).",
    ]
    (RESULT_DIR / "extract_vn_reported.md").write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "ran_at": now_iso(),
        "years": years,
        "total_rows": stats["total_rows"],
        "rows_by_year_flow": stats["rows_by_year_flow"],
        "months_by_code": stats["months_by_code"],
        "validations": validations,
        "fetch_log": fetch_log,
    }
    (RESULT_DIR / "extract_vn_reported.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# =========================
# 5. Modes: fetch / rebuild / selftest
# =========================


def do_fetch(key: str, years: list[int]) -> tuple[list[dict], list[dict]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    fetch_log = []
    all_rows = []

    total_batches = len(FLOWS) * len(years)
    done = 0
    for flow in FLOWS:
        for year in years:
            done += 1
            batch_id = f"vn_{flow}_{year}"
            sha = logical_params_sha(flow, year, HS6_CODES)
            raw_path = RAW_DIR / f"{batch_id}.json"

            if batch_id in manifest and manifest[batch_id].get("sha") == sha and raw_path.exists():
                entry = json.loads(raw_path.read_text(encoding="utf-8"))
                rows = normalize_rows(entry.get("rows_raw", []), flow, year, batch_id)
                all_rows.extend(rows)
                fetch_log.append({"batch_id": batch_id, "status": "SKIP (cache)", "rows": len(rows), "mode": "cache", "note": manifest[batch_id].get("note", "")})
                print(f"[{done}/{total_batches}] {batch_id} — co trong cache, bo qua ({len(rows)} dong)")
                continue

            print(f"[{done}/{total_batches}] {batch_id} — goi API (12 ky, 14 ma, 6 partner)...")
            t0 = time.time()
            try:
                rows_raw, meta = fetch_batch(key, flow, year, HS6_CODES)
            except RuntimeError as exc:
                fetch_log.append({"batch_id": batch_id, "status": "FAIL", "rows": None, "mode": meta if 'meta' in dir() else "—", "note": str(exc)})
                print(f"    [FAIL] {exc}")
                print("    Cac batch da thanh cong van duoc giu. Chay lai lenh nay de resume, hoac xu ly theo docs/08 muc 6.")
                save_manifest(manifest)
                break

            raw_path.write_text(
                json.dumps({"batch_id": batch_id, "saved_at": now_iso(), "sha": sha, "flow": flow, "year": year, "rows_raw": rows_raw}, ensure_ascii=False),
                encoding="utf-8",
            )
            rows = normalize_rows(rows_raw, flow, year, batch_id)
            all_rows.extend(rows)
            manifest[batch_id] = {"sha": sha, "rows": len(rows), "saved_at": now_iso(), "note": meta.get("note", "")[:120]}
            save_manifest(manifest)
            fetch_log.append({"batch_id": batch_id, "status": "OK", "rows": len(rows), "mode": meta.get("mode", "single"), "note": meta.get("note", "")})
            print(f"    -> {len(rows)} dong, {time.time() - t0:.1f}s")
            time.sleep(SLEEP_SECONDS_BETWEEN_CALLS)

    return all_rows, fetch_log


def do_rebuild() -> tuple[list[dict], list[dict]]:
    all_rows = []
    fetch_log = []
    for raw_path in sorted(RAW_DIR.glob("vn_*.json")):
        entry = json.loads(raw_path.read_text(encoding="utf-8"))
        rows = normalize_rows(entry.get("rows_raw", []), entry.get("flow", "?"), entry.get("year", 0), entry.get("batch_id", raw_path.stem))
        all_rows.extend(rows)
        fetch_log.append({"batch_id": entry.get("batch_id", raw_path.stem), "status": "REBUILT", "rows": len(rows), "mode": "cache", "note": ""})
    return all_rows, fetch_log


def selftest() -> int:
    """Test offline cac ham logic: normalize, index, validation, sha on dinh."""
    print("=== SELFTEST W2-NV2 ===")
    failures = []

    fake_raw = [
        {
            "period": "202301", "flowCode": "X", "reporterCode": 704,
            "partnerCode": 392, "partnerDesc": "Japan", "cmdCode": "90111",  # co y thieu so 0 dau de thu regex
            "cmdDesc": "Coffee", "primaryValue": 10.5, "fobvalue": 10.5, "cifvalue": None,
            "netWgt": 1.0, "qty": 2.0,
        },
        {
            "period": "202301", "flowCode": "X", "reporterCode": 704,
            "partnerCode": 392, "partnerDesc": "Japan", "cmdCode": "090111",
            "cmdDesc": "Coffee", "primaryValue": 10.5, "fobvalue": 10.5, "cifvalue": None,
            "netWgt": 1.0, "qty": 2.0,
        },
        {
            "period": "202301", "flowCode": "M", "reporterCode": 704,
            "partnerCode": "156", "partnerDesc": "China", "cmdCode": "851762",
            "cmdDesc": "Net equip", "primaryValue": 29869079.442, "fobvalue": None, "cifvalue": 29869079.442,
            "netWgt": 3.5, "qty": 0.0,
        },
    ]
    rows = normalize_rows(fake_raw, "X", 2023, "vn_X_2023")
    if len(rows) != 2:
        failures.append(f"normalize_rows phai loai 1 dong cmdCode khong hop le → mong 2, duoc {len(rows)}")
    index = build_cell_index(rows + normalize_rows(fake_raw[2:], "M", 2023, "vn_M_2023"))
    if index.get(("X", "392", "090111", "202301")) != 10.5:
        failures.append("cell index khong tim thay (X,392,090111,202301)=10.5")

    wanted = [
        {"case_id": "FAKE_OK", "cell": ("X", "392", "090111", "202301"), "week1_value": 10.5},
        {"case_id": "FAKE_BAD", "cell": ("X", "392", "090111", "202301"), "week1_value": 999.0},
        {"case_id": "FAKE_MISSING", "cell": ("M", "999", "000000", "202001"), "week1_value": 1.0},
    ]
    vres = run_validations(index, wanted)
    statuses = [v["status"] for v in vres]
    if statuses != ["MATCH", "MISMATCH", "MISSING_IN_EXTRACT"]:
        failures.append(f"validation cho ra {statuses}, khong dung ky vong")

    if not re.fullmatch(r"[0-9a-f]{16}", logical_params_sha("X", 2023, HS6_CODES)):
        failures.append("sha khong dang ky 16 hex")
    if logical_params_sha("X", 2023, HS6_CODES) != logical_params_sha("X", 2023, list(reversed(HS6_CODES))):
        failures.append("sha khong on dinh khi thu tu codes doi (can sort)")

    stats = coverage_stats(rows)
    if stats["total_rows"] != 2 or stats["months_by_code"].get("090111") != 1:
        failures.append(f"coverage_stats sai: {stats}")

    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        print("SELFTEST: FAIL")
        return 1
    print("Tat ca 5 nhom kiem tra offline deu dat.")
    print("SELFTEST: PASS")
    return 0


def parse_years(spec: str) -> list[int]:
    years: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            years.extend(range(int(a), int(b) + 1))
        elif part:
            years.append(int(part))
    return sorted(set(y for y in years if 2000 <= y <= 2100))


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Comtrade loi VN_REPORTED (W2-NV2)")
    parser.add_argument("--years", default="", help="Vi du '2015' hoac '2015-2017'. Mac dinh: 2015-2024")
    parser.add_argument("--force", action="store_true", help=" Goi lai du batch da co trong cache")
    parser.add_argument("--rebuild-only", action="store_true", help="Khong goi API; tai tao bang/staging/report tu raw da cache")
    parser.add_argument("--selftest", action="store_true", help="Chi chay test logic offline, khong touch du lieu that")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    years = parse_years(args.years) if args.years else DEFAULT_YEARS
    if not years:
        print("Nam khong hop le."); return 1

    if args.rebuild_only:
        print("=== REBUILD TU RAW (khong goi API) ===")
        all_rows, fetch_log = do_rebuild()
    else:
        key = load_subscription_key()
        if not key:
            print("[FAIL] Khong tim thay COMTRADE_SUBSCRIPTION_KEY trong .env.")
            print("       Extract hang loat bat buoc dung key (preview khong ho tro batch).")
            print("       Xem W2-NV1: docs/07, chay scripts/utils/verify_comtrade_key.py truoc.")
            return 2
        print("=== TUAN 2 - NV2: EXTRACT COMTRADE LOI VN_REPORTED ===")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Key: {mask_key(key)} | Nam: {years[0]}-{years[-1]} | Flow: X, M | Batches: {len(years) * 2}")
        print("")
        if args.force and MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink()
        all_rows, fetch_log = do_fetch(key, years)

    if not all_rows and not args.rebuild_only:
        print("\n[FAIL] Khong co dong nao duoc thu thap — kiem tra bang nhat ky o tren.")
        return 1

    n_staged = write_staging_csv(all_rows)
    validations = run_validations(build_cell_index(all_rows), load_week1_validation_cells())
    stats = coverage_stats(all_rows)
    write_report(stats, validations, fetch_log, years)

    matched = sum(1 for v in validations if v["status"] == "MATCH")
    failed = [v for v in validations if v["status"] != "MATCH"]
    print("")
    print("=== TONG KET ===")
    print(f"- Dong staging: {n_staged} (data/staging/stg_comtrade_vn_reported.csv)")
    print(f"- Validation vs tuan 1: {matched}/{len(validations)} khop")
    for v in failed:
        print(f"  [!] {v['case_id']}: {v['status']} (extract={v['extract_value']}, week1={v['week1_value']})")
    if any(f["status"] == "FAIL" for f in fetch_log):
        print("- CO BATCH FAIL — xem nhat ky; chay lai lenh nay de resume.")
        return 1
    print("Xong W2-NV2. Mo results/week2/extract_vn_reported.md de bao cao.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
