-- silver/stg_order_items.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Silver: Cleaned order_items records.
--
-- Cleaning applied:
--   1. Flag negative quantities as returns (is_return = true)
--   2. Use ABS(quantity) for all calculations
--   3. Filter orphan rows (order_id NOT in stg_orders)
--   4. Recalculate total_amount for consistency
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='silver') }}

WITH valid_orders AS (
    SELECT order_id FROM {{ ref('stg_orders') }}
),

cleaned AS (
    SELECT
        oi.order_item_id,
        oi.order_id,
        oi.product_id,

        -- Flag returns (negative qty)
        CASE WHEN oi.quantity < 0 THEN TRUE ELSE FALSE END      AS is_return,
        ABS(oi.quantity)                                        AS quantity,

        oi.unit_price,
        oi.discount_pct,

        -- Recalculate total for consistency
        ROUND(ABS(oi.quantity) * oi.unit_price * (1 - oi.discount_pct / 100), 2)
                                                                AS total_amount,
        oi.created_at,
        oi._ingested_at,
        oi._source,
        NOW()                                                   AS cleaned_at
    FROM {{ ref('bronze_order_items') }} oi
    -- Remove orphan rows (Fix: referential integrity)
    INNER JOIN valid_orders vo ON oi.order_id = vo.order_id
)

SELECT * FROM cleaned
