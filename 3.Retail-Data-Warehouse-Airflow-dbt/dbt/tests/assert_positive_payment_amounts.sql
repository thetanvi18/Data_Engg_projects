-- tests/assert_positive_payment_amounts.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Custom Singular Test: All successful payments must have amount > 0.
-- Zero-amount payments should only have status 'Pending' or be flagged
-- as free orders. Successful payments with amount = 0 indicate a bug.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    payment_id,
    order_id,
    amount,
    payment_status,
    'Successful payment with zero amount — data anomaly' AS failure_reason
FROM {{ ref('fact_payments') }}
WHERE payment_status = 'Success'
  AND amount = 0
  AND is_free_order = FALSE
