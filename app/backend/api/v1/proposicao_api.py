"""
Router de Proposições e Votações — Camada de transporte HTTP.

Segurança (OWASP):
  - A01 / Broken Access Control: apenas leitura (GET); sem endpoints de
    escrita expostos publicamente. Path params validados pelo Pydantic
    via Path(gt=0).
  - A03 / Excessive Data Exposure: response_model garante que somente os
    campos declarados no schema chegam ao cliente — nenhum campo extra vaza.
  - A04 / Insecure Design: query params com Query() possuem limites mínimos
    e máximos declarados; valores fora do intervalo são rejeitados pelo
    FastAPI com 422 antes de chegar ao serviço.
  - A09 / Logging & Monitoring: logs estruturados em todas as rotas (sem
    dados pessoais); nenhum stack trace chega ao cliente.

Endpoints expostos:
  GET /proposicoes/                     → lista proposições (filtros + paginação)
  GET /proposicoes/{id}                 → detalhe + tramitação + autores + temas
  GET /proposicoes/{id}/votacoes        → votações vinculadas a uma proposição
  GET /votacoes/                        → lista votações (filtros + paginação)
  GET /votacoes/{id}                    → detalhe + orientações por partido
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import (
    ProposicaoDetalhe,
    ProposicaoResponse,
    VotacaoDetalhe,
    VotacaoResponse,
)
from backend.services.proposicao_service import ProposicaoService
from fastapi_cache.decorator import cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos anotados para Query params — evita repetição e garante validação
# ---------------------------------------------------------------------------

LimitQuery  = Annotated[int, Query(ge=1, le=100, description="Máximo de itens por página")]
OffsetQuery = Annotated[int, Query(ge=0, description="Deslocamento para paginação")]

ProposicaoIdPath = Annotated[int, Path(gt=0, description="ID interno da proposição")]
VotacaoIdPath    = Annotated[int, Path(gt=0, description="ID interno da votação")]

# ---------------------------------------------------------------------------
# Routers — prefixos e tags separados para o Swagger ficar organizado
# ---------------------------------------------------------------------------

router_proposicoes = APIRouter(
    prefix="/proposicoes",
    tags=["Proposições"],
)

router_votacoes = APIRouter(
    prefix="/votacoes",
    tags=["Votações"],
)

# ---------------------------------------------------------------------------
# Helpers de injeção de dependência
# ---------------------------------------------------------------------------

def _proposicao_service(db: AsyncSession = Depends(get_db)) -> ProposicaoService:
    """Factory para injeção de dependência do serviço."""
    return ProposicaoService(db)


# ===========================================================================
# PROPOSIÇÕES
# ===========================================================================

@router_proposicoes.get(
    "/",
    response_model=list[ProposicaoResponse],
    summary="Lista proposições com filtros opcionais",
)
@cache(expire=3600)
async def listar_proposicoes(
    q: Annotated[
        str | None,
        Query(max_length=200, description="Busca por texto na ementa"),
    ] = None,
    sigla_tipo: Annotated[
        str | None,
        Query(max_length=10, description="Tipo da proposição: PL, PEC, MPV, PDC..."),
    ] = None,
    ano: Annotated[
        int | None,
        Query(ge=1988, le=2100, description="Ano de apresentação da proposição"),
    ] = None,
    tema_id: Annotated[
        int | None,
        Query(gt=0, description="ID interno de um tema legislativo"),
    ] = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
    service: ProposicaoService = Depends(_proposicao_service),
):
    """
    Retorna uma lista paginada de proposições.

    Todos os filtros são opcionais e combináveis:
    - **q**: busca livre na ementa (ex: `?q=reforma tributária`)
    - **sigla_tipo**: filtra por tipo (`PL`, `PEC`, `MPV`, `PDC`, `PRC`...)
    - **ano**: filtra por ano de apresentação
    - **tema_id**: filtra por tema legislativo (use `GET /temas` para listar)

    Retorna lista vazia se nenhum resultado for encontrado.
    """
    logger.info(
        "Listando proposições | q=%s sigla_tipo=%s ano=%s tema_id=%s limit=%s offset=%s",
        q, sigla_tipo, ano, tema_id, limit, offset,
    )
    return await service.listar_proposicoes_service(
        q=q,
        sigla_tipo=sigla_tipo,
        ano=ano,
        tema_id=tema_id,
        limit=limit,
        offset=offset,
    )


@router_proposicoes.get(
    "/{proposicao_id}",
    response_model=ProposicaoDetalhe,
    summary="Detalha uma proposição pelo ID",
    responses={404: {"description": "Proposição não encontrada"}},
)
@cache(expire=3600)
async def get_proposicao(
    proposicao_id: ProposicaoIdPath,
    service: ProposicaoService = Depends(_proposicao_service),
):
    """
    Retorna o detalhe completo de uma proposição.

    Inclui:
    - **autores**: deputados e entidades que assinaram a proposição
    - **temas**: temas legislativos associados
    - **tramitacoes**: histórico completo de movimentação entre órgãos,
      ordenado cronologicamente
    - **ementa_detalhada** e **justificativa**: textos completos

    Lança `404` se o ID não existir.
    """
    logger.info("Detalhe da proposição id=%s", proposicao_id)
    return await service.get_proposicao_service(proposicao_id)


@router_proposicoes.get(
    "/{proposicao_id}/votacoes",
    response_model=list[VotacaoResponse],
    summary="Votações vinculadas a uma proposição",
    responses={404: {"description": "Proposição não encontrada"}},
)
@cache(expire=3600)
async def get_votacoes_da_proposicao(
    proposicao_id: ProposicaoIdPath,
    service: ProposicaoService = Depends(_proposicao_service),
):
    """
    Retorna todas as votações realizadas sobre uma proposição específica.

    Uma proposição pode ter múltiplas votações (ex: votação em comissão
    e depois em plenário, ou votações de destaques e emendas).

    Retorna lista vazia se a proposição existir mas ainda não tiver sido
    votada (em tramitação). Lança `404` se a proposição não existir.
    """
    logger.info("Votações da proposição id=%s", proposicao_id)
    return await service.get_votacoes_da_proposicao_service(proposicao_id)


# ===========================================================================
# VOTAÇÕES
# ===========================================================================

@router_votacoes.get(
    "/",
    response_model=list[VotacaoResponse],
    summary="Lista votações com filtros opcionais",
)
@cache(expire=3600)
async def listar_votacoes(
    ano: Annotated[
        int | None,
        Query(ge=1988, le=2100, description="Ano da votação"),
    ] = None,
    aprovacao: Annotated[
        int | None,
        Query(description="Resultado: 1 = aprovada, 0 = rejeitada, -1 = indefinido"),
    ] = None,
    sigla_tipo: Annotated[
        str | None,
        Query(max_length=10, description="Tipo da proposição vinculada: PL, PEC..."),
    ] = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
    service: ProposicaoService = Depends(_proposicao_service),
):
    """
    Retorna uma lista paginada de votações.

    Todos os filtros são opcionais e combináveis:
    - **ano**: filtra por ano da votação
    - **aprovacao**: `1` (aprovada), `0` (rejeitada), `-1` (indefinido)
    - **sigla_tipo**: filtra pelo tipo da proposição votada (`PL`, `PEC`...)

    Inclui os dados da proposição vinculada diretamente na resposta,
    sem necessidade de um segundo request.

    Retorna lista vazia se nenhum resultado for encontrado.
    """
    logger.info(
        "Listando votações | ano=%s aprovacao=%s sigla_tipo=%s limit=%s offset=%s",
        ano, aprovacao, sigla_tipo, limit, offset,
    )
    return await service.listar_votacoes_service(
        ano=ano,
        aprovacao=aprovacao,
        sigla_tipo=sigla_tipo,
        limit=limit,
        offset=offset,
    )


@router_votacoes.get(
    "/{votacao_id}",
    response_model=VotacaoDetalhe,
    summary="Detalha uma votação pelo ID",
    responses={404: {"description": "Votação não encontrada"}},
)
@cache(expire=3600)
async def get_votacao(
    votacao_id: VotacaoIdPath,
    service: ProposicaoService = Depends(_proposicao_service),
):
    """
    Retorna o detalhe completo de uma votação.

    Inclui:
    - Todos os campos da listagem (proposição vinculada, resultado, tipo...)
    - **orientacoes**: como cada partido/bloco parlamentar orientou o voto
      de seus membros (`Sim`, `Não`, `Libera`, `Obstrução`)

    Lança `404` se o ID não existir.
    """
    logger.info("Detalhe da votação id=%s", votacao_id)
    return await service.get_votacao_service(votacao_id)