import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import AsyncClient, ASGITransport
from main import app
from config import settings

@pytest.fixture(autouse=True, scope="session")
def setup_cache():
    FastAPICache.init(InMemoryBackend(), prefix="test-cache")

@pytest.fixture(autouse=True, scope="session")
async def seed_db():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        with open("tests/fixtures.sql") as f:
            await conn.execute(text(f.read()))
    await engine.dispose()

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c
