WITH component_bounds AS (
    SELECT
        dd.calendar_year,
        ft.partner_key,
        dc.commodity_group,
        dtt.code AS tariff_type_code,
        ft.combo_code,
        MIN(ft.ad_valorem_pct) AS min_component_pct,
        MAX(ft.ad_valorem_pct) AS max_component_pct
    FROM {{ ref('fact_tariff_rate') }} ft
    JOIN {{ ref('dim_date') }} dd         ON dd.date_key        = ft.date_key
    JOIN {{ ref('dim_commodity') }} dc    ON dc.commodity_key   = ft.commodity_key
    JOIN {{ ref('dim_tariff_type') }} dtt ON dtt.tariff_type_key = ft.tariff_type_key
    WHERE ft.ad_valorem_pct IS NOT NULL
      AND dd.granularity = 'YEAR'
      AND COALESCE(ft.total_lines, 0) > 0
    GROUP BY
        dd.calendar_year,
        ft.partner_key,
        dc.commodity_group,
        dtt.code,
        ft.combo_code
)
SELECT
    m.calendar_year,
    m.partner_key,
    m.partner_name,
    m.commodity_group,
    m.tariff_type_code,
    m.combo_code,
    m.weighted_avg_tariff_pct,
    b.min_component_pct,
    b.max_component_pct
FROM {{ ref('mart_tariff_weighted') }} m
LEFT JOIN component_bounds b
  ON b.calendar_year    = m.calendar_year
 AND b.partner_key      = m.partner_key
 AND b.commodity_group  = m.commodity_group
 AND b.tariff_type_code = m.tariff_type_code
 AND b.combo_code       = m.combo_code
WHERE m.weighted_avg_tariff_pct IS NOT NULL
  AND (
      b.min_component_pct IS NULL
      OR m.weighted_avg_tariff_pct < 0
      OR m.weighted_avg_tariff_pct < b.min_component_pct - 0.0001
      OR m.weighted_avg_tariff_pct > b.max_component_pct + 0.0001
  )
