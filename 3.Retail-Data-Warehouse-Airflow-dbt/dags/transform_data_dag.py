"""
dags/transform_data_dag.py
───────────────────────────
DAG: transform_data
Runs dbt models for the silver layer (cleaned, validated data).
Triggered after extract_data completes.

Tasks:
  1. dbt_debug          → Validate dbt connection
  2. dbt_deps           → Install dbt packages
  3. dbt_run_bronze     → Materialize bronze staging views
  4. dbt_run_silver     → Materialize silver cleaned tables
  5. dbt_snapshot       → Run SCD Type 2 snapshot on customers
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
    dag_id="transform_data",
    description="Transform: Run dbt silver layer models and SCD2 snapshot",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,          # Triggered by master_pipeline
    catchup=False,
    tags=["retail_dw", "transform", "silver", "dbt"],
) as dag:

    t_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"{DBT_CMD} deps",
    )

    t_bronze = BashOperator(
        task_id="dbt_run_bronze",
        bash_command=f"{DBT_CMD} run --select bronze.*",
    )

    t_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=f"{DBT_CMD} run --select silver.*",
    )

    t_snapshot = BashOperator(
        task_id="dbt_snapshot_customers",
        bash_command=f"{DBT_CMD} snapshot --select snap_customers",
    )

    t_deps >> t_bronze >> t_silver >> t_snapshot
