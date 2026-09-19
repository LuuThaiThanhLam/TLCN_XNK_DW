"""
TUAN 2 — NV3: EXTRACT MIRROR (PARTNER_MIRROR) — 5 doi tac bao cao ve Viet Nam
Đe tai: Kho du lieu ho tro phan tich va ra quyet dinh XNK hang hoa Viet Nam

Ban chat: dao chieu goc nhin. Voi moi doi tac p trong {156,276,392,410,842}:
  - p IMPORT (M) tu VN  <-> bang chung VN EXPORT (X) toi p   [RECON_VN_EXPORT]
  - p EXPORT (X) sang VN <-> bang chung VN IMPORT  (M) tu p  [RECON_VN_MIRROR→RECON_VN_IMPORT]
  - to hop con lai (vd p X sang VN ma mat hang VN cung xuat) = INFO_EXTRA, van giu.
Reconciliation (tinh lech %, co cờ LOW/MOD/HIGH) lam o tang transform — O DAY CHỈ
extract va luu du 2 cot moc de join: (period, hs6_final, vn_flow_du_doi).

Pham vi: 5 reporter × 10 nam (2015–2024, 2024 co the mirror da co som hon VN —
dac diem nay la chat lieu cho D3, GIU NGUYEN khong loc bo). Ma dien thoai: tu dong
dung 851712 cho 2015–2021 va 851713 cho 2022+ (cung thu tuc bridge nhu NV2b ben VN).

Goi API: 1 call = 1 reporter × 1 nam, flowCode="X,M" (neu bi 400 → tu dong tach
tung flow). 50 call toan bo. Resume qua manifest_mirror.json nhu NV2.

Validation: doi chieu gia tri mirror cua 5 case 2023M01/2024M01 trong
results/week1/mirror_check_results.json (truong co mirror_value_usd != null).

Chay:
    python scripts/extract/extract_comtrade_mirror.py --selftest      # offline
    python scripts/extract/extract_comtrade_mirror.py --years 2015    # rehearsal 5 call
    python scripts/extract/extract_comtrade_mirror.py                 # 50 call (~6-8 phut)
    python scripts/extract/extract_comtrade_mirror.py --rebuild-only  # tai tao tu raw
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_comtrade_core as core  # noqa: E402

MIRROR_URL = "https://comtradeapi.un.org/data/v1/get/C/M/HS"
REPORTERS = [
    ("156", "China"),
    ("276", "Germany"),
    ("392", "Japan"),
    ("410", "Rep. of Korea"),
    ("842", "United States"),
]
VN_CODE = core.VIETNAM_CODE  # "704"

VN_EXPORT_CODES = ["090111", "100630", "080132", "090411", "610910", "640399", "854442"]
VN_IMPORT_CODES = ["851762", "854231", "847330", "721049", "540761", "390120"]
PHONE_OLD, PHONE_NEW = "851712", "851713"
BRIDGE_CUTOVER = 2022  # nam dau tien cua 851713

MIRROR_RAW = core.RAW_DIR / "manifest_mirror.json"
MIRROR_STAGING = core.STAGING_DIR / "stg_comtrade_partner_mirror.csv"
MIRROR_MD = core.RESULT_DIR / "mirror_partner_extract.md"
MIRROR_JSON = core.RESULT_DIR / "mirror_partner_extract.json"
WEEK1_MIRROR_JSON = core.PROJECT_ROOT / "results" / "week1" / "mirror_check_results.json"

MIRROR_FIELDS = core.STAGING_FIELDS + [
    "is_reported", "mirror_role", "hs6_original", "maps_to_hs6", "hs_nomenclature",
]


def codes_for_year(year: int) -> list[str]:
    phone = PHONE_OLD if year < BRIDGE_CUTOVER else PHONE_NEW
    return VN_EXPORT_CODES + [phone] + VN_IMPORT_CODES


def mirror_role(flow: str, hs6_final: str) -> str:
    if flow == "M" and hs6_final in VN_EXPORT_CODES:
        return "RECON_VN_EXPORT"
    if flow == "X" and hs6_final in VN_IMPORT_CODES:
        return "RECON_VN_IMPORT"
    if flow == "M" and hs6_final in VN_IMPORT_CODES:
        return "INFO_EXTRA"
    if flow == "X" and hs6_final in VN_EXPORT_CODES:
        return "INFO_EXTRA"
    if flow in ("M", "X") and hs6_final == PHONE_NEW:
        return "RECON_VN_EXPORT" if flow == "M" else "RECON_VN_IMPORT"
    return "INFO_EXTRA"


def sha_batch(reporter: str, year: int) -> str:
    payload = {
        "reporter": reporter, "year": year, "partner": VN_CODE,
        "flows": "X,M", "codes": sorted(codes_for_year(year)),
        "cutover": BRIDGE_CUTOVER, "scope": "partner_mirror_w2nv3_v1",
        "locks": {"motCode": "0", "customsCode": "C00", "partner2Code": "0"},
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


# ========================= API =========================


def call_mirror_once(key: str, reporter: str, year: int, flows: str) -> tuple[bool, list[dict], str, int]:
    params = {
        "subscription-key": key,
        "cmdCode": ",".join(codes_for_year(year)),
        "flowCode": flows,
        "reporterCode": reporter,
        "partnerCode": VN_CODE,
        "period": ",".join(core.periods_for_year(year)),
        "motCode": "0",
        "customsCode": "C00",
        "partner2Code": "0",
        "includeDesc": "true",
        "maxrecords": "100000",
    }
    try:
        resp = core.request_with_retry(MIRROR_URL, params=params, timeout=60, tries=3)
        if resp.status_code != 200:
            return (False, [], f"HTTP {resp.status_code}: {core.clean_text(resp.text, 300)}", resp.status_code)
        data = resp.json()
        return (True, data.get("data") or [], core.clean_text(data.get("error") or "OK", 120), resp.status_code)
    except Exception as exc:  # noqa: BLE001
        return (False, [], f"{type(exc).__name__}: {core.clean_text(str(exc), 200)}", 0)


def fetch_batch(key: str, reporter: str, year: int) -> tuple[list[dict], dict]:
    ok, rows, note, status = call_mirror_once(key, reporter, year, "X,M")
    if ok:
        return rows, {"mode": "dual-flow"}
    if status == 400 and "invalid" in note.lower():
        print("    [400] flowCode='X,M' bi tu choi → tach 2 call rieng X / M...")
        rows_all, notes = [], []
        for fl in ("X", "M"):
            time.sleep(core.SLEEP_SECONDS_BETWEEN_CALLS)
            ok2, r2, n2, _s = call_mirror_once(key, reporter, year, fl)
            if not ok2:
                raise RuntimeError(f"Mirror {reporter}{year} flow {fl} fail: {n2}")
            rows_all.extend(r2)
            notes.append(f"{fl}:{n2}")
        return rows_all, {"mode": "per-flow-fallback", "note": "; ".join(notes)}
    raise RuntimeError(f"Mirror {reporter}{year} fail: {note}")


# ========================= Normalize =========================


def normalize_mirror(rows_raw: list[dict], reporter: str, year: int, batch_id: str) -> list[dict]:
    # Batch chua 2 flow → normalize tung dong va lay flow_code tu chinh dong do
    # (tham so flow cua core.normalize_rows chi co nghia khi batch 1 flow).
    fixed = []
    for d_raw in rows_raw:
        base = core.normalize_rows([d_raw], str(d_raw.get("flowCode") or "?"), year, batch_id)
        if not base:
            continue
        r = base[0]
        r["reporter_code"] = str(d_raw.get("reporterCode") or reporter)
        r["partner_code"] = "704"
        r["partner_name"] = "Vietnam"
        r["is_aggregate_partner"] = False
        r["reporting_perspective"] = "PARTNER_MIRROR"
        r["is_reported"] = bool(d_raw.get("isReported", True))
        code = r["hs6"]
        r["hs6_original"] = code
        if code == PHONE_OLD and year < BRIDGE_CUTOVER:
            r["maps_to_hs6"] = PHONE_NEW
            r["hs_nomenclature"] = "HS2017"
            hs_final = PHONE_NEW
        else:
            r["maps_to_hs6"] = ""
            r["hs_nomenclature"] = "HS2022" if year >= BRIDGE_CUTOVER else "HS2017"
            hs_final = code
        r["mirror_role"] = mirror_role(r["flow_code"], hs_final)
        fixed.append(r)
    return fixed


# ========================= Validation vs tuan 1 =========================


def load_week1_mirror_cells() -> list[dict]:
    if not WEEK1_MIRROR_JSON.exists():
        return []
    try:
        cases = json.loads(WEEK1_MIRROR_JSON.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for c in cases:
        mv = c.get("mirror_value_usd")
        if mv is None:
            continue
        rep = str(c.get("partner_code"))
        # VN EXPORT  <-> partner M ; VN IMPORT <-> partner X
        mflow = "M" if c.get("direction") == "EXPORT" else "X"
        hs6 = str(c.get("hs6"))
        out.append({
            "case_id": c.get("case_id"),
            "cell": (rep, mflow, hs6, str(c.get("period"))),
            "week1_value": float(mv),
        })
    return out


def run_validations(index: dict, wanted: list[dict]) -> list[dict]:
    res = []
    for w in wanted:
        got = index.get(w["cell"])
        if got is None:
            status = "MISSING_IN_MIRROR"
        elif abs(got - w["week1_value"]) <= 0.01:
            status = "MATCH"
        else:
            status = "MISMATCH"
        res.append({**w, "mirror_value": got, "status": status})
    return res


def build_mirror_index(rows: list[dict]) -> dict:
    idx = {}
    for r in rows:
        key = (r["reporter_code"], r["flow_code"], r["hs6"], r["period"])
        idx[key] = r["primary_value_usd"]
    return idx


# ========================= Fetch + cache =========================


def load_manifest() -> dict:
    if MIRROR_RAW.exists():
        try:
            return json.loads(MIRROR_RAW.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_manifest(m: dict) -> None:
    MIRROR_RAW.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def do_fetch(key: str, years: list[int], reporters: list[str]) -> tuple[list[dict], list[dict]]:
    core.RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    all_rows, log = [], []
    total = len(years) * len(reporters)
    done = 0
    for year in years:
        for rep in reporters:
            done += 1
            batch_id = f"mir_{rep}_{year}"
            sha = sha_batch(rep, year)
            raw_path = core.RAW_DIR / f"{batch_id}.json"
            if batch_id in manifest and manifest[batch_id].get("sha") == sha and raw_path.exists():
                entry = json.loads(raw_path.read_text(encoding="utf-8"))
                rows = normalize_mirror(entry.get("rows_raw", []), rep, year, batch_id)
                all_rows.extend(rows)
                log.append({"batch_id": batch_id, "status": "SKIP (cache)", "rows": len(rows), "mode": "cache"})
                print(f"[{done}/{total}] {batch_id} — cache, bo qua ({len(rows)} dong)")
                continue
            print(f"[{done}/{total}] {batch_id} — goi mirror API ({len(codes_for_year(year))} ma, X+M, 12 ky)...")
            t0 = time.time()
            try:
                rows_raw, meta = fetch_batch(key, rep, year)
            except RuntimeError as exc:
                log.append({"batch_id": batch_id, "status": "FAIL", "rows": None, "mode": "—", "note": str(exc)})
                print(f"    [FAIL] {exc}")
                print("    Batch OK van duoc giu — chay lai lenh de resume.")
                save_manifest(manifest)
                continue
            raw_path.write_text(
                json.dumps({"batch_id": batch_id, "saved_at": core.now_iso(), "sha": sha,
                            "reporter": rep, "year": year, "rows_raw": rows_raw}, ensure_ascii=False),
                encoding="utf-8",
            )
            rows = normalize_mirror(rows_raw, rep, year, batch_id)
            all_rows.extend(rows)
            manifest[batch_id] = {"sha": sha, "rows": len(rows), "saved_at": core.now_iso(),
                                  "mode": meta.get("mode", "dual-flow"), "note": core.clean_text(meta.get("note", ""), 100)}
            save_manifest(manifest)
            log.append({"batch_id": batch_id, "status": "OK", "rows": len(rows), "mode": meta.get("mode", "dual-flow"),
                        "note": meta.get("note", "")})
            print(f"    -> {len(rows)} dong, {time.time() - t0:.1f}s")
            time.sleep(core.SLEEP_SECONDS_BETWEEN_CALLS)
    return all_rows, log


def do_rebuild(reporters: list[str], years: list[int]) -> tuple[list[dict], list[dict]]:
    all_rows, log = [], []
    for raw_path in sorted(core.RAW_DIR.glob("mir_*.json")):
        entry = json.loads(raw_path.read_text(encoding="utf-8"))
        rep, year = entry.get("reporter", "?"), entry.get("year", 0)
        if rep in reporters and year in years:
            rows = normalize_mirror(entry.get("rows_raw", []), rep, year, entry.get("batch_id", raw_path.stem))
            all_rows.extend(rows)
            log.append({"batch_id": entry.get("batch_id", raw_path.stem), "status": "REBUILT", "rows": len(rows), "mode": "cache"})
    return all_rows, log


# ========================= Outputs =========================


def write_outputs(rows: list[dict], log: list[dict], validations: list[dict], years: list[int]) -> None:
    core.STAGING_DIR.mkdir(parents=True, exist_ok=True)
    core.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with MIRROR_STAGING.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MIRROR_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    by_batch: dict = {}
    recon_months: dict = {}
    n_info = 0
    for r in rows:
        by_batch[r["batch_id"]] = by_batch.get(r["batch_id"], 0) + 1
        if r["mirror_role"] == "INFO_EXTRA":
            n_info += 1
        else:
            recon_months.setdefault((r["reporter_code"], r["mirror_role"], r["hs6_original"]), set()).add(r["period"])

    n_ok = sum(1 for e in log if e["status"] in ("OK", "SKIP (cache)", "REBUILT"))
    matched = sum(1 for v in validations if v["status"] == "MATCH")
    n_ok_years = sum(1 for y in years if 2015 <= y <= 2023)

    lines = [
        "# MIRROR PARTNER — TUAN 2 NV3",
        "",
        f"- Chat luc: {core.now_iso()}",
        "- Goc nhin: PARTNER_MIRROR (reporter = doi tac, partner = 704). Khong bao gio trộn số với VN_REPORTED.",
        f"- Nam: {years[0]}–{years[-1]}. Ma dien thoai tu dong chuyen theo nam (<{BRIDGE_CUTOVER}: {PHONE_OLD}; tu {BRIDGE_CUTOVER}: {PHONE_NEW}).",
        f"- Tong dong: **{len(rows)}** (RECON: {len(rows) - n_info} | INFO_EXTRA: {n_info}) → `data/staging/stg_comtrade_partner_mirror.csv` (khong commit).",
        "",
        "## 1. Validation vs mirror tuan 1 (mirror_check_results.json)",
        "",
        "| Case tuan 1 | O kiem tra (rep/flow/hs6/period) | Gia tri tuan 1 | Gia tri mirror | Ket qua |",
        "|---|---|---:|---:|---|",
    ]
    for v in validations:
        rep, flow, hs6, period = v["cell"]
        got = "—" if v.get("mirror_value") is None else f"{v['mirror_value']:,.3f}"
        mark = {"MATCH": "✅", "MISMATCH": "❌", "MISSING_IN_MIRROR": "⚠️"}.get(v["status"], "")
        lines.append(f"| {v['case_id']} | {rep}/{flow}/{hs6}/{period} | {v['week1_value']:,.3f} | {got} | {mark} {v['status']} |")
    lines += [
        "",
        f"- Khop: {matched}/{len(validations)} (MISSING_IN_MIRROR o nam 2024 co the xay ra — kiem tra bang 3 truoc khi ket luan).",
        "",
        f"## 2. Coverage o RECON (so thang co du lieu / {n_ok_years * 12})",
        "",
        "| Reporter | Vai tro | HS6 | So thang |",
        "|---|---|---|---:|",
    ]
    for (rep, role, hs6), months in sorted(recon_months.items()):
        lines.append(f"| {rep} | {role} | {hs6} | {len(months)} |")
    lines += [
        "",
        "## 3. Nhat ky batch",
        "",
        f"- Batch OK/SKIP: {n_ok}/{len(log)}",
        "",
        "| Batch | Trang thai | So dong | Mode |",
        "|---|---|---:|---|",
    ]
    for e in log:
        lines.append(f"| {e['batch_id']} | {e['status']} | {e.get('rows') if e.get('rows') is not None else '—'} | {e.get('mode', '—')} |")
    lines += [
        "",
        "## 4. Ghi chu su dung o transform (NV4/tuan 3)",
        "",
        "- Join reconciliation: `mirror(period, hs6=maps_to_hs6 or hs6, reporter=p, M)` vs `vn_reported(period, hs6, partner=p, X)` (va nguoc lai cho M/VN-IMPORT).",
        "- Chi so dung primaryValue; lech %abs = |m−v|/max(m,v); co: LOW ≤10%, MODERATE ≤30%, HIGH >30% (docs/06).",
        "- `is_reported=false` (uoc luong cua UN) → khong dung cho so so sanh chinh; dem rieng de minh bach.",
        "- INFO_EXTRA giu nguyen trong staging de phan tich phu, loc khi vao fact.",
    ]
    MIRROR_MD.write_text("\n".join(lines), encoding="utf-8")
    MIRROR_JSON.write_text(
        json.dumps({"ran_at": core.now_iso(), "total_rows": len(rows), "info_extra": n_info,
                    "validations": validations, "log": log}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ========================= Selftest =========================


def selftest() -> int:
    print("=== SELFTEST NV3 mirror ===")
    failures = []
    if codes_for_year(2017)[:8] != VN_EXPORT_CODES + [PHONE_OLD]:
        failures.append("2017 phai dung 851712")
    if codes_for_year(2022)[:8] != VN_EXPORT_CODES + [PHONE_NEW]:
        failures.append("2022 phai chuyen sang 851713 (cutover <=)")
    if PHONE_NEW not in codes_for_year(2023) or PHONE_OLD in codes_for_year(2023):
        failures.append("2023 phai dung 851713, khong co 851712")
    if mirror_role("M", "090111") != "RECON_VN_EXPORT" or mirror_role("X", "854231") != "RECON_VN_IMPORT":
        failures.append("role map sai")
    if mirror_role("X", "090111") != "INFO_EXTRA" or mirror_role("M", "854231") != "INFO_EXTRA":
        failures.append("INFO_EXTRA map sai")
    if mirror_role("M", PHONE_NEW) != "RECON_VN_EXPORT" or mirror_role("X", PHONE_NEW) != "RECON_VN_IMPORT":
        failures.append("role dien thoai sai")
    fake = [
        {"period": "201701", "flowCode": "M", "reporterCode": 392, "partnerCode": 704,
         "cmdCode": "851712", "cmdDesc": "Tel", "primaryValue": 111.111, "isReported": True},
        {"period": "201702", "flowCode": "X", "reporterCode": 392, "partnerCode": 704,
         "cmdCode": "090111", "cmdDesc": "Coffee", "primaryValue": 222.222, "isReported": False},
    ]
    rows = normalize_mirror(fake, "392", 2017, "mir_392_2017")
    if len(rows) != 2:
        failures.append(f"normalize mirror: {len(rows)}")
    else:
        r0, r1 = rows
        if r0["flow_code"] != "M" or r0["maps_to_hs6"] != PHONE_NEW or r0["hs6_original"] != PHONE_OLD:
            failures.append("bridge nhuan 851712→851713 tren mirror sai")
        if r0["mirror_role"] != "RECON_VN_EXPORT" or r0["reporting_perspective"] != "PARTNER_MIRROR":
            failures.append(f"role/perspective sai: {r0['mirror_role']}")
        if r1["flow_code"] != "X" or r1["mirror_role"] != "INFO_EXTRA" or r1["is_reported"] is not False:
            failures.append("dong X/090111 (info_extra, isReported=false) phan loai sai")
    if len(sha_batch("392", 2017)) != 16:
        failures.append("sha batch sai do dai")
    idx = build_mirror_index(rows)
    v = run_validations(idx, [{"case_id": "T", "cell": ("392", "M", "851712", "201701"), "week1_value": 111.111}])
    if v[0]["status"] != "MATCH":
        failures.append("validation vs tuan 1 tren mirror khong khop o case le ra khop")
    if failures:
        for f_ in failures:
            print(f"[FAIL] {f_}")
        print("SELFTEST: FAIL")
        return 1
    print("SELFTEST: PASS (code cutover, role map, bridge, perspective, validation)")
    return 0


# ========================= main =========================


def main() -> int:
    ap = argparse.ArgumentParser(description="NV3 mirror partner extract")
    ap.add_argument("--years", default="", help="Vi du '2015' hoac '2015-2016'. Mac dinh 2015-2024")
    ap.add_argument("--reporters", default="", help="Mac dinh: 156,276,392,410,842")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--rebuild-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    years = core.parse_years(args.years) if args.years else list(range(2015, 2025))
    reporters = [r.strip() for r in args.reporters.split(",") if r.strip()] if args.reporters else [r[0] for r in REPORTERS]

    if args.rebuild_only:
        print("=== REBUILD mirror tu raw (0 call) ===")
        rows, log = do_rebuild(reporters, years)
    else:
        key = core.load_subscription_key()
        if not key:
            print("[FAIL] Khong co key — NV3 bat buoc key nhu NV2. Xem docs/07.")
            return 2
        print(f"=== NV3 MIRROR | reporters={','.join(reporters)} | nam {years[0]}-{years[-1]} | batches={len(years)*len(reporters)} ===")
        if args.force and MIRROR_RAW.exists():
            MIRROR_RAW.unlink()
        rows, log = do_fetch(key, years, reporters)

    if not rows and not args.rebuild_only:
        print("[FAIL] 0 dong — xem log FAIL o tren.")
        return 1

    validations = run_validations(build_mirror_index(rows), load_week1_mirror_cells())
    write_outputs(rows, log, validations, years)
    n_fail = sum(1 for e in log if e["status"] == "FAIL")
    matched = sum(1 for v in validations if v["status"] == "MATCH")
    print("")
    print("=== TONG KET NV3 ===")
    print(f"- Dong staging mirror: {len(rows)} → data/staging/stg_comtrade_partner_mirror.csv")
    print(f"- Batch fail: {n_fail} | Validation vs tuan 1: {matched}/{len(validations)} khop")
    if n_fail:
        print("- Chay lai lenh de resume cac batch FAIL.")
        return 1
    print(f"Xong. Mo {MIRROR_MD.name} trong results/week2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
