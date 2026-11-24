SELECT
    f.trade_key,
    f.reporter_code,
    f.partner_code_src
FROM {{ ref('fact_trade') }} f
JOIN {{ ref('dim_perspective') }} dp ON dp.perspective_key = f.perspective_key
WHERE dp.code = 'PARTNER_MIRROR'
  AND f.partner_code_src <> '704'
