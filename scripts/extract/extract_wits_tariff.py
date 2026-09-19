"""
TUAN 2 — NV4a: WITS/UNCTAD TRAINS — THU QUAN (chieu PHU theo docs/06, khong overclaim FTA)
De tai: Kho du lieu ho tro phan tich va ra quyet dinh XNK hang hoa Viet Nam

3 nhom combo (moi combo 1 call `year/all`, loc nam >= 2015 khi luu):
- VN_IMPORT_MFN : reporter 704, partner 000   → thue MFN VN ap len 6 ma NHAP  (6 call)
- VN_IMPORT_PREF: reporter 704, partner in 5  → MFN/PREF VN ap theo goc xu xu
  (du lieu song phuong CHI ton o phia VN bao cao — da bang chung tuan 1)     (30 call)
- MKT_EXPORT_MFN: reporter in 5, partner 000  → thue MFN cua 5 thi truong ap
  len 8 ma XUAT (dien thoai: ca 851712 (2015-21) lan 851713 (2022+)).
  Luu y phap ly du lieu: chieu doi tac → VN (partner 704) tra ve 404 tren mien
  phi (da tai hien chuan xac tuan 1 + hom nay) → dung MFN-World lam xap xi
  "thue nhap cua thi truong" va KHONG tuyen bo gi ve uu dai FTA phia ban.      (45 call)
- ANCHOR: (704,000,090111) + (704,392,090111) — 2 o bang chung tuan 1 de validation (2 call)

WITS khong can key. CAN User-Agent trinh duyet (Cloudflare chan UA thong thuong —
da phat hien va xu ly). 404 hop le cho 1 so combo (nuoc khong bao cao TRAINS) →
ghi NO_DATA, van cache de resume khong goi lai.

Output: data/staging/stg_wits_tariff.csv (khong commit) +
results/week2/wits_tariff_extract.{md,json} (commit).

Chay:
    python scripts/extract/extract_wits_tariff.py --selftest
    python scripts/extract/extract_wits_tariff.py --scope VN --limit 8   # rehearsal
    python scripts/extract/extract_wits_tariff.py                          # full ~83 call
    python scripts/extract/extract_wits_tariff.py --rebuild-only
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "week2_wits"
MANIFEST_PATH = RAW_DIR / "manifest.json"
STAGING_CSV = PROJECT_ROOT / "data" / "staging" / "stg_wits_tariff.csv"
RESULT_DIR = PROJECT_ROOT / "results" / "week2"
WEEK1_SMOKE = PROJECT_ROOT / "results" / "week1" / "api_smoke_test_results.json"

BASE = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      "Accept": "application/xml"}
SLEEP = 0.7
MIN_YEAR = 2015
PARTNER_CODES = {"156": "China", "276": "Germany", "392": "Japan", "410": "Rep. of Korea", "842": "United States"}
VN_IMPORT_CODES = ["851762", "854231", "847330", "721049", "540761", "390120"]
VN_EXPORT_CODES = ["090111", "100630", "080132", "090411", "610910", "640399", "854442"]
PHONE_CODES = ["851712", "851713"]
ANCHOR_COMBOS = [("704", "000", "090111"), ("704", "392", "090111")]

FIELDS = ["combo_type", "reporter_code", "partner_code", "hs6", "year", "tariff_type",
          "rate_pct", "measure", "min_rate", "max_rate", "total_lines", "pref_lines",
          "mfn_lines", "nomenclature", "datatype", "source_system", "extracted_at"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_combos(scope: str) -> list[tuple]:
    combos = []
    if scope in ("VN", "ALL"):
        for code in VN_IMPORT_CODES:
            combos.append(("VN_IMPORT_MFN", "704", "000", code))
        for p in PARTNER_CODES:
            for code in VN_IMPORT_CODES:
                combos.append(("VN_IMPORT_PREF", "704", p, code))
    if scope in ("MKT", "ALL"):
        for p in PARTNER_CODES:
            for code in VN_EXPORT_CODES + PHONE_CODES:
                combos.append(("MKT_EXPORT_MFN", p, "000", code))
    for rep, par, code in ANCHOR_COMBOS:  # validation anchors — luon co trong ALL/VN
        if not any(c[1:] == (rep, par, code) for c in combos):
            combos.append(("ANCHOR", rep, par, code))
    return combos


def url_for(reporter: str, partner: str, product: str) -> str:
    return f"{BASE}/reporter/{reporter}/partner/{partner}/product/{product}/year/all/datatype/reported"


def parse_sdmx(xml_text: str) -> list[dict]:
    """SDMX-ML StructureSpecific: moi <Series> mang chieu, <Obs> mang gia tri."""
    rows = []
    root = ET.fromstring(xml_text)
    series_attrs: dict = {}
    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        if tag == "Series":
            series_attrs = dict(elem.attrib)
        elif tag == "Obs":
            obs = dict(elem.attrib)
            if "OBS_VALUE" in obs and obs.get("OBS_VALUE") not in (None, "", "."):
                rows.append({**series_attrs, **obs})
    return rows


def to_row(rec: dict, combo_type: str) -> dict | None:
    year_s = str(rec.get("TIME_PERIOD", ""))
    if not re.fullmatch(r"\d{4}", year_s) or int(year_s) < MIN_YEAR:
        return None
    fnum = lambda v: (float(v) if v not in (None, "", ".") else None)  # noqa: E731
    return {
        "combo_type": combo_type,
        "reporter_code": rec.get("REPORTER", ""),
        "partner_code": rec.get("PARTNER", ""),
        "hs6": rec.get("PRODUCTCODE", ""),
        "year": int(year_s),
        "tariff_type": rec.get("TARIFFTYPE", ""),
        "rate_pct": fnum(rec.get("OBS_VALUE")),
        "measure": rec.get("OBS_VALUE_MEASURE", ""),
        "min_rate": fnum(rec.get("MIN_RATE")),
        "max_rate": fnum(rec.get("MAX_RATE")),
        "total_lines": rec.get("TOTALNOOFLINES", ""),
        "pref_lines": rec.get("NBR_PREF_LINES", ""),
        "mfn_lines": rec.get("NBR_MFN_LINES", ""),
        "nomenclature": rec.get("NOMENCODE", ""),
        "datatype": rec.get("DATATYPE", "Reported"),
        "source_system": "WITS TRAINS SDMX V21 (reported)",
        "extracted_at": now_iso(),
    }


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def fetch_combo(cid: str, reporter: str, partner: str, product: str, tries: int = 3) -> dict:
    url = url_for(reporter, partner, product)
    last = ""
    for attempt in range(1, tries + 1):
        try:
            with urlopen(Request(url, headers=UA), timeout=50) as r:
                body = r.read().decode(errors="replace")
            return {"status": "OK", "xml": body}
        except HTTPError as e:
            if e.code == 404:
                return {"status": "NO_DATA", "xml": ""}
            last = f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}"
        time.sleep(2.5 * attempt)
    return {"status": "FAIL", "xml": "", "error": last}


def do_fetch(combos: list[tuple], force: bool) -> tuple[list[dict], list[dict]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest() if not force else {}
    rows, log = [], []
    total = len(combos)
    for i, (ctype, rep, par, code) in enumerate(combos, 1):
        cid = f"{rep}_{par}_{code}"
        raw_path = RAW_DIR / f"{cid}.json"
        if not force and cid in manifest and raw_path.exists():
            entry = json.loads(raw_path.read_text(encoding="utf-8"))
            parsed = [to_row(r, ctype) for r in entry.get("records", [])]
            rows.extend([p for p in parsed if p])
            log.append({"combo": cid, "type": ctype, "status": "SKIP", "rows": len(parsed), "years": ""})
            continue
        res = fetch_combo(cid, rep, par, code)
        records = parse_sdmx(res["xml"]) if res["status"] == "OK" else []
        raw_path.write_text(json.dumps({"combo": cid, "type": ctype, "status": res["status"],
                                        "fetched_at": now_iso(), "records": records}, ensure_ascii=False),
                            encoding="utf-8")
        manifest[cid] = {"status": res["status"], "rows": len(records)}
        MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        parsed = [to_row(r, ctype) for r in records]
        parsed = [p for p in parsed if p]
        rows.extend(parsed)
        yrs = sorted({p["year"] for p in parsed})
        years_s = f"{yrs[0]}-{yrs[-1]}" if yrs else "—"
        log.append({"combo": cid, "type": ctype, "status": res["status"], "rows": len(parsed), "years": years_s})
        print(f"[{i}/{total}] {ctype} {cid} -> {res['status']} {len(parsed)} dong ({years_s})")
        time.sleep(SLEEP)
    return rows, log


def rebuild_rows() -> tuple[list[dict], list[dict]]:
    manifest = load_manifest()
    rows, log = [], []
    for ctype, rep, par, code in build_combos("ALL"):
        cid = f"{rep}_{par}_{code}"
        raw_path = RAW_DIR / f"{cid}.json"
        if not raw_path.exists():
            continue
        entry = json.loads(raw_path.read_text(encoding="utf-8"))
        parsed = [p for p in (to_row(r, ctype) for r in entry.get("records", [])) if p]
        rows.extend(parsed)
        yrs = sorted({p["year"] for p in parsed})
        log.append({"combo": cid, "type": ctype, "status": "REBUILT", "rows": len(parsed),
                    "years": f"{yrs[0]}-{yrs[-1]}" if yrs else "—"})
    return rows, log


def week1_tariff_anchors() -> list[dict]:
    """(reporter, partner, hs6, year, TARIFFTYPE) → rate, tu smoke test tuan 1."""
    out = []
    if not WEEK1_SMOKE.exists():
        return out
    for t in json.loads(WEEK1_SMOKE.read_text(encoding="utf-8-sig")):
        u = str(t.get("url", ""))
        m = re.search(r"reporter/(\d+)/partner/(\d+)/product/(\d+)/year/(\d{4})", u)
        s = t.get("sample")
        if m and isinstance(s, dict) and s.get("obs", {}).get("OBS_VALUE"):
            out.append({"key": (m.group(1), m.group(2), m.group(3), int(m.group(4)), s["obs"]["TARIFFTYPE"]),
                        "rate": float(s["obs"]["OBS_VALUE"]), "url": u[:80]})
    return out


def validate(rows: list[dict], anchors: list[dict]) -> list[dict]:
    idx = {(r["reporter_code"], r["partner_code"], r["hs6"], r["year"], r["tariff_type"]): r["rate_pct"] for r in rows}
    out = []
    for a in anchors:
        got = idx.get(a["key"])
        status = "MATCH" if got is not None and abs(got - a["rate"]) <= 0.001 else ("MISSING" if got is None else "MISMATCH")
        out.append({"cell": "|".join(str(x) for x in a["key"]), "week1": a["rate"], "now": got, "status": status})
    return out


def write_outputs(rows: list[dict], log: list[dict], validations: list[dict]) -> None:
    STAGING_CSV.parent.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with STAGING_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n_ok = sum(1 for e in log if e["status"] in ("OK", "SKIP", "REBUILT"))
    n_nodata = sum(1 for e in log if e["status"] == "NO_DATA")
    latest = max((r["year"] for r in rows), default="—")
    by_type: dict = {}
    for e in log:
        t = by_type.setdefault(e["type"], {"combos": 0, "ok": 0, "rows": 0})
        t["combos"] += 1
        t["ok"] += 1 if e["status"] in ("OK", "SKIP", "REBUILT") else 0
        t["rows"] += e["rows"] or 0

    lines = [
        "# WITS THU QUAN — TUAN 2 NV4a",
        "",
        f"- Chat luc: {now_iso()} | WITS/UNCTAD TRAINS, mien phi, khong key (UA trinh duyet bat buoc — Cloudflare).",
        f"- Combo dat: {n_ok} | NO_DATA (nuoc khong bao cao TRAINS cho cap do): {n_nodata}",
        f"- Tong dong staging: **{len(rows)}** (nam >= {MIN_YEAR}) → `data/staging/stg_wits_tariff.csv` (khong commit)",
        f"- Nam toi da co du lieu: {latest} — WITS lag ~1-2 nam → D4 dung thu theo nam (khong monthly), khong doi 2024.",
        "",
        "## 1. Theo nhom combo",
        "",
        "| Nhom | Combos | Dat | Dong | Y nghia |",
        "|---|---:|---:|---:|---|",
    ]
    meaning = {"VN_IMPORT_MFN": "thue MFN VN ap len dau vao san xuat",
               "VN_IMPORT_PREF": "MFN/PREF VN ap theo goc xu xu (song phuong phia VN bao cao)",
               "MKT_EXPORT_MFN": "MFN cua thi truong ap len hang VN (xap xi — khong phai bilatral)",
               "ANCHOR": "2 o kiem chung vs tuan 1"}
    for t, d in by_type.items():
        lines.append(f"| {t} | {d['combos']} | {d['ok']} | {d['rows']} | {meaning.get(t,'')} |")
    lines += ["", "## 2. Validation vs smoke test tuan 1 (HS 090111/2018)", "",
              "| O (rep|partner|hs6|nam|loai) | Tuan 1 | Bay gio | Ket qua |", "|---|---:|---:|---|"]
    for v in validations:
        nowv = "—" if v["now"] is None else f"{v['now']:,.3f}"
        mark = {"MATCH": "✅", "MISMATCH": "❌", "MISSING": "⚠️"}[v["status"]]
        lines.append(f"| {v['cell']} | {v['week1']:,.3f} | {nowv} | {mark} {v['status']} |")
    lines += ["", "## 3. Nhat ky combo (chi in 12 dong dau — day du trong json)", "",
              "| Combo | Nhom | Trang thai | Dong | Nam |", "|---|---|---|---:|---|"]
    for e in log[:12]:
        lines.append(f"| {e['combo']} | {e['type']} | {e['status']} | {e['rows'] if e['rows'] is not None else '—'} | {e['years']} |")
    lines += [
        "",
        "## 4. Ghi chu phap ly du lieu (dung nguyen khi bao cao / dashboard D4)",
        "",
        "- MKT_EXPORT_MFN la **MFN ap dung cho World** — thu VN phai tra khi vao thi truong co the THAP HON (FTA), khong the cao hon; tuyet doi khong dien thanh 'VN dang huong uu dai'.",
        "- Chieu doi tac bao cao ve VN (reporter=partner, partner=704) tra 404 tren mien phi — da tai hien 2 lan (tuan 1 + hom nay) → bo qua co chu dich, khong phai that bai.",
        "- Kiem tra `nomenclature` (H5=HS1996, H6=HS2007...) khi join voi fact: WITS nam cu co the dung HS cu; transform tuan 3 join theo (hs6, year) va loc nomenclature thich ung.",
        "- Thu la du lieu **nam** (grain A) — khong bao gio join vao fact monthly; vao bang `FACT_TARIFF_ANNUAL` rieng nhu docs/06.",
    ]
    (RESULT_DIR / "wits_tariff_extract.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULT_DIR / "wits_tariff_extract.json").write_text(json.dumps(
        {"ran_at": now_iso(), "total_rows": len(rows), "by_type": by_type,
         "validations": validations, "log": log}, ensure_ascii=False, indent=2), encoding="utf-8")


def selftest() -> int:
    print("=== SELFTEST NV4a (WITS tariff) ===")
    failures = []
    xml = '''<?xml version="1.0"?><message:StructureSpecificData xmlns:message="urn:x">
    <message:DataSet><base:Series xmlns:base="urn:y" REPORTER="704" PARTNER="000" PRODUCTCODE="090111" DATATYPE="Reported">
      <base:Obs TIME_PERIOD="2015" OBS_VALUE="17.2" TARIFFTYPE="MFN" OBS_VALUE_MEASURE="SimpleAverage" MIN_RATE="15" MAX_RATE="20" TOTALNOOFLINES="2" NBR_MFN_LINES="2" NOMENCODE="H6"/>
      <base:Obs TIME_PERIOD="2001" OBS_VALUE="20" TARIFFTYPE="MFN"/>
      <base:Obs TIME_PERIOD="2016" OBS_VALUE="." TARIFFTYPE="MFN"/>
    </base:Series></message:DataSet></message:StructureSpecificData>'''
    recs = parse_sdmx(xml)
    if len(recs) != 2:  # obs "." phai bi loai
        failures.append(f"parse_sdmx: mong 2 obs hop le, duoc {len(recs)}")
    rows = [to_row(r, "ANCHOR") for r in recs]
    rows = [r for r in rows if r]
    if len(rows) != 1 or rows[0]["year"] != 2015 or rows[0]["rate_pct"] != 17.2:
        failures.append(f"to_row/loc nam >= {MIN_YEAR} sai: {rows}")
    combos = build_combos("ALL")
    n_vn_mfn = sum(1 for c in combos if c[0] == "VN_IMPORT_MFN")
    n_vn_pref = sum(1 for c in combos if c[0] == "VN_IMPORT_PREF")
    n_mkt = sum(1 for c in combos if c[0] == "MKT_EXPORT_MFN")
    if (n_vn_mfn, n_vn_pref, n_mkt) != (6, 30, 45):
        failures.append(f"combo count sai: {(n_vn_mfn, n_vn_pref, n_mkt)} le ra (6,30,45)")
    anchors = week1_tariff_anchors()
    if WEEK1_SMOKE.exists() and len(anchors) < 2:
        failures.append(f"doc anchors tuan 1 duoc {len(anchors)}, mong >= 2")
    v = validate(rows + [{"reporter_code": "704", "partner_code": "000", "hs6": "090111",
                          "year": 2018, "tariff_type": "MFN", "rate_pct": 15.0}],
                 [{"key": ("704", "000", "090111", 2018, "MFN"), "rate": 15.0, "url": ""},
                  {"key": ("999", "000", "000000", 2018, "MFN"), "rate": 1.0, "url": ""}])
    if [x["status"] for x in v] != ["MATCH", "MISSING"]:
        failures.append(f"validate sai: {[x['status'] for x in v]}")
    print(f"  anchors tuan 1 doc duoc: {len(anchors)}")
    for f_ in failures:
        print("[FAIL]", f_)
    print("SELFTEST:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="NV4a WITS tariff extract")
    ap.add_argument("--scope", choices=["VN", "MKT", "ALL"], default="ALL")
    ap.add_argument("--limit", type=int, default=0, help="Chi chay N combo dau (rehearsal)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--rebuild-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    if args.rebuild_only:
        rows, log = rebuild_rows()
    else:
        combos = build_combos(args.scope)
        if args.limit:
            combos = combos[: args.limit]
        print(f"=== NV4a WITS THU QUAN | {len(combos)} combo | grain NAM >= {MIN_YEAR} | khong can key ===")
        rows, log = do_fetch(combos, args.force)

    if not rows:
        print("[FAIL] 0 dong — kiem tra mang/HTTP tren may ban hoac chay --scope VN truoc.")
        return 1
    write_outputs(rows, log, validate(rows, week1_tariff_anchors()))
    n_fail = sum(1 for e in log if e["status"] == "FAIL")
    print(f"\n=== TONG KET NV4a === - Dong staging: {len(rows)} | combo fail: {n_fail} | "
          f"combo dat: {sum(1 for e in log if e['status'] in ('OK','SKIP','REBUILT'))}")
    print("Xong. Mo results/week2/wits_tariff_extract.md")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
