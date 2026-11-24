SELECT
    f.tariff_key,
    f.date_key,
    dd.granularity
FROM {{ ref('fact_tariff_rate') }} f
JOIN {{ ref('dim_date') }} dd ON dd.date_key = f.date_key
WHERE (f.date_key % 100) <> 0
   OR dd.granularity <> 'YEAR'
