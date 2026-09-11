"""
dag_etl_camara_historico_noturno.py
====================================
Pipeline noturno de madrugada (01:00 BRT / 04:00 UTC) para ingestão e atualização
de dados históricos pré-2026 da Câmara dos Deputados (2008 a 2025, Legislaturas 51 a 56)
e sincronização no grafo Apache AGE.
Utiliza cache ETag para consultar a Câmara e transferir apenas arquivos atualizados.
"""

from datetime import datetime, timezone, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from airflow import DAG

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    "dag_etl_camara_historico_noturno",
    default_args=default_args,
    description="Pipeline noturno de ingestão de dados históricos pré-2026 e sincronização do grafo AGE",
    schedule="0 4 * * *",  # 01:00 BRT (04:00 UTC)
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["quemvota", "etl", "camara", "historico", "noturno"],
) as dag:
    # 0. Garante schema atualizado via migrations do Alembic
    task_alembic_upgrade = BashOperator(
        task_id="alembic_upgrade_head",
        bash_command="docker exec quemvota_api alembic -c backend/alembic.ini upgrade head",
    )

    # 1. Executa ingestão dos dados históricos pré-2026 (2008..2025 / L51..L56) com ETag cache
    task_etl_historico = BashOperator(
        task_id="etl_camara_historico_pre2026",
        bash_command="uv run python etl_camara.py --historico --reconcile-orfas",
        cwd="/opt/airflow/injest_banco",
        execution_timeout=timedelta(hours=4),
    )

    # 2. Sincroniza dados históricos para o grafo Apache AGE (proposições, temas, autores e votações pré-2026)
    task_sync_graph_historico = BashOperator(
        task_id="sync_graph_age_historico",
        bash_command="uv run python /opt/airflow/tasks/sync_graph.py --pre-2026",
        cwd="/opt/airflow",
        execution_timeout=timedelta(hours=3),
    )

    # 3. Dispara a esteira noturna de enriquecimento histórico
    task_trigger_enriquecimento_hist = TriggerDagRunOperator(
        task_id="trigger_enriquecimento_historico_noturno",
        trigger_dag_id="dag_enriquecimento_historico_noturno",
        wait_for_completion=False,
    )

    (
        task_alembic_upgrade
        >> task_etl_historico
        >> task_sync_graph_historico
        >> task_trigger_enriquecimento_hist
    )
