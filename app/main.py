from fastapi import FastAPI
from backend.routers import politico

app = FastAPI(
    title="Quem Vota API",
    description="API pública de transparência legislativa",
    version="0.1.0"
)

app.include_router(politico.router)
# app.include_router(evento.router)
# app.include_router(orgao.router)
