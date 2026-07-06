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
    schedule_interval="0 3 * * *",  # Roda todos os dias às 03:00 da manhã
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["quemvota", "etl", "camara"],
) as dag:
    # 1. Executa a atualização incremental do ano corrente usando o script core
    # Usamos "uv run" ou "python" dependendo de como o ambiente do Airflow está configurado
    task_update_ano_atual = BashOperator(
        task_id="update_etl_camara_corrente",
        bash_command="uv run python etl_camara.py --update",
        cwd="/opt/airflow/injest_banco",
        # Se preferir definir variáveis de ambiente específicas para a task:
        # env={'DATABASE_URL': '{{ var.value.database_url }}'},
    )

    # 2. Trigger para a DAG de enriquecimento de dados
    task_trigger_enriquecimento = TriggerDagRunOperator(
        task_id="trigger_enriquecimento_dados",
        trigger_dag_id="dag_enriquecimento_dados",
        wait_for_completion=False,  # Dispara e finaliza esta DAG, deixando a outra correr em paralelo
    )

    task_update_ano_atual >> task_trigger_enriquecimento
