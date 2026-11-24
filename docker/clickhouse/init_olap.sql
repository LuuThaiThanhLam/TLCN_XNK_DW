CREATE DATABASE IF NOT EXISTS olap_xnk;

CREATE TABLE IF NOT EXISTS olap_xnk.dim_date (
    date_key       Int32,
    calendar_year  Int16,
    quarter        Nullable(UInt8),
    month          Nullable(UInt8),
    granularity    LowCardinality(String),
    date_label     String
) ENGINE = MergeTree()
ORDER BY (date_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_partner (
    partner_key     Int32,
    code_comtrade   String,
    partner_name    String,
    iso3            Nullable(String),
    is_aggregate    UInt8,
    is_vietnam      UInt8,
    region          LowCardinality(Nullable(String)),
    sub_region      LowCardinality(Nullable(String)),
    income_group    LowCardinality(Nullable(String)),
    has_fta_with_vn UInt8,
    fta_name        Nullable(String)
) ENGINE = MergeTree()
ORDER BY (partner_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_commodity (
    commodity_key   Int32,
    hs6             FixedString(6),
    hs4             FixedString(4),
    hs2             FixedString(2),
    name_en         String,
    commodity_group LowCardinality(String),
    bridge_flag     UInt8,
    bridge_note     Nullable(String)
) ENGINE = MergeTree()
ORDER BY (commodity_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_flow (
    flow_key            UInt8,
    flow_code           FixedString(1),
    name_vi             String,
    vn_side_meaning     String,
    mirror_side_meaning String
) ENGINE = MergeTree()
ORDER BY (flow_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_perspective (
    perspective_key  UInt8,
    code             LowCardinality(String),
    label_vi         String,
    reliability_note String
) ENGINE = MergeTree()
ORDER BY (perspective_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_tariff_type (
    tariff_type_key UInt8,
    code            LowCardinality(String),
    label_vi        String,
    coverage_note   String
) ENGINE = MergeTree()
ORDER BY (tariff_type_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_indicator (
    indicator_key UInt8,
    code_wb       String,
    name_en       String,
    unit          String
) ENGINE = MergeTree()
ORDER BY (indicator_key);

CREATE TABLE IF NOT EXISTS olap_xnk.dim_audit (
    audit_key     Int32,
    batch_id      String,
    source_system String,
    staging_file  String,
    extracted_at  Nullable(String),
    row_count     Int64
) ENGINE = MergeTree()
ORDER BY (audit_key);

CREATE TABLE IF NOT EXISTS olap_xnk.fact_trade (
    trade_key            Int64,
    date_key             Int32,
    calendar_year        Int16,
    month                UInt8,
    partner_key          Int32,
    commodity_key        Int32,
    flow_key             UInt8,
    perspective_key      UInt8,
    audit_key            Int32,
    primary_value_usd    Decimal(18, 3),
    net_wgt_kg           Nullable(Decimal(18, 3)),
    qty                  Nullable(Decimal(18, 3)),
    fob_value_usd        Nullable(Decimal(18, 3)),
    cif_value_usd        Nullable(Decimal(18, 3)),
    hs6_reported         FixedString(6),
    reporter_code        String,
    partner_code_src     String,
    is_aggregate_partner UInt8,
    mirror_role          LowCardinality(Nullable(String)),
    is_reported          Nullable(UInt8)
) ENGINE = MergeTree()
PARTITION BY calendar_year
ORDER BY (perspective_key, flow_key, partner_key, commodity_key, date_key);

CREATE TABLE IF NOT EXISTS olap_xnk.fact_tariff_rate (
    tariff_key      Int64,
    date_key        Int32,
    calendar_year   Int16,
    partner_key     Int32,
    commodity_key   Int32,
    tariff_type_key UInt8,
    audit_key       Int32,
    combo_code      LowCardinality(String),
    ad_valorem_pct  Nullable(Decimal(9, 4)),
    measure_label   Nullable(String),
    min_rate        Nullable(Decimal(9, 4)),
    max_rate        Nullable(Decimal(9, 4)),
    total_lines     Nullable(Int32),
    mfn_lines       Nullable(Int32),
    pref_lines      Nullable(Int32),
    datatype        LowCardinality(Nullable(String))
) ENGINE = MergeTree()
ORDER BY (date_key, partner_key, commodity_key, tariff_type_key, combo_code);

CREATE TABLE IF NOT EXISTS olap_xnk.fact_macro_indicator (
    macro_key     Int64,
    date_key      Int32,
    calendar_year Int16,
    partner_key   Int32,
    indicator_key UInt8,
    audit_key     Int32,
    value         Nullable(Decimal(18, 2))
) ENGINE = MergeTree()
ORDER BY (date_key, partner_key, indicator_key);

CREATE TABLE IF NOT EXISTS olap_xnk.mart_trade_reconciliation (
    date_key              Int32,
    calendar_year         Int16,
    date_label            String,
    partner_key           Int32,
    partner_name          String,
    region                LowCardinality(Nullable(String)),
    sub_region            LowCardinality(Nullable(String)),
    commodity_key         Int32,
    hs6                   FixedString(6),
    commodity_group       LowCardinality(String),
    flow_key              UInt8,
    flow_name             String,
    vn_value              Nullable(Decimal(18, 3)),
    mirror_value_raw      Nullable(Decimal(18, 3)),
    cif_fob_factor_pct    Decimal(5, 2),
    mirror_value_adjusted Nullable(Decimal(18, 3)),
    best_estimate_usd     Nullable(Decimal(18, 3)),
    abs_diff_usd          Nullable(Decimal(18, 3)),
    pct_diff_vs_vn        Nullable(Decimal(12, 4)),
    discrepancy_level     LowCardinality(String),
    data_source_flag      LowCardinality(String),
    reconciliation_note   Nullable(String)
) ENGINE = MergeTree()
PARTITION BY calendar_year
ORDER BY (discrepancy_level, partner_key, commodity_key, date_key);
