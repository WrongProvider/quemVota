FROM apache/airflow:2.8.1-python3.10

USER root

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER airflow
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
