from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from airflow import DAG

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "dag_etl_camara_diario",
    default_args=default_args,
    description="Pipeline diário de carga incremental e atualização de dados da Câmara",
    schedule_interval="0 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["quemvota", "etl", "camara"],
) as dag:
    # 0. Garante que o schema está atualizado antes de qualquer carga.
    # Roda via docker exec no container da api, que já tem backend/ + alembic.ini
    # embutidos na imagem (Opção B) — o Airflow só dispara o comando.
    task_alembic_upgrade = BashOperator(
        task_id="alembic_upgrade_head",
        bash_command="docker exec quemvota_api alembic -c backend/alembic.ini upgrade head",
    )

    task_update_ano_atual = BashOperator(
        task_id="update_etl_camara_corrente",
        bash_command="uv run python etl_camara.py --update",
        cwd="/opt/airflow/injest_banco",
    )

    task_trigger_enriquecimento = TriggerDagRunOperator(
        task_id="trigger_enriquecimento_dados",
        trigger_dag_id="dag_enriquecimento_dados",
        wait_for_completion=False,
    )

    task_alembic_upgrade >> task_update_ano_atual >> task_trigger_enriquecimento
