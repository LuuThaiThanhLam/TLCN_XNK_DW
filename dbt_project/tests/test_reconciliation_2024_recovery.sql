WITH summary AS (
    SELECT
        COUNT(DISTINCT discrepancy_level) AS n_levels,
        SUM(CASE WHEN calendar_year = 2024 AND data_source_flag = 'MIRROR_ESTIMATED' THEN 1 ELSE 0 END) AS n_2024_recovered
    FROM {{ ref('mart_trade_reconciliation') }}
)
SELECT *
FROM summary
WHERE n_levels <> 5
   OR n_2024_recovered <= 0
