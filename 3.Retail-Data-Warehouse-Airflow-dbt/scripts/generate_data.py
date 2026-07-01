"""
scripts/generate_data.py
─────────────────────────
Generates synthetic retail data using Faker and loads it into
the bronze schema of the retail_dw PostgreSQL database.

Data volumes:
  - 5,000  customers
  - 500    products
  - 20,000 orders
  - ~50,000 order_items  (avg 2.5 items/order)
  - 20,000 payments      (1 per order)
  - 500    inventory     (1 per product)

Dirty data injected (for silver-layer cleaning):
  - NULL emails (~5% customers)
  - Malformed phone numbers (~8%)
  - Mixed-case city names (~10%)
  - Duplicate order rows (~1.5%)
  - Future order dates (~1%)
  - Negative quantities / returns (~1% order_items)
  - Orphan order_items (~0.5%)
  - Zero-amount payments (~1%)
  - Zero-price products (~3%)
  - Negative inventory (~5%)
"""

import os
import sys
import random
import uuid
import logging
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("generate_data")

# ── Allow running standalone OR from Airflow (adds project root to path) ─────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    DB_CONFIG, FAKER_SEED, RANDOM_SEED,
    NUM_CUSTOMERS, NUM_PRODUCTS, NUM_ORDERS,
    NULL_EMAIL_RATE, BAD_PHONE_RATE, MIXED_CASE_CITY_RATE,
    DUPLICATE_ORDER_RATE, FUTURE_DATE_RATE,
    NEGATIVE_QTY_RATE, ORPHAN_ITEM_RATE,
    ZERO_PAYMENT_RATE, ZERO_PRICE_RATE, NEGATIVE_INVENTORY_RATE,
    CATEGORIES, BRANDS, PAYMENT_METHODS, ORDER_STATUSES,
    SHIPPING_METHODS, CUSTOMER_SEGMENTS, WAREHOUSES,
    CITY_CASING_VARIANTS,
)

# ── Faker setup ───────────────────────────────────────────────────────────────
fake = Faker("en_IN")
Faker.seed(FAKER_SEED)
random.seed(RANDOM_SEED)

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_conn():
    """Return a fresh psycopg2 connection to retail_dw."""
    return psycopg2.connect(**DB_CONFIG)


def uid() -> str:
    return str(uuid.uuid4())


def rand_date(start_year: int = 2022, end_year: int = 2024) -> datetime:
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def inject_phone_noise(phone: str) -> str:
    """Return a malformed phone string (various realistic bad formats)."""
    noise_formats = [
        phone[:5] + "-" + phone[5:],   # partial dash
        "+" + phone,                    # extra plus
        phone.replace("9", "X"),        # letter in number
        phone[:8],                      # truncated
        "00" + phone,                   # double-zero prefix
    ]
    return random.choice(noise_formats)


def inject_city_casing(city: str) -> str:
    """Return city name with inconsistent casing."""
    if city in CITY_CASING_VARIANTS:
        return random.choice(CITY_CASING_VARIANTS[city])
    return random.choice([city.lower(), city.upper(), city.title()])


# ── Generator functions ───────────────────────────────────────────────────────

def generate_customers() -> list[tuple]:
    logger.info("Generating %d customers ...", NUM_CUSTOMERS)
    rows = []
    cities = list(CITY_CASING_VARIANTS.keys())

    for _ in range(NUM_CUSTOMERS):
        city    = random.choice(cities)
        email   = None if random.random() < NULL_EMAIL_RATE else fake.email()
        phone   = fake.phone_number()
        if random.random() < BAD_PHONE_RATE:
            phone = inject_phone_noise(phone)
        if random.random() < MIXED_CASE_CITY_RATE:
            city = inject_city_casing(city)

        rows.append((
            uid(),
            fake.first_name(),
            fake.last_name(),
            email,
            phone,
            fake.address().replace("\n", ", "),
            city,
            fake.state(),
            "India",
            fake.postcode(),
            random.choice(CUSTOMER_SEGMENTS),
            rand_date(2020, 2023),
            random.random() > 0.05,   # 5% inactive
        ))

    logger.info("Generated %d customer rows.", len(rows))
    return rows


def generate_products() -> list[tuple]:
    logger.info("Generating %d products ...", NUM_PRODUCTS)
    rows = []

    for _ in range(NUM_PRODUCTS):
        cat, subs = random.choice(CATEGORIES)
        sub = random.choice(subs)
        unit_price  = 0.00 if random.random() < ZERO_PRICE_RATE else round(random.uniform(50, 50000), 2)
        cost_price  = round(unit_price * random.uniform(0.4, 0.8), 2) if unit_price > 0 else 0.00

        rows.append((
            uid(),
            f"{random.choice(BRANDS)} {sub} {fake.word().title()}",
            cat,
            sub,
            random.choice(BRANDS),
            unit_price,
            cost_price,
            round(random.uniform(0.1, 25.0), 3),
            random.random() > 0.03,   # 3% inactive
            rand_date(2021, 2023),
        ))

    logger.info("Generated %d product rows.", len(rows))
    return rows


def generate_orders(customer_ids: list[str]) -> list[tuple]:
    logger.info("Generating %d orders ...", NUM_ORDERS)
    rows = []
    now  = datetime.now()

    for _ in range(NUM_ORDERS):
        cust_id    = random.choice(customer_ids)
        order_date = rand_date(2022, 2024)

        # Inject future dates
        if random.random() < FUTURE_DATE_RATE:
            order_date = now + timedelta(days=random.randint(1, 90))

        status     = random.choice(ORDER_STATUSES)
        city       = random.choice(list(CITY_CASING_VARIANTS.keys()))
        total      = round(random.uniform(100, 100000), 2)

        rows.append((
            uid(),
            cust_id,
            order_date,
            status,
            fake.address().replace("\n", ", "),
            city,
            fake.state(),
            "India",
            random.choice(SHIPPING_METHODS),
            total,
            order_date,
            order_date + timedelta(hours=random.randint(1, 72)),
        ))

    # ── Inject duplicate rows (~1.5%) ─────────────────────────────────────────
    num_dupes = int(NUM_ORDERS * DUPLICATE_ORDER_RATE)
    dupes     = random.sample(rows, num_dupes)
    rows.extend(dupes)
    logger.info("Injected %d duplicate order rows.", num_dupes)

    logger.info("Generated %d order rows (including dupes).", len(rows))
    return rows


def generate_order_items(order_ids: list[str], product_ids: list[str]) -> list[tuple]:
    avg_items   = 2.5
    total_items = int(NUM_ORDERS * avg_items)
    logger.info("Generating ~%d order_items ...", total_items)
    rows = []

    for _ in range(total_items):
        order_id = random.choice(order_ids)
        qty      = random.randint(1, 10)

        # Inject negative quantities (returns)
        if random.random() < NEGATIVE_QTY_RATE:
            qty = -abs(qty)

        unit_price   = round(random.uniform(50, 50000), 2)
        discount_pct = round(random.uniform(0, 30), 2)
        total        = round(qty * unit_price * (1 - discount_pct / 100), 2)

        rows.append((
            uid(),
            order_id,
            random.choice(product_ids),
            qty,
            unit_price,
            discount_pct,
            total,
            rand_date(2022, 2024),
        ))

    # ── Inject orphan rows (order_id not in order_ids) ────────────────────────
    num_orphans = int(total_items * ORPHAN_ITEM_RATE)
    for _ in range(num_orphans):
        qty        = random.randint(1, 5)
        unit_price = round(random.uniform(50, 5000), 2)
        rows.append((
            uid(),
            uid(),            # fake / non-existent order_id
            random.choice(product_ids),
            qty,
            unit_price,
            0.0,
            round(qty * unit_price, 2),
            rand_date(2022, 2024),
        ))
    logger.info("Injected %d orphan order_item rows.", num_orphans)

    logger.info("Generated %d order_item rows.", len(rows))
    return rows


def generate_payments(order_ids: list[str]) -> list[tuple]:
    logger.info("Generating %d payments ...", len(order_ids))
    rows = []

    for order_id in order_ids:
        amount = 0.00 if random.random() < ZERO_PAYMENT_RATE else round(random.uniform(100, 100000), 2)
        pay_date = rand_date(2022, 2024)

        rows.append((
            uid(),
            order_id,
            pay_date,
            random.choice(PAYMENT_METHODS),
            random.choice(["Success", "Success", "Success", "Failed", "Pending", "Refunded"]),
            amount,
            uid().replace("-", "").upper()[:16],
        ))

    logger.info("Generated %d payment rows.", len(rows))
    return rows


def generate_inventory(product_ids: list[str]) -> list[tuple]:
    logger.info("Generating %d inventory records ...", len(product_ids))
    rows = []

    for prod_id in product_ids:
        qty = random.randint(-20, 500)

        # Inject intentional negatives (oversell bug)
        if random.random() >= NEGATIVE_INVENTORY_RATE:
            qty = abs(qty)

        rows.append((
            uid(),
            prod_id,
            random.choice(WAREHOUSES),
            qty,
            random.randint(10, 50),
            random.randint(50, 200),
            rand_date(2023, 2024),
            datetime.now(),
        ))

    logger.info("Generated %d inventory rows.", len(rows))
    return rows


# ── Bulk insert helper ────────────────────────────────────────────────────────

def bulk_insert(conn, table: str, columns: list[str], rows: list[tuple], batch_size: int = 1000):
    """Insert rows into table using execute_values for speed."""
    col_str = ", ".join(columns)
    query   = f"INSERT INTO {table} ({col_str}) VALUES %s"

    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            execute_values(cur, query, batch)
            logger.debug("  Inserted batch %d-%d into %s", i, i + len(batch), table)

    conn.commit()
    logger.info("  ✓ Loaded %d rows into %s", len(rows), table)


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run():
    logger.info("=" * 60)
    logger.info("Starting synthetic data generation ...")
    logger.info("=" * 60)

    conn = get_conn()

    try:
        # ── Customers ─────────────────────────────────────────────────────────
        customer_rows = generate_customers()
        bulk_insert(conn, "bronze.raw_customers",
            ["customer_id","first_name","last_name","email","phone",
             "address","city","state","country","zip_code",
             "customer_segment","registration_date","is_active"],
            customer_rows)
        customer_ids = [r[0] for r in customer_rows]

        # ── Products ──────────────────────────────────────────────────────────
        product_rows = generate_products()
        bulk_insert(conn, "bronze.raw_products",
            ["product_id","product_name","category","sub_category","brand",
             "unit_price","cost_price","weight_kg","is_active","created_at"],
            product_rows)
        product_ids = [r[0] for r in product_rows]

        # ── Orders ────────────────────────────────────────────────────────────
        order_rows = generate_orders(customer_ids)
        bulk_insert(conn, "bronze.raw_orders",
            ["order_id","customer_id","order_date","order_status",
             "shipping_address","shipping_city","shipping_state","shipping_country",
             "shipping_method","total_amount","created_at","updated_at"],
            order_rows)
        # Use only unique order_ids for payments/items (exclude injected dupes)
        seen = set()
        unique_order_ids = []
        for r in order_rows:
            if r[0] not in seen:
                seen.add(r[0])
                unique_order_ids.append(r[0])

        # ── Order Items ───────────────────────────────────────────────────────
        item_rows = generate_order_items(unique_order_ids, product_ids)
        bulk_insert(conn, "bronze.raw_order_items",
            ["order_item_id","order_id","product_id","quantity",
             "unit_price","discount_pct","total_amount","created_at"],
            item_rows)

        # ── Payments ──────────────────────────────────────────────────────────
        payment_rows = generate_payments(unique_order_ids)
        bulk_insert(conn, "bronze.raw_payments",
            ["payment_id","order_id","payment_date","payment_method",
             "payment_status","amount","transaction_id"],
            payment_rows)

        # ── Inventory ─────────────────────────────────────────────────────────
        inventory_rows = generate_inventory(product_ids)
        bulk_insert(conn, "bronze.raw_inventory",
            ["inventory_id","product_id","warehouse_location","quantity_on_hand",
             "reorder_point","reorder_quantity","last_restocked_date","updated_at"],
            inventory_rows)

    finally:
        conn.close()

    logger.info("=" * 60)
    logger.info("Data generation complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
