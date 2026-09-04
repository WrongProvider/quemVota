FROM apache/airflow:2.8.1-python3.10

USER root

# CLI do Docker — necessário para o BashOperator falar com o socket montado
# e disparar `docker exec` / `docker run` em outros containers (api, ingest, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# uv + deps do projeto raiz (pandas, opencv, etc.) — necessário porque as DAGs
# de ETL/enriquecimento rodam "uv run python ..." direto neste container
# (Opção A). O alembic continua via docker exec no container da api (Opção B).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project
