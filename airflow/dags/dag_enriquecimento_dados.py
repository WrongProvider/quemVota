from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

with (
    DAG(
        "dag_enriquecimento_dados",
        default_args=default_args,
        description="Pipeline de Backfills, Vínculos de Votações e Upscaling de Fotos",
        schedule_interval=None,  # Configurado como None porque é disparado pela DAG principal
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=["quemvota", "backfill", "ia"],
    ) as dag
):
    # Task A: Preenche campos detalhados dos deputados (nome civil, nascimento, etc)
    task_backfill_politicos = BashOperator(
        task_id="backfill_politicos_detalhes",
        bash_command="uv run python backfill_politicos_detalhes.py",
        cwd="/opt/airflow/injest_banco",
    )

    # Task B: Trata votações cujo idProposicao está nulo usando extração por string
    task_backfill_proposicoes = BashOperator(
        task_id="backfill_proposicoes_missing",
        bash_command="uv run python backfill_proposicoes.py",
        cwd="/opt/airflow/injest_banco",
    )

    # Task C: Varre a API buscando votações órfãs e valida se são administrativas ou vinculáveis
    task_backfill_votacoes_orfas = BashOperator(
        task_id="backfill_votacoes_orfas",
        bash_command="uv run python backfill_votacoes_orfas.py",
        cwd="/opt/airflow/injest_banco",
    )

    # Task D: Coleta novas fotos de políticos e aplica o upscaling com OpenCV + Modelo IA ESPCN
    task_injest_fotos_ia = BashOperator(
        task_id="injest_fotos_upscaling_ia",
        bash_command="uv run python injest_fotos.py",
        cwd="/opt/airflow/injest_banco",
    )

    # =========================================================================
    # Definição do Fluxo de Dependências
    # =========================================================================

    # Os backfills de políticos e proposições/votações podem rodar em paralelo para economizar tempo
    # A ingestão de fotos roda logo após o backfill de detalhes dos políticos coletar as novas URLs de fotos

    task_backfill_politicos >> task_injest_fotos_ia

    # Fluxo das proposições e votações órfãs
    task_backfill_proposicoes >> task_backfill_votacoes_orfas
