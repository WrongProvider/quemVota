"""
dag_etl_camara_manual.py
========================
DAG sob demanda para execução manual do ETL da Câmara dos Deputados.
Permite configurar todos os parâmetros de execução (modo, anos, limites,
flags de cache e reconciliação) diretamente pela interface do Airflow
(Trigger DAG w/ config).
"""

from datetime import datetime, timezone, timedelta

from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from airflow import DAG

default_args = {
    "owner": "quemvota",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

# Template dinâmico para construção do comando etl_camara.py
ETL_BASH_TEMPLATE = (
    "uv run python etl_camara.py "
    "{% if params.modo == 'full' %}--full "
    "{% elif params.modo == 'historico' %}--historico "
    "{% elif params.modo == 'dry-run' %}--dry-run "
    "{% elif params.modo == 'dataset' and params.dataset %}--dataset {{ params.dataset }} "
    "{% else %}--update {% endif %}"
    "{% if params.modo != 'dataset' and params.dataset %}--dataset {{ params.dataset }} {% endif %}"
    "{% if params.reconcile_orfas %}--reconcile-orfas {% endif %}"
    "{% if params.force %}--force {% endif %}"
    "{% if params.anos %}--anos {{ params.anos }} {% endif %}"
    "{% if params.limit and params.limit > 0 %}--limit {{ params.limit }} {% endif %}"
    "{% if params.backfill_deputados %}--backfill-deputados {% endif %}"
    "{% if params.backfill_slug_only %}--backfill-slug-only {% endif %}"
)

ALEMBIC_BASH_TEMPLATE = (
    "{% if params.alembic_upgrade %}"
    "docker exec quemvota_api alembic -c backend/alembic.ini upgrade head "
    "{% else %}"
    "echo 'Alembic upgrade ignorado por parâmetro' "
    "{% endif %}"
)

SYNC_GRAPH_BASH_TEMPLATE = (
    "{% if params.sync_graph %}"
    "uv run python /opt/airflow/tasks/sync_graph.py "
    "{% if params.modo == 'historico' %}--pre-2026 "
    "{% elif params.modo == 'full' %}--todas-legislaturas "
    "{% else %}--legislatura 57 {% endif %}"
    "{% else %}"
    "echo 'Sincronização de grafo AGE ignorada por parâmetro' "
    "{% endif %}"
)


def decide_enriquecimento(**context) -> str:
    """Decide se dispara dag_enriquecimento_dados com base no parâmetro."""
    params = context.get("params", {})
    if params.get("trigger_enriquecimento"):
        return "trigger_enriquecimento_dados"
    return "fim_sem_enriquecimento"


with DAG(
    "dag_etl_camara_manual",
    default_args=default_args,
    description="Execução sob demanda do ETL da Câmara com parâmetros configuráveis na UI",
    schedule=None,  # Apenas execução manual
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["quemvota", "etl", "camara", "manual"],
    params={
        "modo": Param(
            "update",
            type="string",
            enum=["update", "historico", "full", "dry-run", "dataset"],
            description=(
                "Modo de execução do ETL: "
                "'update' (apenas ano corrente 2026), "
                "'historico' (dados pré-2026, anos 2008 a 2025 e L51 a L56), "
                "'full' (histórico completo 2008-hoje), "
                "'dry-run' (validação e contagem sem escrita no banco) ou "
                "'dataset' (apenas o prefixo informado em 'dataset')"
            ),
        ),
        "dataset": Param(
            "",
            type="string",
            description=(
                "Prefixo de dataset específico (ex: 'votacoes', 'deputados', "
                "'proposicoes', 'orgaos'). Deixe vazio para rodar todos do modo."
            ),
        ),
        "anos": Param(
            "",
            type="string",
            description=(
                "Anos específicos separados por espaço (ex: '2024 2025 2026'). "
                "Deixe vazio para usar o padrão do modo selecionado."
            ),
        ),
        "limit": Param(
            0,
            type="integer",
            minimum=0,
            description="Limitar número de datasets a processar (0 = sem limite, ideal p/ testes rápidos)",
        ),
        "force": Param(
            False,
            type="boolean",
            description="Forçar download ignorando cache de ETag (reprocessa tudo)",
        ),
        "reconcile_orfas": Param(
            True,
            type="boolean",
            description="Executar reconciliação de votações e proposições órfãs após a carga",
        ),
        "backfill_deputados": Param(
            False,
            type="boolean",
            description="Executar enriquecimento de deputados incompletos via API REST",
        ),
        "backfill_slug_only": Param(
            False,
            type="boolean",
            description="Apenas recalcular slugs de deputados a partir do nome sem chamar API REST",
        ),
        "alembic_upgrade": Param(
            True,
            type="boolean",
            description="Executar 'alembic upgrade head' no container da API antes da carga",
        ),
        "sync_graph": Param(
            False,
            type="boolean",
            description="Sincronizar dados para o grafo Apache AGE após o término do ETL",
        ),
        "trigger_enriquecimento": Param(
            False,
            type="boolean",
            description="Disparar automaticamente a DAG 'dag_enriquecimento_dados' ao concluir",
        ),
    },
) as dag:
    # 1. Migração de banco (opcional conforme parâmetro alembic_upgrade)
    task_alembic = BashOperator(
        task_id="alembic_upgrade_head",
        bash_command=ALEMBIC_BASH_TEMPLATE,
    )

    # 2. Execução do ETL parametrizado
    task_etl_manual = BashOperator(
        task_id="executar_etl_camara",
        bash_command=ETL_BASH_TEMPLATE,
        cwd="/opt/airflow/injest_banco",
    )

    # 3. Sincronização do Grafo Apache AGE (opcional conforme parâmetro sync_graph)
    task_sync_graph = BashOperator(
        task_id="sync_graph_age",
        bash_command=SYNC_GRAPH_BASH_TEMPLATE,
        cwd="/opt/airflow",
    )

    # 4. Decisão de disparo do pipeline de enriquecimento
    task_branch_enriquecimento = BranchPythonOperator(
        task_id="verificar_disparo_enriquecimento",
        python_callable=decide_enriquecimento,
    )

    task_trigger_enriquecimento = TriggerDagRunOperator(
        task_id="trigger_enriquecimento_dados",
        trigger_dag_id="dag_enriquecimento_dados",
        wait_for_completion=False,
    )

    task_fim_sem_enriquecimento = EmptyOperator(
        task_id="fim_sem_enriquecimento",
    )

    (
        task_alembic
        >> task_etl_manual
        >> task_sync_graph
        >> task_branch_enriquecimento
        >> [task_trigger_enriquecimento, task_fim_sem_enriquecimento]
    )
