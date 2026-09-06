"""
dag_enriquecimento_historico_noturno.py
========================================
Pipeline noturno de backfill e enriquecimento de dados históricos:
- Detalhes e slugs de todos os deputados históricos incompletos
- Vínculos de votações órfãs históricas com proposições
- Upscaling de fotos históricas pendentes com OpenCV + Modelo IA ESPCN
- Disparo da DAG noturna de embeddings e classificação temática
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "dag_enriquecimento_historico_noturno",
    default_args=default_args,
    description="Pipeline noturno de enriquecimento e backfill de dados históricos pré-2026",
    schedule_interval=None,  # Disparado pela DAG dag_etl_camara_historico_noturno
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["quemvota", "backfill", "historico", "noturno"],
) as dag:
    # 1. Backfill de detalhes e slugs para todos os deputados históricos incompletos
    task_backfill_politicos_hist = BashOperator(
        task_id="backfill_politicos_historico",
        bash_command="uv run python etl_camara.py --backfill-deputados --backfill-workers 4",
        cwd="/opt/airflow/injest_banco",
        execution_timeout=timedelta(hours=2),
    )

    # 2. Vínculo de proposições faltantes em votações históricas
    task_backfill_proposicoes_hist = BashOperator(
        task_id="backfill_proposicoes_missing_historico",
        bash_command="uv run python backfill_proposicoes.py",
        cwd="/opt/airflow/injest_banco",
        execution_timeout=timedelta(hours=2),
    )

    # 3. Reconciliação de votações órfãs históricas via API REST
    task_backfill_votacoes_orfas_hist = BashOperator(
        task_id="backfill_votacoes_orfas_historico",
        bash_command="uv run python etl_camara.py --reconcile-orfas",
        cwd="/opt/airflow/injest_banco",
        execution_timeout=timedelta(hours=2),
    )

    # 4. Ingestão e upscaling IA das fotos de parlamentares históricos pendentes
    task_injest_fotos_ia_hist = BashOperator(
        task_id="injest_fotos_upscaling_ia_historico",
        bash_command="uv run python injest_fotos.py",
        cwd="/opt/airflow/injest_banco",
        execution_timeout=timedelta(hours=2),
    )

    # 5. Dispara a esteira noturna de IA e Embeddings
    task_trigger_embeddings_hist = TriggerDagRunOperator(
        task_id="trigger_embeddings_historico_noturno",
        trigger_dag_id="dag_embeddings_historico_noturno",
        wait_for_completion=False,
    )

    # Fluxo de dependências:
    (
        task_backfill_politicos_hist
        >> task_injest_fotos_ia_hist
        >> task_trigger_embeddings_hist
    )
    (
        task_backfill_proposicoes_hist
        >> task_backfill_votacoes_orfas_hist
        >> task_trigger_embeddings_hist
    )
