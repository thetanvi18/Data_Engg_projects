"""
dags/master_pipeline_dag.py
────────────────────────────
DAG: master_pipeline
The single entry-point DAG that orchestrates the full pipeline:

  extract_data  →  transform_data  →  load_data  →  data_quality_checks

Uses TriggerDagRunOperator with wait_for_completion=True so each
stage must succeed before the next begins.

Schedule: @daily — runs every day at midnight.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator

default_args = {
    "owner":            "retail_dw",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}


def pipeline_start(**context):
    import logging
    log = logging.getLogger("master_pipeline")
    log.info("=" * 60)
    log.info("MASTER PIPELINE STARTED")
    log.info("Run date: %s", context["ds"])
    log.info("=" * 60)


def pipeline_end(**context):
    import logging
    log = logging.getLogger("master_pipeline")
    log.info("=" * 60)
    log.info("MASTER PIPELINE COMPLETE ✓")
    log.info("All layers loaded and quality checks passed.")
    log.info("=" * 60)


with DAG(
    dag_id="master_pipeline",
    description="Master: Orchestrates extract → transform → load → quality_checks",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["retail_dw", "master", "orchestration"],
) as dag:

    t_start = PythonOperator(
        task_id="pipeline_start",
        python_callable=pipeline_start,
    )

    t_extract = TriggerDagRunOperator(
        task_id="trigger_extract_data",
        trigger_dag_id="extract_data",
        wait_for_completion=True,
        poke_interval=30,
        reset_dag_run=True,
    )

    t_transform = TriggerDagRunOperator(
        task_id="trigger_transform_data",
        trigger_dag_id="transform_data",
        wait_for_completion=True,
        poke_interval=30,
        reset_dag_run=True,
    )

    t_load = TriggerDagRunOperator(
        task_id="trigger_load_data",
        trigger_dag_id="load_data",
        wait_for_completion=True,
        poke_interval=30,
        reset_dag_run=True,
    )

    t_quality = TriggerDagRunOperator(
        task_id="trigger_data_quality_checks",
        trigger_dag_id="data_quality_checks",
        wait_for_completion=True,
        poke_interval=30,
        reset_dag_run=True,
    )

    t_end = PythonOperator(
        task_id="pipeline_end",
        python_callable=pipeline_end,
    )

    t_start >> t_extract >> t_transform >> t_load >> t_quality >> t_end
