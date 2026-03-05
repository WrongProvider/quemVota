from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.database import get_db
from typing import List
from backend.schemas import MaisPesquisadoSchema
from backend.services.busca_popular import registrar_busca, obter_mais_pesquisados

router = APIRouter(prefix="/busca", tags=["busca"])


@router.post(
    "/registrar/{deputado_id}",
    status_code=204,
    summary="Registra uma visualização de um deputado",
)
async def registrar(
    deputado_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Chamado pelo frontend quando o usuário abre o perfil de um deputado.
    Usa BackgroundTasks para não atrasar a resposta ao usuário.
    """
    if deputado_id <= 0:
        raise HTTPException(status_code=422, detail="ID inválido.")
    background_tasks.add_task(registrar_busca, db, deputado_id)


@router.get(
    "/mais-pesquisados",
    response_model=List[MaisPesquisadoSchema],
    summary="Retorna os N deputados mais buscados",
)
def mais_pesquisados(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if not (1 <= limit <= 50):
        raise HTTPException(status_code=422, detail="limit deve estar entre 1 e 50.")
    return obter_mais_pesquisados(db, limit)