DELETE FROM mart.sum_budget_burn_monthly
WHERE year_month >= :from_month
  AND year_month <= :to_month;

INSERT INTO mart.sum_budget_burn_monthly (
    year_month,
    budget_amount,
    actual_spend_amount,
    variance_amount,
    burn_rate_pct,
    ytd_actual_spend,
    created_ts
)
WITH monthly_spend AS (
    SELECT
        TO_CHAR(gr_date, 'YYYYMM')::INTEGER AS year_month,
        SUM(COALESCE(received_value, 0)) AS actual_spend_amount
    FROM core.fact_goods_receipt_line
    WHERE TO_CHAR(gr_date, 'YYYYMM')::INTEGER >= :from_month
      AND TO_CHAR(gr_date, 'YYYYMM')::INTEGER <= :to_month
    GROUP BY TO_CHAR(gr_date, 'YYYYMM')::INTEGER
)
SELECT
    year_month,
    NULL AS budget_amount,
    actual_spend_amount,
    NULL AS variance_amount,
    NULL AS burn_rate_pct,
    SUM(actual_spend_amount) OVER (ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_actual_spend,
    NOW()
FROM monthly_spend;
