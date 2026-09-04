from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from airflow import DAG

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

with DAG(
    "dag_enriquecimento_dados",
    default_args=default_args,
    description="Pipeline de Backfills, Vínculos de Votações e Upscaling de Fotos",
    schedule_interval=None,  # Disparado pela DAG diária após ETL e sync do grafo
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["quemvota", "backfill", "ia"],
) as dag:
    # Task A: Preenche campos detalhados e slugs únicos via novo módulo modular (backfill.py)
    task_backfill_politicos = BashOperator(
        task_id="backfill_politicos_detalhes",
        bash_command="uv run python etl_camara.py --backfill-deputados --backfill-workers 4",
        cwd="/opt/airflow/injest_banco",
    )

    # Task B: Trata votações cujo idProposicao está nulo usando extração por string
    task_backfill_proposicoes = BashOperator(
        task_id="backfill_proposicoes_missing",
        bash_command="uv run python backfill_proposicoes.py",
        cwd="/opt/airflow/injest_banco",
    )

    # Task C: Reconciliação robusta de votações órfãs via reconciler.py modular
    task_backfill_votacoes_orfas = BashOperator(
        task_id="backfill_votacoes_orfas",
        bash_command="uv run python etl_camara.py --reconcile-orfas",
        cwd="/opt/airflow/injest_banco",
    )

    # Task D: Coleta novas fotos de políticos e aplica o upscaling com OpenCV + Modelo IA ESPCN
    task_injest_fotos_ia = BashOperator(
        task_id="injest_fotos_upscaling_ia",
        bash_command="uv run python injest_fotos.py",
        cwd="/opt/airflow/injest_banco",
    )

    # Task E: Dispara a DAG de IA e Semântica (embeddings + classificação de temas SPEC-001)
    task_trigger_embeddings = TriggerDagRunOperator(
        task_id="trigger_dag_embeddings",
        trigger_dag_id="dag_embeddings",
        wait_for_completion=False,
    )

    # =========================================================================
    # Definição do Fluxo de Dependências
    # =========================================================================

    # Políticos: backfill -> fotos IA -> pipeline semântico
    task_backfill_politicos >> task_injest_fotos_ia >> task_trigger_embeddings

    # Proposições/Votações: vínculos -> reconciliação de órfãs -> pipeline semântico
    task_backfill_proposicoes >> task_backfill_votacoes_orfas >> task_trigger_embeddings
