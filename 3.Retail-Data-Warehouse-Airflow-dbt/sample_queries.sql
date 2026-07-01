SELECT *
FROM bronze.raw_orders
LIMIT 10;

SELECT *
FROM silver.stg_orders
LIMIT 10;

SELECT *
FROM gold.fact_orders
LIMIT 10;