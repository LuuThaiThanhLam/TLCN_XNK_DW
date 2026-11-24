WITH cells(rep, flow_code, hs6, period, expected_usd) AS (
    VALUES
        ('392', 'M', '090111', 202401,  35660719.503::NUMERIC),
        ('842', 'M', '090111', 202301,  37790801.000::NUMERIC),
        ('276', 'M', '090111', 202301,  38271554.955::NUMERIC),
        ('156', 'X', '851762', 202301,  29945226.000::NUMERIC),
        ('410', 'X', '854231', 202301, 217401413.000::NUMERIC),
        ('156', 'X', '851762', 202401,  62727085.000::NUMERIC),
        ('410', 'X', '854231', 202401, 412589570.000::NUMERIC)
)
SELECT
    c.rep,
    c.flow_code,
    c.hs6,
    c.period,
    c.expected_usd,
    f.primary_value_usd AS actual_usd
FROM cells c
LEFT JOIN {{ ref('dim_partner') }} dp   ON dp.code_comtrade = c.rep
LEFT JOIN {{ ref('dim_commodity') }} dc ON dc.hs6 = c.hs6
LEFT JOIN {{ ref('dim_flow') }} df      ON df.flow_code = c.flow_code
LEFT JOIN {{ ref('fact_trade') }} f
       ON f.perspective_key = 2
      AND f.partner_key = dp.partner_key
      AND f.commodity_key = dc.commodity_key
      AND f.flow_key = df.flow_key
      AND f.date_key = c.period
WHERE f.primary_value_usd IS NULL
   OR ABS(f.primary_value_usd - c.expected_usd) > 0.01
