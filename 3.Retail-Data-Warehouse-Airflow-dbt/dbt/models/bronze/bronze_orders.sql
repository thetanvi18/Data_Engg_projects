-- bronze/bronze_orders.sql
{{ config(materialized='view', schema='bronze') }}

SELECT
    order_id,
    customer_id,
    order_date,          -- may be future-dated
    order_status,
    shipping_address,
    shipping_city,
    shipping_state,
    shipping_country,
    shipping_method,
    total_amount,
    created_at,
    updated_at,
    _ingested_at,
    _source,
    md5(COALESCE(order_id,'') || COALESCE(customer_id,'') || order_date::text) AS _row_hash
FROM {{ source('bronze', 'raw_orders') }}
