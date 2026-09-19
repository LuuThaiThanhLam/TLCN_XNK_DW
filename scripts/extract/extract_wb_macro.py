"""
TUAN 2 — NV4b: WORLD BANK MACRO (FACT_MACRO_INDICATOR)
De tai: Kho du lieu ho tro phan tich va ra quyet dinh XNK hang hoa Viet Nam

5 chi so × 6 quoc gia (VN + 5 doi tac), 2015–2024 — chi 5 HTTP call (API WB goi duoc
nhieu nuoc bang dau phay, khong can key). Du lieu phuc vu:
- D2: bubble "quy mo thi truong (GDP) x tang truong x XK VN" cho 5 thi truong.
- D3/D1: giai thich dot bien (ty gia, CPI) — khong suy nguyen nhan, chi de tham chieu.

Validation: doi chieu VNM GDP 2024 + VNM FX 2024 voi bang chung smoke test tuan 1
(`results/week1/api_smoke_test_results.json`) — lech > 0.5% = WB revision, ghi chu.

Chay:
    python scripts/extract/extract_wb_macro.py --selftest
    python scripts/extract/extract_wb_macro.py            # 5 call, ~15 giay
    python scripts/extract/extract_wb_macro.py --rebuild-only
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week2_macro"
STAGING_CSV = PROJECT_ROOT / "data" / "staging" / "stg_wb_macro.csv"
RESULT_DIR = PROJECT_ROOT / "results" / "week2"
WEEK1_SMOKE = PROJECT_ROOT / "results" / "week1" / "api_smoke_test_results.json"

COUNTRIES = ["VNM", "CHN", "DEU", "JPN", "KOR", "USA"]
DATE_RANGE = "2015:2024"
INDICATORS = [
    ("NY.GDP.MKTP.CD", "GDP (current US$)"),
    ("NY.GDP.PCAP.CD", "GDP per capita (current US$)"),
    ("FP.CPI.TOTL.ZG", "Inflation, CPI (annual %)"),
    ("PA.NUS.FCRF", "Official exchange rate (LCU per US$, period average)"),
    ("NE.TRD.GNFS.ZS", "Trade (% of GDP)"),  # BN.TOTL.GD.ZS = ma CHET (WB error 120), da thay + test lai
]


def _flat(v):
    """WB v2: country/indicator co the la dict {id,value} hoac string."""
    if isinstance(v, dict):
        return str(v.get("id") or v.get("value") or "")
    return str(v or "")


def _flat_name(v):
    if isinstance(v, dict):
        return str(v.get("value") or v.get("id") or "")
    return str(v or "")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Accept": "application/json"}

FIELDS = ["country_iso3", "country_name", "indicator", "indicator_name",
          "year", "value", "source_system", "extracted_at"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_url(indicator: str) -> str:
    # WB API: nhieu QUOC GIA trong path ngan nhau bang DAU CHAM PHAI (;) — dau phay
    # bi tu choi voi error 120 (da test ca 2 bien the, xem bien bao cao NV4).
    q = urlencode({"date": DATE_RANGE, "format": "json", "per_page": "2000"})
    return f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}/indicator/{indicator}?{q}"


def fetch(indicator: str, tries: int = 3) -> dict:
    url = build_url(indicator)
    last = None
    for attempt in range(1, tries + 1):
        try:
            with urlopen(Request(url, headers=UA), timeout=45) as r:
                body = json.loads(r.read().decode("utf-8"))
            if isinstance(body, dict):  # WB tra loi loi dang {"message":[...]}
                msg = str(body.get("message", body))[:150]
                return {"ok": False, "error": f"API msg: {msg}"}
            meta = body[0] if body else {}
            rows = body[1] if len(body) > 1 else []
            if not rows and isinstance(meta, dict) and meta.get("message"):
                return {"ok": False, "error": f"API msg: {str(meta['message'])[:150]}"}
            return {"ok": True, "meta": meta if isinstance(meta, dict) else {}, "rows": rows or []}
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(3 * attempt)
    return {"ok": False, "error": last}


def parse_rows(payload: dict) -> list[dict]:
    out = []
    for d in payload.get("rows", []):
        val = d.get("value")
        if val is None:
            continue
        iso = d.get("countryiso3code") or _flat(d.get("country"))
        year = str(d.get("date", ""))[:4]
        if not re.fullmatch(r"\d{4}", year) or len(iso) != 3:
            continue
        out.append({
            "country_iso3": iso,
            "country_name": _flat_name(d.get("country")),
            "indicator": _flat(d.get("indicator")),
            "indicator_name": d.get("indicator_name") or _flat_name(d.get("indicator")),
            "year": int(year),
            "value": float(val),
            "source_system": "World Bank WDI API v2",
            "extracted_at": now_iso(),
        })
    return out


def week1_anchors() -> list[dict]:
    """Lay 2 neo tu smoke test tuan 1 (VNM GDP 2024, VNM FX 2024)."""
    if not WEEK1_SMOKE.exists():
        return []
    wanted = []
    for t in json.loads(WEEK1_SMOKE.read_text(encoding="utf-8-sig")):
        u = str(t.get("url", ""))
        s = t.get("sample") or {}
        if "worldbank.org/v2" not in u or not isinstance(s, dict):
            continue
        if s.get("countryiso3code") == "VNM" and s.get("date") == "2024" and s.get("value"):
            wanted.append({"indicator": s.get("indicator"), "value": float(s["value"]), "url": u[:90]})
    return wanted


def validate(rows: list[dict], anchors: list[dict]) -> list[dict]:
    idx = {(r["country_iso3"], r["indicator"], r["year"]): r["value"] for r in rows}
    out = []
    for a in anchors:
        got = idx.get(("VNM", a["indicator"], 2024))
        if got is None:
            status = "MISSING"
            rel = None
        else:
            rel = abs(got - a["value"]) / a["value"]
            status = "MATCH" if rel <= 0.005 else "WARN_REVISION"
        out.append({"case": f"VNM {a['indicator']} 2024", "week1": a["value"], "now": got, "rel": rel, "status": status})
    return out


def write_outputs(rows: list[dict], log: list[dict], validations: list[dict]) -> None:
    STAGING_CSV.parent.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with STAGING_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    by_cy = {}
    for r in rows:
        by_cy[r["country_iso3"]] = by_cy.get(r["country_iso3"], 0) + 1
    lines = [
        "# WB MACRO — TUAN 2 NV4b",
        "",
        f"- Chat luc: {now_iso()} | Pham vi: {len(INDICATORS)} chi so x {len(COUNTRIES)} nuoc x {DATE_RANGE}",
        f"- Tong dong staging: **{len(rows)}** → `data/staging/stg_wb_macro.csv` (khong commit)",
        "",
        "| Country | So dong |",
        "|---|---:|",
    ]
    for c, n in sorted(by_cy.items()):
        lines.append(f"| {c} | {n} |")
    lines += ["", "## Validation vs smoke test tuan 1 (VNM 2024)", "",
              "| Case | Tuan 1 | Bay gio | Lech | Ket qua |", "|---|---:|---:|---:|---|"]
    for v in validations:
        nowv = "—" if v["now"] is None else f"{v['now']:,.4f}"
        rel = "—" if v["rel"] is None else f"{v['rel']:.3%}"
        mark = {"MATCH": "✅", "WARN_REVISION": "⚠️", "MISSING": "❌"}[v["status"]]
        lines.append(f"| {v['case']} | {v['week1']:,.4f} | {nowv} | {rel} | {mark} {v['status']} |")
    lines += ["", "## Nhat ky goi", "", "| Indicator | HTTP/OK | So dong | Ghi chu |", "|---|---|---:|---|"]
    for e in log:
        lines.append(f"| {e['indicator']} | {e['status']} | {e['rows']} | {e.get('note','')[:80]} |")
    lines += ["", "## Ghi chu", "- Gia tri null cua WB (nam chua phat hanh) duoc loai — vi du nam 2024 co the thieu o vai nuoc/vai chi so: day la coverage thuc cua nguon, ghi nguyen trong bao cao NV5. Neu mot indicator tra 0 dong, do la API_ERROR (log FAIL), khong im lang.", "- Khong dung macro de suy nguyen nhan; chi la truc tham chieu (docs/06)."]
    (RESULT_DIR / "wb_macro.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULT_DIR / "wb_macro.json").write_text(json.dumps(
        {"ran_at": now_iso(), "total_rows": len(rows), "log": log, "validations": validations},
        ensure_ascii=False, indent=2), encoding="utf-8")


def load_raw() -> list[dict]:
    rows, log = [], []
    for p in sorted(RAW_DIR.glob("*.json")):
        entry = json.loads(p.read_text(encoding="utf-8"))
        rows.extend(parse_rows(entry))
        log.append({"indicator": entry["indicator"], "status": "REBUILT", "rows": len(entry.get("rows", []))})
    return rows, log


def selftest() -> int:
    print("=== SELFTEST NV4b (WB macro) ===")
    failures = []
    mock = {"rows": [
        {"country": "Viet Nam", "countryiso3code": "VNM", "indicator": "NY.GDP.MKTP.CD",
         "indicator_name": "GDP (current US$)", "date": "2024", "value": 476324572783.807},
        {"country": "Viet Nam", "countryiso3code": "VNM", "indicator": "NY.GDP.MKTP.CD",
         "indicator_name": "GDP (current US$)", "date": "2015", "value": None},
        {"country": "X", "countryiso3code": "", "indicator": "BAD", "date": "202", "value": 1.0},
    ]}
    rows = parse_rows(mock)
    if len(rows) != 1 or rows[0]["year"] != 2024:
        failures.append(f"parse_rows loi: {rows}")
    v = validate(rows, [{"indicator": "NY.GDP.MKTP.CD", "value": 476324572783.807}, {"indicator": "FP.CPI.TOTL.ZG", "value": 5.0}])
    if [x["status"] for x in v] != ["MATCH", "MISSING"]:
        failures.append(f"validate loi: {[x['status'] for x in v]}")
    if "country/VNM;CHN;DEU;JPN;KOR;USA/indicator/NY.GDP.MKTP.CD" not in build_url("NY.GDP.MKTP.CD"):
        failures.append("build_url sai (phai dung dau ; ngan cach nuoc)")
    anchors = week1_anchors()
    print(f"  anchors tu week1: {len(anchors)} (ky vong 2)")
    if WEEK1_SMOKE.exists() and len(anchors) != 2:
        failures.append("khong doc duoc 2 anchor tu file week1")
    for f_ in failures:
        print("[FAIL]", f_)
    print("SELFTEST:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="NV4b WB macro extract")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rebuild-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    rows, log = [], []
    if args.rebuild_only:
        rows, log = load_raw()
        if not rows:
            print("[FAIL] Khong co raw nao de rebuild"); return 1
    else:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        print(f"=== NV4b WB MACRO | {len(INDICATORS)} call | {DATE_RANGE} | {','.join(COUNTRIES)} ===")
        for ind, name in INDICATORS:
            raw_path = RAW_DIR / f"{ind.replace('.', '_')}.json"
            if raw_path.exists() and not args.force:
                entry = json.loads(raw_path.read_text(encoding="utf-8"))
                parsed = parse_rows(entry)
                rows.extend(parsed)
                log.append({"indicator": ind, "status": "SKIP (cache)", "rows": len(parsed)})
                print(f"[cache] {ind} ({len(parsed)} dong)")
                continue
            res = fetch(ind)
            if not res["ok"]:
                log.append({"indicator": ind, "status": "FAIL", "rows": 0, "note": res["error"]})
                print(f"[FAIL] {ind}: {res['error']}")
                continue
            entry = {"indicator": ind, "name": name, "fetched_at": now_iso(), "meta": res["meta"], "rows": res["rows"]}
            raw_path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
            parsed = parse_rows(entry)
            rows.extend(parsed)
            log.append({"indicator": ind, "status": "OK", "rows": len(parsed), "note": f"API total={res['meta'].get('total')}"})
            print(f"[OK] {ind}: {len(parsed)} dong")
            time.sleep(0.8)

    write_outputs(rows, log, validate(rows, week1_anchors()))
    n_fail = sum(1 for e in log if e["status"] == "FAIL")
    print(f"\n=== TONG KET NV4b === - Dong staging: {len(rows)} | batch fail: {n_fail}")
    print("Xong. Mo results/week2/wb_macro.md")
    return 1 if n_fail or not rows else 0


if __name__ == "__main__":
    sys.exit(main())
