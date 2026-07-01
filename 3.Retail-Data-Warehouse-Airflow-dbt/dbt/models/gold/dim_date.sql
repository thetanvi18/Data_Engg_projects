-- gold/dim_date.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Date dimension covering 2020-01-01 to 2026-12-31.
-- Uses dbt_utils.date_spine to generate one row per calendar day.
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table', schema='gold') }}

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart  = "day",
        start_date = "cast('2020-01-01' as date)",
        end_date   = "cast('2027-01-01' as date)"
    ) }}
),

final AS (
    SELECT
        TO_CHAR(date_day, 'YYYYMMDD')::INTEGER          AS date_key,
        date_day                                         AS full_date,
        EXTRACT(YEAR  FROM date_day)::INTEGER            AS year,
        EXTRACT(QUARTER FROM date_day)::INTEGER          AS quarter,
        EXTRACT(MONTH FROM date_day)::INTEGER            AS month,
        TO_CHAR(date_day, 'Month')                       AS month_name,
        TO_CHAR(date_day, 'Mon')                         AS month_short,
        EXTRACT(WEEK  FROM date_day)::INTEGER            AS week_of_year,
        EXTRACT(DOY   FROM date_day)::INTEGER            AS day_of_year,
        EXTRACT(DAY   FROM date_day)::INTEGER            AS day_of_month,
        EXTRACT(DOW   FROM date_day)::INTEGER            AS day_of_week,   -- 0=Sun
        TO_CHAR(date_day, 'Day')                         AS day_name,
        TO_CHAR(date_day, 'Dy')                          AS day_short,

        -- Flags
        CASE WHEN EXTRACT(DOW FROM date_day) IN (0,6) THEN TRUE ELSE FALSE END
                                                         AS is_weekend,
        CASE WHEN EXTRACT(MONTH FROM date_day) IN (11,12,1)
             THEN TRUE ELSE FALSE END                    AS is_festive_quarter,

        -- Period labels
        'Q' || EXTRACT(QUARTER FROM date_day)::TEXT || '-' ||
        EXTRACT(YEAR FROM date_day)::TEXT                AS quarter_label,
        TO_CHAR(date_day, 'Mon-YYYY')                    AS month_year_label,
        EXTRACT(YEAR FROM date_day)::INTEGER * 100 +
        EXTRACT(MONTH FROM date_day)::INTEGER            AS year_month_key
    FROM date_spine
)

SELECT * FROM final
