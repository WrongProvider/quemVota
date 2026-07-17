from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from airflow import DAG

default_args = {
    "owner": "embeddings",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "dag_embeddings",
    default_args=default_args,
    description="Pipeline para geração de embeddings do banco de dados",
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["quemvota", "embeddings"],
) as dag:
    # 0. Garante que o schema está atualizado antes de qualquer carga.
    # Roda via docker exec no container da api, que já tem backend/ + alembic.ini
    # embutidos na imagem (Opção B) — o Airflow só dispara o comando.
    task_alembic_upgrade = BashOperator(
        task_id="alembic_upgrade_head",
        bash_command="docker exec quemvota_api alembic -c backend/alembic.ini upgrade head",
    )

    task_update_embeddings = BashOperator(
        task_id="update_embeddings",
        bash_command="uv run python gerar_embeddings.py",
        cwd="/opt/airflow/embeddings",
    )

    task_alembic_upgrade >> task_update_embeddings
