from .keybuilder import politico_key_builder
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.ranking_service import RankingService
from fastapi_cache.decorator import cache  
from backend.schemas import RankingDespesaPolitico

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
