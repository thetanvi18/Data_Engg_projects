-- ─────────────────────────────────────────────────────────────────────────────
--  setup_schemas.sql
--  Executed inside retail_dw on first boot.
--  Creates bronze / silver / gold schemas + all raw (bronze) tables.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Schemas ──────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ── BRONZE: raw_customers ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.raw_customers (
    customer_id         VARCHAR(36),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    email               VARCHAR(200),          -- nullable (injected nulls ~5%)
    phone               VARCHAR(50),           -- mixed formats (injected noise)
    address             TEXT,
    city                VARCHAR(100),          -- mixed casing (injected noise)
    state               VARCHAR(100),
    country             VARCHAR(100),
    zip_code            VARCHAR(20),
    customer_segment    VARCHAR(50),
    registration_date   TIMESTAMP,
    is_active           BOOLEAN,
    _ingested_at        TIMESTAMP DEFAULT NOW(),
    _source             VARCHAR(50) DEFAULT 'faker_erp'
);

-- ── BRONZE: raw_products ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.raw_products (
    product_id          VARCHAR(36),
    product_name        VARCHAR(200),
    category            VARCHAR(100),
    sub_category        VARCHAR(100),
    brand               VARCHAR(100),
    unit_price          NUMERIC(12,2),         -- some 0.00 prices (injected)
    cost_price          NUMERIC(12,2),
    weight_kg           NUMERIC(8,3),
    is_active           BOOLEAN,
    created_at          TIMESTAMP,
    _ingested_at        TIMESTAMP DEFAULT NOW(),
    _source             VARCHAR(50) DEFAULT 'faker_erp'
);

-- ── BRONZE: raw_orders ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.raw_orders (
    order_id            VARCHAR(36),
    customer_id         VARCHAR(36),
    order_date          TIMESTAMP,             -- some future dates (injected)
    order_status        VARCHAR(50),
    shipping_address    TEXT,
    shipping_city       VARCHAR(100),
    shipping_state      VARCHAR(100),
    shipping_country    VARCHAR(100),
    shipping_method     VARCHAR(50),
    total_amount        NUMERIC(14,2),
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP,
    _ingested_at        TIMESTAMP DEFAULT NOW(),
    _source             VARCHAR(50) DEFAULT 'faker_erp'
);

-- ── BRONZE: raw_order_items ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.raw_order_items (
    order_item_id       VARCHAR(36),
    order_id            VARCHAR(36),           -- some orphans without parent order
    product_id          VARCHAR(36),
    quantity            INTEGER,               -- some negatives = returns
    unit_price          NUMERIC(12,2),
    discount_pct        NUMERIC(5,2),
    total_amount        NUMERIC(14,2),
    created_at          TIMESTAMP,
    _ingested_at        TIMESTAMP DEFAULT NOW(),
    _source             VARCHAR(50) DEFAULT 'faker_erp'
);

-- ── BRONZE: raw_payments ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.raw_payments (
    payment_id          VARCHAR(36),
    order_id            VARCHAR(36),
    payment_date        TIMESTAMP,
    payment_method      VARCHAR(50),
    payment_status      VARCHAR(50),
    amount              NUMERIC(14,2),         -- some 0.00 (free orders)
    transaction_id      VARCHAR(100),
    _ingested_at        TIMESTAMP DEFAULT NOW(),
    _source             VARCHAR(50) DEFAULT 'faker_erp'
);

-- ── BRONZE: raw_inventory ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.raw_inventory (
    inventory_id        VARCHAR(36),
    product_id          VARCHAR(36),
    warehouse_location  VARCHAR(100),
    quantity_on_hand    INTEGER,               -- some negatives (oversell bug)
    reorder_point       INTEGER,
    reorder_quantity    INTEGER,
    last_restocked_date TIMESTAMP,
    updated_at          TIMESTAMP,
    _ingested_at        TIMESTAMP DEFAULT NOW(),
    _source             VARCHAR(50) DEFAULT 'faker_erp'
);

-- ── Indexes on bronze PKs (speed up dbt source queries) ──────────────────────
CREATE INDEX IF NOT EXISTS idx_raw_customers_id   ON bronze.raw_customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_raw_products_id    ON bronze.raw_products(product_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_id      ON bronze.raw_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_raw_orders_cust    ON bronze.raw_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_raw_order_items_id ON bronze.raw_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_raw_payments_id    ON bronze.raw_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_raw_inventory_id   ON bronze.raw_inventory(product_id);
