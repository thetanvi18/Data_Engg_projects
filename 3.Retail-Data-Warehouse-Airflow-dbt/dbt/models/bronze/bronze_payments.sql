-- bronze/bronze_payments.sql
{{ config(materialized='view', schema='bronze') }}

SELECT
    payment_id,
    order_id,
    payment_date,
    payment_method,
    payment_status,
    amount,             -- may be 0.00 (free orders)
    transaction_id,
    _ingested_at,
    _source
FROM {{ source('bronze', 'raw_payments') }}
