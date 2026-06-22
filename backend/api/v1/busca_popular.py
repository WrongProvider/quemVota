from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from shared.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rate_limit import limiter
from backend.schemas import MaisPesquisadoSchema
from backend.services.busca_popular import obter_mais_pesquisados, registrar_busca

router = APIRouter(prefix="/busca", tags=["busca"])


@router.post(
    "/registrar/{deputado_id}",
    status_code=204,
    summary="Registra uma visualização de um deputado",
)
@limiter.limit("10/minute")
async def registrar(
    request: Request,
    deputado_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Chamado pelo frontend quando o usuário abre o perfil de um deputado.
    Usa BackgroundTasks para não atrasar a resposta ao usuário.
    """
    if deputado_id <= 0:
        raise HTTPException(status_code=422, detail="ID inválido.")
    background_tasks.add_task(registrar_busca, db, deputado_id)


@router.get("/mais-pesquisados", response_model=List[MaisPesquisadoSchema])
async def mais_pesquisados(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    if not (1 <= limit <= 50):
        raise HTTPException(status_code=422, detail="limit deve estar entre 1 e 50.")
    return await obter_mais_pesquisados(db, limit)
