-- gold/fact_payments.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Fact table: Payments (grain = one row per payment).
-- Incremental: only processes new/changed payments since last run.
-- Excludes: zero-amount payments (flagged separately for reporting).
-- ─────────────────────────────────────────────────────────────────────────────

{{
  config(
    materialized  = 'incremental',
    unique_key    = 'payment_id',
    schema        = 'gold',
    on_schema_change = 'append_new_columns'
  )
}}

WITH payments AS (
    SELECT * FROM {{ ref('stg_payments') }}
),

orders AS (
    SELECT
        order_id,
        customer_id,
        order_date_key
    FROM {{ ref('stg_orders') }}
    WHERE is_future_dated = FALSE
),

customers AS (
    SELECT customer_sk, customer_nk
    FROM {{ ref('dim_customer') }}
    WHERE is_current = TRUE
),

final AS (
    SELECT
        p.payment_id,
        p.order_id,

        -- Dimension keys
        c.customer_sk                       AS customer_key,
        TO_CHAR(p.payment_date, 'YYYYMMDD')::INTEGER
                                            AS payment_date_key,
        o.order_date_key,

        -- Payment attributes
        p.payment_method,
        p.payment_status,
        p.transaction_id,

        -- Metrics
        p.amount,

        -- Flags
        p.is_free_order,
        p.is_unknown_method,
        p.is_unknown_status,
        CASE WHEN p.payment_status = 'Success'  THEN TRUE ELSE FALSE END
                                            AS is_successful,
        CASE WHEN p.payment_status = 'Refunded' THEN TRUE ELSE FALSE END
                                            AS is_refunded,

        p.payment_date,
        p.cleaned_at                        AS dbt_updated_at

    FROM payments p
    LEFT JOIN orders o    ON p.order_id     = o.order_id
    LEFT JOIN customers c ON o.customer_id  = c.customer_nk
)

SELECT * FROM final

{% if is_incremental() %}
    WHERE dbt_updated_at > (SELECT MAX(dbt_updated_at) FROM {{ this }})
{% endif %}
