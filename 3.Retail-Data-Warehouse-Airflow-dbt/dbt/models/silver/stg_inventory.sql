-- silver/stg_inventory.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Silver: Cleaned inventory records.
--
-- Cleaning applied:
--   1. Clamp negative quantity_on_hand to 0 (oversell bug fix)
--   2. Flag originally negative records (is_oversold = true)
--   3. Deduplicate by product_id (keep latest updated_at)
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='silver') }}

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY updated_at DESC
        ) AS rn
    FROM {{ ref('bronze_inventory') }}
),

cleaned AS (
    SELECT
        inventory_id,
        product_id,
        warehouse_location,

        -- Fix: clamp negatives to 0, flag the original record
        GREATEST(quantity_on_hand, 0)                           AS quantity_on_hand,
        CASE WHEN quantity_on_hand < 0 THEN TRUE ELSE FALSE END AS is_oversold,
        quantity_on_hand                                        AS raw_quantity_on_hand,

        reorder_point,
        reorder_quantity,

        -- Stock status derived field
        CASE
            WHEN GREATEST(quantity_on_hand, 0) = 0           THEN 'Out of Stock'
            WHEN GREATEST(quantity_on_hand, 0) <= reorder_point THEN 'Low Stock'
            ELSE 'In Stock'
        END                                                     AS stock_status,

        last_restocked_date::DATE                               AS last_restocked_date,
        updated_at,
        _ingested_at,
        _source,
        NOW()                                                   AS cleaned_at
    FROM ranked
    WHERE rn = 1
)

SELECT * FROM cleaned
