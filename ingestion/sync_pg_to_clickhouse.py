from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.common import get_clickhouse_client, get_pg_connection, load_config

SYNC_SPECS = [
    {
        "pg_table": "core_dwh.dim_date",
        "ch_table": "olap_xnk.dim_date",
        "cols": ["date_key", "calendar_year", "quarter", "month", "granularity", "date_label"],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.dim_partner",
        "ch_table": "olap_xnk.dim_partner",
        "cols": [
            "partner_key", "code_comtrade", "partner_name", "iso3",
            "is_aggregate", "is_vietnam", "region", "sub_region",
            "income_group", "has_fta_with_vn", "fta_name",
        ],
        "bool_idx": [4, 5, 9],
    },
    {
        "pg_table": "core_dwh.dim_commodity",
        "ch_table": "olap_xnk.dim_commodity",
        "cols": [
            "commodity_key", "hs6", "hs4", "hs2", "name_en",
            "commodity_group", "bridge_flag", "bridge_note",
        ],
        "bool_idx": [6],
    },
    {
        "pg_table": "core_dwh.dim_flow",
        "ch_table": "olap_xnk.dim_flow",
        "cols": ["flow_key", "flow_code", "name_vi", "vn_side_meaning", "mirror_side_meaning"],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.dim_perspective",
        "ch_table": "olap_xnk.dim_perspective",
        "cols": ["perspective_key", "code", "label_vi", "reliability_note"],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.dim_tariff_type",
        "ch_table": "olap_xnk.dim_tariff_type",
        "cols": ["tariff_type_key", "code", "label_vi", "coverage_note"],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.dim_indicator",
        "ch_table": "olap_xnk.dim_indicator",
        "cols": ["indicator_key", "code_wb", "name_en", "unit"],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.dim_audit",
        "ch_table": "olap_xnk.dim_audit",
        "cols": ["audit_key", "batch_id", "source_system", "staging_file", "extracted_at", "row_count"],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.fact_trade",
        "ch_table": "olap_xnk.fact_trade",
        "cols": [
            "trade_key", "date_key", "calendar_year", "month", "partner_key",
            "commodity_key", "flow_key", "perspective_key", "audit_key",
            "primary_value_usd", "net_wgt_kg", "qty", "fob_value_usd",
            "cif_value_usd", "hs6_reported", "reporter_code", "partner_code_src",
            "is_aggregate_partner", "mirror_role", "is_reported",
        ],
        "bool_idx": [17, 19],
    },
    {
        "pg_table": "core_dwh.fact_tariff_rate",
        "ch_table": "olap_xnk.fact_tariff_rate",
        "cols": [
            "tariff_key", "date_key", "calendar_year", "partner_key",
            "commodity_key", "tariff_type_key", "audit_key", "combo_code",
            "ad_valorem_pct", "measure_label", "min_rate", "max_rate",
            "total_lines", "mfn_lines", "pref_lines", "datatype",
        ],
        "bool_idx": [],
    },
    {
        "pg_table": "core_dwh.fact_macro_indicator",
        "ch_table": "olap_xnk.fact_macro_indicator",
        "cols": [
            "macro_key", "date_key", "calendar_year", "partner_key",
            "indicator_key", "audit_key", "value",
        ],
        "bool_idx": [],
    },
    {
        "pg_table": "mart.mart_trade_reconciliation",
        "ch_table": "olap_xnk.mart_trade_reconciliation",
        "cols": [
            "date_key", "calendar_year", "date_label", "partner_key",
            "partner_name", "region", "sub_region", "commodity_key",
            "hs6", "commodity_group", "flow_key", "flow_name",
            "vn_value", "mirror_value_raw", "cif_fob_factor_pct",
            "mirror_value_adjusted", "best_estimate_usd", "abs_diff_usd",
            "pct_diff_vs_vn", "discrepancy_level", "data_source_flag",
            "reconciliation_note",
        ],
        "bool_idx": [],
    },
]


def _normalize_row(row: tuple, bool_idx: list[int]) -> list:
    if not bool_idx:
        return list(row)
    items = list(row)
    for idx in bool_idx:
        if items[idx] is not None:
            items[idx] = 1 if bool(items[idx]) else 0
    return items


def sync_all(batch_size: int = 20000) -> dict[str, tuple[int, int]]:
    cfg = load_config()
    pg_conn = get_pg_connection(cfg)
    ch_client = get_clickhouse_client(cfg)
    summary: dict[str, tuple[int, int]] = {}

    try:
        ch_client.command(
            """
            CREATE TABLE IF NOT EXISTS olap_xnk.dim_audit (
                audit_key     Int32,
                batch_id      String,
                source_system String,
                staging_file  String,
                extracted_at  Nullable(String),
                row_count     Int64
            ) ENGINE = MergeTree()
            ORDER BY (audit_key)
            """
        )
        for spec in SYNC_SPECS:
            pg_table = spec["pg_table"]
            ch_table = spec["ch_table"]
            cols = spec["cols"]
            bool_idx = spec["bool_idx"]
            col_sql = ", ".join(cols)

            ch_client.command(f"TRUNCATE TABLE IF EXISTS {ch_table}")

            pg_total = 0
            with pg_conn.cursor(name=f"cur_{pg_table.replace('.', '_')}") as cur:
                cur.itersize = batch_size
                cur.execute(f"SELECT {col_sql} FROM {pg_table}")
                while True:
                    batch = cur.fetchmany(batch_size)
                    if not batch:
                        break
                    normalized = [_normalize_row(r, bool_idx) for r in batch]
                    ch_client.insert(ch_table, normalized, column_names=cols)
                    pg_total += len(normalized)

            ch_total = int(ch_client.query(f"SELECT count() FROM {ch_table}").first_row[0])
            if pg_total != ch_total:
                raise RuntimeError(
                    f"Row count mismatch after sync {pg_table} -> {ch_table}: PG={pg_total}, CH={ch_total}"
                )
            summary[ch_table] = (pg_total, ch_total)
            print(f"[CH SYNC] {pg_table} -> {ch_table}: {ch_total:,} rows verified")
    finally:
        pg_conn.close()
        ch_client.close()

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync PostgreSQL DWH tables to ClickHouse OLAP")
    parser.add_argument("--batch-size", type=int, default=20000)
    args = parser.parse_args()
    sync_all(batch_size=args.batch_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
