{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['indicator_key'], 'unique': True},
            {'columns': ['code_wb'], 'unique': True}
        ]
    )
}}

SELECT 1::SMALLINT AS indicator_key, 'NY.GDP.MKTP.CD'::VARCHAR(20) AS code_wb, 'GDP (current US$)'::VARCHAR(120) AS name_en, 'USD'::VARCHAR(10) AS unit
UNION ALL
SELECT 2::SMALLINT, 'NY.GDP.PCAP.CD'::VARCHAR(20), 'GDP per capita (current US$)'::VARCHAR(120), 'USD'::VARCHAR(10)
UNION ALL
SELECT 3::SMALLINT, 'FP.CPI.TOTL.ZG'::VARCHAR(20), 'Inflation, CPI (annual %)'::VARCHAR(120), '%'::VARCHAR(10)
UNION ALL
SELECT 4::SMALLINT, 'PA.NUS.FCRF'::VARCHAR(20), 'Official exchange rate (LCU per US$, period average)'::VARCHAR(120), 'LCU/USD'::VARCHAR(10)
UNION ALL
SELECT 5::SMALLINT, 'NE.TRD.GNFS.ZS'::VARCHAR(20), 'Trade (% of GDP)'::VARCHAR(120), '%'::VARCHAR(10)
