\echo '======================================================='
\echo '  1. BRONZE LAYER (RAW CUSTOMERS)                      '
\echo '======================================================='
-- Notice how the cities are messy and lowercase here!
SELECT customer_id, city, state 
FROM bronze.raw_customers 
LIMIT 5;

\echo ' '
\echo '======================================================='
\echo '  2. SILVER LAYER (CLEANED CUSTOMERS)                  '
\echo '======================================================='
-- Notice how dbt cleaned and Capitalized the cities!
SELECT customer_id, customer_city, customer_state 
FROM silver.stg_customers 
LIMIT 5;

\echo ' '
\echo '======================================================='
\echo '  3. GOLD LAYER (STAR SCHEMA FACT TABLE)               '
\echo '======================================================='
-- Final aggregated data joined from multiple tables!
\x on
SELECT 
    order_id, 
    order_status, 
    total_amount, 
    items_total_amount, 
    order_date
FROM gold.fact_orders 
ORDER BY total_amount DESC
LIMIT 3;
\x off
