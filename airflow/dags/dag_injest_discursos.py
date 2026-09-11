"""
airflow/dags/dag_injest_discursos.py — DAG de Ingestão de Discursos da Câmara (SPEC-007)

Execução semanal (aos domingos às 03:00 AM) para atualizar os pronunciamentos
de plenário dos deputados federais da 57ª Legislatura via API de Dados Abertos.
"""

from datetime import datetime, timezone, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
}

with DAG(
    "dag_injest_discursos_semanal",
    default_args=default_args,
    description="Pipeline de coleta e sincronização de discursos da Câmara dos Deputados",
    schedule="0 3 * * 0",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["quemvota", "etl", "camara", "discursos", "spec-007"],
) as dag:
    task_injest_discursos_camara = BashOperator(
        task_id="injest_discursos_camara",
        bash_command="uv run python -m injest_banco.injest_discursos --legislatura 57",
        cwd="/opt/airflow",
    )

