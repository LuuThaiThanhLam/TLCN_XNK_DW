"""
TUAN 3 — KIEM CHUAN is_reported (viem da ghi so tu Tuan 2, muc 8 bao cao GVHD)
Muc dich: truoc khi ap luat "loai dong uoc luong" o tang transform, can biet thuc te
co bao nhieu dong bi UN danh dau la uoc luong (isReported=false), o phia nao va
candoi tac nao. Script DOC FILE thuan tuy — 0 goi API, chay offline tren may nao.

Ngu:
  - data/staging/stg_comtrade_partner_mirror.csv  (cot is_reported co san tu NV3 Tuan 2)
  - data/raw/week2_extract/*.json                 (rows_raw cua moi batch; chua ca
    batch core 'w2_*', bridge 'br_*', mirror 'mir_*' — cau truc list hoac
    {"rows_raw": [...]} deu doc duoc)

Ket luan ruoi ( tien quyet dinh cho transform ):
  - core bilateral false > 30%  → KHONG ap luat loc o core (chuyen thanh co den)
  - mirror RECON false > 50%     → nen co cot/loc o view reconciliation
  - ngac lai → du sach, dung het khong can loc

Cach chay:
  python scripts/profiling/check_is_reported.py                 # tai goc repo
  python scripts/profiling/check_is_reported.py --selftest      # tu kiem, khong can data
Exit: 0 = chay xong (du co the ket luan "loc"/"khong loc"), 1 = thieu dau vao.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def _rows_of(blob) -> list[dict]:
    if isinstance(blob, list):
        return [x for x in blob if isinstance(x, dict)]
    if isinstance(blob, dict):
        for k in ("rows_raw", "rows", "data"):
            if isinstance(blob.get(k), list):
                return [x for x in blob[k] if isinstance(x, dict)]
    return []


def scan_raw(raw_dir: Path) -> dict:
    res = {"agg_true": 0, "agg_false": 0, "bil_true": 0, "bil_false": 0, "files": 0,
           "false_by_reporter": defaultdict(int), "files_unread": 0}
    if not raw_dir.exists():
        return res
    for p in sorted(raw_dir.glob("*.json")):
        if p.name.startswith("manifest"):
            continue
        try:
            rows = _rows_of(json.loads(p.read_text(encoding="utf-8-sig")))
        except Exception:  # noqa: BLE001
            res["files_unread"] += 1
            continue
        res["files"] += 1
        for d in rows:
            partner = str(d.get("partnerCode") or "").strip() or "0"
            agg = partner in ("0", "None", "")
            is_rep = bool(d.get("isReported", True))
            res[("agg_" if agg else "bil_") + ("true" if is_rep else "false")] += 1
            rep = str(d.get("reporterCode") or "?")
            if not is_rep:
                res["false_by_reporter"][rep] += 1
    return res


def scan_staging_mirror(path: Path) -> dict:
    out = {"total": 0, "by_reporter": defaultdict(lambda: [0, 0]),
           "by_role": defaultdict(lambda: [0, 0])}   # [rows, est_false]
    if not path.exists():
        return out
    with path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            out["total"] += 1
            false = r.get("is_reported", "True") == "False"
            for key, bucket in ((r.get("reporter_code", "?"), out["by_reporter"]),
                                (r.get("mirror_role", "?"), out["by_role"])):
                bucket[key][0] += 1
                if false:
                    bucket[key][1] += 1
    return out


def check(root: Path) -> tuple[dict, int]:
    staging = root / "data" / "staging" / "stg_comtrade_partner_mirror.csv"
    raw = root / "data" / "raw" / "week2_extract"
    if not staging.exists() and not raw.exists():
        print("[FAIL] Thieu ca hai dau vao (staging mirror + raw week2_extract).")
        print("       Can noi dung `data/` tu may da chay Tuan 2 (xem tai lieu ban giao noi bo nhom, cach A),")
        print("       hoac chay extract that truoc (cach B).")
        return {}, 1
    raw_res = scan_raw(raw)
    mir = scan_staging_mirror(staging)
    bil = raw_res["bil_true"] + raw_res["bil_false"]
    agg = raw_res["agg_true"] + raw_res["agg_false"]
    pct_bil = 100.0 * raw_res["bil_false"] / bil if bil else 0.0
    pct_agg = 100.0 * raw_res["agg_false"] / agg if agg else 0.0
    recon_total = sum(v[0] for k, v in mir["by_role"].items() if k != "INFO_EXTRA")
    recon_false = sum(v[1] for k, v in mir["by_role"].items() if k != "INFO_EXTRA")
    pct_recon = 100.0 * recon_false / recon_total if recon_total else 0.0

    recs = []
    if pct_bil > 30.0:
        recs.append("core: ti le bilateral uoc luong CAO → KHONG ap luat loc o tang "
                    "transform cua VN_REPORTED; giu du lieu + co, ghi chu vao dashboard.")
    elif bil:
        recs.append("core: bilateral sach → khong can lua chon loc cho VN_REPORTED.")
    if pct_recon > 50.0:
        recs.append("mirror: RECON nhieu dong uoc luong → view reconciliation nen co "
                    "cot flag_estimated va tuy chon loc mac dinh = BAT (de user tat duoc).")
    elif recon_total:
        recs.append("mirror: RECON sach → view reconciliation dung het, chi giu cot "
                    "is_reported nhu thong tin, khong loc.")
    payload = {
        "core_raw": {k: v for k, v in raw_res.items() if k != "false_by_reporter"},
        "core_false_by_reporter": dict(sorted(raw_res["false_by_reporter"].items(),
                                              key=lambda kv: -kv[1])),
        "mirror_staging_total": mir["total"],
        "mirror_pct_est_recon": round(pct_recon, 2),
        "mirror_by_reporter": {k: {"rows": v[0], "estimated": v[1]} for k, v in sorted(mir["by_reporter"].items())},
        "mirror_by_role": {k: {"rows": v[0], "estimated": v[1]} for k, v in sorted(mir["by_role"].items())},
        "core_pct_bil_est": round(pct_bil, 2), "core_pct_agg_est": round(pct_agg, 2),
        "recommendations": recs,
    }
    out_dir = root / "results" / "week3"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "is_reported_check.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# KIEM CHUAN is_reported (Tuan 3 — tien quyet dinh transform)", "",
             "## So lieu", "",
             f"- Raw core/bridge batch da doc: {raw_res['files']} file "
             f"({raw_res['files_unread']} file khong doc duoc — bo qua an toan)",
             f"- Dong aggregate (World) phia VN uoc luong: {raw_res['agg_false']}/{agg} = {pct_agg:.1f}%",
             f"- Dong bilateral phia VN uoc luong: **{raw_res['bil_false']}/{bil} = {pct_bil:.1f}%**",
             f"- Mirror RECON uoc luong: {recon_false}/{recon_total} = {pct_recon:.1f}%",
             "", "## Theo reporter (mirror)", "",
             "| Reporter | Dong | Uoc luong | % |", "|---|---:|---:|---:|"]
    for rep, v in sorted(mir["by_reporter"].items()):
        lines.append(f"| {rep} | {v[0]} | {v[1]} | {100.0 * v[1] / v[0] if v[0] else 0:.1f}% |")
    lines += ["", "## Ket luan tien quyet dinh", ""]
    for r in recs:
        lines.append(f"- {r}")
    lines.append("")
    (out_dir / "is_reported_check.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n→ {out_dir / 'is_reported_check.md'} (+ .json)")
    return payload, 0


def selftest() -> int:
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "data" / "staging").mkdir(parents=True)
        raw = root / "data" / "raw" / "week2_extract"
        raw.mkdir(parents=True)
        (raw / "manifest.json").write_text("{}")            # phai bo qua
        (raw / "w2_X_2015.json").write_text(json.dumps({"rows_raw": [
            {"partnerCode": 0, "reporterCode": 704, "isReported": True},
            {"partnerCode": 156, "reporterCode": 704, "isReported": False}]}))
        (raw / "mir_156_2023.json").write_text(json.dumps([  # dang list thuan
            {"partnerCode": 704, "reporterCode": 156, "isReported": False},
            {"partnerCode": 704, "reporterCode": 156, "isReported": True}]))
        (root / "data" / "staging" / "stg_comtrade_partner_mirror.csv").write_text(
            "reporter_code,mirror_role,is_reported\n"
            "156,RECON_VN_EXPORT,True\n156,RECON_VN_IMPORT,False\n156,INFO_EXTRA,False\n",
            encoding="utf-8-sig")
        pj, rc = check(root)
        fails = [] if rc == 0 else [f"exit {rc}"]
        if pj.get("core_raw", {}).get("files") != 2:
            fails.append("so file raw doc duoc sai (manifest phai bi bo qua)")
        if pj.get("core_raw", {}).get("bil_false") != 2 or pj.get("core_raw", {}).get("agg_true") != 1:
            fails.append("dem core sai (bil_false=2, agg_true=1 mong loi)")
        if pj.get("mirror_by_role", {}).get("RECON_VN_IMPORT", {}).get("estimated") != 1:
            fails.append("dem mirror theo role sai")
        if not pj.get("recommendations"):
            fails.append("thieu ket luan tien quyet dinh")
        if (root / "results" / "week3" / "is_reported_check.md").exists() is False:
            fails.append("file md khong duoc ghi")
        if fails:
            print(json.dumps(pj, indent=1))
            for f in fails:
                print("[FAIL]", f)
            return 1
    print("SELFTEST: PASS (doc raw 2 cau truc, bo manifest, dem mirror csv, ket luan, ghi file)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="is_reported pre-check (Tuan 3)")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else check(Path(a.root))[1])
