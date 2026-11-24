from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "dwh-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="dag_01_ingest_raw_to_minio",
    description="Extract Comtrade/WITS/World Bank datasets (seed or api mode) and upload to MinIO with SHA-256 manifest.",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 9, 1),
    schedule=None,
    catchup=False,
    params={
        "mode": Param("seed", enum=["seed", "api"], description="Use 'seed' for offline reproducibility or 'api' for live extraction"),
    },
    tags=["ingestion", "minio", "open-source-dwh"],
) as dag:

    extract_comtrade_vn = BashOperator(
        task_id="extract_comtrade_vn",
        bash_command="python /opt/airflow/ingestion/extract/extract_comtrade_vn.py --mode {{ params.mode }}",
    )

    extract_comtrade_mirror = BashOperator(
        task_id="extract_comtrade_mirror",
        bash_command="python /opt/airflow/ingestion/extract/extract_comtrade_mirror.py --mode {{ params.mode }}",
    )

    extract_wits_tariff = BashOperator(
        task_id="extract_wits_tariff",
        bash_command="python /opt/airflow/ingestion/extract/extract_wits_tariff.py --mode {{ params.mode }}",
    )

    extract_wb_macro = BashOperator(
        task_id="extract_wb_macro",
        bash_command="python /opt/airflow/ingestion/extract/extract_wb_macro.py --mode {{ params.mode }}",
    )

    load_to_minio = BashOperator(
        task_id="load_to_minio",
        bash_command="python /opt/airflow/ingestion/load_to_minio.py --date {{ ds }}",
    )

    [extract_comtrade_vn, extract_comtrade_mirror, extract_wits_tariff, extract_wb_macro] >> load_to_minio
