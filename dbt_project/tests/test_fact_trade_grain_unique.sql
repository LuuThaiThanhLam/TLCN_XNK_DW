SELECT
    date_key,
    partner_key,
    commodity_key,
    flow_key,
    perspective_key,
    COUNT(*) AS row_cnt
FROM {{ ref('fact_trade') }}
GROUP BY date_key, partner_key, commodity_key, flow_key, perspective_key
HAVING COUNT(*) > 1
