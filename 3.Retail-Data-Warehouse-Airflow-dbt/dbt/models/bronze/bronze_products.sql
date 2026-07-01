-- bronze/bronze_products.sql
{{ config(materialized='view', schema='bronze') }}

SELECT
    product_id,
    product_name,
    category,
    sub_category,
    brand,
    unit_price,         -- may be 0.00
    cost_price,
    weight_kg,
    is_active,
    created_at,
    _ingested_at,
    _source,
    md5(COALESCE(product_id,'') || COALESCE(product_name,'') || unit_price::text) AS _row_hash
FROM {{ source('bronze', 'raw_products') }}
