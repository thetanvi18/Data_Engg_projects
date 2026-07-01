-- bronze/bronze_inventory.sql
{{ config(materialized='view', schema='bronze') }}

SELECT
    inventory_id,
    product_id,
    warehouse_location,
    quantity_on_hand,   -- may be negative (oversell bug)
    reorder_point,
    reorder_quantity,
    last_restocked_date,
    updated_at,
    _ingested_at,
    _source
FROM {{ source('bronze', 'raw_inventory') }}
