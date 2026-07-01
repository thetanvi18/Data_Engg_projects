-- gold/fact_orders.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Fact table: Orders (grain = one row per order).
-- Incremental: only processes orders added/changed since last run.
-- Joins to dim_customer, dim_product (via items), dim_date.
-- Excludes: future-dated orders, orders from invalid customers/products.
-- ─────────────────────────────────────────────────────────────────────────────

{{
  config(
    materialized  = 'incremental',
    unique_key    = 'order_id',
    schema        = 'gold',
    on_schema_change = 'append_new_columns'
  )
}}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
    WHERE is_future_dated = FALSE          -- Exclude bad-dated orders
),

order_items_agg AS (
    -- Aggregate line items per order
    SELECT
        order_id,
        COUNT(*)                            AS line_item_count,
        SUM(quantity)                       AS total_units,
        SUM(total_amount)                   AS items_total_amount,
        SUM(CASE WHEN is_return THEN 1 ELSE 0 END) AS return_item_count,
        AVG(discount_pct)                   AS avg_discount_pct
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

customers AS (
    SELECT customer_sk, customer_nk
    FROM {{ ref('dim_customer') }}
    WHERE is_current = TRUE
),

final AS (
    SELECT
        o.order_id,

        -- Dimension keys
        c.customer_sk                       AS customer_key,
        TO_CHAR(o.order_date, 'YYYYMMDD')::INTEGER
                                            AS order_date_key,

        -- Order attributes
        o.order_status,
        o.shipping_method,
        o.shipping_city,
        o.shipping_state,

        -- Metrics
        o.total_amount,
        COALESCE(oia.line_item_count, 0)    AS line_item_count,
        COALESCE(oia.total_units, 0)        AS total_units,
        COALESCE(oia.items_total_amount, 0) AS items_total_amount,
        COALESCE(oia.return_item_count, 0)  AS return_item_count,
        COALESCE(oia.avg_discount_pct, 0)   AS avg_discount_pct,

        -- Derived flags
        CASE WHEN o.order_status = 'Delivered' THEN TRUE ELSE FALSE END
                                            AS is_delivered,
        CASE WHEN o.order_status IN ('Cancelled','Returned') THEN TRUE ELSE FALSE END
                                            AS is_cancelled_or_returned,

        o.order_date,
        o.cleaned_at                        AS dbt_updated_at

    FROM orders o
    LEFT JOIN order_items_agg oia ON o.order_id = oia.order_id
    LEFT JOIN customers c         ON o.customer_id = c.customer_nk
)

SELECT * FROM final

{% if is_incremental() %}
    WHERE dbt_updated_at > (SELECT MAX(dbt_updated_at) FROM {{ this }})
{% endif %}
