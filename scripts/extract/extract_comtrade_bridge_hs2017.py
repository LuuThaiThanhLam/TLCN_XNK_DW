"""
TUAN 2 — NV2b: BRIDGE MA HS2017 851712 (dien thoai) cho 2015–2021
De tai: Kho du lieu ho tro phan tich va ra quyet dinh XNK hang hoa Viet Nam

Boi canh (phat hien sau audit coverage W2-NV2):
- Ma 851713 chi co 24/108 thang (2022–2023) vi he thong HS doi nam 2022:
  8517.12 (HS2017, "dien thoai cho mang cel-lular hoac mang khac") duoc thay
  bang 8517.13 (smartphone) + 8517.14 (con lai). Comtrade KHONG hoi ma tu dong.
- Script nay extract 851712 cho X+M, 2015–2021, de chuoi du lieu dien thoai
  lien mach 2015–2023; transform tuan 3 noi theo cot maps_to_hs6.

Thiet ke:
- Tai dung toi da extract_comtrade_core.py (call_once, normalize_rows, PARTNERS, key).
- Batch id `vnbr_{flow}_{nam}`, raw rieng, manifest rieng → Khong đụng cham gì
  toan bo bang chung NV2/NV1 da commit.
- KIEM TRA NOI BO: goi 1 query annual (data/v1/get/C/A/HS, period=2015..2021) roi
  doichieu tung nam voi tong 12 thang World (partner 0). Lech > 0.01 USD → WARN
  (khong fail cuoc chay, vi co the la revision giua 2 lan goi trong luc chay).

Cach chay (Git Bash):
    cd /d/Year26_27_HKI/TLCN/TLCN_XNK_DW && source .venv/Scripts/activate
    python scripts/extract/extract_comtrade_bridge_hs2017.py            # 14 call batch + 2 call annual
    python scripts/extract/extract_comtrade_bridge_hs2017.py --selftest # logic offline, khong network
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

# Tai dung core script cung thu muc
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_comtrade_core as core  # noqa: E402

BRIDGE_CODE = "851712"
MAPS_TO = "851713"
BRIDGE_YEARS = list(range(2015, 2022))  # 2015–2021 (2022+ da co 851713 nguyen ban)
FLOWS = ["X", "M"]
ANNUAL_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

BRIDGE_RAW_DIR = core.RAW_DIR
BRIDGE_MANIFEST = core.RAW_DIR / "manifest_bridge.json"
BRIDGE_STAGING_CSV = core.STAGING_DIR / "stg_comtrade_vn_reported_bridge.csv"
BRIDGE_RESULT_MD = core.RESULT_DIR / "extract_bridge_hs2017.md"
BRIDGE_RESULT_JSON = core.RESULT_DIR / "extract_bridge_hs2017.json"

BRIDGE_FIELDS = core.STAGING_FIELDS + ["hs_nomenclature", "maps_to_hs6"]


def sha_batch(flow: str, year: int) -> str:
    payload = {
        "flow": flow, "year": year, "codes": [BRIDGE_CODE], "maps_to": MAPS_TO,
        "partners": sorted(p[0] for p in core.PARTNERS), "reporter": core.VIETNAM_CODE,
        "scope": "vn_bridge_hs2017_v1",
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def load_manifest() -> dict:
    if BRIDGE_MANIFEST.exists():
        try:
            return json.loads(BRIDGE_MANIFEST.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_manifest(manifest: dict) -> None:
    BRIDGE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def do_fetch(key: str) -> tuple[list[dict], list[dict]]:
    BRIDGE_RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    all_rows, log = [], []
    total = len(FLOWS) * len(BRIDGE_YEARS)
    done = 0
    for flow in FLOWS:
        for year in BRIDGE_YEARS:
            done += 1
            batch_id = f"vnbr_{flow}_{year}"
            sha = sha_batch(flow, year)
            raw_path = BRIDGE_RAW_DIR / f"{batch_id}.json"
            if batch_id in manifest and manifest[batch_id].get("sha") == sha and raw_path.exists():
                entry = json.loads(raw_path.read_text(encoding="utf-8"))
                rows = core.normalize_rows(entry.get("rows_raw", []), flow, year, batch_id)
                all_rows.extend(rows)
                log.append({"batch_id": batch_id, "status": "SKIP (cache)", "rows": len(rows)})
                print(f"[{done}/{total}] {batch_id} — cache, bo qua ({len(rows)} dong)")
                continue
            print(f"[{done}/{total}] {batch_id} — goi API ({BRIDGE_CODE} 12 ky x 6 partner)...")
            ok, rows_raw, note, status = core.call_once(key, flow, core.periods_for_year(year), [BRIDGE_CODE])
            if not ok:
                log.append({"batch_id": batch_id, "status": "FAIL", "rows": None, "note": note})
                print(f"    [FAIL] {note}")
                print("    Batch OK van duoc giu — chay lai lenh de resume.")
                save_manifest(manifest)
                break
            raw_path.write_text(
                json.dumps({"batch_id": batch_id, "saved_at": core.now_iso(), "sha": sha,
                            "flow": flow, "year": year, "rows_raw": rows_raw}, ensure_ascii=False),
                encoding="utf-8",
            )
            rows = core.normalize_rows(rows_raw, flow, year, batch_id)
            all_rows.extend(rows)
            manifest[batch_id] = {"sha": sha, "rows": len(rows), "saved_at": core.now_iso()}
            save_manifest(manifest)
            log.append({"batch_id": batch_id, "status": "OK", "rows": len(rows)})
            print(f"    -> {len(rows)} dong")
            time.sleep(core.SLEEP_SECONDS_BETWEEN_CALLS)
    return all_rows, log


def annual_consistency_check(key: str, rows: list[dict]) -> list[dict]:
    """1 query annual/flow: moi nam phai = tong 12 thang cua dong World (partner 0)."""
    # tong thang tu data bridge da thu thap
    sums: dict = {}
    for r in rows:
        if r["partner_code"] == "0":
            k = (r["flow_code"], r["year"])
            sums[k] = sums.get(k, 0.0) + (r["primary_value_usd"] or 0.0)

    results = []
    for flow in FLOWS:
        params = {
            "subscription-key": key,
            "cmdCode": BRIDGE_CODE,
            "flowCode": flow,
            "reporterCode": core.VIETNAM_CODE,
            "partnerCode": "0",
            "period": ",".join(str(y) for y in BRIDGE_YEARS),
            "motCode": "0",
            "customsCode": "C00",
            "partner2Code": "0",
            "maxrecords": "10000",
        }
        print(f"[check] annual-vs-monthly {flow} (data/v1/get/C/A/HS)...")
        try:
            resp = core.request_with_retry(ANNUAL_URL, params=params, timeout=60, tries=2)
            annual_rows = (resp.json().get("data") or []) if resp.status_code == 200 else []
        except Exception as exc:  # noqa: BLE001
            results.append({"flow": flow, "status": "CHECK_ERROR", "detail": core.clean_text(str(exc), 150)})
            continue
        by_year = {str(d.get("period")): core.to_float(d.get("primaryValue")) for d in annual_rows}
        for year in BRIDGE_YEARS:
            a = by_year.get(str(year))
            m = sums.get((flow, year))
            if a is None and not m:
                results.append({"flow": flow, "year": year, "annual": None, "monthly_sum": None, "status": "NO_DATA"})
            elif a is None or m is None:
                results.append({"flow": flow, "year": year, "annual": a, "monthly_sum": m, "status": "WARN_PARTIAL"})
            elif abs(a - m) <= 0.01:
                results.append({"flow": flow, "year": year, "annual": a, "monthly_sum": m, "status": "MATCH"})
            else:
                results.append({"flow": flow, "year": year, "annual": a, "monthly_sum": m,
                                "status": "WARN_MISMATCH", "diff": a - m})
        time.sleep(core.SLEEP_SECONDS_BETWEEN_CALLS)
    return results


def write_outputs(rows: list[dict], log: list[dict], checks: list[dict], fetched: bool) -> None:
    core.STAGING_DIR.mkdir(parents=True, exist_ok=True)
    core.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    for r in rows:
        r["hs_nomenclature"] = "HS2017"
        r["maps_to_hs6"] = MAPS_TO
    with BRIDGE_STAGING_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BRIDGE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    by_year_flow = {}
    for r in rows:
        k = f"{r['flow_code']}|{r['year']}"
        by_year_flow[k] = by_year_flow.get(k, 0) + 1
    n_match = sum(1 for c in checks if c["status"] == "MATCH")
    n_warn = sum(1 for c in checks if c["status"].startswith("WARN"))

    lines = [
        "# BRIDGE HS2017 851712 → 851713 — TUAN 2 NV2b",
        "",
        f"- Chat luc: {core.now_iso()}",
        f"- Ly do: audit coverage NV2 phat hien 851713 chi co 24/108 thang (revision HS 2022).",
        f"- Extract {BRIDGE_CODE} cho {BRIDGE_YEARS[0]}–{BRIDGE_YEARS[-1]}, X+M, 6 partner, grain thang.",
        f"- Tong dong staging: **{len(rows)}** → `data/staging/stg_comtrade_vn_reported_bridge.csv` (khong commit).",
        "",
        "## 1. Dong theo flow x nam",
        "",
        "| Flow | Nam | So dong |",
        "|---|---:|---:|",
    ]
    for k, n in sorted(by_year_flow.items()):
        fl, yr = k.split("|")
        lines.append(f"| {fl} | {yr} | {n} |")
    lines += [
        "",
        "## 2. Nhat ky batch",
        "",
        "| Batch | Trang thai | So dong |",
        "|---|---|---:|",
    ]
    for e in log:
        lines.append(f"| {e['batch_id']} | {e['status']} | {e.get('rows') if e.get('rows') is not None else '—'} |")
    lines += [
        "",
        "## 3. Annual-vs-monthly (tu kiem chung noi bo)",
        "",
        f"- MATCH: {n_match}/{len(checks)} — WARN: {n_warn}. Monthly sum lay tu dong World (partner 0) cua bridge; annual tu query A cung key.",
        "",
        "| Flow | Nam | Annual | Sum 12 thang | Ket qua |",
        "|---|---|---:|---:|---|",
    ]
    for c in checks:
        a = "—" if c.get("annual") is None else f"{c['annual']:,.3f}"
        m = "—" if c.get("monthly_sum") is None else f"{c['monthly_sum']:,.3f}"
        mark = {"MATCH": "✅", "NO_DATA": "∅"}.get(c["status"], "⚠️")
        lines.append(f"| {c['flow']} | {c.get('year', c.get('detail', ''))} | {a} | {m} | {mark} {c['status']} |")
    lines += [
        "",
        "## 4. Cach su dung o tang transform (tuan 3)",
        "",
        "- Noi bridge vao bang fact: `hs6 = maps_to_hs6 (851713)` khi load, giu nguyen `hs6_original=851712` + cot `hs_nomenclature`.",
        "- Dashboard D1 hien ghi chu: `giai doan 2015–2021 theo ma cu 8517.12 (gom ca dien thoai thuong) — bridge gan dung, kh phai map 1-1`.",
        "- Khong trộn vao batch NV2 goc; moi layer tai liệu hóa nguồn riêng (batch_id vnbr_*).",
        "*(Bao cao nay sinh sau khi audit NV2; fetched=" + str(fetched) + ")*",
    ]
    BRIDGE_RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    BRIDGE_RESULT_JSON.write_text(
        json.dumps({"ran_at": core.now_iso(), "total_rows": len(rows), "log": log, "annual_checks": checks},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def selftest() -> int:
    print("=== SELFTEST NV2b (bridge) ===")
    failures = []
    fake = [{
        "period": "201905", "flowCode": "X", "reporterCode": 704, "partnerCode": 0,
        "partnerDesc": "World", "cmdCode": "851712", "cmdDesc": "Tel cellular",
        "primaryValue": 123.456, "netWgt": 1.0, "qty": 2.0,
    }]
    rows = core.normalize_rows(fake, "X", 2019, "vnbr_X_2019")
    if len(rows) != 1 or rows[0]["hs6"] != "851712" or rows[0]["partner_code"] != "0":
        failures.append(f"normalize bridge sai: {rows}")
    if len(sha_batch("X", 2019)) != 16 or sha_batch("X", 2019) != sha_batch("X", 2019):
        failures.append("sha batch khong on dinh")
    sums = {}
    for r in rows:
        if r["partner_code"] == "0":
            sums[(r["flow_code"], r["year"])] = sums.get((r["flow_code"], r["year"]), 0.0) + r["primary_value_usd"]
    if abs(sums[("X", 2019)] - 123.456) > 0.001:
        failures.append("cong World sai cho annual-check")
    if failures:
        for f_ in failures:
            print(f"[FAIL] {f_}")
        print("SELFTEST: FAIL")
        return 1
    print("SELFTEST: PASS (normalize, sha on dinh, cong World)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NV2b bridge 851712 (HS2017) 2015-2021")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--rebuild-only", action="store_true", help="Tai tao output tu raw da cache, khong goi API")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    rows, log = [], []
    if args.rebuild_only:
        for p in sorted(BRIDGE_RAW_DIR.glob("vnbr_*.json")):
            entry = json.loads(p.read_text(encoding="utf-8"))
            rows.extend(core.normalize_rows(entry.get("rows_raw", []), entry.get("flow", "?"), entry.get("year", 0), entry.get("batch_id", p.stem)))
            log.append({"batch_id": entry.get("batch_id", p.stem), "status": "REBUILT", "rows": len(rows)})
        write_outputs(rows, log, [], fetched=False)
        print(f"Rebuild xong: {len(rows)} dong → {BRIDGE_RESULT_MD}")
        return 0

    key = core.load_subscription_key()
    if not key:
        print("[FAIL] Khong co key trong .env — NV2b cung bat buoc key nhu NV2.")
        return 2
    print(f"=== NV2b BRIDGE {BRIDGE_CODE}→{MAPS_TO} | Nam {BRIDGE_YEARS[0]}-{BRIDGE_YEARS[-1]} | {len(FLOWS)*len(BRIDGE_YEARS)} batch ===")
    rows, log = do_fetch(key)
    checks = annual_consistency_check(key, rows)
    write_outputs(rows, log, checks, fetched=True)
    n_fail = sum(1 for e in log if e["status"] == "FAIL")
    print("")
    print("=== TONG KET NV2b ===")
    print(f"- Dong staging bridge: {len(rows)} → data/staging/stg_comtrade_vn_reported_bridge.csv")
    print(f"- Batch fail: {n_fail} | Annual-check MATCH: {sum(1 for c in checks if c['status'] == 'MATCH')}/{len(checks)}")
    for c in checks:
        if c["status"].startswith("WARN"):
            print(f"  [WARN] {c['flow']} {c.get('year')}: annual={c.get('annual')} monthly={c.get('monthly_sum')}")
    if n_fail:
        return 1
    print(f"Xong. Mo {BRIDGE_RESULT_MD.relative_to(core.PROJECT_ROOT)} de xem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
