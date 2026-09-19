"""
TUAN 2 — AUDIT COVERAGE TOAN PHAM VI (2015–2023 + 2024) sau NV2/NV2b
De tai: Kho du lieu ho tro phan tich va ra quyet dinh XNK hang hoa Viet Nam

Muc dich (tra loi cau hoi: "pham vi de cuong co lay du khong?"):
1. Doc 2 file staging local (khong goi API):
   - data/staging/stg_comtrade_vn_reported.csv        (NV2, 14 ma x 2015-2024)
   - data/staging/stg_comtrade_vn_reported_bridge.csv (NV2b, 851712 x 2015-2021)
2. Lap ma tran code x flow x nam: so thang co du lieu World (max 12).
   - 2015–2023: ky vong 12/12, NGOAI 851713 cac nam 2015–2021 (doi bridge nap vao).
   - 2024: ky vong 0/12 — "gap nguồn" đã chứng minh 2 tầng (W1 TOTAL, W2 theo ma) → INFO, không FAIL.
3. Noi bridge: coverage 851713 = core ∪ bridge theo thang.
4. Neo docs/06 §3.3: Σ 12 thang World 2023 cua TUNG ma (dung chieu X/M tuong ung) so voi ANNUAL
   da chốt tuần 1. Ngưỡng theo tinh thần docs/09 §2b: ≤0.5% MATCH, ≤2% CLOSE
   (A≠ΣM là đặc tính nguồn), >2% SOURCE_DIFF (phải giải trình), 0 dòng → MISSING.
5. Thang 5/10: Σ partners ≤ World × 1.02 (World là cực đại chứa partners).

Exit 0 khi khong co FAIL; FAIL = o 2015–2023 tron trang ma LE ra phai co (bridge
thiếu / batch hu / file staging cut doi). Khong sua bat ky file nao khac 2 output.

Chay:
    python scripts/profiling/audit_week2_coverage.py
    python scripts/profiling/audit_week2_coverage.py --staging-dir X --out-dir Y --no-anchors   (debug)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CODES = [
    "090111", "100630", "080132", "090411", "610910", "640399", "854442", "851713",
    "851762", "854231", "847330", "721049", "540761", "390120",
]
FLOWS = ["X", "M"]
YEARS = list(range(2015, 2025))
CORE_FULL_YEARS = range(2015, 2024)
BRIDGE_CODE = "851712"
BRIDGE_MAPS_TO = "851713"
BRIDGE_YEARS = range(2015, 2022)
PRE_HS2022_CELLS = {(BRIDGE_MAPS_TO, flow, y) for flow in FLOWS for y in BRIDGE_YEARS}

# Neo docs/06 §3.3 (annual World 2023, USD) — do grep lai tu docs/06 ngay 2026-09-19
ANCHORS = {
    ("X", "851713"): 26460317776.0,
    ("X", "640399"): 4991396908.0,
    ("X", "100630"): 4060727368.0,
    ("X", "090111"): 2977954667.0,
    ("X", "080132"): 2916825905.0,
    ("X", "854442"): 2062142409.0,
    ("X", "610910"): 1401669880.0,
    ("X", "090411"): 683211713.0,
    ("M", "854231"): 17797673474.0,
    ("M", "847330"): 928122689.0,
    ("M", "851762"): 841528135.0,
    ("M", "390120"): 827368947.0,
    ("M", "540761"): 484289054.0,
    ("M", "721049"): 137743539.0,
}


def read_staging(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for d in csv.DictReader(f):
            rows.append(d)
    return rows


def index_months(rows: list[dict]) -> dict:
    """(code, flow, year) → set(periods World)"""
    idx: dict = {}
    for r in rows:
        if r.get("is_aggregate_partner") != "True" or r.get("partner_code") != "0":
            continue
        code = r["hs6"]
        flow = r["flow_code"]
        year = int(r["year"])
        idx.setdefault((code, flow, year), set()).add(r["period"])
    return idx


def anchor_sums(rows: list[dict]) -> dict:
    """(code, flow) → Σ primary_value World 2023 (12 thang)."""
    out: dict = {}
    for r in rows:
        if r.get("partner_code") != "0" or int(r["year"]) != 2023:
            continue
        key = (r["hs6"], r["flow_code"])
        try:
            out[key] = out.get(key, 0.0) + float(r["primary_value_usd"] or 0.0)
        except ValueError:
            pass
    return out


def world_vs_partners(rows: list[dict]) -> list[dict]:
    """Σ 5 partner ≤ World*1.02 theo o (code, flow, year)."""
    w: dict = {}
    p: dict = {}
    for r in rows:
        key = (r["hs6"], r["flow_code"], int(r["year"]))
        try:
            v = float(r["primary_value_usd"] or 0.0)
        except ValueError:
            continue
        if r.get("partner_code") == "0":
            w[key] = w.get(key, 0.0) + v
        else:
            p[key] = p.get(key, 0.0) + v
    flags = []
    for key, pv in p.items():
        wv = w.get(key, 0.0)
        if wv > 0 and pv > wv * 1.02:
            flags.append({"cell": "|".join([key[0], key[1], str(key[2])]),
                          "sum_partners": pv, "world": wv, "ratio": pv / wv})
    return sorted(flags, key=lambda x: -x["ratio"])


def audit(staging_dir: Path, out_dir: Path, with_anchors: bool) -> int:
    core_path = staging_dir / "stg_comtrade_vn_reported.csv"
    bridge_path = staging_dir / "stg_comtrade_vn_reported_bridge.csv"
    if not core_path.exists():
        print(f"[FAIL] Thieu file core: {core_path}")
        return 1

    core_rows = read_staging(core_path)
    bridge_rows = read_staging(bridge_path) if bridge_path.exists() else []
    if not bridge_rows:
        print("[WARN] Khong co staging bridge — 851713 se thieu 2015–2021 (dung nhu thiet ke NV2; chay NV2b roi audit lai).")

    core_idx = index_months(core_rows)
    bridge_idx = index_months(bridge_rows)
    # Bridge nap thang cho 851713: doi ma ve 851713
    merged_idx = {k: set(v) for k, v in core_idx.items()}
    for (code, flow, year), months in bridge_idx.items():
        if code == BRIDGE_CODE and year in BRIDGE_YEARS:
            tgt = (BRIDGE_MAPS_TO, flow, year)
            merged_idx.setdefault(tgt, set()).update(months)

    fails: list[str] = []
    warns: list[str] = []
    grid: dict = {}
    for flow in FLOWS:
        grid[flow] = {}
        for code in CODES:
            cells = {}
            for year in YEARS:
                months = len(merged_idx.get((code, flow, year), set()))
                if year in CORE_FULL_YEARS:
                    expected_bridge_only = (code, flow, year) in PRE_HS2022_CELLS and not core_idx.get((code, flow, year))
                    if months == 12:
                        status = "OK"
                    elif expected_bridge_only:
                        status = "BRIDGE_MISSING"
                        fails.append(f"{code}|{flow}|{year}: 0 thang, bridge khong bu (chay NV2b?)")
                    elif months == 0 and (code == BRIDGE_MAPS_TO) and year in BRIDGE_YEARS:
                        status = "BRIDGE_MISSING"
                    elif months == 0:
                        fails.append(f"{code}|{flow}|{year}: 0 thang (le ra 12)")
                        status = "FAIL_EMPTY"
                    else:
                        warns.append(f"{code}|{flow}|{year}: {months}/12 thang")
                        status = f"PARTIAL_{months}"
                elif year == 2024:
                    status = "GAP2024" if months == 0 else f"HAS_{months}"
                cells[year] = status
            grid[flow][code] = cells

    anchor_results = []
    if with_anchors:
        sums = anchor_sums(core_rows)
        for (flow, code), anchor in ANCHORS.items():
            got = sums.get((code, flow))
            if got is None or got == 0.0:
                status = "MISSING"
                rel = None
            else:
                rel = abs(got - anchor) / anchor
                status = "MATCH" if rel <= 0.005 else ("CLOSE" if rel <= 0.02 else "SOURCE_DIFF")
                if status == "SOURCE_DIFF":
                    warns.append(f"neo {flow}/{code} 2023: lech {rel:.1%} — giai trinh theo docs/09 §2b")
            anchor_results.append({"flow": flow, "code": code, "anchor": anchor, "sum_months": got, "rel": rel, "status": status})

    partner_flags = world_vs_partners(core_rows)
    for f in partner_flags:
        warns.append(f"World<Σpartners o {f['cell']} (ratio {f['ratio']:.2f})")

    # ---- Xuat md ----
    out_dir.mkdir(parents=True, exist_ok=True)
    n_ok = sum(1 for flow in FLOWS for code in CODES for y in CORE_FULL_YEARS if grid[flow][code][y] == "OK")
    n_cells_core = len(CODES) * len(FLOWS) * len(list(CORE_FULL_YEARS))
    n_match = sum(1 for a in anchor_results if a["status"] == "MATCH")
    n_close = sum(1 for a in anchor_results if a["status"] == "CLOSE")

    sym = {"OK": "✓", "GAP2024": "∅", "BRIDGE_MISSING": "✗", "MATCH": "✓", "CLOSE": "~", "SOURCE_DIFF": "!", "MISSING": "✗"}
    lines = [
        "# AUDIT COVERAGE TOAN PHAM VI — TUAN 2 (NV2 + NV2b)",
        "",
        f"- Chat luc: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Nguon: {core_path.name} ({len(core_rows)} dong) + {bridge_path.name if bridge_rows else 'bridge THIU'} ({len(bridge_rows)} dong)",
        f"- **Coverage lõi 2015–2023: {n_ok}/{n_cells_core} o code×flow×nam dat 12/12 thang** (tinh sau khi noi bridge cho 851713).",
        f"- **Neo docs/06 §3.3 (Σ thang 2023 vs annual): MATCH {n_match}/{len(anchor_results)}, CLOSE {n_close}, SOURCE_DIFF {len(anchor_results) - n_match - n_close - sum(1 for a in anchor_results if a['status'] == 'MISSING')}.**",
        f"- 2024: ∅ = đã được gọi API và nguồn trả 0 dòng (bằng chứng gap, vào D3) — KHÔNG tính là lỗi.",
        "",
        "## 1. Ma tran coverage (12 thang = ✓ | partial ghi si so | ∅ gap nguon 2024 | ✗ thieu that)",
        "",
    ]
    for flow in FLOWS:
        lines.append(f"### Flow {flow}")
        lines.append("")
        lines.append("| HS6 | " + " | ".join(str(y) for y in YEARS) + " |")
        lines.append("|---|" + "---:|" * len(YEARS))
        for code in CODES:
            row = []
            for year in YEARS:
                s = grid[flow][code][year]
                row.append(sym.get(s, "12" if s == "OK" else s.replace("PARTIAL_", "")))
            lines.append(f"| {code} | " + " | ".join(row) + " |")
        lines.append("")
    lines += [
        "## 2. Neo docs/06 §3.3 — Σ 12 tháng World 2023 vs annual đã chốt",
        "",
        "| Flow | HS6 | Anchor (annual) | Σ tháng 2023 | Lệch | Kết quả |",
        "|---|---|---:|---:|---:|---|",
    ]
    for a in anchor_results:
        sm = "—" if a["sum_months"] is None else f"{a['sum_months']:,.0f}"
        rel = "—" if a["rel"] is None else f"{a['rel']:.3%}"
        lines.append(f"| {a['flow']} | {a['code']} | {a['anchor']:,.0f} | {sm} | {rel} | {sym.get(a['status'], '')} {a['status']} |")
    lines += [
        "",
        "## 3. World là cực đại chứa partners (Σ 5 partner ≤ World × 1.02)",
        "",
        ("- Không ô nào vi phạm." if not partner_flags else f"- {len(partner_flags)} ô cần xem (thường là kỳ World chưa được UN aggregate):")
    ]
    for f in partner_flags[:10]:
        lines.append(f"  - {f['cell']}: Σpartners={f['sum_partners']:,.0f} vs World={f['world']:,.0f}")
    lines += [
        "",
        "## 4. Ket luan",
        "",
        f"- FAIL: {len(fails)} — {' '.join(fails[:3]) if fails else '(không)'}",
        f"- WARN: {len(warns)}" + (f" — 3 dau: {'; '.join(warns[:3])}" if warns else ""),
        "- Doc y: 'pham vi 2015–2021' chi la lop bridge cua DUNG ma 851712; 13 ma con lai va chinh 851713 (tu 2022) van nam trong NV2 2015–2024 nhu de cuong.",
        "",
        f"== AUDIT: {'PASS' if not fails else 'FAIL'} ==",
    ]
    (out_dir / "coverage_audit.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "coverage_audit.json").write_text(
        json.dumps({"ran_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "coverage_ok_cells": n_ok, "coverage_total_cells": n_cells_core,
                    "anchors": anchor_results, "world_vs_partners_flags": partner_flags,
                    "fails": fails, "warns": warns}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Loi = {n_ok}/{n_cells_core} o 12/12 thang (sau noi bridge)")
    print(f"Nean 2023: MATCH {n_match}/{len(anchor_results)}, CLOSE {n_close}")
    print(f"2024: da goi API, 0 dong = gap nguon (thong tin, khong phai loi)")
    for m in fails:
        print(f"[FAIL] {m}")
    for m in warns[:8]:
        print(f"[warn] {m}")
    if len(warns) > 8:
        print(f"...va {len(warns) - 8} WARN nua trong md")
    print(f"Xong. Mo: {(out_dir / 'coverage_audit.md').relative_to(PROJECT_ROOT) if out_dir.exists() and str(out_dir).startswith(str(PROJECT_ROOT)) else out_dir / 'coverage_audit.md'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit coverage toan pham vi Tuan 2")
    ap.add_argument("--staging-dir", default=str(PROJECT_ROOT / "data" / "staging"))
    ap.add_argument("--out-dir", default=str(PROJECT_ROOT / "results" / "week2"))
    ap.add_argument("--no-anchors", action="store_true", help="Bo qua buoc doi neo docs/06")
    args = ap.parse_args()
    return audit(Path(args.staging_dir), Path(args.out_dir), with_anchors=not args.no_anchors)


if __name__ == "__main__":
    sys.exit(main())
