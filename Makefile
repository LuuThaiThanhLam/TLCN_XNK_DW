.PHONY: up down status logs trigger-all dbt-run dbt-test dbt-docs benchmark verify-offline

SHELL := /bin/bash
COMPOSE := docker compose

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=100

trigger-all:
	$(COMPOSE) exec -T airflow-scheduler bash -lc "for dag in dag_01_ingest_raw_to_minio dag_02_dwh_elt_pipeline dag_03_benchmark_and_audit; do airflow dags unpause \$$dag >/dev/null && airflow dags trigger \$$dag; done"

dbt-run:
	$(COMPOSE) exec -T airflow-scheduler bash -lc "cd /opt/airflow/dbt_project && dbt seed --profiles-dir . && dbt run --profiles-dir . --select staging && dbt snapshot --profiles-dir . && dbt run --profiles-dir . --select intermediate core_dwh marts"

dbt-test:
	$(COMPOSE) exec -T airflow-scheduler bash -lc "cd /opt/airflow/dbt_project && dbt test --profiles-dir ."

dbt-docs:
	$(COMPOSE) run --rm -p 8081:8081 --no-deps airflow-scheduler bash -lc "cd /opt/airflow/dbt_project && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir . --host 0.0.0.0 --port 8081"

benchmark:
	$(COMPOSE) exec -T airflow-scheduler python /opt/airflow/scripts/benchmark_architecture.py

verify-offline:
	python scripts/verify_offline.py
