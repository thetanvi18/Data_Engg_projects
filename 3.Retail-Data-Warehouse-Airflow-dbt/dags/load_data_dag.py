"""
dags/load_data_dag.py
──────────────────────
DAG: load_data
Runs dbt gold layer models to build the Star Schema.
Triggered after transform_data completes.

Tasks:
  1. dbt_run_gold       → Materialize all gold models (dims + facts)
  2. dbt_run_dim_date   → Materialize dim_date (date spine)
  3. dbt_run_dims       → Materialize dim_customer, dim_product
  4. dbt_run_facts      → Materialize fact_orders, fact_payments (incremental)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner":            "retail_dw",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=3),
}

DBT_DIR      = "/opt/airflow/dbt"
DBT_PROFILES = "/opt/airflow/dbt"
DBT_CMD      = f"cd {DBT_DIR} && dbt"

with DAG(
    dag_id="load_data",
    description="Load: Run dbt gold layer (Star Schema — facts and dimensions)",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,          # Triggered by master_pipeline
    catchup=False,
    tags=["retail_dw", "load", "gold", "star_schema", "dbt"],
) as dag:

    t_dim_date = BashOperator(
        task_id="dbt_run_dim_date",
        bash_command=f"{DBT_CMD} run --select gold.dim_date",
    )

    t_dims = BashOperator(
        task_id="dbt_run_dimensions",
        bash_command=f"{DBT_CMD} run --select gold.dim_customer gold.dim_product",
    )

    t_facts = BashOperator(
        task_id="dbt_run_facts",
        bash_command=f"{DBT_CMD} run --select gold.fact_orders gold.fact_payments",
    )

    t_generate_docs = BashOperator(
        task_id="dbt_generate_docs",
        bash_command=f"{DBT_CMD} docs generate",
    )

    # dims depend on date spine; facts depend on all dims
    t_dim_date >> t_dims >> t_facts >> t_generate_docs
