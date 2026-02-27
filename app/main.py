"""
main.py — Entrada da aplicação Quem Vota API.

Segurança (OWASP):
  - A05 Security Misconfiguration : CORS configurado com lista de origens
    explícita e restrita; método OPTIONS permitido (obrigatório para Preflight
    CORS — bloqueá-lo não aumenta segurança e quebra browsers modernos).
  - A09 Logging & Monitoring      : sem exposição de stack traces em respostas.
"""

from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from backend.api.v1 import politico_api, ranking_api, proposicao_api

# ─────────────────────────────────────────────────────────────────────────────
# Origens permitidas — edite aqui ao adicionar novos ambientes
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",        # React CRA / dev
    "http://localhost:5173",        # Vite dev
    # "https://quemvota.com.br",    # produção — descomente quando necessário
]

# ─────────────────────────────────────────────────────────────────────────────
# Headers que o cliente pode enviar — lista explícita (não "*")
#
# OWASP A05: nunca use allow_headers="*" em produção; declare apenas os headers
# que o seu frontend realmente envia.
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_HEADERS: list[str] = [
    "Accept",
    "Content-Type",
    "X-Requested-With",   # adicionado pelo client.ts refatorado
]

# ─────────────────────────────────────────────────────────────────────────────
# Métodos permitidos — API de leitura pública usa apenas GET
#
# OPTIONS é obrigatório: é o método do Preflight CORS enviado pelo browser.
# Bloqueá-lo não aumenta a segurança — o browser apenas recusa a requisição
# real antes mesmo de enviá-la, quebrando o frontend sem nenhum ganho.
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_METHODS: list[str] = [
    "GET",
    "HEAD",
    "OPTIONS",   # preflight CORS — obrigatório para qualquer header customizado
]


# ─────────────────────────────────────────────────────────────────────────────
# Ciclo de vida da aplicação
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    valkey_client = redis.from_url(
        "redis://localhost:6379",
        # "redis://valkey:6379", #produção — descomente quando necessário
        encoding="utf8",
        decode_responses=False,
    )
    FastAPICache.init(RedisBackend(valkey_client), prefix="quem-vota-cache")
    print("🚀 Valkey conectado e Cache inicializado!")

    yield  # API em execução

    # SHUTDOWN
    await valkey_client.close()
    print("🛑 Conexão com Valkey encerrada com sucesso.")


# ─────────────────────────────────────────────────────────────────────────────
# Instância FastAPI
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Quem Vota API",
    description="API pública de transparência legislativa",
    version="0.1.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS — deve ser adicionado ANTES dos routers
#
# allow_credentials=False: a API é pública e não usa cookies de sessão.
# Manter True com allow_origins específico seria seguro, mas False é mais
# correto para uma API de leitura pública sem autenticação por cookie.
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,      # sem cookies cross-origin
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    max_age=600,                  # browser cacheia o preflight por 10 min
                                  # reduz número de requisições OPTIONS
)

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(politico_api.router)
app.include_router(ranking_api.router)
app.include_router(proposicao_api.router_proposicoes)
app.include_router(proposicao_api.router_votacoes)


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root() -> dict:
    return {
        "status": "ok",
        "api": "Quem Vota",
        "docs": "/docs",
    }