"""
scripts/init_db.py
──────────────────
Verifies that the required schemas and tables exist in retail_dw.
Called by the first Airflow task before data generation starts.
"""
import os
import sys
import logging
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("init_db")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import DB_CONFIG

REQUIRED_SCHEMAS = ["bronze", "silver", "gold"]
REQUIRED_TABLES  = [
    ("bronze", "raw_customers"),
    ("bronze", "raw_products"),
    ("bronze", "raw_orders"),
    ("bronze", "raw_order_items"),
    ("bronze", "raw_payments"),
    ("bronze", "raw_inventory"),
]


def check_schema(conn, schema: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
            (schema,)
        )
        return cur.fetchone() is not None


def check_table(conn, schema: str, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT table_name FROM information_schema.tables
               WHERE table_schema = %s AND table_name = %s""",
            (schema, table)
        )
        return cur.fetchone() is not None


def truncate_bronze(conn):
    """Clear bronze tables before each fresh load (idempotent runs)."""
    tables = [
        "bronze.raw_customers",
        "bronze.raw_products",
        "bronze.raw_orders",
        "bronze.raw_order_items",
        "bronze.raw_payments",
        "bronze.raw_inventory",
    ]
    with conn.cursor() as cur:
        for tbl in tables:
            cur.execute(f"TRUNCATE TABLE {tbl}")
            logger.info("Truncated %s", tbl)
    conn.commit()
    logger.info("Bronze layer cleared — ready for fresh load.")


def run():
    logger.info("Connecting to retail_dw ...")
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Verify schemas
        for schema in REQUIRED_SCHEMAS:
            exists = check_schema(conn, schema)
            status = "✓" if exists else "✗ MISSING"
            logger.info("Schema %-10s → %s", schema, status)
            if not exists:
                raise RuntimeError(f"Schema '{schema}' not found. Run setup_schemas.sql first.")

        # Verify bronze tables
        for schema, table in REQUIRED_TABLES:
            exists = check_table(conn, schema, table)
            status = "✓" if exists else "✗ MISSING"
            logger.info("Table  %-30s → %s", f"{schema}.{table}", status)
            if not exists:
                raise RuntimeError(f"Table '{schema}.{table}' not found.")

        # Truncate bronze for a clean run
        truncate_bronze(conn)
        logger.info("DB init check passed. Ready to generate data.")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
