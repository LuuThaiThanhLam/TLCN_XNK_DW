DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_date') THEN
        ALTER TABLE core_dwh.dim_date ADD CONSTRAINT pk_dim_date PRIMARY KEY (date_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_partner') THEN
        ALTER TABLE core_dwh.dim_partner ADD CONSTRAINT pk_dim_partner PRIMARY KEY (partner_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_commodity') THEN
        ALTER TABLE core_dwh.dim_commodity ADD CONSTRAINT pk_dim_commodity PRIMARY KEY (commodity_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_flow') THEN
        ALTER TABLE core_dwh.dim_flow ADD CONSTRAINT pk_dim_flow PRIMARY KEY (flow_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_perspective') THEN
        ALTER TABLE core_dwh.dim_perspective ADD CONSTRAINT pk_dim_perspective PRIMARY KEY (perspective_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_tariff_type') THEN
        ALTER TABLE core_dwh.dim_tariff_type ADD CONSTRAINT pk_dim_tariff_type PRIMARY KEY (tariff_type_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_indicator') THEN
        ALTER TABLE core_dwh.dim_indicator ADD CONSTRAINT pk_dim_indicator PRIMARY KEY (indicator_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_dim_audit') THEN
        ALTER TABLE core_dwh.dim_audit ADD CONSTRAINT pk_dim_audit PRIMARY KEY (audit_key);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_fact_trade') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT pk_fact_trade PRIMARY KEY (trade_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_fact_tariff_rate') THEN
        ALTER TABLE core_dwh.fact_tariff_rate ADD CONSTRAINT pk_fact_tariff_rate PRIMARY KEY (tariff_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_fact_macro_indicator') THEN
        ALTER TABLE core_dwh.fact_macro_indicator ADD CONSTRAINT pk_fact_macro_indicator PRIMARY KEY (macro_key);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_trade_date') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT fk_fact_trade_date FOREIGN KEY (date_key) REFERENCES core_dwh.dim_date (date_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_trade_partner') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT fk_fact_trade_partner FOREIGN KEY (partner_key) REFERENCES core_dwh.dim_partner (partner_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_trade_commodity') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT fk_fact_trade_commodity FOREIGN KEY (commodity_key) REFERENCES core_dwh.dim_commodity (commodity_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_trade_flow') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT fk_fact_trade_flow FOREIGN KEY (flow_key) REFERENCES core_dwh.dim_flow (flow_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_trade_perspective') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT fk_fact_trade_perspective FOREIGN KEY (perspective_key) REFERENCES core_dwh.dim_perspective (perspective_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_trade_audit') THEN
        ALTER TABLE core_dwh.fact_trade ADD CONSTRAINT fk_fact_trade_audit FOREIGN KEY (audit_key) REFERENCES core_dwh.dim_audit (audit_key);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_tariff_date') THEN
        ALTER TABLE core_dwh.fact_tariff_rate ADD CONSTRAINT fk_fact_tariff_date FOREIGN KEY (date_key) REFERENCES core_dwh.dim_date (date_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_tariff_partner') THEN
        ALTER TABLE core_dwh.fact_tariff_rate ADD CONSTRAINT fk_fact_tariff_partner FOREIGN KEY (partner_key) REFERENCES core_dwh.dim_partner (partner_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_tariff_commodity') THEN
        ALTER TABLE core_dwh.fact_tariff_rate ADD CONSTRAINT fk_fact_tariff_commodity FOREIGN KEY (commodity_key) REFERENCES core_dwh.dim_commodity (commodity_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_tariff_type') THEN
        ALTER TABLE core_dwh.fact_tariff_rate ADD CONSTRAINT fk_fact_tariff_type FOREIGN KEY (tariff_type_key) REFERENCES core_dwh.dim_tariff_type (tariff_type_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_tariff_audit') THEN
        ALTER TABLE core_dwh.fact_tariff_rate ADD CONSTRAINT fk_fact_tariff_audit FOREIGN KEY (audit_key) REFERENCES core_dwh.dim_audit (audit_key);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_macro_date') THEN
        ALTER TABLE core_dwh.fact_macro_indicator ADD CONSTRAINT fk_fact_macro_date FOREIGN KEY (date_key) REFERENCES core_dwh.dim_date (date_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_macro_partner') THEN
        ALTER TABLE core_dwh.fact_macro_indicator ADD CONSTRAINT fk_fact_macro_partner FOREIGN KEY (partner_key) REFERENCES core_dwh.dim_partner (partner_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_macro_indicator') THEN
        ALTER TABLE core_dwh.fact_macro_indicator ADD CONSTRAINT fk_fact_macro_indicator FOREIGN KEY (indicator_key) REFERENCES core_dwh.dim_indicator (indicator_key);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fact_macro_audit') THEN
        ALTER TABLE core_dwh.fact_macro_indicator ADD CONSTRAINT fk_fact_macro_audit FOREIGN KEY (audit_key) REFERENCES core_dwh.dim_audit (audit_key);
    END IF;
END $$;
