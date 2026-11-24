from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ingestion.common import load_config, now_iso, stage_seed_csv

COUNTRIES = ["VNM", "CHN", "DEU", "JPN", "KOR", "USA"]
DATE_RANGE = "2015:2024"
INDICATORS = [
    ("NY.GDP.MKTP.CD", "GDP (current US$)"),
    ("NY.GDP.PCAP.CD", "GDP per capita (current US$)"),
    ("FP.CPI.TOTL.ZG", "Inflation, CPI (annual %)"),
    ("PA.NUS.FCRF", "Official exchange rate (LCU per US$, period average)"),
    ("NE.TRD.GNFS.ZS", "Trade (% of GDP)"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/126.0 Safari/537.36", "Accept": "application/json"}

FILENAME = "stg_wb_macro.csv"
EXPECTED_COLS = [
    "country_iso3", "country_name", "indicator", "indicator_name",
    "year", "value", "source_system", "extracted_at",
]


def _flat(val: object, key: str = "id") -> str:
    if isinstance(val, dict):
        return str(val.get(key) or val.get("value") or val.get("id") or "")
    return str(val or "")


def extract_api(dest_path: Path) -> int:
    all_rows: list[dict] = []
    for ind_code, ind_name in INDICATORS:
        q = urlencode({"date": DATE_RANGE, "format": "json", "per_page": "2000"})
        url = f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}/indicator/{ind_code}?{q}"
        with urlopen(Request(url, headers=HEADERS), timeout=45) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        raw_rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        for d in raw_rows or []:
            val = d.get("value")
            if val is None:
                continue
            iso = str(d.get("countryiso3code") or _flat(d.get("country")))
            year = str(d.get("date", ""))[:4]
            if not re.fullmatch(r"\d{4}", year) or len(iso) != 3:
                continue
            all_rows.append({
                "country_iso3": iso,
                "country_name": _flat(d.get("country"), "value"),
                "indicator": ind_code,
                "indicator_name": ind_name,
                "year": int(year),
                "value": float(val),
                "source_system": "World Bank WDI API v2",
                "extracted_at": now_iso(),
            })
        time.sleep(0.5)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLS)
        writer.writeheader()
        writer.writerows(all_rows)
    return len(all_rows)


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Extract World Bank WDI v2 macro indicators")
    parser.add_argument("--mode", choices=["seed", "api"], default=cfg.ingestion_mode)
    parser.add_argument("--output-dir", type=Path, default=cfg.runtime_staging_dir)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        assert len(COUNTRIES) == 6 and len(INDICATORS) == 5
        print("[PASS] extract_wb_macro selftest")
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
