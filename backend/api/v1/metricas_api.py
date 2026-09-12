import logging
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_db

from backend.schemas import MetricasDeputado
from backend.services.metricas_factuais import get_metricas_factuais

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metricas",
    tags=["Métricas Factuais"],
)


@router.get(
    "/deputados/{id}",
    response_model=MetricasDeputado,
    summary="Obtém estatísticas factuais desagregadas de um deputado",
)
async def obter_metricas_deputado(
    id: int = Path(gt=0, description="ID interno do deputado"),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_metricas_factuais(db, id)
    except Exception as e:
        logger.error(f"Erro ao obter métricas do deputado {id}: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno ao processar métricas"
        )


from fastapi_cache.decorator import cache

@router.get(
    "/resumo",
    summary="Obtém o resumo comparativo de métricas de todos os deputados",
)
@cache(expire=3600)
async def obter_resumo_metricas(db: AsyncSession = Depends(get_db)):
    from backend.services.metricas_factuais import get_resumo_metricas_factuais

    try:
        return await get_resumo_metricas_factuais(db)
    except Exception as e:
        logger.error(f"Erro ao obter resumo de métricas: {e}")
        raise HTTPException(
            status_code=500, detail="Erro interno ao processar métricas"
        )
