from __future__ import annotations

import csv
import math
import py_compile
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_STAGING = PROJECT_ROOT / "data" / "seed_staging"
DBT_SEEDS = PROJECT_ROOT / "dbt_project" / "seeds"
REPORT_PATH = PROJECT_ROOT / "results" / "offline_verification_report.md"

FORBIDDEN_PATTERNS = [
    (r"\bSSAS\b", "Legacy SSAS reference"),
    (r"SQLEXPRESS", "Legacy SQL Server instance reference"),
    (r"Power BI", "Legacy Power BI reference"),
    (r"\bTRY_CONVERT\b", "T-SQL TRY_CONVERT syntax"),
    (r"\bTRY_CAST\b", "T-SQL TRY_CAST syntax"),
    (r"\bNVARCHAR\b", "T-SQL NVARCHAR type"),
    (r"\bdbo\.", "T-SQL dbo schema prefix"),
    (r"\bCREATE OR ALTER\b", "T-SQL CREATE OR ALTER syntax"),
    (r"\bOUTER APPLY\b", "T-SQL OUTER APPLY syntax"),
    (r"\bMSSQLSERVER1\b", "Legacy SSAS instance reference"),
    (r"Effectively Handled", "Incorrect tariff term (use Effectively Applied AHS)"),
    (r"khóa luận", "Wrong document type (use tiểu luận)"),
    (r"Data Mart vật lý", "Imprecise terminology (use Summary Table / Materialized View)"),
    (r"semi-additive", "Incorrect tariff additivity term (use Non-additive)"),
]

ANCHORS_WORLD_2023 = [
    ("X", "851713", 26460317776.0),
    ("X", "640399",  4991396908.0),
    ("X", "100630",  4060727368.0),
    ("X", "090111",  2977954667.0),
    ("X", "080132",  2916825905.0),
    ("X", "854442",  2062142409.0),
    ("X", "610910",  1401669880.0),
    ("X", "090411",   683211713.0),
    ("M", "854231", 17797673474.0),
    ("M", "847330",   928122689.0),
    ("M", "851762",   841528135.0),
    ("M", "390120",   827368947.0),
    ("M", "540761",   484289054.0),
    ("M", "721049",   137743539.0),
]

ANCHORS_MIRROR_7 = [
    ("392", "M", "090111", 202401,  35660719.503),
    ("842", "M", "090111", 202301,  37790801.000),
    ("276", "M", "090111", 202301,  38271554.955),
    ("156", "X", "851762", 202301,  29945226.000),
    ("410", "X", "854231", 202301, 217401413.000),
    ("156", "X", "851762", 202401,  62727085.000),
    ("410", "X", "854231", 202401, 412589570.000),
]


def _num_or_none(val: str | None) -> float | None:
    if val is None:
        return None
    s = val.strip()
    if not s:
        return None
    return float(s)


def check_python_compile() -> list[str]:
    errors = []
    for folder in ("ingestion", "airflow/dags", "scripts"):
        base = PROJECT_ROOT / folder
        for py_file in sorted(base.rglob("*.py")):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"{py_file}: {exc}")
    return errors


def check_yaml_structure() -> list[str]:
    errors = []
    dbt_root = PROJECT_ROOT / "dbt_project"
    yml_files = [PROJECT_ROOT / "docker-compose.yml"] + sorted(
        yf
        for yf in dbt_root.rglob("*.yml")
        if yf.is_file() and not any(part in ("target", "dbt_packages") for part in yf.relative_to(dbt_root).parts)
    )
    for yf in yml_files:
        text = yf.read_text(encoding="utf-8")
        if "\t" in text:
            errors.append(f"{yf}: contains tab character(s)")
        if not text.strip():
            errors.append(f"{yf}: empty YAML file")
    dc_text = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    for req in ("services:", "postgres:", "minio:", "clickhouse:", "airflow-webserver:", "airflow-scheduler:", "metabase:"):
        if req not in dc_text:
            errors.append(f"docker-compose.yml missing '{req}'")
    return errors


def check_cleanliness() -> list[str]:
    findings = []
    scan_exts = {".sql", ".yml", ".py", ".md", ".csv"}
    skip_rel = {
        "results/offline_verification_report.md",
        "docs/02_terminology_glossary.md",
    }
    for path in sorted(PROJECT_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in scan_exts:
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel in skip_rel or rel.startswith("data/seed_staging/") or rel.startswith("dbt_project/target/") or "__pycache__" in rel:
            continue
        if rel == "scripts/verify_offline.py":
            continue
        content = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN_PATTERNS:
            for m in re.finditer(pattern, content, flags=re.IGNORECASE | re.MULTILINE):
                line_no = content[: m.start()].count("\n") + 1
                findings.append(f"{rel}:{line_no} [{label}] -> '{m.group(0)}'")
    return findings


def check_cli_selftests() -> list[str]:
    errors = []
    cmds = [
        [sys.executable, str(PROJECT_ROOT / "ingestion" / "extract" / "extract_comtrade_vn.py"), "--selftest"],
        [sys.executable, str(PROJECT_ROOT / "ingestion" / "extract" / "extract_comtrade_mirror.py"), "--selftest"],
        [sys.executable, str(PROJECT_ROOT / "ingestion" / "extract" / "extract_wits_tariff.py"), "--selftest"],
        [sys.executable, str(PROJECT_ROOT / "ingestion" / "extract" / "extract_wb_macro.py"), "--selftest"],
        [sys.executable, str(PROJECT_ROOT / "ingestion" / "load_to_minio.py"), "--dry-run"],
    ]
    for cmd in cmds:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append(f"Command failed ({' '.join(cmd)}): {proc.stderr or proc.stdout}")
    return errors


def _load_csv_into_sqlite(conn: sqlite3.Connection, csv_path: Path, table: str, cols: list[str]) -> int:
    placeholders = ", ".join(["?"] * len(cols))
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f"CREATE TABLE {table} ({col_defs})")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != cols:
            raise ValueError(f"Header mismatch in {csv_path.name}: {reader.fieldnames} != {cols}")
        batch = [tuple(row[c] for c in cols) for row in reader]
    conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", batch)
    return len(batch)


def run_dwh_simulation() -> dict:
    conn = sqlite3.connect(":memory:")
    conn.create_function("POWER", 2, lambda a, b: math.pow(float(a), float(b)) if a is not None else None)
    conn.create_function("LPAD", 3, lambda s, n, ch: ("" if s is None else str(s)).rjust(int(n), str(ch)))
    conn.create_function("SCI_ROUND2", 1, lambda s: round(float(s), 2) if s and s.strip() else None)
    conn.create_function("NUM_OR_NONE", 1, _num_or_none)

    raw_counts = {
        "raw_vn_reported": _load_csv_into_sqlite(
            conn,
            SEED_STAGING / "stg_comtrade_all_partners_monthly.csv",
            "raw_vn_reported",
            [
                "batch_id", "period", "year", "month", "flow_code", "reporter_code",
                "partner_code", "partner_name", "is_aggregate_partner", "hs6",
                "commodity_desc", "primary_value_usd", "fob_value_usd", "cif_value_usd",
                "net_wgt_kg", "qty", "source_system", "reporting_perspective", "extracted_at",
            ],
        ),
        "raw_partner_mirror": _load_csv_into_sqlite(
            conn,
            SEED_STAGING / "stg_comtrade_partner_mirror.csv",
            "raw_partner_mirror",
            [
                "batch_id", "period", "year", "month", "flow_code", "reporter_code",
                "partner_code", "partner_name", "is_aggregate_partner", "hs6",
                "commodity_desc", "primary_value_usd", "fob_value_usd", "cif_value_usd",
                "net_wgt_kg", "qty", "source_system", "reporting_perspective", "extracted_at",
                "is_reported", "mirror_role", "hs6_original", "maps_to_hs6", "hs_nomenclature",
            ],
        ),
        "raw_wits_tariff": _load_csv_into_sqlite(
            conn,
            SEED_STAGING / "stg_wits_tariff.csv",
            "raw_wits_tariff",
            [
                "combo_type", "reporter_code", "partner_code", "hs6", "year", "tariff_type",
                "rate_pct", "measure", "min_rate", "max_rate", "total_lines", "pref_lines",
                "mfn_lines", "nomenclature", "datatype", "source_system", "extracted_at",
            ],
        ),
        "raw_wb_macro": _load_csv_into_sqlite(
            conn,
            SEED_STAGING / "stg_wb_macro.csv",
            "raw_wb_macro",
            [
                "country_iso3", "country_name", "indicator", "indicator_name",
                "year", "value", "source_system", "extracted_at",
            ],
        ),
        "seed_ref_country_codes": _load_csv_into_sqlite(
            conn,
            DBT_SEEDS / "ref_country_codes.csv",
            "seed_ref_country_codes",
            [
                "code_comtrade", "iso3", "iso2", "country_name_en", "country_name_vi",
                "region", "sub_region", "income_group", "is_aggregate", "has_fta_with_vn", "fta_name",
            ],
        ),
        "seed_ref_cif_fob_factor": _load_csv_into_sqlite(
            conn,
            DBT_SEEDS / "ref_cif_fob_factor.csv",
            "seed_ref_cif_fob_factor",
            ["commodity_group", "transport_route", "factor_pct", "source_reference"],
        ),
        "seed_ref_hs_bridge": _load_csv_into_sqlite(
            conn,
            DBT_SEEDS / "ref_hs_bridge.csv",
            "seed_ref_hs_bridge",
            ["hs6_source", "hs6_target", "from_revision", "to_revision", "note"],
        ),
        "seed_dw_usage_rule": _load_csv_into_sqlite(
            conn,
            DBT_SEEDS / "dw_usage_rule.csv",
            "seed_dw_usage_rule",
            ["rule_id", "applies_to", "rule_vi", "enforcement"],
        ),
    }

    conn.executescript(
        """
        CREATE TABLE stg_comtrade_vn AS
        SELECT
            TRIM(s.batch_id) AS batch_id,
            CAST(TRIM(s.period) AS INTEGER) AS date_key,
            CAST(TRIM(s.year) AS INTEGER) AS calendar_year,
            CAST(TRIM(s.month) AS INTEGER) AS month,
            TRIM(s.flow_code) AS flow_code,
            TRIM(s.reporter_code) AS reporter_code,
            TRIM(s.partner_code) AS partner_code,
            TRIM(s.partner_name) AS partner_name,
            CASE WHEN UPPER(TRIM(s.is_aggregate_partner)) IN ('TRUE','1','T') THEN 1 ELSE 0 END AS is_aggregate_partner,
            COALESCE(b.hs6_target, LPAD(TRIM(s.hs6), 6, '0')) AS hs6_mapped,
            CASE WHEN COALESCE(b.hs6_target, LPAD(TRIM(s.hs6), 6, '0')) = '851713' AND CAST(TRIM(s.year) AS INTEGER) < 2022
                 THEN '851712' ELSE LPAD(TRIM(s.hs6), 6, '0') END AS hs6_reported,
            TRIM(s.commodity_desc) AS commodity_desc,
            NUM_OR_NONE(s.primary_value_usd) AS primary_value_usd,
            NUM_OR_NONE(s.fob_value_usd) AS fob_value_usd,
            NUM_OR_NONE(s.cif_value_usd) AS cif_value_usd,
            NUM_OR_NONE(s.net_wgt_kg) AS net_wgt_kg,
            NUM_OR_NONE(s.qty) AS qty,
            TRIM(s.source_system) AS source_system,
            TRIM(s.extracted_at) AS extracted_at
        FROM raw_vn_reported s
        LEFT JOIN seed_ref_hs_bridge b ON b.hs6_source = LPAD(TRIM(s.hs6), 6, '0')
        WHERE TRIM(s.period) <> '' AND TRIM(s.flow_code) IN ('X','M');

        CREATE TABLE stg_comtrade_mirror AS
        SELECT
            TRIM(s.batch_id) AS batch_id,
            CAST(TRIM(s.period) AS INTEGER) AS date_key,
            CAST(TRIM(s.year) AS INTEGER) AS calendar_year,
            CAST(TRIM(s.month) AS INTEGER) AS month,
            TRIM(s.flow_code) AS flow_code,
            TRIM(s.reporter_code) AS reporter_code,
            TRIM(s.partner_code) AS partner_code_src,
            TRIM(s.reporter_code) AS partner_code_comtrade,
            0 AS is_aggregate_partner,
            LPAD(COALESCE(NULLIF(TRIM(s.maps_to_hs6), ''), b.hs6_target, TRIM(s.hs6)), 6, '0') AS hs6_mapped,
            LPAD(COALESCE(NULLIF(TRIM(s.hs6_original), ''), TRIM(s.hs6)), 6, '0') AS hs6_reported,
            TRIM(s.commodity_desc) AS commodity_desc,
            NUM_OR_NONE(s.primary_value_usd) AS primary_value_usd,
            NUM_OR_NONE(s.fob_value_usd) AS fob_value_usd,
            NUM_OR_NONE(s.cif_value_usd) AS cif_value_usd,
            NUM_OR_NONE(s.net_wgt_kg) AS net_wgt_kg,
            NUM_OR_NONE(s.qty) AS qty,
            TRIM(s.source_system) AS source_system,
            TRIM(s.extracted_at) AS extracted_at,
            CASE WHEN UPPER(TRIM(s.is_reported)) IN ('TRUE','1','T') THEN 1 ELSE 0 END AS is_reported,
            TRIM(s.mirror_role) AS mirror_role
        FROM raw_partner_mirror s
        LEFT JOIN seed_ref_hs_bridge b ON b.hs6_source = LPAD(TRIM(s.hs6), 6, '0')
        WHERE TRIM(s.period) <> '' AND TRIM(s.flow_code) IN ('X','M');

        CREATE TABLE stg_wits_tariff AS
        WITH ranked AS (
            SELECT
                CAST(TRIM(s.year) AS INTEGER) * 100 AS date_key,
                CAST(TRIM(s.year) AS INTEGER) AS calendar_year,
                CASE WHEN TRIM(s.reporter_code) = '704' THEN
                     CASE WHEN TRIM(s.partner_code) IN ('000','0') THEN '0' ELSE TRIM(s.partner_code) END
                     ELSE TRIM(s.reporter_code) END AS partner_code_comtrade,
                LPAD(COALESCE(b.hs6_target, TRIM(s.hs6)), 6, '0') AS hs6_mapped,
                TRIM(s.tariff_type) AS tariff_type_code,
                TRIM(s.combo_type) AS combo_code,
                NUM_OR_NONE(s.rate_pct) AS ad_valorem_pct,
                NULLIF(TRIM(s.measure), '') AS measure_label,
                NUM_OR_NONE(s.min_rate) AS min_rate,
                NUM_OR_NONE(s.max_rate) AS max_rate,
                CAST(NULLIF(TRIM(s.total_lines), '') AS INTEGER) AS total_lines,
                CAST(NULLIF(TRIM(s.mfn_lines), '') AS INTEGER) AS mfn_lines,
                CAST(NULLIF(TRIM(s.pref_lines), '') AS INTEGER) AS pref_lines,
                NULLIF(TRIM(s.datatype), '') AS datatype,
                TRIM(s.source_system) AS source_system,
                TRIM(s.extracted_at) AS extracted_at,
                ROW_NUMBER() OVER (
                    PARTITION BY CAST(TRIM(s.year) AS INTEGER), TRIM(s.reporter_code), TRIM(s.partner_code),
                                 LPAD(COALESCE(b.hs6_target, TRIM(s.hs6)), 6, '0'), TRIM(s.tariff_type), TRIM(s.combo_type)
                    ORDER BY NULLIF(TRIM(s.nomenclature), '') DESC
                ) AS rn
            FROM raw_wits_tariff s
            LEFT JOIN seed_ref_hs_bridge b ON b.hs6_source = LPAD(TRIM(s.hs6), 6, '0')
            WHERE TRIM(s.year) <> ''
        )
        SELECT * FROM ranked WHERE rn = 1;

        CREATE TABLE stg_wb_macro AS
        SELECT
            CAST(TRIM(year) AS INTEGER) * 100 AS date_key,
            CAST(TRIM(year) AS INTEGER) AS calendar_year,
            UPPER(TRIM(country_iso3)) AS country_iso3,
            TRIM(indicator) AS code_wb,
            SCI_ROUND2(value) AS value,
            TRIM(source_system) AS source_system,
            TRIM(extracted_at) AS extracted_at
        FROM raw_wb_macro
        WHERE TRIM(year) <> '' AND TRIM(country_iso3) <> '';

        CREATE TABLE dim_date AS
        WITH months AS (
            SELECT DISTINCT date_key FROM stg_comtrade_vn
            UNION SELECT DISTINCT date_key FROM stg_comtrade_mirror
        ),
        years AS (
            SELECT DISTINCT calendar_year * 100 AS date_key FROM stg_comtrade_vn
            UNION SELECT DISTINCT calendar_year * 100 FROM stg_comtrade_mirror
            UNION SELECT DISTINCT date_key FROM stg_wits_tariff
            UNION SELECT DISTINCT date_key FROM stg_wb_macro
        ),
        combined AS (
            SELECT date_key, 'MONTH' AS granularity FROM months
            UNION SELECT date_key, 'YEAR' AS granularity FROM years
        )
        SELECT
            date_key,
            date_key / 100 AS calendar_year,
            CASE WHEN granularity='MONTH' THEN ((date_key % 100 - 1) / 3 + 1) ELSE NULL END AS quarter,
            CASE WHEN granularity='MONTH' THEN (date_key % 100) ELSE NULL END AS month,
            granularity,
            CASE WHEN granularity='MONTH' THEN CAST(date_key/100 AS TEXT) || '-' || LPAD(date_key%100, 2, '0')
                 ELSE CAST(date_key/100 AS TEXT) END AS date_label
        FROM combined;

        CREATE TABLE dim_partner AS
        WITH codes AS (
            SELECT partner_code AS code FROM stg_comtrade_vn
            UNION SELECT partner_code_comtrade FROM stg_comtrade_mirror
            UNION SELECT '704' UNION SELECT '0'
        ),
        latest_names AS (
            SELECT code, partner_name FROM (
                SELECT partner_code AS code, partner_name,
                       ROW_NUMBER() OVER (PARTITION BY partner_code ORDER BY date_key DESC) AS rn
                FROM stg_comtrade_vn WHERE TRIM(partner_name) <> ''
            ) WHERE rn = 1
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY c.code) AS partner_key,
            c.code AS code_comtrade,
            COALESCE(NULLIF(TRIM(r.country_name_en),''), n.partner_name,
                     CASE c.code WHEN '704' THEN 'Viet Nam' WHEN '0' THEN 'World' END) AS partner_name,
            NULLIF(TRIM(COALESCE(NULLIF(TRIM(r.iso3),''), CASE c.code WHEN '704' THEN 'VNM' ELSE NULL END)), '') AS iso3,
            CASE WHEN c.code='0' OR COALESCE(CAST(r.is_aggregate AS INTEGER),0)=1 THEN 1 ELSE 0 END AS is_aggregate,
            CASE WHEN c.code='704' THEN 1 ELSE 0 END AS is_vietnam,
            NULLIF(TRIM(r.region),'') AS region,
            NULLIF(TRIM(r.sub_region),'') AS sub_region,
            NULLIF(TRIM(r.income_group),'') AS income_group,
            CASE WHEN COALESCE(CAST(r.has_fta_with_vn AS INTEGER),0)=1 THEN 1 ELSE 0 END AS has_fta_with_vn,
            NULLIF(TRIM(r.fta_name),'') AS fta_name
        FROM codes c
        LEFT JOIN latest_names n ON n.code = c.code
        LEFT JOIN seed_ref_country_codes r ON TRIM(r.code_comtrade) = c.code;

        CREATE TABLE dim_commodity AS
        WITH targets AS (
            SELECT DISTINCT hs6_mapped AS hs6 FROM stg_comtrade_vn
            UNION SELECT DISTINCT hs6_mapped FROM stg_comtrade_mirror
        ),
        latest_desc AS (
            SELECT hs6, commodity_desc FROM (
                SELECT hs6_mapped AS hs6, commodity_desc,
                       ROW_NUMBER() OVER (
                           PARTITION BY hs6_mapped
                           ORDER BY CASE WHEN commodity_desc LIKE '[BRIDGED%' THEN 1 ELSE 0 END, date_key DESC
                       ) AS rn
                FROM stg_comtrade_vn WHERE TRIM(commodity_desc) <> ''
            ) WHERE rn = 1
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY t.hs6) AS commodity_key,
            t.hs6,
            SUBSTR(t.hs6,1,4) AS hs4,
            SUBSTR(t.hs6,1,2) AS hs2,
            COALESCE(d.commodity_desc, t.hs6) AS name_en,
            CASE
                WHEN t.hs6 IN ('851713','851762','854231','847330','854442') THEN 'Nhóm 1 · Điện tử – viễn thông'
                WHEN t.hs6 IN ('610910','640399','540761')                      THEN 'Nhóm 2 · Dệt may – giày dép'
                WHEN t.hs6 IN ('090111','090411','100630','080132')             THEN 'Nhóm 3 · Nông sản – thực phẩm'
                WHEN t.hs6 IN ('390120','721049')                                THEN 'Nhóm 4 · Nhựa – công nghiệp nặng'
                ELSE 'Khác'
            END AS commodity_group,
            CASE WHEN b.hs6_target IS NOT NULL THEN 1 ELSE 0 END AS bridge_flag
        FROM targets t
        LEFT JOIN latest_desc d ON d.hs6 = t.hs6
        LEFT JOIN (SELECT DISTINCT hs6_target FROM seed_ref_hs_bridge) b ON b.hs6_target = t.hs6;

        CREATE TABLE dim_flow (flow_key INTEGER PRIMARY KEY, flow_code TEXT, name_vi TEXT);
        INSERT INTO dim_flow VALUES (1,'X','Xuất khẩu'),(2,'M','Nhập khẩu');

        CREATE TABLE dim_perspective (perspective_key INTEGER PRIMARY KEY, code TEXT, label_vi TEXT);
        INSERT INTO dim_perspective VALUES (1,'VN_REPORTED','Việt Nam khai'),(2,'PARTNER_MIRROR','Đối tác khai về VN');

        CREATE TABLE dim_tariff_type (tariff_type_key INTEGER PRIMARY KEY, code TEXT, label_vi TEXT);
        INSERT INTO dim_tariff_type VALUES (1,'MFN','Thuế MFN'),(2,'PREF','Thuế ưu đãi (AHS)');

        CREATE TABLE dim_indicator (indicator_key INTEGER PRIMARY KEY, code_wb TEXT, name_en TEXT, unit TEXT);
        INSERT INTO dim_indicator VALUES
            (1,'NY.GDP.MKTP.CD','GDP (current US$)','USD'),
            (2,'NY.GDP.PCAP.CD','GDP per capita (current US$)','USD'),
            (3,'FP.CPI.TOTL.ZG','Inflation, CPI (annual %)','%'),
            (4,'PA.NUS.FCRF','Official exchange rate','LCU/USD'),
            (5,'NE.TRD.GNFS.ZS','Trade (% of GDP)','%');

        CREATE TABLE dim_audit AS
        WITH b AS (
            SELECT batch_id, source_system, 'stg_comtrade_all_partners_monthly.csv' AS staging_file, MAX(extracted_at) AS extracted_at, COUNT(*) AS row_count FROM stg_comtrade_vn GROUP BY batch_id, source_system
            UNION ALL
            SELECT batch_id, source_system, 'stg_comtrade_partner_mirror.csv', MAX(extracted_at), COUNT(*) FROM stg_comtrade_mirror GROUP BY batch_id, source_system
            UNION ALL
            SELECT 'wits_tariff_batch', MAX(source_system), 'stg_wits_tariff.csv', MAX(extracted_at), COUNT(*) FROM stg_wits_tariff
            UNION ALL
            SELECT 'wb_macro_batch', MAX(source_system), 'stg_wb_macro.csv', MAX(extracted_at), COUNT(*) FROM stg_wb_macro
        )
        SELECT ROW_NUMBER() OVER (ORDER BY source_system, batch_id) AS audit_key, * FROM b;

        CREATE TABLE int_trade_unified AS
        SELECT batch_id, date_key, calendar_year, month, flow_code, reporter_code,
               partner_code AS partner_code_comtrade, partner_code AS partner_code_src,
               is_aggregate_partner, hs6_mapped, hs6_reported, primary_value_usd,
               fob_value_usd, cif_value_usd, net_wgt_kg, qty,
               'VN_REPORTED' AS perspective_code, NULL AS mirror_role, NULL AS is_reported
        FROM stg_comtrade_vn
        UNION ALL
        SELECT batch_id, date_key, calendar_year, month, flow_code, reporter_code,
               partner_code_comtrade, partner_code_src,
               is_aggregate_partner, hs6_mapped, hs6_reported, primary_value_usd,
               fob_value_usd, cif_value_usd, net_wgt_kg, qty,
               'PARTNER_MIRROR' AS perspective_code, mirror_role, is_reported
        FROM stg_comtrade_mirror;

        CREATE TABLE fact_trade AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY u.date_key, dp.partner_key, dc.commodity_key, df.flow_key, dv.perspective_key) AS trade_key,
            dd.date_key, dd.calendar_year, u.month, dp.partner_key, dc.commodity_key,
            df.flow_key, dv.perspective_key, da.audit_key,
            u.primary_value_usd, u.net_wgt_kg, u.qty, u.fob_value_usd, u.cif_value_usd,
            u.hs6_reported, u.reporter_code, u.partner_code_src, u.is_aggregate_partner,
            u.mirror_role, u.is_reported
        FROM int_trade_unified u
        JOIN dim_date dd ON dd.date_key = u.date_key
        JOIN dim_partner dp ON dp.code_comtrade = u.partner_code_comtrade
        JOIN dim_commodity dc ON dc.hs6 = u.hs6_mapped
        JOIN dim_flow df ON df.flow_code = u.flow_code
        JOIN dim_perspective dv ON dv.code = u.perspective_code
        JOIN dim_audit da ON da.batch_id = u.batch_id;

        CREATE TABLE fact_tariff_rate AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY dd.date_key, dp.partner_key, dc.commodity_key, dt.tariff_type_key, s.combo_code) AS tariff_key,
            dd.date_key, dd.calendar_year, dp.partner_key, dc.commodity_key, dt.tariff_type_key,
            da.audit_key, s.combo_code, s.ad_valorem_pct, s.measure_label, s.min_rate, s.max_rate,
            s.total_lines, s.mfn_lines, s.pref_lines, s.datatype
        FROM stg_wits_tariff s
        JOIN dim_date dd ON dd.date_key = s.date_key
        JOIN dim_partner dp ON dp.code_comtrade = s.partner_code_comtrade
        JOIN dim_commodity dc ON dc.hs6 = s.hs6_mapped
        JOIN dim_tariff_type dt ON dt.code = s.tariff_type_code
        JOIN dim_audit da ON da.batch_id = 'wits_tariff_batch';

        CREATE TABLE fact_macro_indicator AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY dd.date_key, dp.partner_key, di.indicator_key) AS macro_key,
            dd.date_key, dd.calendar_year, dp.partner_key, di.indicator_key,
            da.audit_key, s.value
        FROM stg_wb_macro s
        JOIN dim_date dd ON dd.date_key = s.date_key
        JOIN dim_partner dp ON dp.iso3 = s.country_iso3
        JOIN dim_indicator di ON di.code_wb = s.code_wb
        JOIN dim_audit da ON da.batch_id = 'wb_macro_batch';

        CREATE TABLE mart_trade_reconciliation AS
        WITH vn AS (
            SELECT f.date_key, f.partner_key, f.commodity_key, f.flow_key, f.primary_value_usd AS vn_value
            FROM fact_trade f JOIN dim_partner dp ON dp.partner_key = f.partner_key
            WHERE f.perspective_key = 1 AND dp.is_aggregate = 0
        ),
        mi AS (
            SELECT f.date_key, f.partner_key, f.commodity_key,
                   CASE f.flow_key WHEN 1 THEN 2 ELSE 1 END AS flow_key,
                   f.primary_value_usd AS mirror_value_raw,
                   dc.commodity_group, dp.region, dp.sub_region
            FROM fact_trade f
            JOIN dim_commodity dc ON dc.commodity_key = f.commodity_key
            JOIN dim_partner dp ON dp.partner_key = f.partner_key
            WHERE f.perspective_key = 2
        ),
        joined AS (
            SELECT vn.date_key AS v_dk, vn.partner_key AS v_pk, vn.commodity_key AS v_ck, vn.flow_key AS v_fk, vn.vn_value,
                   mi.date_key AS m_dk, mi.partner_key AS m_pk, mi.commodity_key AS m_ck, mi.flow_key AS m_fk,
                   mi.mirror_value_raw, mi.commodity_group AS m_cg, mi.region AS m_reg, mi.sub_region AS m_sub
            FROM vn
            LEFT JOIN mi ON mi.date_key=vn.date_key AND mi.partner_key=vn.partner_key AND mi.commodity_key=vn.commodity_key AND mi.flow_key=vn.flow_key
            UNION ALL
            SELECT NULL, NULL, NULL, NULL, NULL,
                   mi.date_key, mi.partner_key, mi.commodity_key, mi.flow_key,
                   mi.mirror_value_raw, mi.commodity_group, mi.region, mi.sub_region
            FROM mi
            LEFT JOIN vn ON vn.date_key=mi.date_key AND vn.partner_key=mi.partner_key AND vn.commodity_key=mi.commodity_key AND vn.flow_key=mi.flow_key
            WHERE vn.date_key IS NULL
        ),
        base_recon AS (
            SELECT
                COALESCE(j.v_dk, j.m_dk) AS date_key,
                COALESCE(j.v_pk, j.m_pk) AS partner_key,
                COALESCE(j.v_ck, j.m_ck) AS commodity_key,
                COALESCE(j.v_fk, j.m_fk) AS flow_key,
                j.vn_value,
                j.mirror_value_raw,
                COALESCE(CAST(cf.factor_pct AS REAL), 6.0) AS cif_fob_factor_pct,
                CASE WHEN j.mirror_value_raw IS NOT NULL
                     THEN ROUND(j.mirror_value_raw / (1.0 + COALESCE(CAST(cf.factor_pct AS REAL), 6.0)/100.0), 3)
                     ELSE NULL END AS mirror_value_adjusted,
                CASE WHEN j.vn_value IS NOT NULL THEN j.vn_value
                     WHEN j.mirror_value_raw IS NOT NULL
                     THEN ROUND(j.mirror_value_raw / (1.0 + COALESCE(CAST(cf.factor_pct AS REAL), 6.0)/100.0), 3)
                     ELSE NULL END AS best_estimate_usd,
                CASE WHEN j.vn_value IS NULL THEN 'MISSING_VN_REPORTED'
                     WHEN j.mirror_value_raw IS NULL THEN 'MISSING_MIRROR'
                     WHEN j.vn_value = 0 THEN 'HIGH'
                     WHEN ABS(100.0 * (j.mirror_value_raw - j.vn_value) / j.vn_value) <= 10 THEN 'LOW'
                     WHEN ABS(100.0 * (j.mirror_value_raw - j.vn_value) / j.vn_value) <= 30 THEN 'MODERATE'
                     ELSE 'HIGH' END AS discrepancy_level,
                CASE WHEN j.vn_value IS NOT NULL AND j.mirror_value_raw IS NOT NULL THEN 'BOTH_AVAILABLE'
                     WHEN j.vn_value IS NOT NULL THEN 'VN_OFFICIAL_ONLY'
                     WHEN j.mirror_value_raw IS NOT NULL THEN 'MIRROR_ESTIMATED'
                     ELSE 'NO_DATA' END AS data_source_flag
            FROM joined j
            LEFT JOIN seed_ref_cif_fob_factor cf
              ON cf.commodity_group = COALESCE(j.m_cg, 'Mặc định')
             AND cf.transport_route = CASE
                   WHEN COALESCE(j.m_reg,'') = 'Châu Á' OR COALESCE(j.m_sub,'') IN ('Đông Nam Á','Đông Bắc Á','Đông Á','Nam Á','Tây Á','Trung Á') THEN 'INTRA_ASIA'
                   WHEN COALESCE(j.m_reg,'') = 'Châu Mỹ' OR COALESCE(j.m_sub,'') IN ('Bắc Mỹ','Nam Mỹ','Trung Mỹ','Vùng Caribbean') THEN 'TRANS_PACIFIC'
                   WHEN COALESCE(j.m_reg,'') = 'Châu Âu' OR COALESCE(j.m_sub,'') IN ('Tây Âu','Đông Âu','Bắc Âu','Nam Âu') THEN 'ASIA_EUROPE'
                   ELSE 'UNKNOWN' END
        )
        SELECT b.*, dd.calendar_year, dd.date_label, dp.partner_name, dp.region, dc.hs6, dc.commodity_group, df.name_vi AS flow_name
        FROM base_recon b
        JOIN dim_date dd ON dd.date_key = b.date_key
        JOIN dim_partner dp ON dp.partner_key = b.partner_key
        JOIN dim_commodity dc ON dc.commodity_key = b.commodity_key
        JOIN dim_flow df ON df.flow_key = b.flow_key;
        """
    )

    tests = []

    def add_test(tid: str, desc: str, expected, actual, passed: bool):
        tests.append({"id": tid, "desc": desc, "expected": expected, "actual": actual, "status": "PASS" if passed else "FAIL"})

    ft_p1 = conn.execute("SELECT COUNT(*) FROM fact_trade WHERE perspective_key = 1").fetchone()[0]
    ft_p2 = conn.execute("SELECT COUNT(*) FROM fact_trade WHERE perspective_key = 2").fetchone()[0]
    ftr = conn.execute("SELECT COUNT(*) FROM fact_tariff_rate").fetchone()[0]
    fmi = conn.execute("SELECT COUNT(*) FROM fact_macro_indicator").fetchone()[0]
    dp_cnt = conn.execute("SELECT COUNT(*) FROM dim_partner").fetchone()[0]
    dc_cnt = conn.execute("SELECT COUNT(*) FROM dim_commodity").fetchone()[0]
    dd_cnt = conn.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0]
    da_cnt = conn.execute("SELECT COUNT(*) FROM dim_audit").fetchone()[0]
    r_cnt = conn.execute("SELECT COUNT(*) FROM seed_dw_usage_rule").fetchone()[0]

    add_test("V1-FT1", "fact_trade perspective=1 (VN_REPORTED)", 98596, ft_p1, ft_p1 == 98596)
    add_test("V1-FT2", "fact_trade perspective=2 (PARTNER_MIRROR)", 13252, ft_p2, ft_p2 == 13252)
    add_test("V1-TR", "fact_tariff_rate", 419, ftr, ftr == 419)
    add_test("V1-MC", "fact_macro_indicator", 300, fmi, fmi == 300)
    add_test("V1-DP", "dim_partner", 98, dp_cnt, dp_cnt == 98)
    add_test("V1-DC", "dim_commodity", 14, dc_cnt, dc_cnt == 14)
    add_test("V1-DD", "dim_date (120 months + 10 year sentinels)", 130, dd_cnt, dd_cnt == 130)
    add_test("V1-DA", "dim_audit (>=126 batches)", ">=126", da_cnt, da_cnt >= 126)
    add_test("V1-RL", "dw_usage_rule", 5, r_cnt, r_cnt == 5)

    ft_dup = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT date_key, partner_key, commodity_key, flow_key, perspective_key
            FROM fact_trade GROUP BY 1,2,3,4,5 HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    tr_dup = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT date_key, partner_key, commodity_key, tariff_type_key, combo_code
            FROM fact_tariff_rate GROUP BY 1,2,3,4,5 HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    mc_dup = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT date_key, partner_key, indicator_key
            FROM fact_macro_indicator GROUP BY 1,2,3 HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    add_test("V2-FT", "fact_trade grain duplicates", 0, ft_dup, ft_dup == 0)
    add_test("V2-TR", "fact_tariff_rate grain duplicates", 0, tr_dup, tr_dup == 0)
    add_test("V2-MC", "fact_macro_indicator grain duplicates", 0, mc_dup, mc_dup == 0)

    mirror_inv = conn.execute("SELECT COUNT(*) FROM fact_trade WHERE perspective_key = 2 AND partner_code_src <> '704'").fetchone()[0]
    sentinel_viol_ft = conn.execute("SELECT COUNT(*) FROM fact_trade f JOIN dim_date d ON d.date_key=f.date_key WHERE d.granularity <> 'MONTH'").fetchone()[0]
    sentinel_viol_tr = conn.execute("SELECT COUNT(*) FROM fact_tariff_rate f JOIN dim_date d ON d.date_key=f.date_key WHERE d.granularity <> 'YEAR'").fetchone()[0]
    sentinel_viol_mc = conn.execute("SELECT COUNT(*) FROM fact_macro_indicator f JOIN dim_date d ON d.date_key=f.date_key WHERE d.granularity <> 'YEAR'").fetchone()[0]
    add_test("V3-MIR", "Mirror partner_code_src = '704' invariant", 0, mirror_inv, mirror_inv == 0)
    add_test("V3-R5-FT", "fact_trade strictly MONTH granularity", 0, sentinel_viol_ft, sentinel_viol_ft == 0)
    add_test("V3-R5-TR", "fact_tariff_rate strictly YEAR sentinel", 0, sentinel_viol_tr, sentinel_viol_tr == 0)
    add_test("V3-R5-MC", "fact_macro_indicator strictly YEAR sentinel", 0, sentinel_viol_mc, sentinel_viol_mc == 0)

    anchor_partners = conn.execute("""
        SELECT DISTINCT dp.code_comtrade
        FROM fact_tariff_rate ft
        JOIN dim_partner dp ON dp.partner_key = ft.partner_key
        WHERE ft.combo_code = 'ANCHOR'
        ORDER BY 1
    """).fetchall()
    anchor_codes = [r[0] for r in anchor_partners]
    add_test("V3-WITS-ANCHOR", "WITS ANCHOR mapped to World('0') and Japan('392')", ["0", "392"], anchor_codes, anchor_codes == ["0", "392"])

    for flow, hs6, exp in ANCHORS_WORLD_2023:
        row = conn.execute("""
            SELECT SUM(f.primary_value_usd)
            FROM fact_trade f
            JOIN dim_commodity dc ON dc.commodity_key = f.commodity_key
            JOIN dim_partner dp ON dp.partner_key = f.partner_key
            JOIN dim_flow df ON df.flow_key = f.flow_key
            WHERE f.perspective_key = 1 AND dp.code_comtrade = '0'
              AND f.date_key BETWEEN 202301 AND 202312
              AND df.flow_code = ? AND dc.hs6 = ?
        """, (flow, hs6)).fetchone()
        act = row[0] or 0.0
        ok = abs(act - exp) <= exp * 0.0001
        add_test(f"V4-{flow}-{hs6}", f"World 2023 anchor {flow}/{hs6}", round(exp, 2), round(act, 2), ok)

    for rep, flow, hs6, period, exp in ANCHORS_MIRROR_7:
        row = conn.execute("""
            SELECT f.primary_value_usd
            FROM fact_trade f
            JOIN dim_commodity dc ON dc.commodity_key = f.commodity_key
            JOIN dim_partner dp ON dp.partner_key = f.partner_key
            JOIN dim_flow df ON df.flow_key = f.flow_key
            WHERE f.perspective_key = 2 AND dp.code_comtrade = ?
              AND df.flow_code = ? AND dc.hs6 = ? AND f.date_key = ?
        """, (rep, flow, hs6, period)).fetchone()
        act = row[0] if row else None
        ok = act is not None and abs(act - exp) <= 0.01
        add_test(f"V5-{rep}-{flow}-{hs6}-{period}", f"Mirror cell {rep}/{flow}/{hs6}/{period}", exp, act, ok)

    disc_levels = [r[0] for r in conn.execute("SELECT DISTINCT discrepancy_level FROM mart_trade_reconciliation ORDER BY 1").fetchall()]
    rec_2024 = conn.execute("""
        SELECT COUNT(*), ROUND(SUM(best_estimate_usd)/1e6, 2)
        FROM mart_trade_reconciliation
        WHERE calendar_year = 2024 AND data_source_flag = 'MIRROR_ESTIMATED'
    """).fetchone()
    recon_total = conn.execute("SELECT COUNT(*) FROM mart_trade_reconciliation").fetchone()[0]
    add_test("V7-LEVELS", "5 distinct discrepancy levels", 5, len(disc_levels), len(disc_levels) == 5)
    add_test("V7-2024", "2024 Mirror recovery cells > 0", ">0", rec_2024[0], rec_2024[0] > 0)

    recon_by_flag = conn.execute("""
        SELECT data_source_flag, COUNT(*), ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(), 1), ROUND(SUM(best_estimate_usd)/1e6, 2)
        FROM mart_trade_reconciliation GROUP BY data_source_flag ORDER BY 2 DESC
    """).fetchall()

    hhi_rows = conn.execute("""
        WITH yp AS (
            SELECT dd.calendar_year, f.flow_key, dp.partner_key, SUM(f.primary_value_usd) AS pv,
                   SUM(SUM(f.primary_value_usd)) OVER (PARTITION BY dd.calendar_year, f.flow_key) AS yt
            FROM fact_trade f
            JOIN dim_date dd ON dd.date_key = f.date_key
            JOIN dim_partner dp ON dp.partner_key = f.partner_key
            WHERE f.perspective_key = 1 AND dp.is_aggregate = 0 AND dd.granularity = 'MONTH'
            GROUP BY 1,2,3
        ),
        sh AS (
            SELECT calendar_year, flow_key, 100.0*pv/yt AS sp,
                   RANK() OVER (PARTITION BY calendar_year, flow_key ORDER BY pv DESC) AS rk
            FROM yp
        )
        SELECT calendar_year,
               ROUND(SUM(CASE WHEN flow_key=1 THEN POWER(sp,2) ELSE 0 END), 0),
               ROUND(SUM(CASE WHEN flow_key=1 AND rk<=4 THEN sp ELSE 0 END), 2),
               ROUND(SUM(CASE WHEN flow_key=2 THEN POWER(sp,2) ELSE 0 END), 0),
               ROUND(SUM(CASE WHEN flow_key=2 AND rk<=4 THEN sp ELSE 0 END), 2)
        FROM sh GROUP BY calendar_year ORDER BY calendar_year
    """).fetchall()

    balance_top5 = conn.execute("""
        SELECT dp.partner_name,
               ROUND(SUM(CASE WHEN f.flow_key=1 THEN f.primary_value_usd ELSE 0 END)/1e9, 2) AS exp_b,
               ROUND(SUM(CASE WHEN f.flow_key=2 THEN f.primary_value_usd ELSE 0 END)/1e9, 2) AS imp_b,
               ROUND((SUM(CASE WHEN f.flow_key=1 THEN f.primary_value_usd ELSE 0 END)
                    - SUM(CASE WHEN f.flow_key=2 THEN f.primary_value_usd ELSE 0 END))/1e9, 2) AS net_b
        FROM fact_trade f
        JOIN dim_partner dp ON dp.partner_key = f.partner_key
        WHERE f.perspective_key = 1 AND dp.is_aggregate = 0
        GROUP BY dp.partner_name
        ORDER BY (SUM(CASE WHEN f.flow_key=1 THEN f.primary_value_usd ELSE 0 END)
                + SUM(CASE WHEN f.flow_key=2 THEN f.primary_value_usd ELSE 0 END)) DESC
        LIMIT 5
    """).fetchall()

    tariff_bounds = conn.execute("""
        SELECT COUNT(*), MIN(w), MAX(w) FROM (
            SELECT
                SUM(ft.ad_valorem_pct * ft.total_lines) * 1.0 / NULLIF(SUM(ft.total_lines), 0) AS w,
                MIN(ft.ad_valorem_pct) AS min_r,
                MAX(ft.ad_valorem_pct) AS max_r
            FROM fact_tariff_rate ft
            JOIN dim_commodity dc ON dc.commodity_key = ft.commodity_key
            WHERE ft.ad_valorem_pct IS NOT NULL AND ft.total_lines > 0
            GROUP BY ft.calendar_year, ft.partner_key, dc.commodity_group, ft.tariff_type_key, ft.combo_code
        ) WHERE w < 0 OR w < min_r - 0.0001 OR w > max_r + 0.0001
    """).fetchone()
    add_test("V7-TARIFF-R2", "Weighted-Average Bounds Check (>=0 and within [min, max] of components)", 0, tariff_bounds[0], tariff_bounds[0] == 0)

    conn.close()
    return {
        "raw_counts": raw_counts,
        "tests": tests,
        "recon_total": recon_total,
        "recon_2024_cells": rec_2024[0],
        "recon_2024_mil_usd": rec_2024[1],
        "recon_by_flag": recon_by_flag,
        "hhi_rows": hhi_rows,
        "balance_top5": balance_top5,
    }


def write_report(py_errs: list[str], yml_errs: list[str], clean_errs: list[str], cli_errs: list[str], sim: dict) -> bool:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_tests_pass = all(t["status"] == "PASS" for t in sim["tests"])
    overall_ok = not (py_errs or yml_errs or clean_errs or cli_errs) and all_tests_pass

    lines = [
        "# Báo cáo Kiểm chứng Offline — TLCN_DW_XNK (Phương án A)",
        "",
        f"- Thời điểm chạy: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        f"- Kết luận tổng thể: **{'100% PASS' if overall_ok else 'FAIL'}**",
        "",
        "## 1. Kiểm tra Tĩnh (Syntax, YAML, Thuật ngữ & Sạch mã nguồn cũ)",
        "",
        f"- Python `py_compile`: **{'PASS' if not py_errs else 'FAIL'}** ({len(py_errs)} lỗi)",
        f"- YAML / Docker Compose structure: **{'PASS' if not yml_errs else 'FAIL'}** ({len(yml_errs)} lỗi)",
        f"- Quét sạch T-SQL / Microsoft stack / lỗi thuật ngữ: **{'PASS' if not clean_errs else 'FAIL'}** ({len(clean_errs)} phát hiện)",
        f"- CLI Extractors selftest & MinIO dry-run: **{'PASS' if not cli_errs else 'FAIL'}** ({len(cli_errs)} lỗi)",
        "",
    ]
    for title, errs in [("Python errors", py_errs), ("YAML errors", yml_errs), ("Cleanliness findings", clean_errs), ("CLI errors", cli_errs)]:
        if errs:
            lines.append(f"### {title}")
            for e in errs:
                lines.append(f"- `{e}`")
            lines.append("")

    lines += [
        "## 2. Kết quả Kiểm định Kho dữ liệu End-to-End (V0–V7 & Luật R1–R5)",
        "",
        "| Mã Test | Hạng mục | Kỳ vọng | Thực tế | Kết quả |",
        "|---|---|---:|---:|:---:|",
    ]
    for t in sim["tests"]:
        lines.append(f"| `{t['id']}` | {t['desc']} | `{t['expected']}` | `{t['actual']}` | **{t['status']}** |")

    lines += [
        "",
        "## 3. Bộ Số liệu Nhất quán Đã Kiểm chứng (Single Source of Truth)",
        "",
        f"- Tổng số ô trong `mart_trade_reconciliation`: **{sim['recon_total']:,}** ô",
        f"- Năm 2024 phục hồi qua dữ liệu gương (`MIRROR_ESTIMATED`): **{sim['recon_2024_cells']:,}** ô, tương đương **{sim['recon_2024_mil_usd']:,.2f} triệu USD**",
        "",
        "### Phân bổ `data_source_flag` trong `mart_trade_reconciliation`",
        "",
        "| Cờ nguồn dữ liệu | Số ô | Tỷ trọng (%) | Giá trị Best Estimate (Triệu USD) |",
        "|---|---:|---:|---:|",
    ]
    for flag, cnt, pct, musd in sim["recon_by_flag"]:
        lines.append(f"| `{flag}` | {cnt:,} | {pct}% | {musd:,.2f} |")

    lines += [
        "",
        "### Chỉ số tập trung thị trường HHI & CR-4 (2015–2023, trong phạm vi 14 mã HS6)",
        "",
        "| Năm | HHI Xuất khẩu | CR-4 Xuất khẩu (%) | HHI Nhập khẩu | CR-4 Nhập khẩu (%) |",
        "|:---:|---:|---:|---:|---:|",
    ]
    for yr, hhi_x, cr_x, hhi_m, cr_m in sim["hhi_rows"]:
        lines.append(f"| {yr} | {int(hhi_x):,} | {cr_x:.2f}% | {int(hhi_m):,} | {cr_m:.2f}% |")

    lines += [
        "",
        "### Top 5 đối tác theo tổng kim ngạch (2015–2023, trong phạm vi rổ 14 mã HS6 khảo sát)",
        "",
        "| Đối tác | Xuất khẩu (Tỷ USD) | Nhập khẩu (Tỷ USD) | Cán cân ròng rổ 14 HS6 (Tỷ USD) |",
        "|---|---:|---:|---:|",
    ]
    for name, exp_b, imp_b, net_b in sim["balance_top5"]:
        lines.append(f"| {name} | {exp_b:,.2f} | {imp_b:,.2f} | {net_b:+,.2f} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return overall_ok


def main() -> int:
    py_errs = check_python_compile()
    yml_errs = check_yaml_structure()
    clean_errs = check_cleanliness()
    cli_errs = check_cli_selftests()
    sim = run_dwh_simulation()
    ok = write_report(py_errs, yml_errs, clean_errs, cli_errs, sim)

    print(f"Python compile errors : {len(py_errs)}")
    print(f"YAML structure errors : {len(yml_errs)}")
    print(f"Cleanliness findings  : {len(clean_errs)}")
    print(f"CLI selftest errors   : {len(cli_errs)}")
    passed = sum(1 for t in sim["tests"] if t["status"] == "PASS")
    print(f"DWH Acceptance Tests  : {passed}/{len(sim['tests'])} PASS")
    print(f"Report written to     : {REPORT_PATH}")
    if clean_errs:
        for f in clean_errs[:10]:
            print("  CLEANLINESS:", f)
    if not ok:
        for t in sim["tests"]:
            if t["status"] != "PASS":
                print("  FAILED TEST:", t)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
