from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ingestion.common import load_config, now_iso, stage_seed_csv

WITS_BASE = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36",
    "Accept": "application/xml",
}
MIN_YEAR = 2015
PARTNERS = ["156", "276", "392", "410", "842"]
VN_IMPORT_CODES = ["851762", "854231", "847330", "721049", "540761", "390120"]
VN_EXPORT_CODES = ["090111", "100630", "080132", "090411", "610910", "640399", "854442"]
PHONE_CODES = ["851712", "851713"]
ANCHORS = [("704", "000", "090111"), ("704", "392", "090111")]

FILENAME = "stg_wits_tariff.csv"
EXPECTED_COLS = [
    "combo_type", "reporter_code", "partner_code", "hs6", "year", "tariff_type",
    "rate_pct", "measure", "min_rate", "max_rate", "total_lines", "pref_lines",
    "mfn_lines", "nomenclature", "datatype", "source_system", "extracted_at",
]


def _build_combos() -> list[tuple[str, str, str, str]]:
    combos = [("VN_IMPORT_MFN", "704", "000", c) for c in VN_IMPORT_CODES]
    for p in PARTNERS:
        for c in VN_IMPORT_CODES:
            combos.append(("VN_IMPORT_PREF", "704", p, c))
        for c in VN_EXPORT_CODES + PHONE_CODES:
            combos.append(("MKT_EXPORT_MFN", p, "000", c))
    for rep, par, c in ANCHORS:
        combos.append(("ANCHOR", rep, par, c))
    return combos


def _parse_sdmx(xml_text: str) -> list[dict]:
    rows = []
    root = ET.fromstring(xml_text)
    series_attrs: dict = {}
    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        if tag == "Series":
            series_attrs = dict(elem.attrib)
        elif tag == "Obs":
            obs = dict(elem.attrib)
            if obs.get("OBS_VALUE") not in (None, "", "."):
                rows.append({**series_attrs, **obs})
    return rows


def extract_api(dest_path: Path) -> int:
    all_rows: list[dict] = []
    for ctype, rep, par, code in _build_combos():
        url = f"{WITS_BASE}/reporter/{rep}/partner/{par}/product/{code}/year/all/datatype/reported"
        xml_text = ""
        for attempt in range(1, 4):
            try:
                with urlopen(Request(url, headers=HEADERS), timeout=50) as resp:
                    xml_text = resp.read().decode(errors="replace")
                break
            except HTTPError as err:
                if err.code == 404:
                    xml_text = ""
                    break
                time.sleep(2.0 * attempt)
            except Exception:
                time.sleep(2.0 * attempt)

        if xml_text:
            for rec in _parse_sdmx(xml_text):
                year_s = str(rec.get("TIME_PERIOD", ""))
                if not re.fullmatch(r"\d{4}", year_s) or int(year_s) < MIN_YEAR:
                    continue
                all_rows.append({
                    "combo_type": ctype,
                    "reporter_code": rec.get("REPORTER", rep),
                    "partner_code": rec.get("PARTNER", par),
                    "hs6": rec.get("PRODUCTCODE", code),
                    "year": int(year_s),
                    "tariff_type": rec.get("TARIFFTYPE", ""),
                    "rate_pct": rec.get("OBS_VALUE", ""),
                    "measure": rec.get("OBS_VALUE_MEASURE", ""),
                    "min_rate": rec.get("MIN_RATE", ""),
                    "max_rate": rec.get("MAX_RATE", ""),
                    "total_lines": rec.get("TOTALNOOFLINES", ""),
                    "pref_lines": rec.get("NBR_PREF_LINES", ""),
                    "mfn_lines": rec.get("NBR_MFN_LINES", ""),
                    "nomenclature": rec.get("NOMENCODE", ""),
                    "datatype": rec.get("DATATYPE", "Reported"),
                    "source_system": "WITS TRAINS SDMX V21 (reported)",
                    "extracted_at": now_iso(),
                })
        time.sleep(0.7)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLS)
        writer.writeheader()
        writer.writerows(all_rows)
    return len(all_rows)


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Extract WITS TRAINS tariff rates")
    parser.add_argument("--mode", choices=["seed", "api"], default=cfg.ingestion_mode)
    parser.add_argument("--output-dir", type=Path, default=cfg.runtime_staging_dir)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        assert len(_build_combos()) == 83
        print("[PASS] extract_wits_tariff selftest")
        return 0

    dest_path = args.output_dir / FILENAME
    if args.mode == "seed":
        rows = stage_seed_csv(cfg.seed_dir / FILENAME, dest_path, EXPECTED_COLS)
        print(f"[SEED] {FILENAME}: {rows:,} rows staged to {dest_path}")
    else:
        rows = extract_api(dest_path)
        print(f"[API] {FILENAME}: {rows:,} rows extracted to {dest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
