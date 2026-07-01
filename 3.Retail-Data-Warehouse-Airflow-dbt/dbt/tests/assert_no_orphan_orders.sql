-- tests/assert_no_orphan_orders.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Custom Singular Test: No orphan order_items in the GOLD layer.
-- (Orphans should have been filtered in silver — this confirms it.)
-- Returns rows if the test FAILS (i.e., orphans found → test error).
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    oi.order_item_id,
    oi.order_id,
    'Orphan order_item — no matching order in fact_orders' AS failure_reason
FROM {{ ref('stg_order_items') }} oi
LEFT JOIN {{ ref('fact_orders') }} fo ON oi.order_id = fo.order_id
WHERE fo.order_id IS NULL
