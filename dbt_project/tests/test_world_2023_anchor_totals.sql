WITH anchors(flow_code, hs6, expected_usd) AS (
    VALUES
        ('X', '851713', 26460317776.0::NUMERIC),
        ('X', '640399',  4991396908.0::NUMERIC),
        ('X', '100630',  4060727368.0::NUMERIC),
        ('X', '090111',  2977954667.0::NUMERIC),
        ('X', '080132',  2916825905.0::NUMERIC),
        ('X', '854442',  2062142409.0::NUMERIC),
        ('X', '610910',  1401669880.0::NUMERIC),
        ('X', '090411',   683211713.0::NUMERIC),
        ('M', '854231', 17797673474.0::NUMERIC),
        ('M', '847330',   928122689.0::NUMERIC),
        ('M', '851762',   841528135.0::NUMERIC),
        ('M', '390120',   827368947.0::NUMERIC),
        ('M', '540761',   484289054.0::NUMERIC),
        ('M', '721049',   137743539.0::NUMERIC)
),
actuals AS (
    SELECT
        df.flow_code,
        dc.hs6,
        SUM(f.primary_value_usd) AS actual_usd
    FROM {{ ref('fact_trade') }} f
    JOIN {{ ref('dim_commodity') }} dc ON dc.commodity_key = f.commodity_key
    JOIN {{ ref('dim_partner') }} dp   ON dp.partner_key   = f.partner_key
    JOIN {{ ref('dim_flow') }} df      ON df.flow_key      = f.flow_key
    WHERE f.perspective_key = 1
      AND dp.code_comtrade = '0'
      AND f.date_key BETWEEN 202301 AND 202312
    GROUP BY df.flow_code, dc.hs6
)
SELECT
    a.flow_code,
    a.hs6,
    a.expected_usd,
    COALESCE(x.actual_usd, 0) AS actual_usd
FROM anchors a
LEFT JOIN actuals x
  ON x.flow_code = a.flow_code
 AND x.hs6 = a.hs6
WHERE x.actual_usd IS NULL
   OR ABS(x.actual_usd - a.expected_usd) > a.expected_usd * 0.0001
