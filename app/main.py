from fastapi import FastAPI
from backend.routers import politico
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Quem Vota API",
    description="API pública de transparência legislativa",
    version="0.1.0"
)

app.include_router(politico.router)
# app.include_router(evento.router)
# app.include_router(orgao.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET,HEAD"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "api": "Quem Vota",
        "docs": "/docs"
    }
