from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from shared.config import settings

# 1. URLs de Conexão
# O Async precisa do driver +asyncpg, o Sync usa o padrão (psycopg2)
raw_url = settings.DATABASE_URL
ASYNC_URL = (
    raw_url.replace("postgresql://", "postgresql+asyncpg://")
    if "+asyncpg" not in raw_url
    else raw_url
)
SYNC_URL = ASYNC_URL.replace("+asyncpg", "")


class Base(DeclarativeBase):
    pass


# --- CONFIGURAÇÃO ASYNC (Para o FastAPI) ---
async_engine = create_async_engine(
    ASYNC_URL,
    echo=False,
    pool_size=15,
    max_overflow=25,
    pool_timeout=15,
    pool_recycle=1800,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# --- CONFIGURAÇÃO SYNC (Para os Scripts de Ingestão) ---
sync_engine = create_engine(SYNC_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)
