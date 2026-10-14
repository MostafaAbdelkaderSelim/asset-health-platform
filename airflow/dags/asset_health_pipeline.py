from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/project"
PY = "/home/airflow/venv/bin/python"
DBT = "/home/airflow/venv/bin/dbt"

with DAG(
    dag_id="asset_health_gold_to_alerts",
    description="Silver -> Gold (dbt) -> audit -> Postgres -> RBAC -> alerts",
    start_date=datetime(2026, 10, 1),
    schedule=None,          # manual trigger for now
    catchup=False,
    max_active_runs=1,      # one run at a time: DuckDB allows one writer
    default_args={"retries": 1, "retry_delay": timedelta(minutes=1)},
    tags=["asset-health"],
) as dag:

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT}/dbt && DBT_PROFILES_DIR=. {DBT} build --no-use-colors",
    )

    audit = BashOperator(
        task_id="audit_log",
        bash_command=f"cd {PROJECT} && {PY} governance/audit_run.py",
    )

    publish = BashOperator(
        task_id="publish_to_postgres",
        bash_command=f"cd {PROJECT} && {PY} governance/publish_to_postgres.py",
    )

    rbac = BashOperator(
        task_id="apply_rbac",
        bash_command=(
            f"cd {PROJECT} && PGPASSWORD=$PG_ADMIN_PASSWORD "
            "psql -h $PG_HOST -p $PG_PORT -U admin -d assethealth "
            "-v ON_ERROR_STOP=1 -f governance/rbac.sql"
        ),
    )

    alerts = BashOperator(
        task_id="generate_alerts",
        bash_command=f"cd {PROJECT} && {PY} ml/generate_alerts.py",
    )

    dbt_build >> audit >> publish >> rbac >> alerts
