-- silver/stg_customers.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Silver: Cleaned customer records (source: Olist e-commerce dataset).
--
-- Cleaning applied:
--   1. Deduplicate by customer_id (keep latest _ingested_at)
--   2. Impute NULL emails → 'unknown@retaildw.com'
--      (Olist has NO email data — ALL rows will have is_email_imputed = TRUE)
--   3. Normalize NULL phone → 'N/A'
--      (Olist has NO phone data — flagged for completeness)
--   4. INITCAP city names (Olist cities are ALL lowercase: 'sao paulo'→'Sao Paulo')
--   5. Add cleaned_at audit timestamp
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='silver') }}

WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY _ingested_at DESC
        ) AS rn
    FROM {{ ref('bronze_customers') }}
),

deduped AS (
    SELECT * FROM ranked WHERE rn = 1
),

cleaned AS (
    SELECT
        customer_id,
        TRIM(first_name)                                        AS first_name,
        TRIM(last_name)                                         AS last_name,

        -- Fix 1: NULL email imputation (ALL rows from Olist — no email data)
        COALESCE(LOWER(TRIM(email)), 'unknown@retaildw.com')    AS email,
        CASE WHEN email IS NULL THEN TRUE ELSE FALSE END        AS is_email_imputed,

        -- Fix 2: Phone — Olist has no phone data, normalize NULL → 'N/A'
        COALESCE(phone, 'N/A')                                  AS phone,
        CASE WHEN phone IS NULL THEN TRUE ELSE FALSE END        AS is_phone_cleaned,

        -- Fix 3: City casing — Olist cities are lowercase ('sao paulo', 'rio de janeiro')
        INITCAP(TRIM(city))                                     AS city,
        TRIM(state)                                             AS state,
        TRIM(country)                                           AS country,
        TRIM(zip_code)                                          AS zip_code,

        customer_segment,
        registration_date::DATE                                 AS registration_date,
        is_active,
        _ingested_at,
        _source,
        NOW()                                                   AS cleaned_at
    FROM deduped
)

SELECT * FROM cleaned
