from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ingestion.common import load_config, now_iso, stage_seed_csv

DATA_API_URL = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
VIETNAM_CODE = "704"
DEFAULT_YEARS = list(range(2015, 2024))
SLEEP_SECONDS = 1.6

COMMODITIES = [
    {"code": "090111", "bridge_code": None},
    {"code": "100630", "bridge_code": None},
    {"code": "080132", "bridge_code": None},
    {"code": "090411", "bridge_code": None},
    {"code": "610910", "bridge_code": None},
    {"code": "640399", "bridge_code": None},
    {"code": "854442", "bridge_code": None},
    {"code": "851713", "bridge_code": "851712"},
    {"code": "851762", "bridge_code": None},
    {"code": "854231", "bridge_code": None},
    {"code": "847330", "bridge_code": None},
    {"code": "721049", "bridge_code": None},
    {"code": "540761", "bridge_code": None},
    {"code": "390120", "bridge_code": None},
]

FILENAME = "stg_comtrade_all_partners_monthly.csv"
EXPECTED_COLS = [
    "batch_id", "period", "year", "month", "flow_code", "reporter_code",
    "partner_code", "partner_name", "is_aggregate_partner", "hs6",
    "commodity_desc", "primary_value_usd", "fob_value_usd", "cif_value_usd",
    "net_wgt_kg", "qty", "source_system", "reporting_perspective", "extracted_at",
]


def _clean_text(value: object, limit: int = 300) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _call_api_once(
    session: requests.Session, key: str, query_code: str, periods: list[str]
) -> tuple[bool, list[dict], str, int]:
    params = {
        "subscription-key": key,
        "reporterCode": VIETNAM_CODE,
        "cmdCode": query_code,
        "flowCode": "M,X",
        "period": ",".join(periods),
        "includeDesc": "true",
        "maxrecords": "100000",
    }
    headers = {"Cache-Control": "no-cache", "Ocp-Apim-Subscription-Key": key}
    for attempt in range(1, 4):
        try:
            resp = session.get(DATA_API_URL, params=params, headers=headers, timeout=60)
            if resp.status_code == 429:
                time.sleep(5 * attempt)
                continue
            if resp.status_code != 200:
                return False, [], f"HTTP {resp.status_code}", resp.status_code
            return True, resp.json().get("data") or [], "OK", resp.status_code
        except Exception as exc:
            if attempt == 3:
                return False, [], str(exc), 0
            time.sleep(3 * attempt)
    return False, [], "Timeout", 0


def _normalize_rows(
    batch_rows: list[dict], target_hs6: str, original_query_code: str, batch_id: str
) -> list[dict]:
    out = []
    is_bridged = original_query_code != target_hs6
    for d in batch_rows:
        period = str(d.get("period") or "")
        partner_code = "" if d.get("partnerCode") is None else str(d.get("partnerCode")).strip()
        cmd_code = str(d.get("cmdCode") or "")
        if not re.fullmatch(r"\d{6}", period) or not re.fullmatch(r"\d{6}", cmd_code):
            continue
        mot_code = d.get("motCode")
        if mot_code is not None and mot_code != 0:
            continue
        flow_code = str(d.get("flowCode") or "")
        if flow_code not in ("M", "X"):
            continue
        desc = _clean_text(d.get("cmdDesc"), 200)
        if is_bridged:
            desc = f"[BRIDGED from {original_query_code}] " + desc
        out.append({
            "batch_id": batch_id,
            "period": period,
            "year": int(period[:4]),
            "month": int(period[4:6]),
            "flow_code": flow_code,
            "reporter_code": str(d.get("reporterCode") or VIETNAM_CODE),
            "partner_code": partner_code,
            "partner_name": _clean_text(d.get("partnerDesc"), 120),
            "is_aggregate_partner": partner_code == "0",
            "hs6": str(target_hs6).strip().zfill(6),
            "commodity_desc": desc,
            "primary_value_usd": _to_float(d.get("primaryValue")),
            "fob_value_usd": _to_float(d.get("fobvalue")),
            "cif_value_usd": _to_float(d.get("cifvalue")),
            "net_wgt_kg": _to_float(d.get("netWgt")),
            "qty": _to_float(d.get("qty")),
            "source_system": "UN_COMTRADE_ALL_PARTNERS_MONTHLY",
            "reporting_perspective": "VN_REPORTED",
            "extracted_at": now_iso(),
        })
    return out


def extract_api(key: str, dest_path: Path, years: list[int]) -> int:
    if not key or key == "your_key_here":
        raise RuntimeError("COMTRADE_PRIMARY_KEY is required in API mode.")
    session = requests.Session()
    all_rows: list[dict] = []
    for item in COMMODITIES:
        target_code = item["code"]
        bridge_code = item["bridge_code"]
        for year in years:
            query_code = bridge_code if (year < 2022 and bridge_code) else target_code
            batch_id = f"{target_code}_{year}"
            periods = [f"{year}{m:02d}" for m in range(1, 13)]
            ok, raw_rows, note, status = _call_api_once(session, key, query_code, periods)
            if not ok and status in (0, 400):
                raw_rows = []
                for half in (periods[:6], periods[6:]):
                    time.sleep(SLEEP_SECONDS)
                    ok2, r2, n2, _ = _call_api_once(session, key, query_code, half)
                    if not ok2:
                        raise RuntimeError(f"Comtrade VN failed {batch_id}: {n2}")
                    raw_rows.extend(r2)
            elif not ok:
                raise RuntimeError(f"Comtrade VN failed {batch_id}: {note}")
            all_rows.extend(_normalize_rows(raw_rows, target_code, query_code, batch_id))
            time.sleep(SLEEP_SECONDS)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLS)
        writer.writeheader()
        writer.writerows(all_rows)
    return len(all_rows)


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Extract UN Comtrade VN-Reported monthly")
    parser.add_argument("--mode", choices=["seed", "api"], default=cfg.ingestion_mode)
    parser.add_argument("--output-dir", type=Path, default=cfg.runtime_staging_dir)
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        assert len(COMMODITIES) == 14
        assert len(EXPECTED_COLS) == 19
        print("[PASS] extract_comtrade_vn selftest")
        return 0

    dest_path = args.output_dir / FILENAME
    if args.mode == "seed":
        rows = stage_seed_csv(cfg.seed_dir / FILENAME, dest_path, EXPECTED_COLS)
        print(f"[SEED] {FILENAME}: {rows:,} rows staged to {dest_path}")
    else:
        rows = extract_api(cfg.comtrade_key, dest_path, sorted(args.years))
        print(f"[API] {FILENAME}: {rows:,} rows extracted to {dest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
