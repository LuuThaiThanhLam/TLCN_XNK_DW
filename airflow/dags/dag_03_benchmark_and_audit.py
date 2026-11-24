from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow")

DEFAULT_ARGS = {
    "owner": "dwh-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def _run_benchmark_and_log(**context) -> None:
    from ingestion.common import get_pg_connection, load_config
    from scripts.benchmark_architecture import run_benchmark

    payload = run_benchmark()
    cfg = load_config()
    conn = get_pg_connection(cfg)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit.etl_batch_log
                        (run_id, dag_id, source_table, minio_object_key, file_sha256, row_count, status, notes)
                    VALUES (%s, %s, %s, NULL, NULL, %s, %s, %s);
                    """,
                    (
                        str(context.get("run_id", "manual_bench")),
                        str(context.get("dag").dag_id),
                        "benchmark_3_tier",
                        len(payload.get("benchmarks", [])),
                        "SUCCESS",
                        json.dumps(payload.get("benchmarks", []), ensure_ascii=False)[:1000],
                    ),
                )
    finally:
        conn.close()


with DAG(
    dag_id="dag_03_benchmark_and_audit",
    description="Benchmark PG Core vs PG Partitioned+MV vs ClickHouse Columnar OLAP and log audit entry.",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 9, 1),
    schedule=None,
    catchup=False,
    tags=["benchmark", "audit", "open-source-dwh"],
) as dag:

    run_benchmark_task = PythonOperator(
        task_id="run_benchmark_and_audit",
        python_callable=_run_benchmark_and_log,
    )
