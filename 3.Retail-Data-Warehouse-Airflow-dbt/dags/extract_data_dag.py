"""
dags/extract_data_dag.py
─────────────────────────
DAG: extract_data
Loads the 5 Olist e-commerce CSV datasets into the bronze schema.

Tasks:
  1. init_db_check    → Verify schemas exist, truncate bronze tables
  2. load_olist_data  → Read 5 CSVs and bulk-load into bronze.*

Replaces the original Faker-based synthetic data generator.
"""

from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner":            "retail_dw",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=3),
    "retry_exponential_backoff": True,
}


def task_init_db():
    sys.path.insert(0, "/opt/airflow")
    from scripts.init_db import run
    run()


def task_load_olist():
    sys.path.insert(0, "/opt/airflow")
    from scripts.load_olist_data import run
    run()


with DAG(
    dag_id="extract_data",
    description="Extract: Load Olist CSV datasets into bronze layer",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["retail_dw", "extract", "bronze", "olist"],
) as dag:

    t_init = PythonOperator(
        task_id="init_db_check",
        python_callable=task_init_db,
    )

    t_load = PythonOperator(
        task_id="load_olist_data",
        python_callable=task_load_olist,
    )

    t_init >> t_load
