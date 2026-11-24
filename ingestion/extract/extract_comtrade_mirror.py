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

MIRROR_URL = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
VN_CODE = "704"
REPORTERS = ["156", "276", "392", "410", "842"]
DEFAULT_YEARS = list(range(2015, 2025))
VN_EXPORT_CODES = ["090111", "100630", "080132", "090411", "610910", "640399", "854442"]
VN_IMPORT_CODES = ["851762", "854231", "847330", "721049", "540761", "390120"]
PHONE_OLD, PHONE_NEW = "851712", "851713"
BRIDGE_CUTOVER = 2022
SLEEP_SECONDS = 1.6

FILENAME = "stg_comtrade_partner_mirror.csv"
EXPECTED_COLS = [
    "batch_id", "period", "year", "month", "flow_code", "reporter_code",
    "partner_code", "partner_name", "is_aggregate_partner", "hs6",
    "commodity_desc", "primary_value_usd", "fob_value_usd", "cif_value_usd",
    "net_wgt_kg", "qty", "source_system", "reporting_perspective", "extracted_at",
    "is_reported", "mirror_role", "hs6_original", "maps_to_hs6", "hs_nomenclature",
]


def _codes_for_year(year: int) -> list[str]:
    phone = PHONE_OLD if year < BRIDGE_CUTOVER else PHONE_NEW
    return VN_EXPORT_CODES + [phone] + VN_IMPORT_CODES


def _mirror_role(flow: str, hs6_final: str) -> str:
    if flow == "M" and hs6_final in VN_EXPORT_CODES:
        return "RECON_VN_EXPORT"
    if flow == "X" and hs6_final in VN_IMPORT_CODES:
        return "RECON_VN_IMPORT"
    if hs6_final == PHONE_NEW:
        return "RECON_VN_EXPORT" if flow == "M" else "RECON_VN_IMPORT"
    return "INFO_EXTRA"


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


def _call_mirror(
    session: requests.Session, key: str, reporter: str, year: int, flows: str
) -> list[dict]:
    params = {
        "subscription-key": key,
        "cmdCode": ",".join(_codes_for_year(year)),
        "flowCode": flows,
        "reporterCode": reporter,
        "partnerCode": VN_CODE,
        "period": ",".join(f"{year}{m:02d}" for m in range(1, 13)),
        "motCode": "0",
        "customsCode": "C00",
        "partner2Code": "0",
        "includeDesc": "true",
        "maxrecords": "100000",
    }
    headers = {"Cache-Control": "no-cache", "Ocp-Apim-Subscription-Key": key}
    for attempt in range(1, 4):
        resp = session.get(MIRROR_URL, params=params, headers=headers, timeout=60)
        if resp.status_code == 429:
            time.sleep(5 * attempt)
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} for {reporter}/{year}/{flows}")
        return resp.json().get("data") or []
    raise RuntimeError(f"Timeout for mirror {reporter}/{year}")


def _normalize_mirror(raw_rows: list[dict], reporter: str, year: int, batch_id: str) -> list[dict]:
    out = []
    for d in raw_rows:
        period = str(d.get("period") or "")
        code = str(d.get("cmdCode") or "").strip().zfill(6)
        flow_code = str(d.get("flowCode") or "")
        if not re.fullmatch(r"\d{6}", period) or flow_code not in ("M", "X"):
            continue
        if code == PHONE_OLD and year < BRIDGE_CUTOVER:
            maps_to, nomen, hs_final = PHONE_NEW, "HS2017", PHONE_NEW
        else:
            maps_to = ""
            nomen = "HS2022" if year >= BRIDGE_CUTOVER else "HS2017"
            hs_final = code
        out.append({
            "batch_id": batch_id,
            "period": period,
            "year": int(period[:4]),
            "month": int(period[4:6]),
            "flow_code": flow_code,
            "reporter_code": str(d.get("reporterCode") or reporter),
            "partner_code": VN_CODE,
            "partner_name": "Vietnam",
            "is_aggregate_partner": False,
            "hs6": code,
            "commodity_desc": _clean_text(d.get("cmdDesc"), 200),
            "primary_value_usd": _to_float(d.get("primaryValue")),
            "fob_value_usd": _to_float(d.get("fobvalue")),
            "cif_value_usd": _to_float(d.get("cifvalue")),
            "net_wgt_kg": _to_float(d.get("netWgt")),
            "qty": _to_float(d.get("qty")),
            "source_system": "UN Comtrade data/v1/get (subscription key)",
            "reporting_perspective": "PARTNER_MIRROR",
            "extracted_at": now_iso(),
            "is_reported": bool(d.get("isReported", True)),
            "mirror_role": _mirror_role(flow_code, hs_final),
            "hs6_original": code,
            "maps_to_hs6": maps_to,
            "hs_nomenclature": nomen,
        })
    return out


def extract_api(key: str, dest_path: Path, years: list[int]) -> int:
    if not key or key == "your_key_here":
        raise RuntimeError("COMTRADE_PRIMARY_KEY is required in API mode.")
    session = requests.Session()
    all_rows: list[dict] = []
    for year in years:
        for rep in REPORTERS:
            batch_id = f"mir_{rep}_{year}"
            try:
                raw_rows = _call_mirror(session, key, rep, year, "X,M")
            except RuntimeError:
                raw_rows = []
                for fl in ("X", "M"):
                    time.sleep(SLEEP_SECONDS)
                    raw_rows.extend(_call_mirror(session, key, rep, year, fl))
            all_rows.extend(_normalize_mirror(raw_rows, rep, year, batch_id))
            time.sleep(SLEEP_SECONDS)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLS)
        writer.writeheader()
        writer.writerows(all_rows)
    return len(all_rows)


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Extract UN Comtrade Partner Mirror")
    parser.add_argument("--mode", choices=["seed", "api"], default=cfg.ingestion_mode)
    parser.add_argument("--output-dir", type=Path, default=cfg.runtime_staging_dir)
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        assert len(REPORTERS) == 5
        assert _mirror_role("M", "090111") == "RECON_VN_EXPORT"
        print("[PASS] extract_comtrade_mirror selftest")
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
