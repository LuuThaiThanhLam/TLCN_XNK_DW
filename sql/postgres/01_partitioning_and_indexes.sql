CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_partitioned (
    trade_key            BIGINT         NOT NULL,
    date_key             INTEGER        NOT NULL,
    calendar_year        SMALLINT       NOT NULL,
    month                SMALLINT       NOT NULL,
    partner_key          INTEGER        NOT NULL,
    commodity_key        INTEGER        NOT NULL,
    flow_key             SMALLINT       NOT NULL,
    perspective_key      SMALLINT       NOT NULL,
    audit_key            INTEGER        NOT NULL,
    primary_value_usd    NUMERIC(18, 3) NOT NULL,
    net_wgt_kg           NUMERIC(18, 3) NULL,
    qty                  NUMERIC(18, 3) NULL,
    fob_value_usd        NUMERIC(18, 3) NULL,
    cif_value_usd        NUMERIC(18, 3) NULL,
    hs6_reported         CHAR(6)        NOT NULL,
    reporter_code        VARCHAR(10)    NOT NULL,
    partner_code_src     VARCHAR(10)    NOT NULL,
    is_aggregate_partner BOOLEAN        NOT NULL,
    mirror_role          VARCHAR(20)    NULL,
    is_reported          BOOLEAN        NULL
) PARTITION BY RANGE (calendar_year);

CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2015 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2015) TO (2016);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2016 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2016) TO (2017);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2017 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2017) TO (2018);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2018 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2018) TO (2019);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2019 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2019) TO (2020);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2020 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2020) TO (2021);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2021 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2021) TO (2022);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2022 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2022) TO (2023);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2023 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2023) TO (2024);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2024 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2024) TO (2025);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_p2025 PARTITION OF core_dwh.fact_trade_partitioned FOR VALUES FROM (2025) TO (2026);
CREATE TABLE IF NOT EXISTS core_dwh.fact_trade_pdefault PARTITION OF core_dwh.fact_trade_partitioned DEFAULT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ftp_grain
    ON core_dwh.fact_trade_partitioned (calendar_year, date_key, partner_key, commodity_key, flow_key, perspective_key);

CREATE INDEX IF NOT EXISTS ix_ftp_comm_date
    ON core_dwh.fact_trade_partitioned (commodity_key, date_key)
    INCLUDE (primary_value_usd, perspective_key);

CREATE INDEX IF NOT EXISTS ix_ftp_partner_date
    ON core_dwh.fact_trade_partitioned (partner_key, date_key)
    INCLUDE (primary_value_usd, perspective_key);

CREATE INDEX IF NOT EXISTS ix_ftp_date_brin
    ON core_dwh.fact_trade_partitioned USING BRIN (date_key);

TRUNCATE TABLE core_dwh.fact_trade_partitioned;

INSERT INTO core_dwh.fact_trade_partitioned (
    trade_key, date_key, calendar_year, month, partner_key, commodity_key,
    flow_key, perspective_key, audit_key, primary_value_usd, net_wgt_kg,
    qty, fob_value_usd, cif_value_usd, hs6_reported, reporter_code,
    partner_code_src, is_aggregate_partner, mirror_role, is_reported
)
SELECT
    trade_key, date_key, calendar_year, month, partner_key, commodity_key,
    flow_key, perspective_key, audit_key, primary_value_usd, net_wgt_kg,
    qty, fob_value_usd, cif_value_usd, hs6_reported, reporter_code,
    partner_code_src, is_aggregate_partner, mirror_role, is_reported
FROM core_dwh.fact_trade;

ANALYZE core_dwh.fact_trade;
ANALYZE core_dwh.fact_trade_partitioned;
