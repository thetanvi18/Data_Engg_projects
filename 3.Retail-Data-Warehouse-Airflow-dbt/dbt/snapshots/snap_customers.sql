-- snapshots/snap_customers.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- SCD Type 2 snapshot on customers.
-- Tracks changes to: email, phone, city, state, customer_segment, is_active.
-- On each dbt snapshot run, changed records get:
--   - dbt_valid_to set on the old row
--   - A new row inserted with dbt_valid_from = current timestamp
-- ─────────────────────────────────────────────────────────────────────────────

{% snapshot snap_customers %}

{{
    config(
        target_schema   = 'gold',
        unique_key      = 'customer_id',
        strategy        = 'check',
        check_cols      = ['email', 'phone', 'city', 'state', 'customer_segment', 'is_active'],
        invalidate_hard_deletes = True
    )
}}

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    state,
    country,
    zip_code,
    customer_segment,
    registration_date,
    is_active,
    cleaned_at AS updated_at
FROM {{ ref('stg_customers') }}

{% endsnapshot %}
