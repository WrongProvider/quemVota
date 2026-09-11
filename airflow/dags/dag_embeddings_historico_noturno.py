"""
dag_embeddings_historico_noturno.py
====================================
Pipeline noturno para geração de embeddings e classificação temática histórica:
- Vetorização em lotes contínuos das proposições históricas pendentes (pré-2026, 5000 itens por noite)
- Semeamento da taxonomia canônica de 20 temas de atuação
- Classificação temática dos parlamentares das legislaturas anteriores (Leg 56, 55...)
"""

from datetime import datetime, timezone, timedelta

from airflow.operators.bash import BashOperator

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
    "dag_embeddings_historico_noturno",
    default_args=default_args,
    description="Pipeline noturno de geração de embeddings e classificação temática pré-2026",
    schedule=None,  # Disparado pela dag_enriquecimento_historico_noturno
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["quemvota", "embeddings", "historico", "noturno"],
) as dag:
    # 0. Garante schema e migrações vetoriais atualizadas
    task_alembic_upgrade = BashOperator(
        task_id="alembic_upgrade_head",
        bash_command="docker exec quemvota_api alembic -c backend/alembic.ini upgrade head",
    )

    # 1. Garante taxonomia dos 20 temas de atuação semeada e vetorizada
    task_seed_temas = BashOperator(
        task_id="seed_temas_atuacao",
        bash_command="uv run python /opt/airflow/tasks/seed_temas_atuacao.py",
        cwd="/opt/airflow",
    )

    # 2. Gera embeddings semânticos das proposições históricas pendentes (limite de 5000 por noite)
    task_embeddings_historico = BashOperator(
        task_id="gerar_embeddings_historico_pre2026",
        bash_command="uv run python gerar_embeddings.py --pre-2026 --limit 5000",
        cwd="/opt/airflow/embeddings",
        execution_timeout=timedelta(hours=3),
    )

    # 3. Classifica temas e calcula perfil temático para parlamentares de legislaturas anteriores (56 e 55)
    task_classificar_temas_hist = BashOperator(
        task_id="classificar_temas_deputados_historico",
        bash_command="uv run python /opt/airflow/tasks/classificar_temas.py --legislaturas 56 55",
        cwd="/opt/airflow",
        execution_timeout=timedelta(hours=3),
    )

    (
        task_alembic_upgrade
        >> task_seed_temas
        >> task_embeddings_historico
        >> task_classificar_temas_hist
    )
