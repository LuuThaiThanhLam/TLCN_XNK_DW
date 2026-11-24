from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.common import get_clickhouse_client, get_pg_connection, load_config, now_iso

BENCHMARK_QUERIES = [
    {
        "id": "B1",
        "name": "Annual Trade Rollup (Year x Region x Flow)",
        "pg_core": """
            SELECT dd.calendar_year, dp.region, df.name_vi, SUM(f.primary_value_usd)
            FROM core_dwh.fact_trade f
            JOIN core_dwh.dim_date dd ON dd.date_key = f.date_key
            JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
            JOIN core_dwh.dim_flow df ON df.flow_key = f.flow_key
            WHERE f.perspective_key = 1 AND dp.is_aggregate = FALSE AND dd.granularity = 'MONTH'
            GROUP BY dd.calendar_year, dp.region, df.name_vi
        """,
        "pg_opt": """
            SELECT calendar_year, region, flow_name, SUM(total_value_usd)
            FROM mart.mv_trade_summary
            GROUP BY calendar_year, region, flow_name
        """,
        "ch_olap": """
            SELECT dd.calendar_year, dp.region, df.name_vi, sum(f.primary_value_usd)
            FROM olap_xnk.fact_trade f
            INNER JOIN olap_xnk.dim_date dd ON dd.date_key = f.date_key
            INNER JOIN olap_xnk.dim_partner dp ON dp.partner_key = f.partner_key
            INNER JOIN olap_xnk.dim_flow df ON df.flow_key = f.flow_key
            WHERE f.perspective_key = 1 AND dp.is_aggregate = 0 AND dd.granularity = 'MONTH'
            GROUP BY dd.calendar_year, dp.region, df.name_vi
        """,
    },
    {
        "id": "B2",
        "name": "Bilateral Trade Balance (14 HS6 Scope)",
        "pg_core": """
            SELECT dd.calendar_year, dp.partner_name,
                   SUM(CASE WHEN f.flow_key = 1 THEN f.primary_value_usd ELSE 0 END) -
                   SUM(CASE WHEN f.flow_key = 2 THEN f.primary_value_usd ELSE 0 END)
            FROM core_dwh.fact_trade f
            JOIN core_dwh.dim_date dd ON dd.date_key = f.date_key
            JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
            WHERE f.perspective_key = 1 AND dp.is_aggregate = FALSE AND dd.granularity = 'MONTH'
            GROUP BY dd.calendar_year, dp.partner_name
        """,
        "pg_opt": """
            SELECT calendar_year, partner_name, trade_balance_usd
            FROM mart.mv_trade_balance
        """,
        "ch_olap": """
            SELECT dd.calendar_year, dp.partner_name,
                   sumIf(f.primary_value_usd, f.flow_key = 1) - sumIf(f.primary_value_usd, f.flow_key = 2)
            FROM olap_xnk.fact_trade f
            INNER JOIN olap_xnk.dim_date dd ON dd.date_key = f.date_key
            INNER JOIN olap_xnk.dim_partner dp ON dp.partner_key = f.partner_key
            WHERE f.perspective_key = 1 AND dp.is_aggregate = 0 AND dd.granularity = 'MONTH'
            GROUP BY dd.calendar_year, dp.partner_name
        """,
    },
    {
        "id": "B3",
        "name": "Market Concentration Index (HHI & CR-4)",
        "pg_core": """
            WITH yp AS (
                SELECT dd.calendar_year, f.flow_key, dp.partner_key,
                       SUM(f.primary_value_usd) AS pv,
                       SUM(SUM(f.primary_value_usd)) OVER (PARTITION BY dd.calendar_year, f.flow_key) AS yt
                FROM core_dwh.fact_trade f
                JOIN core_dwh.dim_date dd ON dd.date_key = f.date_key
                JOIN core_dwh.dim_partner dp ON dp.partner_key = f.partner_key
                WHERE f.perspective_key = 1 AND dp.is_aggregate = FALSE AND dd.granularity = 'MONTH'
                GROUP BY dd.calendar_year, f.flow_key, dp.partner_key
            ), sh AS (
                SELECT calendar_year, flow_key, 100.0 * pv / NULLIF(yt, 0) AS sp,
                       RANK() OVER (PARTITION BY calendar_year, flow_key ORDER BY pv DESC) AS rk
                FROM yp
            )
            SELECT calendar_year, flow_key, SUM(POWER(sp, 2)), SUM(CASE WHEN rk <= 4 THEN sp ELSE 0 END)
            FROM sh GROUP BY calendar_year, flow_key
        """,
        "pg_opt": """
            SELECT calendar_year, flow_name, hhi_index, cr4_pct
            FROM mart.mv_market_concentration
        """,
        "ch_olap": """
            WITH yp AS (
                SELECT dd.calendar_year AS cy, f.flow_key AS fk, dp.partner_key AS pk,
                       sum(f.primary_value_usd) AS pv
                FROM olap_xnk.fact_trade f
                INNER JOIN olap_xnk.dim_date dd ON dd.date_key = f.date_key
                INNER JOIN olap_xnk.dim_partner dp ON dp.partner_key = f.partner_key
                WHERE f.perspective_key = 1 AND dp.is_aggregate = 0 AND dd.granularity = 'MONTH'
                GROUP BY dd.calendar_year, f.flow_key, dp.partner_key
            ), sh AS (
                SELECT cy, fk, 100.0 * pv / nullIf(sum(pv) OVER (PARTITION BY cy, fk), 0) AS sp,
                       rank() OVER (PARTITION BY cy, fk ORDER BY pv DESC) AS rk
                FROM yp
            )
            SELECT cy, fk, sum(pow(sp, 2)), sumIf(sp, rk <= 4)
            FROM sh GROUP BY cy, fk
        """,
    },
    {
        "id": "B4",
        "name": "Partition Pruning Slice (Year = 2023 x Commodity)",
        "pg_core": """
            SELECT commodity_key, flow_key, SUM(primary_value_usd)
            FROM core_dwh.fact_trade
            WHERE calendar_year = 2023 AND perspective_key = 1 AND is_aggregate_partner = FALSE
            GROUP BY commodity_key, flow_key
        """,
        "pg_opt": """
            SELECT commodity_key, flow_key, SUM(primary_value_usd)
            FROM core_dwh.fact_trade_partitioned
            WHERE calendar_year = 2023 AND perspective_key = 1 AND is_aggregate_partner = FALSE
            GROUP BY commodity_key, flow_key
        """,
        "ch_olap": """
            SELECT commodity_key, flow_key, sum(primary_value_usd)
            FROM olap_xnk.fact_trade
            WHERE calendar_year = 2023 AND perspective_key = 1 AND is_aggregate_partner = 0
            GROUP BY commodity_key, flow_key
        """,
    },
    {
        "id": "B5",
        "name": "2024 Mirror Reconciliation & Coverage Aggregation",
        "pg_core": """
            SELECT data_source_flag, COUNT(*), SUM(best_estimate_usd)
            FROM intermediate.int_trade_reconciliation r
            JOIN core_dwh.dim_date dd ON dd.date_key = r.date_key
            WHERE dd.calendar_year = 2024
            GROUP BY data_source_flag
        """,
        "pg_opt": """
            SELECT data_source_flag, COUNT(*), SUM(best_estimate_usd)
            FROM mart.mv_trade_reconciliation
            WHERE calendar_year = 2024
            GROUP BY data_source_flag
        """,
        "ch_olap": """
            SELECT data_source_flag, count(), sum(best_estimate_usd)
            FROM olap_xnk.mart_trade_reconciliation
            WHERE calendar_year = 2024
            GROUP BY data_source_flag
        """,
    },
]


def _run_pg_timed(conn, sql: str, runs: int = 3) -> dict:
    times_ms = []
    rows_count = 0
    explain_summary = ""
    with conn.cursor() as cur:
        for i in range(runs):
            t0 = time.perf_counter()
            cur.execute(sql)
            rows = cur.fetchall()
            times_ms.append((time.perf_counter() - t0) * 1000.0)
            rows_count = len(rows)
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}")
        plan = cur.fetchone()[0][0]
        explain_summary = f"Execution={plan.get('Execution Time', 0):.2f}ms"
    return {
        "cold_ms": round(times_ms[0], 2),
        "warm_avg_ms": round(sum(times_ms[1:]) / max(len(times_ms) - 1, 1), 2),
        "rows": rows_count,
        "explain": explain_summary,
    }


def _run_ch_timed(client, sql: str, runs: int = 3) -> dict:
    times_ms = []
    rows_count = 0
    for _ in range(runs):
        t0 = time.perf_counter()
        res = client.query(sql)
        times_ms.append((time.perf_counter() - t0) * 1000.0)
        rows_count = len(res.result_rows)
    return {
        "cold_ms": round(times_ms[0], 2),
        "warm_avg_ms": round(sum(times_ms[1:]) / max(len(times_ms) - 1, 1), 2),
        "rows": rows_count,
    }


def run_benchmark() -> dict:
    cfg = load_config()
    pg_conn = get_pg_connection(cfg)
    ch_client = get_clickhouse_client(cfg)
    results = []

    try:
        for q in BENCHMARK_QUERIES:
            pg_core = _run_pg_timed(pg_conn, q["pg_core"])
            pg_opt = _run_pg_timed(pg_conn, q["pg_opt"])
            ch_olap = _run_ch_timed(ch_client, q["ch_olap"])
            results.append({
                "id": q["id"],
                "name": q["name"],
                "pg_core": pg_core,
                "pg_opt": pg_opt,
                "ch_olap": ch_olap,
            })
            print(
                f"[{q['id']}] PG Core={pg_core['warm_avg_ms']}ms | "
                f"PG Opt/MV={pg_opt['warm_avg_ms']}ms | CH OLAP={ch_olap['warm_avg_ms']}ms"
            )
    finally:
        pg_conn.close()
        ch_client.close()

    out_dir = Path(__file__).resolve().parents[1] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"ran_at": now_iso(), "benchmarks": results}
    (out_dir / "benchmark_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Báo cáo Benchmark kiến trúc Data Warehouse mã nguồn mở (3 tầng)",
        "",
        f"- Thời điểm đo: `{payload['ran_at']}`",
        "- So sánh 3 tầng: **PostgreSQL 16 Core (Fact Constellation Schema)** vs **PostgreSQL Partitioned + Materialized Views** vs **ClickHouse 24.8 Columnar OLAP**.",
        "",
        "| Mã | Kịch bản | PG Core Warm (ms) | PG Part/MV Warm (ms) | ClickHouse Warm (ms) | Số dòng |",
        "|:---:|---|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| **{r['id']}** | {r['name']} | {r['pg_core']['warm_avg_ms']:.2f} | "
            f"{r['pg_opt']['warm_avg_ms']:.2f} | {r['ch_olap']['warm_avg_ms']:.2f} | {r['pg_core']['rows']} |"
        )
    (out_dir / "benchmark_report.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


if __name__ == "__main__":
    run_benchmark()
