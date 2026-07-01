-- silver/stg_orders.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Silver: Cleaned order records.
--
-- Cleaning applied:
--   1. Deduplicate by order_id (keep latest record)
--   2. Flag and exclude future-dated orders (order_date > CURRENT_DATE)
--   3. Validate order_status against accepted values
--   4. Add is_future_dated flag (kept in silver for audit, excluded from gold)
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='silver') }}

WITH deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY _ingested_at DESC
        ) AS rn
    FROM {{ ref('bronze_orders') }}
),

cleaned AS (
    SELECT
        order_id,
        customer_id,
        order_date::TIMESTAMP                                   AS order_date,
        order_date::DATE                                        AS order_date_key,

        -- Flag future-dated orders (data entry error)
        CASE
            WHEN order_date > CURRENT_TIMESTAMP THEN TRUE
            ELSE FALSE
        END                                                     AS is_future_dated,

        order_status,

        -- Flag invalid statuses
        CASE
            WHEN order_status NOT IN (
                'Pending','Processing','Shipped','Delivered','Cancelled','Returned'
            ) THEN TRUE ELSE FALSE
        END                                                     AS is_invalid_status,

        shipping_address,
        INITCAP(shipping_city)                                  AS shipping_city,
        shipping_state,
        shipping_country,
        shipping_method,
        total_amount,
        created_at,
        updated_at,
        _ingested_at,
        _source,
        NOW()                                                   AS cleaned_at
    FROM deduped
    WHERE rn = 1
)

SELECT * FROM cleaned
