"""
airflow/dags/dag_verba_gabinete.py — DAG mensal para coleta de Verba de Gabinete dos Deputados

Executado no 5º dia de cada mês (04:00 AM) para consolidar e atualizar os gastos
e disponibilidades de verba de gabinete dos deputados federais ativos.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    "dag_verba_gabinete_mensal",
    default_args=default_args,
    description="Pipeline mensal de coleta e consolidação da Verba de Gabinete dos Deputados",
    schedule_interval="0 4 5 * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["quemvota", "etl", "camara", "verba_gabinete"],
) as dag:
    task_injest_verba = BashOperator(
        task_id="injest_verba_gabinete_mensal",
        bash_command="uv run python -m injest_banco.injest_verba_gabinete --workers 8",
        cwd="/opt/airflow",
    )

    task_injest_verba
