-- gold/dim_product.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Product dimension — SCD Type 1 (overwrite).
-- Excludes zero-price products (not valid for analytics).
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='gold') }}

SELECT
    {{ generate_surrogate_key(['product_id']) }}     AS product_sk,
    product_id                                       AS product_nk,
    product_name,
    category,
    sub_category,
    brand,
    unit_price,
    cost_price,
    gross_margin_pct,
    weight_kg,
    is_active,
    is_zero_price,
    is_cost_inverted,
    created_date,
    cleaned_at                                       AS last_updated_at

FROM {{ ref('stg_products') }}
WHERE is_zero_price = FALSE   -- Exclude invalid products from gold layer
