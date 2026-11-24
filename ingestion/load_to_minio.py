from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.common import (
    count_csv_rows,
    ensure_minio_bucket,
    get_minio_client,
    load_config,
    now_iso,
    sha256_file,
)

DATASETS = [
    ("vn_reported", "stg_comtrade_all_partners_monthly.csv", "raw.vn_reported"),
    ("partner_mirror", "stg_comtrade_partner_mirror.csv", "raw.partner_mirror"),
    ("wits_tariff", "stg_wits_tariff.csv", "raw.wits_tariff"),
    ("wb_macro", "stg_wb_macro.csv", "raw.wb_macro"),
    ("ref_country_codes", "ref_country_codes.csv", "seed.ref_country_codes"),
]


def resolve_input_file(filename: str, runtime_dir: Path, seed_dir: Path) -> Path:
    runtime_file = runtime_dir / filename
    if runtime_file.exists():
        return runtime_file
    seed_file = seed_dir / filename
    if seed_file.exists():
        return seed_file
    raise FileNotFoundError(f"Dataset file not found in {runtime_dir} or {seed_dir}: {filename}")


def upload_all(run_date: str | None = None, dry_run: bool = False) -> dict:
    cfg = load_config()
    dt = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    manifest = {
        "generated_at": now_iso(),
        "partition_date": dt,
        "bucket": cfg.minio_bucket,
        "datasets": {},
    }

    client = None
    if not dry_run:
        client = get_minio_client(cfg)
        ensure_minio_bucket(client, cfg.minio_bucket)

    for source_name, filename, pg_target in DATASETS:
        local_path = resolve_input_file(filename, cfg.runtime_staging_dir, cfg.seed_dir)
        object_key = f"source={source_name}/dt={dt}/{filename}"
        checksum = sha256_file(local_path)
        rows = count_csv_rows(local_path)

        if not dry_run and client is not None:
            client.upload_file(str(local_path), cfg.minio_bucket, object_key)

        manifest["datasets"][source_name] = {
            "filename": filename,
            "pg_target": pg_target,
            "object_key": object_key,
            "sha256": checksum,
            "row_count": rows,
            "size_bytes": local_path.stat().st_size,
        }
        print(f"[{'DRY-RUN' if dry_run else 'MINIO'}] {object_key} | rows={rows:,} | sha256={checksum[:12]}...")

    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    if not dry_run and client is not None:
        client.put_object(
            Bucket=cfg.minio_bucket,
            Key="manifests/latest_manifest.json",
            Body=manifest_bytes,
            ContentType="application/json",
        )
        client.put_object(
            Bucket=cfg.minio_bucket,
            Key=f"manifests/dt={dt}/manifest.json",
            Body=manifest_bytes,
            ContentType="application/json",
        )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload staged CSV datasets to MinIO")
    parser.add_argument("--date", default=None, help="Partition date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Compute manifest without calling MinIO")
    args = parser.parse_args()
    upload_all(run_date=args.date, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
