from .keybuilder import politico_key_builder
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.ranking_service import RankingService
from fastapi_cache.decorator import cache  
from backend.schemas import RankingDespesaPolitico, RankingEmpresaLucro, RankingDiscursoPolitico

router = APIRouter(
    prefix="/ranking",
    tags=["Ranking"]
)

@router.get("/despesa_politico",response_model=list[RankingDespesaPolitico])
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def ranking_despesas_politicos(
    q: str | None = None,
    uf: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    service = RankingService(db)
    return await service.get_ranking_despesas_politicos(q=q, uf=uf, limit=limit, offset=offset)


@router.get("/lucro_empresas", response_model=list[RankingEmpresaLucro])
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def ranking_lucro_empresas(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    service = RankingService(db)
    return await service.get_ranking_lucro_empresas(limit=limit, offset=offset)


@router.get("/discursos", response_model=list[RankingDiscursoPolitico])
@cache(expire=86400, namespace="quem-vota-cache", key_builder=politico_key_builder)
async def ranking_discursos(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    service = RankingService(db)
    return await service.get_ranking_discursos_politicos(limit=limit, offset=offset)