import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import AsyncClient, ASGITransport
from main import app
from database import get_db
from config import settings


@pytest.fixture(autouse=True, scope="session")
def setup_cache():
    FastAPICache.init(InMemoryBackend(), prefix="test-cache")


@pytest.fixture(scope="session")
async def engine():
    _engine = create_async_engine(settings.DATABASE_URL)
    yield _engine
    await _engine.dispose()

@pytest.fixture(autouse=True, scope="session")
async def seed_db(engine):
    with open("tests/fixtures.sql") as f:
        sql = f.read()
    linhas = [lines for lines in sql.splitlines() if not lines.strip().startswith("--")]
    sql_limpo = "\n".join(linhas)
    statements = [s.strip() for s in sql_limpo.split(";") if s.strip()]

    async with engine.begin() as conn:
        await conn.execute(text(
        "TRUNCATE TABLE deputados, partidos, legislaturas RESTART IDENTITY CASCADE"
    ))
        for statement in statements:
            await conn.execute(text(statement))

    yield  # testes rodam aqui

    # cleanup
    async with engine.begin() as conn:
        await conn.execute(text(
            "TRUNCATE TABLE deputados, partidos, legislaturas RESTART IDENTITY CASCADE"
        ))
 
@pytest.fixture(scope="session")       
async def client(engine):  # <- recebe o engine da session
    # sobrescreve o get_db da app para usar o mesmo engine
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with async_session() as session:
            yield session
            await session.close()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()

