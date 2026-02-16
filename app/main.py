from fastapi import FastAPI
from backend.api.v1 import politico_api
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# 1. Definimos o que acontece durante a vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP (O que acontece ao ligar) ---
    # Conecta ao Valkey
    valkey_client = redis.from_url(
        "redis://localhost:6379", 
        encoding="utf8", 
        decode_responses=False
    )
    
    
    # Inicializa o Cache
    FastAPICache.init(RedisBackend(valkey_client), prefix="quem-vota-cache")
    
    print("🚀 Valkey conectado e Cache inicializado!")
    
    yield # Aqui é onde a API "vive" e atende requisições
    
    # --- SHUTDOWN (O que acontece ao desligar) ---
    await valkey_client.close()
    print("🛑 Conexão com Valkey encerrada com sucesso.")

# 2. Passamos o lifespan para a instância do FastAPI
app = FastAPI(
    title="Quem Vota API",
    description="API pública de transparência legislativa",
    version="0.1.0",
    lifespan=lifespan
)


app.include_router(politico_api.router)
# app.include_router(evento.router)
# app.include_router(orgao.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", # react
        "http://localhost:5173", # vite
    ],
    allow_credentials=True,
    allow_methods=["GET,HEAD"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    return {
        "status": "ok",
        "api": "Quem Vota",
        "docs": "/docs"
    }
