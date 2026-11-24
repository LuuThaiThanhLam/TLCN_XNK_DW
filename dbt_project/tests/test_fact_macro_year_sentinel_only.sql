SELECT
    f.macro_key,
    f.date_key,
    dd.granularity
FROM {{ ref('fact_macro_indicator') }} f
JOIN {{ ref('dim_date') }} dd ON dd.date_key = f.date_key
WHERE (f.date_key % 100) <> 0
   OR dd.granularity <> 'YEAR'
