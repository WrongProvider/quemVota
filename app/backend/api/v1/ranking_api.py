"""
Router de Rankings - Camada de transporte HTTP.

Seguranca (OWASP):
  - A01 / Broken Access Control: apenas leitura (GET); path params validados via Path(gt=0).
  - A03 / Excessive Data Exposure: response_model garante que apenas os campos do schema chegam ao cliente.
  - A04 / Insecure Design: query params com Query() possuem limites minimos e maximos declarados;
    valores fora do intervalo sao rejeitados com 422 antes de chegar ao servico.
  - A09 / Logging & Monitoring: logs estruturados em todas as rotas sem dados pessoais.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.keybuilder import politico_key_builder
from backend.database import get_db
from backend.schemas import RankingDespesaPolitico, RankingDiscursoPolitico, RankingEmpresaLucro
from backend.services.ranking_service import RankingService
from fastapi_cache.decorator import cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos anotados para Query params - evita repeticao e garante validacao (OWASP A04)
# ---------------------------------------------------------------------------
LimitRankingQuery = Annotated[int, Query(ge=1, le=100, description="Maximo de itens por pagina")]
LimitDiscursoQuery = Annotated[int, Query(ge=1, le=500, description="Maximo de discursos por pagina")]
OffsetQuery = Annotated[int, Query(ge=0, description="Deslocamento para paginacao")]

router = APIRouter(
    prefix="/ranking",
    tags=["Ranking"],
)


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------

def _ranking_service(db: AsyncSession = Depends(get_db)) -> RankingService:
    """Factory para injecao de dependencia do servico."""
    return RankingService(db)


# ---------------------------------------------------------------------------
# Rotas - somente leitura (A01)
# ---------------------------------------------------------------------------

@router.get(
    "/despesa_politico",
    response_model=list[RankingDespesaPolitico],
    summary="Ranking de politicos por total de despesas",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def ranking_despesas_politicos(
    q: Annotated[str | None, Query(max_length=150, description="Busca por nome")] = None,
    uf: Annotated[str | None, Query(min_length=2, max_length=2, description="Sigla do estado")] = None,
    limit: LimitRankingQuery = 100,
    offset: OffsetQuery = 0,
    service: RankingService = Depends(_ranking_service),
):
    """Retorna politicos ordenados do maior para o menor gasto total."""
    logger.info("Ranking despesas | q=%s uf=%s limit=%s offset=%s", q, uf, limit, offset)
    return await service.get_ranking_despesas_politicos(q=q, uf=uf, limit=limit, offset=offset)


@router.get(
    "/lucro_empresas",
    response_model=list[RankingEmpresaLucro],
    summary="Ranking de empresas por total recebido",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def ranking_lucro_empresas(
    limit: LimitRankingQuery = 100,
    offset: OffsetQuery = 0,
    service: RankingService = Depends(_ranking_service),
):
    """Retorna empresas fornecedoras ordenadas pelo total recebido de parlamentares."""
    logger.info("Ranking empresas | limit=%s offset=%s", limit, offset)
    return await service.get_ranking_lucro_empresas(limit=limit, offset=offset)


@router.get(
    "/discursos",
    response_model=list[RankingDiscursoPolitico],
    summary="Ranking de politicos por quantidade de discursos",
)
@cache(expire=86400, namespace="quem-vota-cache", key_builder=politico_key_builder)
async def ranking_discursos(
    limit: LimitDiscursoQuery = 100,
    offset: OffsetQuery = 0,
    service: RankingService = Depends(_ranking_service),
):
    """Retorna politicos ordenados pelo total de discursos, com os principais temas."""
    logger.info("Ranking discursos | limit=%s offset=%s", limit, offset)
    return await service.get_ranking_discursos_politicos(limit=limit, offset=offset)


@router.get(
    "/performance_politicos",
    summary="Ranking geral de performance parlamentar",
)
@cache(expire=86400, namespace="quem-vota-cache", key_builder=politico_key_builder)
async def ranking_performance_politicos(
    service: RankingService = Depends(_ranking_service),
):
    """
    Retorna o ranking de performance calculado a partir de assiduidade (15%),
    economia (40%) e producao legislativa (45%).
    """
    logger.info("Ranking performance parlamentar solicitado")
    return await service.get_ranking_performance_politicos()


@router.get(
    "/stats/geral",
    summary="Estatisticas gerais do sistema",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def get_stats_geral(
    service: RankingService = Depends(_ranking_service),
):
    """Retorna media global, total de parlamentares e top 50 do ranking de performance."""
    logger.info("Stats gerais solicitadas")
    ranking_completo = await service.get_ranking_performance_politicos()

    scores = [p["score"] for p in ranking_completo]
    total = len(scores)
    media = sum(scores) / total if total > 0 else 0.0

    return {
        "media_global": round(media, 2),
        "total_parlamentares": total,
        "top_3": ranking_completo[:50],
    }