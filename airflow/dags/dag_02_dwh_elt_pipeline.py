from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow")

DEFAULT_ARGS = {
    "owner": "dwh-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
}


def _apply_postgres_optimizations() -> None:
    from ingestion.common import get_pg_connection, load_config

    cfg = load_config()
    sql_dir = Path("/opt/airflow/sql/postgres")
    conn = get_pg_connection(cfg)
    try:
        with conn:
            with conn.cursor() as cur:
                for filename in ("00_constraints.sql", "01_partitioning_and_indexes.sql", "02_materialized_views.sql"):
                    sql_text = (sql_dir / filename).read_text(encoding="utf-8")
                    cur.execute(sql_text)

        conn.autocommit = True
        with conn.cursor() as cur:
            for mv_name in (
                "mart.mv_trade_summary",
                "mart.mv_trade_balance",
                "mart.mv_market_concentration",
                "mart.mv_trade_reconciliation",
            ):
                cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name};")
                cur.execute(f"ANALYZE {mv_name};")
    finally:
        conn.close()


with DAG(
    dag_id="dag_02_dwh_elt_pipeline",
    description="Full ELT orchestration: MinIO -> PostgreSQL raw -> dbt seed/snapshot/run/test -> Partition+MV & ClickHouse sync -> dbt docs.",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 9, 1),
    schedule=None,
    catchup=False,
    tags=["elt", "dbt", "postgres", "clickhouse", "open-source-dwh"],
) as dag:

    load_minio_to_pg_raw = BashOperator(
        task_id="load_minio_to_pg_raw",
        bash_command="python /opt/airflow/ingestion/load_minio_to_pg_raw.py --run-id '{{ run_id }}' --dag-id '{{ dag.dag_id }}'",
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command="cd /opt/airflow/dbt_project && dbt seed --profiles-dir .",
    )

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir . --select staging",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command="cd /opt/airflow/dbt_project && dbt snapshot --profiles-dir .",
    )

    dbt_run_core = BashOperator(
        task_id="dbt_run_core",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir . --select intermediate core_dwh",
    )

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir . --select marts",
    )

    dbt_test_quality_gates = BashOperator(
        task_id="dbt_test_quality_gates",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir .",
    )

    pg_build_partitions_and_mvs = PythonOperator(
        task_id="pg_build_partitions_and_mvs",
        python_callable=_apply_postgres_optimizations,
    )

    sync_pg_to_clickhouse = BashOperator(
        task_id="sync_pg_to_clickhouse",
        bash_command="python /opt/airflow/ingestion/sync_pg_to_clickhouse.py",
    )

    dbt_docs_generate = BashOperator(
        task_id="dbt_docs_generate",
        bash_command="cd /opt/airflow/dbt_project && dbt docs generate --profiles-dir .",
    )

    (
        load_minio_to_pg_raw
        >> dbt_seed
        >> dbt_run_staging
        >> dbt_snapshot
        >> dbt_run_core
        >> dbt_run_marts
        >> dbt_test_quality_gates
        >> [pg_build_partitions_and_mvs, sync_pg_to_clickhouse]
        >> dbt_docs_generate
    )
