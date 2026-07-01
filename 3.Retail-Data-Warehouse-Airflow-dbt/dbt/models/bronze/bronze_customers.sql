-- bronze/bronze_customers.sql
-- Bronze view: raw_customers with row hash for change detection.
-- NO cleaning — raw data preserved exactly as ingested.

{{ config(materialized='view', schema='bronze') }}

SELECT
    customer_id,
    first_name,
    last_name,
    email,                          -- may be NULL
    phone,                          -- may be malformed
    address,
    city,                           -- may have mixed casing
    state,
    country,
    zip_code,
    customer_segment,
    registration_date,
    is_active,
    _ingested_at,
    _source,
    -- Row hash for downstream change detection
    md5(
        COALESCE(customer_id,'') ||
        COALESCE(first_name,'')  ||
        COALESCE(last_name,'')   ||
        COALESCE(email,'')       ||
        COALESCE(phone,'')       ||
        COALESCE(city,'')
    ) AS _row_hash
FROM {{ source('bronze', 'raw_customers') }}
