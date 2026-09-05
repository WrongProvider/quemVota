from datetime import datetime, timedelta

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
        bash_command="uv run python gerar_embeddings.py --legislatura 57 --limit 2000",
        cwd="/opt/airflow/embeddings",
        execution_timeout=timedelta(hours=2),
    )

    # Garante que a taxonomia canônica de 20 temas de atuação esteja semeada e vetorizada
    task_seed_temas = BashOperator(
        task_id="seed_temas_atuacao",
        bash_command="uv run python /opt/airflow/tasks/seed_temas_atuacao.py",
        cwd="/opt/airflow",
    )

    # Classifica proposições e agrega o perfil temático dos parlamentares da legislatura (SPEC-001)
    task_classificar_temas = BashOperator(
        task_id="classificar_temas_deputados",
        bash_command="uv run python /opt/airflow/tasks/classificar_temas.py --legislatura 57",
        cwd="/opt/airflow",
    )

    (
        task_alembic_upgrade
        >> task_update_embeddings
        >> task_seed_temas
        >> task_classificar_temas
    )
