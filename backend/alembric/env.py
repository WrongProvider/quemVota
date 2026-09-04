from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import dos modelos para registro no autogenerate
import shared.models  # noqa: F401 — registra modelos da API Câmara
import shared.models_vetorial  # noqa: F401 — registra camada vetorial / IA

# Importa a Base e a SYNC_URL tratada diretamente da sua central de banco
from shared.database import SYNC_URL, Base

# Objeto de configuração do Alembic
config = context.config

# Define a URL de conexão síncrona (psycopg2 / psycopg)
config.set_main_option("sqlalchemy.url", str(SYNC_URL))

# Configura o sistema de logs do Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define os metadados dos modelos para detecção automática (autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline'.

    Gera os scripts SQL diretamente sem abrir uma conexão ativa com o banco.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações no modo 'online'.

    Cria uma engine síncrona e aplica as migrações diretamente na base de dados.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
