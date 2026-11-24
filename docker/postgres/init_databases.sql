SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

SELECT 'CREATE DATABASE metabase'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec

\connect tlcn_dwh

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS core_dwh;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS snapshots;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS raw.vn_reported (
    batch_id               TEXT,
    period                 TEXT,
    year                   TEXT,
    month                  TEXT,
    flow_code              TEXT,
    reporter_code          TEXT,
    partner_code           TEXT,
    partner_name           TEXT,
    is_aggregate_partner   TEXT,
    hs6                    TEXT,
    commodity_desc         TEXT,
    primary_value_usd      TEXT,
    fob_value_usd          TEXT,
    cif_value_usd          TEXT,
    net_wgt_kg             TEXT,
    qty                    TEXT,
    source_system          TEXT,
    reporting_perspective  TEXT,
    extracted_at           TEXT
);

CREATE TABLE IF NOT EXISTS raw.partner_mirror (
    batch_id               TEXT,
    period                 TEXT,
    year                   TEXT,
    month                  TEXT,
    flow_code              TEXT,
    reporter_code          TEXT,
    partner_code           TEXT,
    partner_name           TEXT,
    is_aggregate_partner   TEXT,
    hs6                    TEXT,
    commodity_desc         TEXT,
    primary_value_usd      TEXT,
    fob_value_usd          TEXT,
    cif_value_usd          TEXT,
    net_wgt_kg             TEXT,
    qty                    TEXT,
    source_system          TEXT,
    reporting_perspective  TEXT,
    extracted_at           TEXT,
    is_reported            TEXT,
    mirror_role            TEXT,
    hs6_original           TEXT,
    maps_to_hs6            TEXT,
    hs_nomenclature        TEXT
);

CREATE TABLE IF NOT EXISTS raw.wits_tariff (
    combo_type             TEXT,
    reporter_code          TEXT,
    partner_code           TEXT,
    hs6                    TEXT,
    year                   TEXT,
    tariff_type            TEXT,
    rate_pct               TEXT,
    measure                TEXT,
    min_rate               TEXT,
    max_rate               TEXT,
    total_lines            TEXT,
    pref_lines             TEXT,
    mfn_lines              TEXT,
    nomenclature           TEXT,
    datatype               TEXT,
    source_system          TEXT,
    extracted_at           TEXT
);

CREATE TABLE IF NOT EXISTS raw.wb_macro (
    country_iso3           TEXT,
    country_name           TEXT,
    indicator              TEXT,
    indicator_name         TEXT,
    year                   TEXT,
    value                  TEXT,
    source_system          TEXT,
    extracted_at           TEXT
);

CREATE TABLE IF NOT EXISTS audit.etl_batch_log (
    log_id                 BIGSERIAL PRIMARY KEY,
    run_id                 VARCHAR(128) NOT NULL,
    dag_id                 VARCHAR(128) NOT NULL,
    source_table           VARCHAR(100) NOT NULL,
    minio_object_key       VARCHAR(256) NULL,
    file_sha256            CHAR(64)     NULL,
    row_count              BIGINT       NOT NULL DEFAULT 0,
    status                 VARCHAR(32)  NOT NULL,
    notes                  TEXT         NULL,
    loaded_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
