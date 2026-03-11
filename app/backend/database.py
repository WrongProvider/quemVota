import os
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine

# 1. URLs de Conexão
# O Async precisa do driver +asyncpg, o Sync usa o padrão (psycopg2)
ASYNC_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/quemvota")
SYNC_URL = ASYNC_URL.replace("+asyncpg", "") # Remove o driver async para o engine sync

class Base(DeclarativeBase):
    pass

# --- CONFIGURAÇÃO ASYNC (Para o FastAPI) ---
async_engine = create_async_engine(ASYNC_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# --- CONFIGURAÇÃO SYNC (Para os Scripts de Ingestão) ---
sync_engine = create_engine(SYNC_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)