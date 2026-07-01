"""
dags/data_quality_checks_dag.py
─────────────────────────────────
DAG: data_quality_checks
Runs dbt schema tests + custom singular tests against all layers.
Triggered after load_data completes.

Tasks:
  1. dbt_test_sources   → Test bronze source freshness + nullability
  2. dbt_test_silver    → Test silver models (not_null, unique, accepted_values)
  3. dbt_test_gold      → Test gold models (referential integrity, facts)
  4. dbt_test_custom    → Run custom singular SQL tests
  5. log_test_results   → Log pass/fail summary to Airflow logs
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner":            "retail_dw",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=2),
}

DBT_DIR      = "/opt/airflow/dbt"
DBT_PROFILES = "/opt/airflow/dbt"
DBT_CMD      = f"cd {DBT_DIR} && dbt"


def log_results(**context):
    import logging
    log = logging.getLogger("dq_checks")
    log.info("=" * 60)
    log.info("DATA QUALITY CHECKS COMPLETE")
    log.info("All dbt schema tests and singular tests passed.")
    log.info("Gold layer is ready for consumption.")
    log.info("=" * 60)


with DAG(
    dag_id="data_quality_checks",
    description="Quality: Run dbt tests across bronze, silver and gold layers",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["retail_dw", "data_quality", "dbt", "testing"],
) as dag:

    t_test_sources = BashOperator(
        task_id="dbt_test_bronze_sources",
        bash_command=f"{DBT_CMD} test --select source:bronze",
    )

    t_test_silver = BashOperator(
        task_id="dbt_test_silver",
        bash_command=f"{DBT_CMD} test --select silver.*",
    )

    t_test_gold = BashOperator(
        task_id="dbt_test_gold",
        bash_command=f"{DBT_CMD} test --select gold.*",
    )

    t_test_custom = BashOperator(
        task_id="dbt_test_custom_singular",
        bash_command=(
            f"{DBT_CMD} test --select "
            "test_type:singular"
        ),
    )

    t_log = PythonOperator(
        task_id="log_test_summary",
        python_callable=log_results,
    )

    t_test_sources >> t_test_silver >> t_test_gold >> t_test_custom >> t_log
