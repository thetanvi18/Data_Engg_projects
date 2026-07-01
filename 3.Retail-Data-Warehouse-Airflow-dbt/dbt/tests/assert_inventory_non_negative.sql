-- tests/assert_inventory_non_negative.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Custom Singular Test: No negative inventory quantities in silver.
-- The silver layer should clamp all negatives to 0.
-- Any remaining negatives = cleaning logic failure.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    inventory_id,
    product_id,
    quantity_on_hand,
    'Negative inventory quantity survived silver cleaning' AS failure_reason
FROM {{ ref('stg_inventory') }}
WHERE quantity_on_hand < 0
