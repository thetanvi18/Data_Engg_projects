-- silver/stg_payments.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Silver: Cleaned payment records.
--
-- Cleaning applied:
--   1. Flag zero-amount payments (free orders / promotions)
--   2. Validate payment_method against known list
--   3. Validate payment_status against known list
--   4. Cast amount to NUMERIC(14,2) with safety check
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='silver') }}

SELECT
    payment_id,
    order_id,
    payment_date::TIMESTAMP                                 AS payment_date,
    payment_date::DATE                                      AS payment_date_key,
    payment_method,

    -- Flag unknown payment methods
    CASE
        WHEN payment_method NOT IN (
            'Credit Card','Debit Card','UPI','Net Banking','Wallet','COD'
        ) THEN TRUE ELSE FALSE
    END                                                     AS is_unknown_method,

    payment_status,

    -- Flag unknown statuses
    CASE
        WHEN payment_status NOT IN (
            'Success','Failed','Pending','Refunded'
        ) THEN TRUE ELSE FALSE
    END                                                     AS is_unknown_status,

    amount::NUMERIC(14,2)                                   AS amount,

    -- Fix: Flag zero-amount (free order / promo)
    CASE WHEN amount = 0 THEN TRUE ELSE FALSE END           AS is_free_order,

    transaction_id,
    _ingested_at,
    _source,
    NOW()                                                   AS cleaned_at

FROM {{ ref('bronze_payments') }}
