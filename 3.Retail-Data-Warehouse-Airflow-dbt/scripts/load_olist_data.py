"""
scripts/load_olist_data.py
───────────────────────────
Loads the 5 Olist Brazilian e-commerce CSVs into the bronze schema.
Replaces generate_data.py as the data source.

Source CSVs (in datasets/ folder):
  olist_customers_dataset.csv     → bronze.raw_customers
  olist_products_dataset.csv      → bronze.raw_products
  olist_orders_dataset.csv        → bronze.raw_orders
  olist_order_items_dataset.csv   → bronze.raw_order_items
  olist_order_payments_dataset.csv→ bronze.raw_payments

Real dirty data preserved from Olist (cleaned in silver layer):
  ✗ Customer cities are lowercase   ('sao paulo', 'franca', 'rio de janeiro')
  ✗ Product categories in Portuguese ('perfumaria', 'eletronicos', 'beleza_saude')
  ✗ ~600 NULL product category names
  ✗ NULL delivery dates for undelivered orders
  ✗ 'not_defined' payment type in some rows
  ✗ Multiple payments per order (installments → multiple rows per order_id)
  ✗ No email / phone data for customers → all NULL (silver imputes)
  ✗ No product names → derived identifiers used
  ✗ Same customer_unique_id maps to multiple customer_ids (repeat buyers)
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("load_olist")

# ── Paths ─────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import DB_CONFIG

# Inside Docker, datasets mount at /opt/airflow/datasets
# Locally, they are at P3/datasets/
DATASETS_DIR = Path(
    os.getenv("DATASETS_DIR", os.path.join(os.path.dirname(__file__), "..", "datasets"))
)

INGESTED_AT = datetime.now(timezone.utc).replace(tzinfo=None)
SOURCE = "olist_ecommerce"

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def read_csv(filename: str) -> pd.DataFrame:
    path = DATASETS_DIR / filename
    logger.info("Reading %s ...", path)
    df = pd.read_csv(path, low_memory=False)
    logger.info("  → %d rows, %d columns", len(df), len(df.columns))
    return df


def bulk_insert(conn, table: str, columns: list, rows: list, batch_size: int = 2000):
    if not rows:
        logger.warning("No rows to insert into %s — skipping.", table)
        return
    col_str = ", ".join(columns)
    query   = f"INSERT INTO {table} ({col_str}) VALUES %s ON CONFLICT DO NOTHING"
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            execute_values(cur, query, rows[i: i + batch_size])
    conn.commit()
    logger.info("  ✓ Loaded %d rows into %s", len(rows), table)


# ── Column maps & value maps ──────────────────────────────────────────────────

# Olist order_status → our schema values
ORDER_STATUS_MAP = {
    "delivered":          "Delivered",
    "shipped":            "Shipped",
    "canceled":           "Cancelled",
    "invoiced":           "Processing",
    "processing":         "Processing",
    "created":            "Pending",
    "approved":           "Pending",
    "unavailable":        "Cancelled",
}

# Olist payment_type → our schema values
PAYMENT_METHOD_MAP = {
    "credit_card":  "Credit Card",
    "debit_card":   "Debit Card",
    "boleto":       "Net Banking",
    "voucher":      "Wallet",
    "not_defined":  "Unknown",         # Real dirty value in Olist!
}

# Olist customer_state → customer_segment
# SP/RJ (largest states) → Premium, MG/RS/PR → Regular, others → Budget
def derive_segment(state: str) -> str:
    if pd.isna(state):
        return "Regular"
    state = str(state).upper()
    if state in ("SP", "RJ"):
        return "Premium"
    elif state in ("MG", "RS", "PR", "SC", "BA"):
        return "Regular"
    else:
        return "Budget"


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_customers(conn) -> list:
    """Load Olist customers into bronze.raw_customers."""
    df = read_csv("olist_customers_dataset.csv")

    logger.info("Applying customer transformations ...")
    rows = []
    for _, r in df.iterrows():
        rows.append((
            str(r["customer_id"]),
            "Customer",                                  # no real name in Olist
            str(r["customer_unique_id"])[:8],            # use partial hash as last_name
            None,                                        # email → ALL NULL (silver imputes)
            None,                                        # phone → NULL (silver flags)
            f"ZIP {r['customer_zip_code_prefix']}, {r['customer_city']}, {r['customer_state']}",
            str(r["customer_city"]),                     # DIRTY: lowercase ('sao paulo')
            str(r["customer_state"]),
            "Brazil",
            str(r["customer_zip_code_prefix"]),
            derive_segment(r["customer_state"]),
            None,                                        # registration_date → NULL
            True,
            INGESTED_AT,
            SOURCE,
        ))

    bulk_insert(conn, "bronze.raw_customers",
        ["customer_id","first_name","last_name","email","phone",
         "address","city","state","country","zip_code",
         "customer_segment","registration_date","is_active",
         "_ingested_at","_source"],
        rows)

    customer_ids = df["customer_id"].tolist()
    logger.info("Customer load complete. %d unique customer_ids.", len(customer_ids))
    return customer_ids


def load_products(conn, order_items_df: pd.DataFrame) -> list:
    """Load Olist products into bronze.raw_products.
    Unit price is computed as median price per product from order_items."""
    df = read_csv("olist_products_dataset.csv")

    # Compute median price per product from order_items
    logger.info("Computing median unit_price from order_items ...")
    price_map = order_items_df.groupby("product_id")["price"].median().to_dict()

    logger.info("Applying product transformations ...")
    rows = []
    for _, r in df.iterrows():
        pid        = str(r["product_id"])
        cat        = r["product_category_name"]          # DIRTY: Portuguese, some NULL
        unit_price = round(float(price_map.get(pid, 0.0)), 2)
        cost_price = round(unit_price * 0.60, 2) if unit_price > 0 else 0.0

        # weight: Olist in grams → convert to kg
        weight_g = r.get("product_weight_g")
        weight_kg = round(float(weight_g) / 1000, 3) if pd.notna(weight_g) else None

        rows.append((
            pid,
            f"Product_{pid[:8]}",                        # no product name in Olist
            str(cat) if pd.notna(cat) else None,         # DIRTY: NULL ~600 rows
            str(cat) if pd.notna(cat) else None,         # sub_category = same as category
            "Olist Seller",
            unit_price,
            cost_price,
            weight_kg,
            True,
            INGESTED_AT,
            INGESTED_AT,
            SOURCE,
        ))

    bulk_insert(conn, "bronze.raw_products",
        ["product_id","product_name","category","sub_category","brand",
         "unit_price","cost_price","weight_kg","is_active",
         "created_at","_ingested_at","_source"],
        rows)

    product_ids = df["product_id"].tolist()
    logger.info("Product load complete. %d products.", len(product_ids))
    return product_ids


def load_orders(conn, customers_df: pd.DataFrame, payments_df: pd.DataFrame) -> list:
    """Load Olist orders into bronze.raw_orders."""
    df = read_csv("olist_orders_dataset.csv")

    # Build customer city/state lookup (customer_id → city, state)
    cust_lookup = customers_df.set_index("customer_id")[["customer_city", "customer_state"]].to_dict("index")

    # Build total_amount from payments (sum per order_id)
    total_map = payments_df.groupby("order_id")["payment_value"].sum().to_dict()

    logger.info("Applying order transformations ...")
    rows = []
    for _, r in df.iterrows():
        oid     = str(r["order_id"])
        cid     = str(r["customer_id"])
        cust    = cust_lookup.get(cid, {})
        status  = ORDER_STATUS_MAP.get(str(r["order_status"]).lower(), "Pending")

        order_date = pd.to_datetime(r["order_purchase_timestamp"], errors="coerce")
        updated_at = pd.to_datetime(r.get("order_delivered_customer_date"), errors="coerce")
        if pd.isna(updated_at):
            updated_at = pd.to_datetime(r.get("order_approved_at"), errors="coerce")
        if pd.isna(updated_at):
            updated_at = order_date

        rows.append((
            oid,
            cid,
            order_date.to_pydatetime() if pd.notna(order_date) else None,
            status,
            "N/A",                                        # no shipping address in Olist
            str(cust.get("customer_city", "Unknown")),    # DIRTY: lowercase city
            str(cust.get("customer_state", "Unknown")),
            "Brazil",
            "Standard",                                   # no shipping method in Olist
            round(float(total_map.get(oid, 0.0)), 2),
            order_date.to_pydatetime() if pd.notna(order_date) else None,
            updated_at.to_pydatetime() if pd.notna(updated_at) else None,
            INGESTED_AT,
            SOURCE,
        ))

    bulk_insert(conn, "bronze.raw_orders",
        ["order_id","customer_id","order_date","order_status",
         "shipping_address","shipping_city","shipping_state","shipping_country",
         "shipping_method","total_amount","created_at","updated_at",
         "_ingested_at","_source"],
        rows)

    order_ids = df["order_id"].tolist()
    logger.info("Order load complete. %d orders.", len(order_ids))
    return order_ids


def load_order_items(conn, order_items_df: pd.DataFrame):
    """Load Olist order_items into bronze.raw_order_items."""
    logger.info("Applying order_item transformations ...")
    rows = []
    for _, r in order_items_df.iterrows():
        # Composite key: order_id_sequenceNumber
        item_id = f"{r['order_id']}_{int(r['order_item_id'])}"
        price   = float(r["price"])
        freight = float(r.get("freight_value", 0.0))
        total   = round(price + freight, 2)               # include freight in total

        rows.append((
            item_id,
            str(r["order_id"]),
            str(r["product_id"]),
            1,                                             # Olist: each row = 1 unit
            round(price, 2),
            0.0,                                           # no discount data in Olist
            total,
            pd.to_datetime(r.get("shipping_limit_date"), errors="coerce").to_pydatetime()
            if pd.notna(pd.to_datetime(r.get("shipping_limit_date"), errors="coerce"))
            else INGESTED_AT,
            INGESTED_AT,
            SOURCE,
        ))

    bulk_insert(conn, "bronze.raw_order_items",
        ["order_item_id","order_id","product_id","quantity",
         "unit_price","discount_pct","total_amount","created_at",
         "_ingested_at","_source"],
        rows)

    logger.info("Order_items load complete. %d rows.", len(rows))


def load_payments(conn, orders_df: pd.DataFrame):
    """Load Olist payments into bronze.raw_payments."""
    df = read_csv("olist_order_payments_dataset.csv")

    # Build order_status and approved_at lookup
    orders_df["order_approved_at"] = pd.to_datetime(orders_df["order_approved_at"], errors="coerce")
    status_map  = orders_df.set_index("order_id")["order_status"].to_dict()
    date_map    = orders_df.set_index("order_id")["order_approved_at"].to_dict()

    logger.info("Applying payment transformations ...")
    rows = []
    for _, r in df.iterrows():
        oid     = str(r["order_id"])
        seq     = int(r["payment_sequential"])
        pid     = f"{oid}_{seq}"
        method  = PAYMENT_METHOD_MAP.get(
            str(r["payment_type"]).lower(), "Unknown"
        )                                                  # DIRTY: 'not_defined' exists

        raw_status = str(status_map.get(oid, "processing")).lower()
        pay_status = {
            "delivered": "Success",
            "shipped":   "Success",
            "canceled":  "Failed",
            "invoiced":  "Success",
        }.get(raw_status, "Pending")

        pay_date = date_map.get(oid)
        pay_date = pay_date.to_pydatetime() if pd.notna(pay_date) else INGESTED_AT

        rows.append((
            pid,
            oid,
            pay_date,
            method,
            pay_status,
            round(float(r["payment_value"]), 2),
            pid,                                           # transaction_id = payment_id
            INGESTED_AT,
            SOURCE,
        ))

    bulk_insert(conn, "bronze.raw_payments",
        ["payment_id","order_id","payment_date","payment_method",
         "payment_status","amount","transaction_id",
         "_ingested_at","_source"],
        rows)

    logger.info("Payment load complete. %d rows.", len(rows))


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    logger.info("=" * 60)
    logger.info("OLIST DATA LOADER — Starting ...")
    logger.info("Datasets dir: %s", DATASETS_DIR.resolve())
    logger.info("=" * 60)

    conn = get_conn()

    try:
        # Pre-load order_items for product price computation + orders loader
        order_items_df = read_csv("olist_order_items_dataset.csv")
        orders_raw_df  = read_csv("olist_orders_dataset.csv")
        payments_raw_df = read_csv("olist_order_payments_dataset.csv")
        customers_raw_df = read_csv("olist_customers_dataset.csv")

        # Load in dependency order
        logger.info("\n── [1/5] Loading customers ...")
        load_customers(conn)

        logger.info("\n── [2/5] Loading products ...")
        load_products(conn, order_items_df)

        logger.info("\n── [3/5] Loading orders ...")
        load_orders(conn, customers_raw_df, payments_raw_df)

        logger.info("\n── [4/5] Loading order_items ...")
        load_order_items(conn, order_items_df)

        logger.info("\n── [5/5] Loading payments ...")
        load_payments(conn, orders_raw_df)

    finally:
        conn.close()

    logger.info("=" * 60)
    logger.info("OLIST DATA LOADER — Complete! ✓")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
