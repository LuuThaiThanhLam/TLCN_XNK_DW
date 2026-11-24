SELECT
    date_key,
    partner_key,
    indicator_key,
    COUNT(*) AS row_cnt
FROM {{ ref('fact_macro_indicator') }}
GROUP BY date_key, partner_key, indicator_key
HAVING COUNT(*) > 1
