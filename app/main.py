# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.services import (
    buscar_politico_por_nome,
    obter_politico_por_id,
)
from backend.schemas import PoliticoBase

app = FastAPI(
    title="QuemVota API",
    description="API pública de políticos brasileiros",
    version="0.1.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/politicos/busca", response_model=list[PoliticoBase])
def buscar_politicos(nome: str, db: Session = Depends(get_db)):
    resultados = buscar_politico_por_nome(nome, db)

    if not resultados:
        raise HTTPException(status_code=404, detail="Nenhum político encontrado")

    return resultados


@app.get("/politicos/{id_camara}", response_model=PoliticoBase)
def detalhes_politico(id_camara: int, db: Session = Depends(get_db)):
    politico = obter_politico_por_id(id_camara, db)

    if not politico:
        raise HTTPException(status_code=404, detail="Político não encontrado")

    return politico

@app.get("/politicos/{id_camara}/despesas")
def despesas_politico(id_camara: int, db: Session = Depends(get_db)):
    return obter_despesas(id_camara)
