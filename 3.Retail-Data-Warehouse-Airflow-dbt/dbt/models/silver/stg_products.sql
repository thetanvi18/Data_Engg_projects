-- silver/stg_products.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Silver: Cleaned product records (source: Olist e-commerce dataset).
--
-- Cleaning applied:
--   1. Deduplicate by product_id (keep latest)
--   2. Flag zero-price products (products never ordered have price = 0)
--   3. Flag cost-inverted records
--   4. Flag NULL category names (~600 rows in Olist have NULL category)
--   5. Flag Portuguese category names (all Olist categories are in Portuguese)
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='silver') }}

WITH deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY _ingested_at DESC) AS rn
    FROM {{ ref('bronze_products') }}
),

cleaned AS (
    SELECT
        product_id,
        TRIM(product_name)                  AS product_name,
        INITCAP(REPLACE(COALESCE(category, 'uncategorized'), '_', ' '))
                                            AS category,             -- Fix: Portuguese underscored names → readable
        INITCAP(REPLACE(COALESCE(sub_category, 'uncategorized'), '_', ' '))
                                            AS sub_category,
        TRIM(brand)                         AS brand,
        unit_price,
        cost_price,

        -- Flag: price anomalies
        CASE WHEN unit_price = 0  THEN TRUE  ELSE FALSE END         AS is_zero_price,
        CASE WHEN cost_price > unit_price THEN TRUE ELSE FALSE END  AS is_cost_inverted,

        -- Flag: NULL category (real Olist issue ~600 rows)
        CASE WHEN category IS NULL THEN TRUE ELSE FALSE END         AS is_category_null,
        CASE
            WHEN unit_price > 0
            THEN ROUND(((unit_price - cost_price) / unit_price) * 100, 2)
            ELSE NULL
        END                             AS gross_margin_pct,

        weight_kg,
        is_active,
        created_at::DATE                AS created_date,
        _ingested_at,
        _source,
        NOW()                           AS cleaned_at
    FROM deduped
    WHERE rn = 1
)

SELECT * FROM cleaned
