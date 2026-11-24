from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.common import get_minio_client, get_pg_connection, load_config

RAW_TARGETS = [
    ("vn_reported", "raw.vn_reported", "stg_comtrade_all_partners_monthly.csv"),
    ("partner_mirror", "raw.partner_mirror", "stg_comtrade_partner_mirror.csv"),
    ("wits_tariff", "raw.wits_tariff", "stg_wits_tariff.csv"),
    ("wb_macro", "raw.wb_macro", "stg_wb_macro.csv"),
]


def _strip_bom_and_decode(raw_bytes: bytes) -> str:
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raw_bytes = raw_bytes[3:]
    return raw_bytes.decode("utf-8")


def load_raw_tables(run_id: str, dag_id: str, local_fallback: bool = False) -> dict[str, int]:
    cfg = load_config()
    manifest = {}
    minio_client = None

    if not local_fallback:
        minio_client = get_minio_client(cfg)
        obj = minio_client.get_object(Bucket=cfg.minio_bucket, Key="manifests/latest_manifest.json")
        manifest = json.loads(obj["Body"].read().decode("utf-8"))

    counts: dict[str, int] = {}
    conn = get_pg_connection(cfg)
    try:
        with conn:
            with conn.cursor() as cur:
                for source_name, table_name, default_filename in RAW_TARGETS:
                    object_key = None
                    expected_sha = None

                    if not local_fallback and minio_client is not None:
                        meta = manifest.get("datasets", {}).get(source_name)
                        if not meta:
                            raise KeyError(f"Missing '{source_name}' in MinIO latest_manifest.json")
                        object_key = meta["object_key"]
                        expected_sha = meta["sha256"]
                        resp = minio_client.get_object(Bucket=cfg.minio_bucket, Key=object_key)
                        raw_bytes = resp["Body"].read()
                    else:
                        local_path = cfg.runtime_staging_dir / default_filename
                        if not local_path.exists():
                            local_path = cfg.seed_dir / default_filename
                        raw_bytes = local_path.read_bytes()
                        object_key = f"local://{local_path.name}"

                    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
                    if expected_sha and actual_sha != expected_sha:
                        raise ValueError(
                            f"SHA-256 mismatch for {object_key}: expected {expected_sha}, got {actual_sha}"
                        )

                    clean_csv = _strip_bom_and_decode(raw_bytes)
                    cur.execute(f"TRUNCATE TABLE {table_name};")
                    copy_sql = (
                        f"COPY {table_name} FROM STDIN "
                        "WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8')"
                    )
                    cur.copy_expert(copy_sql, io.StringIO(clean_csv))
                    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = int(cur.fetchone()[0])
                    counts[table_name] = row_count

                    cur.execute(
                        """
                        INSERT INTO audit.etl_batch_log
                            (run_id, dag_id, source_table, minio_object_key, file_sha256, row_count, status, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (
                            run_id,
                            dag_id,
                            table_name,
                            object_key,
                            actual_sha,
                            row_count,
                            "SUCCESS",
                            "Idempotent TRUNCATE + COPY FROM STDIN",
                        ),
                    )
                    print(f"[PG RAW] {table_name}: {row_count:,} rows loaded (sha256={actual_sha[:12]}...)")
    finally:
        conn.close()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Load raw CSV objects from MinIO to PostgreSQL raw.*")
    parser.add_argument("--run-id", default="manual_run")
    parser.add_argument("--dag-id", default="manual_cli")
    parser.add_argument("--local", action="store_true", help="Load from local staging/seed instead of MinIO")
    args = parser.parse_args()
    load_raw_tables(run_id=args.run_id, dag_id=args.dag_id, local_fallback=args.local)
    return 0


if __name__ == "__main__":
    sys.exit(main())
