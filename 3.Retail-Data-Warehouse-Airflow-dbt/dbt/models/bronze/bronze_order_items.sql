-- bronze/bronze_order_items.sql
{{ config(materialized='view', schema='bronze') }}

SELECT
    order_item_id,
    order_id,
    product_id,
    quantity,            -- may be negative (returns)
    unit_price,
    discount_pct,
    total_amount,
    created_at,
    _ingested_at,
    _source
FROM {{ source('bronze', 'raw_order_items') }}
