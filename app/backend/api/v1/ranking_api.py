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
LimitRankingQuery  = Annotated[int, Query(ge=1, le=100, description="Maximo de itens por pagina")]
LimitDiscursoQuery = Annotated[int, Query(ge=1, le=500, description="Maximo de discursos por pagina")]
OffsetQuery        = Annotated[int, Query(ge=0, description="Deslocamento para paginacao")]
AnoQuery           = Annotated[int | None, Query(ge=2011, le=2030, description="Ano de referência (2011+). Quando informado, o ranking compara apenas deputados com dados naquele ano, eliminando vantagem de mandatos mais longos.")]
QNomeQuery         = Annotated[str | None, Query(max_length=150, description="Busca parcial por nome do parlamentar (case-insensitive)")]
UFQuery            = Annotated[str | None, Query(min_length=2, max_length=2, description="Sigla do estado (ex: SP, RJ)")]
PartidoQuery       = Annotated[str | None, Query(max_length=20, description="Sigla do partido (ex: PT, PL)")]

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
    ano: AnoQuery = None,
    q: QNomeQuery = None,
    uf: UFQuery = None,
    partido: PartidoQuery = None,
    service: RankingService = Depends(_ranking_service),
):
    """
    Retorna o ranking de performance calculado a partir de assiduidade (15%),
    economia (40%) e producao legislativa (45%).

    **Filtros disponíveis:**
    - `ano`     — restringe o ranking a um único ano calendário. Todos os
                  parlamentares são comparados no **mesmo período**, eliminando
                  a vantagem de deputados com mandatos mais longos. Ideal para
                  construir a timeline histórica do ranking.
    - `q`       — busca parcial por nome do parlamentar.
    - `uf`      — filtra por estado (ex: `SP`, `MG`).
    - `partido` — filtra por sigla do partido (ex: `PT`, `PL`).

    **Nota:** inclui apenas parlamentares a partir da legislatura 54 (eleitos em 2010,
    em exercício a partir de 2011). Deputados de legislaturas anteriores à 54
    (eleitos antes de 2010) não registravam gastos de forma sistemática na plataforma
    da Câmara, o que tornaria a comparação injusta e os scores distorcidos.
    Parlamentares de legislaturas anteriores à 53 (antes de 2008) não tinham
    obrigação de registro e estão completamente ausentes da base de dados.
    """
    logger.info(
        "Ranking performance parlamentar | ano=%s q=%s uf=%s partido=%s",
        ano, q, uf, partido,
    )
    ranking = await service.get_ranking_performance_politicos(
        ano=ano, q=q, uf=uf, partido=partido
    )

    aviso = (
        "Este ranking considera apenas parlamentares eleitos a partir de 2010 "
        "(legislatura 54+). Deputados de legislaturas anteriores não registravam "
        "gastos de forma sistemática. Antes de 2008 (legislatura 52 e anteriores), "
        "não havia obrigatoriedade de registro de despesas."
    )
    if ano is not None:
        aviso += (
            f" Ranking filtrado para o ano {ano}: apenas parlamentares com despesas "
            f"registradas nesse período estão incluídos."
        )

    return {
        "aviso": aviso,
        "ano_referencia": ano,
        "total": len(ranking),
        "ranking": ranking,
    }


@router.get(
    "/stats/geral",
    summary="Estatisticas gerais do sistema",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def get_stats_geral(
    ano: AnoQuery = None,
    q: QNomeQuery = None,
    uf: UFQuery = None,
    partido: PartidoQuery = None,
    service: RankingService = Depends(_ranking_service),
):
    """
    Retorna media global, total de parlamentares e top 50 do ranking de performance.

    Aceita os mesmos filtros de `/performance_politicos`:
    - `ano`     — calcula as estatísticas para um ano específico (ranking anual).
    - `q`       — filtra por nome.
    - `uf`      — filtra por estado.
    - `partido` — filtra por partido.
    """
    logger.info("Stats gerais | ano=%s q=%s uf=%s partido=%s", ano, q, uf, partido)
    ranking_completo = await service.get_ranking_performance_politicos(
        ano=ano, q=q, uf=uf, partido=partido
    )

    scores = [p["score"] for p in ranking_completo]
    total  = len(scores)
    media  = sum(scores) / total if total > 0 else 0.0

    aviso = (
        "Estatísticas calculadas apenas sobre parlamentares eleitos a partir de 2010 "
        "(legislatura 54+). Deputados de legislaturas anteriores não registravam "
        "gastos de forma sistemática. Antes de 2008 (legislatura 52 e anteriores), "
        "não havia obrigatoriedade de registro de despesas."
    )
    if ano is not None:
        aviso += (
            f" Estatísticas referentes ao ano {ano}: apenas parlamentares com "
            f"despesas registradas nesse período estão incluídos."
        )

    return {
        "aviso": aviso,
        "ano_referencia": ano,
        "media_global": round(media, 2),
        "total_parlamentares": total,
        "top_50": ranking_completo[:50],
    }