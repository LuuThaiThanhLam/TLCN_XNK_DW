from __future__ import annotations

import csv
import hashlib
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv is not None and (PROJECT_ROOT / ".env").exists():
    load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    ingestion_mode: str
    comtrade_key: str
    seed_dir: Path
    runtime_staging_dir: Path
    pg_host: str
    pg_port: int
    pg_db: str
    pg_user: str
    pg_password: str
    minio_endpoint: str
    minio_user: str
    minio_password: str
    minio_bucket: str
    ch_host: str
    ch_port: int
    ch_db: str
    ch_user: str
    ch_password: str


def load_config() -> Config:
    return Config(
        ingestion_mode=os.getenv("INGESTION_MODE", "seed").strip().lower(),
        comtrade_key=os.getenv("COMTRADE_PRIMARY_KEY", "").strip(),
        seed_dir=Path(os.getenv("SEED_DIR", str(PROJECT_ROOT / "data" / "seed_staging"))),
        runtime_staging_dir=Path(
            os.getenv("RUNTIME_STAGING_DIR", str(PROJECT_ROOT / "data" / "runtime_staging"))
        ),
        pg_host=os.getenv("POSTGRES_HOST", "localhost"),
        pg_port=int(os.getenv("POSTGRES_PORT", "5432")),
        pg_db=os.getenv("POSTGRES_DB", "tlcn_dwh"),
        pg_user=os.getenv("POSTGRES_USER", "dwh_admin"),
        pg_password=os.getenv("POSTGRES_PASSWORD", "dwh_secret_change_me"),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        minio_user=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        minio_password=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me"),
        minio_bucket=os.getenv("MINIO_BUCKET", "tlcn-raw"),
        ch_host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        ch_port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        ch_db=os.getenv("CLICKHOUSE_DB", "olap_xnk"),
        ch_user=os.getenv("CLICKHOUSE_USER", "olap_user"),
        ch_password=os.getenv("CLICKHOUSE_PASSWORD", "olap_secret_change_me"),
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return sum(1 for _ in reader)


def stage_seed_csv(seed_path: Path, dest_path: Path, expected_cols: list[str]) -> int:
    if not seed_path.exists():
        raise FileNotFoundError(f"Seed staging file not found: {seed_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with seed_path.open("r", encoding="utf-8-sig", newline="") as fin:
        reader = csv.reader(fin)
        header = next(reader, None)
        if not header:
            raise ValueError(f"Seed CSV is empty: {seed_path}")
        if header != expected_cols:
            raise ValueError(
                f"Header mismatch in {seed_path.name}: expected {expected_cols}, got {header}"
            )

    raw_bytes = seed_path.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        dest_path.write_bytes(raw_bytes[3:])
    else:
        shutil.copy2(seed_path, dest_path)

    return count_csv_rows(dest_path)


def get_minio_client(cfg: Config) -> Any:
    import boto3
    from botocore.client import Config as BotoConfig

    return boto3.client(
        "s3",
        endpoint_url=cfg.minio_endpoint,
        aws_access_key_id=cfg.minio_user,
        aws_secret_access_key=cfg.minio_password,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_minio_bucket(client: Any, bucket: str) -> None:
    existing = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    if bucket not in existing:
        client.create_bucket(Bucket=bucket)


def get_pg_connection(cfg: Config) -> Any:
    import psycopg2

    return psycopg2.connect(
        host=cfg.pg_host,
        port=cfg.pg_port,
        dbname=cfg.pg_db,
        user=cfg.pg_user,
        password=cfg.pg_password,
    )


def get_clickhouse_client(cfg: Config) -> Any:
    import clickhouse_connect

    return clickhouse_connect.get_client(
        host=cfg.ch_host,
        port=cfg.ch_port,
        username=cfg.ch_user,
        password=cfg.ch_password,
        database=cfg.ch_db,
    )
