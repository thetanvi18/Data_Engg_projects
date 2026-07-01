-- gold/dim_customer.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Customer dimension — SCD Type 2 aware.
-- Reads from the snap_customers snapshot (which tracks history).
-- For the current record, dbt_scd_id / dbt_valid_to = NULL.
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='gold') }}

WITH snapshot_data AS (
    SELECT
        dbt_scd_id                                              AS customer_scd_key,
        customer_id                                             AS customer_nk,       -- natural key
        {{ generate_surrogate_key(['customer_id', 'dbt_updated_at::text']) }}
                                                                AS customer_sk,       -- surrogate key

        first_name,
        last_name,
        first_name || ' ' || last_name                         AS full_name,
        email,
        phone,
        city,
        state,
        country,
        zip_code,
        customer_segment,
        registration_date,
        is_active,

        -- SCD2 metadata
        dbt_valid_from                                          AS valid_from,
        COALESCE(dbt_valid_to, '9999-12-31'::TIMESTAMP)        AS valid_to,
        CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current

    FROM {{ ref('snap_customers') }}
)

SELECT * FROM snapshot_data
