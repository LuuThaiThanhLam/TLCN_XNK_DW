SELECT
    date_key,
    partner_key,
    commodity_key,
    tariff_type_key,
    combo_code,
    COUNT(*) AS row_cnt
FROM {{ ref('fact_tariff_rate') }}
GROUP BY date_key, partner_key, commodity_key, tariff_type_key, combo_code
HAVING COUNT(*) > 1
