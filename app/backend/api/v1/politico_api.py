"""
Router de Políticos — Camada de transporte HTTP.

Segurança (OWASP):
  - A01 / Broken Access Control: apenas leitura (GET); sem endpoints de escrita
    expostos publicamente. Path params validados pelo Pydantic via `Path(gt=0)`.
  - A03 / Excessive Data Exposure: `response_model` garante que somente os campos
    declarados no schema chegam ao cliente — nenhum campo extra vaza.
  - A04 / Insecure Design: query params com `Query()` possuem limites mínimos e
    máximos declarados; valores fora do intervalo são rejeitados pelo FastAPI com
    422 antes de chegar ao serviço.
  - A05 / Security Misconfiguration: cabeçalhos de segurança adicionados via
    middleware (ver `security_headers`). Cache-Control definido explicitamente.
  - A09 / Logging & Monitoring: logs estruturados em todas as rotas (sem dados
    pessoais); nenhum stack trace chega ao cliente.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import (
    PoliticoDespesaDetalhe,
    PoliticoDespesaResumo,
    PoliticoDespesaResumoCompleto,
    PoliticoEstatisticasResponse,
    PoliticoResponse,
    PoliticoVoto,
)
from backend.services.politico_service import PoliticoService
from backend.api.v1.keybuilder import politico_key_builder
from fastapi_cache.decorator import cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos anotados para Query params
# ---------------------------------------------------------------------------
LimitQuery      = Annotated[int, Query(ge=1, le=100, description="Máximo de itens por página")]
OffsetQuery     = Annotated[int, Query(ge=0, description="Deslocamento para paginação")]
PoliticoIdPath  = Annotated[int, Path(gt=0, description="ID interno do político")]
AnoQuery        = Annotated[int | None, Query(ge=2000, le=2100, description="Filtro por ano")]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(
    prefix="/politicos",
    tags=["Políticos"],
)


def _politico_service(db: AsyncSession = Depends(get_db)) -> PoliticoService:
    return PoliticoService(db)


# ---------------------------------------------------------------------------
# Rotas — somente leitura
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[PoliticoResponse],
    summary="Lista políticos com filtros opcionais",
)
@cache(expire=3600, key_builder=politico_key_builder)
async def listar_politicos(
    q: Annotated[str | None, Query(max_length=150, description="Busca por nome")] = None,
    uf: Annotated[str | None, Query(min_length=2, max_length=2, description="Sigla do estado")] = None,
    partido: Annotated[str | None, Query(min_length=1, max_length=20, description="Sigla do partido")] = None,
    limit: LimitQuery = 100,
    offset: OffsetQuery = 0,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Listando políticos | q=%s uf=%s partido=%s limit=%s offset=%s", q, uf, partido, limit, offset)
    return await service.get_politicos_service(q=q, uf=uf, partido=partido, limit=limit, offset=offset)


@router.get(
    "/{politico_id}",
    response_model=PoliticoResponse,
    summary="Detalha um político pelo ID",
    responses={404: {"description": "Político não encontrado"}},
)
@cache(expire=3600, key_builder=politico_key_builder)
async def get_politico(
    politico_id: PoliticoIdPath,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Detalhe do político id=%s", politico_id)
    return await service.get_politicos_detalhe_service(politico_id)


@router.get(
    "/{politico_id}/votacoes",
    response_model=list[PoliticoVoto],
    summary="Últimas votações de um político",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def ultimas_votacoes(
    politico_id: PoliticoIdPath,
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    ano: AnoQuery = None,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Votações | político id=%s limit=%s ano=%s", politico_id, limit, ano)
    return await service.get_politicos_votacoes_service(politico_id, limit=limit, ano=ano)


@router.get(
    "/{politico_id}/despesas",
    response_model=list[PoliticoDespesaDetalhe],
    summary="Despesas individuais paginadas",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def listar_despesas_detalhadas(
    politico_id: PoliticoIdPath,
    ano: AnoQuery = None,
    mes: Annotated[int | None, Query(ge=1, le=12)] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Despesas | político id=%s ano=%s mes=%s", politico_id, ano, mes)
    return await service.get_politicos_despesas_services(politico_id, ano=ano, mes=mes, limit=limit)


@router.get(
    "/{politico_id}/despesas/resumo",
    response_model=list[PoliticoDespesaResumo],
    summary="Resumo mensal de gastos",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def resumo_despesas(
    politico_id: PoliticoIdPath,
    ano: AnoQuery = None,
    limit: Annotated[int, Query(ge=1, le=60)] = 60,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Resumo despesas | político id=%s ano=%s", politico_id, ano)
    return await service.get_politicos_despesas_resumo_services(politico_id, ano=ano, limit=limit)


@router.get(
    "/{politico_id}/despesas/resumo_completo",
    response_model=PoliticoDespesaResumoCompleto,
    summary="Resumo completo: histórico + top fornecedores + categorias",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def resumo_despesas_completo(
    politico_id: PoliticoIdPath,
    ano: AnoQuery = None,
    limit_meses: Annotated[int, Query(ge=1, le=60)] = 60,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Resumo completo despesas | político id=%s ano=%s", politico_id, ano)
    return await service.get_politicos_despesas_resumo_completo_services(
        politico_id, ano=ano, limit_meses=limit_meses
    )


@router.get(
    "/{politico_id}/estatisticas",
    response_model=PoliticoEstatisticasResponse,
    summary="Estatísticas gerais do político",
    description=(
        "Retorna totais de votações, despesas, gastos e média mensal. "
        "Use `ano` para filtrar um ano específico e comparar na linha do tempo."
    ),
)
@cache(expire=86400, key_builder=politico_key_builder)
async def estatisticas(
    politico_id: PoliticoIdPath,
    ano: AnoQuery = None,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Estatísticas | político id=%s ano=%s", politico_id, ano)
    return await service.get_politico_estatisticas_service(politico_id, ano=ano)


@router.get(
    "/{politico_id}/performance",
    response_model=dict,
    summary="Score de performance parlamentar",
    description=(
        "Calcula assiduidade (15%), economia (40%) e produção (45%). "
        "Use `ano` para obter o score de um ano específico — "
        "útil para comparação justa na linha do tempo."
    ),
    responses={404: {"description": "Político não encontrado"}},
)
@cache(expire=86400, key_builder=politico_key_builder)
async def performance(
    politico_id: PoliticoIdPath,
    ano: AnoQuery = None,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Performance | político id=%s ano=%s", politico_id, ano)
    return await service.get_politico_performance_service(politico_id, ano=ano)


@router.get(
    "/{politico_id}/timeline",
    response_model=list[dict],
    summary="Linha do tempo anual do parlamentar",
    description=(
        "Retorna a evolução ano a ano do score de performance, estatísticas "
        "e gastos do parlamentar. Cada item representa um ano com dados registrados. "
        "Ideal para exibir gráficos de evolução histórica e comparar mandatos."
    ),
    responses={404: {"description": "Político não encontrado"}},
)
@cache(expire=86400, key_builder=politico_key_builder)
async def timeline(
    politico_id: PoliticoIdPath,
    service: PoliticoService = Depends(_politico_service),
):
    """
    Exemplo de resposta:
    ```json
    [
      {
        "ano": 2023,
        "score": 61.4,
        "notas": { "assiduidade": 87.0, "economia": 74.2, "producao": 38.5 },
        "estatisticas": {
          "total_votacoes": 142,
          "total_despesas": 89,
          "total_gasto": 312400.0,
          "media_mensal": 26033.33
        },
        "info": {
          "valor_cota_mensal": 42837.33,
          "meses_ativos": 12,
          "cota_total": 514047.96,
          "cota_utilizada_pct": 60.73
        }
      }
    ]
    ```
    """
    logger.info("Timeline | político id=%s", politico_id)
    return await service.get_politico_timeline_service(politico_id)