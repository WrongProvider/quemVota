"""
Router de Deputados — Camada de transporte HTTP.

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

from datetime import date
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from fastapi_cache.decorator import cache
from shared.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.keybuilder import politico_key_builder
from backend.schemas import (
    AfinidadesPoliticoResponse,
    AtividadeLegislativaResponse,
    ComparacaoPoliticosGrafoResponse,
    FidelidadePartidariaResponse,
    PoliticoDespesaDetalhe,
    PoliticoDespesaResumo,
    PoliticoDespesaResumoCompleto,
    PoliticoEstatisticasResponse,
    PoliticoResponse,
    PoliticoVoto,
    ProposicaoParaPolitico,
    RedeCoautoriaResponse,
)
from backend.services.politico_service import PoliticoService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tipos anotados para Query params
# ---------------------------------------------------------------------------
LimitQuery = Annotated[
    int, Query(ge=1, le=100, description="Máximo de itens por página")
]
OffsetQuery = Annotated[int, Query(ge=0, description="Deslocamento para paginação")]
DeputadoIdPath = Annotated[int, Path(gt=0, description="ID interno do deputado")]
DeputadoSlugPath = Annotated[
    str, Path(min_length=1, max_length=120, description="Slug ou ID do deputado")
]
AnoQuery = Annotated[int | None, Query(ge=2000, le=2100, description="Filtro por ano")]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(
    prefix="/politicos",
    tags=["Deputados"],
)


def _politico_service(db: AsyncSession = Depends(get_db)) -> PoliticoService:
    return PoliticoService(db)


# ---------------------------------------------------------------------------
# Rotas — somente leitura
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[PoliticoResponse],
    summary="Lista deputados com filtros opcionais",
)
@cache(expire=3600, key_builder=politico_key_builder)
async def listar_politicos(
    q: Annotated[
        str | None, Query(max_length=150, description="Busca por nome")
    ] = None,
    uf: Annotated[
        str | None, Query(min_length=2, max_length=2, description="Sigla do estado")
    ] = None,
    partido: Annotated[
        str | None, Query(min_length=1, max_length=20, description="Sigla do partido")
    ] = None,
    limit: LimitQuery = 100,
    offset: OffsetQuery = 0,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info(
        "Listando deputados | q=%s uf=%s partido=%s limit=%s offset=%s",
        q,
        uf,
        partido,
        limit,
        offset,
    )
    return await service.get_politicos_service(
        q=q, uf=uf, partido=partido, limit=limit, offset=offset
    )


@router.get(
    "/slug/{slug}",
    response_model=PoliticoResponse,
    summary="Detalha um deputado pelo slug do nome",
    responses={404: {"description": "Deputado não encontrado"}},
)
@cache(expire=3600, key_builder=politico_key_builder)
async def get_politico_by_slug(
    slug: Annotated[
        str, Path(min_length=1, max_length=120, description="Slug do nome do deputado")
    ],
    service: PoliticoService = Depends(_politico_service),
):
    """
    Busca um deputado pelo slug do nome (ex: `joao-silva-neto`).
    Retorna os mesmos dados que o endpoint por ID.
    """
    logger.info("Detalhe do deputado slug=%s", slug)
    return await service.get_politico_by_slug_service(slug)


@router.get(
    "/comparar/{id_or_slug1}/{id_or_slug2}",
    response_model=ComparacaoPoliticosGrafoResponse,
    summary="Compara posicionamento de votos entre 2 políticos (Apache AGE Graph)",
    description=(
        "Executa análise comparativa do histórico de votações entre dois deputados. "
        "Prioriza travessia de grafo no Apache AGE com fallback de reconciliação relacional. "
        "Calcula taxa de alinhamento percentual e lista principais divergências e votos alinhados "
        "de maneira estritamente factual e neutra."
    ),
    responses={
        400: {"description": "Parâmetros inválidos ou mesmo deputado informado"},
        404: {"description": "Deputado não encontrado"},
    },
)
@cache(expire=3600, key_builder=politico_key_builder)
async def comparar_politicos(
    id_or_slug1: Annotated[
        str,
        Path(min_length=1, max_length=120, description="Slug ou ID do 1º parlamentar"),
    ],
    id_or_slug2: Annotated[
        str,
        Path(min_length=1, max_length=120, description="Slug ou ID do 2º parlamentar"),
    ],
    tema: Annotated[
        Optional[str], Query(max_length=100, description="Filtro por tema legislativo")
    ] = None,
    limit_divergencias: Annotated[
        int, Query(ge=1, le=100, description="Limite de divergências a exibir")
    ] = 50,
    limit_alinhamentos: Annotated[
        int, Query(ge=1, le=100, description="Limite de alinhamentos a exibir")
    ] = 20,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info(
        "Comparando politicos | %s vs %s | tema=%s | lim_div=%s lim_aln=%s",
        id_or_slug1,
        id_or_slug2,
        tema,
        limit_divergencias,
        limit_alinhamentos,
    )
    return await service.comparar_politicos_service(
        id_or_slug1=id_or_slug1,
        id_or_slug2=id_or_slug2,
        tema=tema,
        limit_divergencias=limit_divergencias,
        limit_alinhamentos=limit_alinhamentos,
    )


@router.get(
    "/{politico_id}/comparar/{outro_politico_id}",
    response_model=ComparacaoPoliticosGrafoResponse,
    summary="Compara deputado com outro parlamentar (Apache AGE Graph)",
    description="Alias para a rota de comparação entre dois parlamentares.",
    responses={
        400: {"description": "Parâmetros inválidos ou mesmo deputado informado"},
        404: {"description": "Deputado não encontrado"},
    },
)
@cache(expire=3600, key_builder=politico_key_builder)
async def comparar_politicos_alias(
    politico_id: Annotated[
        str,
        Path(min_length=1, max_length=120, description="Slug ou ID do deputado base"),
    ],
    outro_politico_id: Annotated[
        str,
        Path(min_length=1, max_length=120, description="Slug ou ID do outro deputado"),
    ],
    tema: Annotated[
        Optional[str], Query(max_length=100, description="Filtro por tema legislativo")
    ] = None,
    limit_divergencias: Annotated[
        int, Query(ge=1, le=100, description="Limite de divergências a exibir")
    ] = 50,
    limit_alinhamentos: Annotated[
        int, Query(ge=1, le=100, description="Limite de alinhamentos a exibir")
    ] = 20,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info(
        "Comparando politicos (alias) | %s vs %s | tema=%s | lim_div=%s lim_aln=%s",
        politico_id,
        outro_politico_id,
        tema,
        limit_divergencias,
        limit_alinhamentos,
    )
    return await service.comparar_politicos_service(
        id_or_slug1=politico_id,
        id_or_slug2=outro_politico_id,
        tema=tema,
        limit_divergencias=limit_divergencias,
        limit_alinhamentos=limit_alinhamentos,
    )


@router.get(
    "/{politico_id}/grafo/coautoria",
    response_model=RedeCoautoriaResponse,
    summary="Rede de Coautoria Legislativa (Apache AGE Graph)",
    description=(
        "Mapeia a rede de cooperação legislativa do parlamentar: deputados com quem mais "
        "apresenta proposições em conjunto, proporção de autoria principal vs coautoria, "
        "parcerias suprapartidárias e temas mais frequentes."
    ),
    responses={404: {"description": "Deputado não encontrado"}},
)
@cache(expire=3600, key_builder=politico_key_builder)
async def rede_coautoria(
    politico_id: DeputadoSlugPath,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
            description="Quantidade de parceiros principais a retornar",
        ),
    ] = 20,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Rede de coautoria | politico=%s limit=%s", politico_id, limit)
    return await service.get_rede_coautoria_service(politico_id, limit=limit)


@router.get(
    "/{politico_id}/grafo/afinidades",
    response_model=AfinidadesPoliticoResponse,
    summary="Radar de Afinidades e Oposições de Voto (Apache AGE Graph)",
    description=(
        "Identifica parlamentares com maior convergência e divergência em votações nominais, "
        "além da taxa média de alinhamento por bancada partidária."
    ),
    responses={404: {"description": "Deputado não encontrado"}},
)
@cache(expire=3600, key_builder=politico_key_builder)
async def afinidades_voto(
    politico_id: DeputadoSlugPath,
    min_votacoes_comuns: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Mínimo de votações em comum para significância estatística",
        ),
    ] = 10,
    apenas_outros_partidos: Annotated[
        bool,
        Query(
            description="Se True, filtra apenas parlamentares de partidos diferentes do deputado base"
        ),
    ] = False,
    limit: Annotated[
        int, Query(ge=1, le=30, description="Quantidade de parlamentares por lista")
    ] = 10,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info(
        "Afinidades de voto | politico=%s min_comuns=%s outros_partidos=%s limit=%s",
        politico_id,
        min_votacoes_comuns,
        apenas_outros_partidos,
        limit,
    )
    return await service.get_afinidades_service(
        id_or_slug=politico_id,
        min_comuns=min_votacoes_comuns,
        apenas_outros_partidos=apenas_outros_partidos,
        limit=limit,
    )


@router.get(
    "/{politico_id}/grafo/fidelidade-partidaria",
    response_model=FidelidadePartidariaResponse,
    summary="Fidelidade Partidária em Votações Nominais (Cruzamento Factual)",
    description=(
        "Calcula o alinhamento factual entre os votos individuais do parlamentar e as "
        "orientações oficiais emitidas pela liderança da bancada do seu partido."
    ),
    responses={
        400: {"description": "Parlamentar sem partido registrado"},
        404: {"description": "Deputado não encontrado"},
    },
)
@cache(expire=3600, key_builder=politico_key_builder)
async def fidelidade_partidaria(
    politico_id: DeputadoSlugPath,
    limit_divergencias: Annotated[
        int, Query(ge=1, le=100, description="Limite de matérias divergentes a exibir")
    ] = 50,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info(
        "Fidelidade partidaria | politico=%s lim_div=%s",
        politico_id,
        limit_divergencias,
    )
    return await service.get_fidelidade_partidaria_service(
        id_or_slug=politico_id,
        limit_divergencias=limit_divergencias,
    )


@router.get(
    "/{politico_id}",
    response_model=PoliticoResponse,
    summary="Detalha um deputado pelo ID ou slug",
    responses={404: {"description": "Deputado não encontrado"}},
)
@cache(expire=3600, key_builder=politico_key_builder)
async def get_politico(
    politico_id: DeputadoSlugPath,
    service: PoliticoService = Depends(_politico_service),
):
    """
    Aceita tanto o ID numérico (`1047`) quanto o slug do nome (`joao-silva-neto`).
    O frontend usa esta rota após a migração de URLs — IDs antigos continuam funcionando.
    """
    logger.info("Detalhe do deputado id_or_slug=%s", politico_id)
    return await service.get_politico_by_id_or_slug_service(politico_id)


@router.get(
    "/{politico_id}/votacoes",
    response_model=list[PoliticoVoto],
    summary="Últimas votações de um deputado",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def ultimas_votacoes(
    politico_id: DeputadoIdPath,
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    ano: AnoQuery = None,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Votações | deputado id=%s limit=%s ano=%s", politico_id, limit, ano)
    return await service.get_politicos_votacoes_service(
        politico_id, limit=limit, ano=ano
    )


@router.get(
    "/{politico_id}/despesas",
    response_model=list[PoliticoDespesaDetalhe],
    summary="Despesas individuais paginadas",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def listar_despesas_detalhadas(
    politico_id: DeputadoIdPath,
    ano: AnoQuery = None,
    mes: Annotated[int | None, Query(ge=1, le=12)] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Despesas | deputado id=%s ano=%s mes=%s", politico_id, ano, mes)
    return await service.get_politicos_despesas_services(
        politico_id, ano=ano, mes=mes, limit=limit
    )


@router.get(
    "/{politico_id}/despesas/resumo",
    response_model=list[PoliticoDespesaResumo],
    summary="Resumo mensal de gastos",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def resumo_despesas(
    politico_id: DeputadoIdPath,
    ano: AnoQuery = None,
    limit: Annotated[int, Query(ge=1, le=60)] = 60,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Resumo despesas | deputado id=%s ano=%s", politico_id, ano)
    return await service.get_politicos_despesas_resumo_services(
        politico_id, ano=ano, limit=limit
    )


@router.get(
    "/{politico_id}/despesas/resumo_completo",
    response_model=PoliticoDespesaResumoCompleto,
    summary="Resumo completo: histórico + top fornecedores + categorias",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def resumo_despesas_completo(
    politico_id: DeputadoIdPath,
    ano: AnoQuery = None,
    limit_meses: Annotated[int, Query(ge=1, le=60)] = 60,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Resumo completo despesas | deputado id=%s ano=%s", politico_id, ano)
    return await service.get_politicos_despesas_resumo_completo_services(
        politico_id, ano=ano, limit_meses=limit_meses
    )


@router.get(
    "/{politico_id}/estatisticas",
    response_model=PoliticoEstatisticasResponse,
    summary="Estatísticas gerais do deputado",
    description=(
        "Retorna totais de votações, despesas, gastos e média mensal. "
        "Use `ano` para filtrar um ano específico e comparar na linha do tempo."
    ),
)
@cache(expire=86400, key_builder=politico_key_builder)
async def estatisticas(
    politico_id: DeputadoIdPath,
    ano: AnoQuery = None,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Estatísticas | deputado id=%s ano=%s", politico_id, ano)
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
    responses={404: {"description": "Deputado não encontrado"}},
)
@cache(expire=86400, key_builder=politico_key_builder)
async def performance(
    politico_id: DeputadoIdPath,
    ano: AnoQuery = None,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Performance | deputado id=%s ano=%s", politico_id, ano)
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
    responses={404: {"description": "Deputado não encontrado"}},
)
@cache(expire=86400, key_builder=politico_key_builder)
async def timeline(
    politico_id: DeputadoIdPath,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info("Timeline | deputado id=%s", politico_id)
    return await service.get_politico_timeline_service(politico_id)


@router.get(
    "/{politico_id}/proposicoes",
    response_model=list[ProposicaoParaPolitico],
    summary="Proposições em que o deputado é autor ou coautor",
)
@cache(expire=86400, key_builder=politico_key_builder)
async def proposicoes_do_politico(
    politico_id: DeputadoIdPath,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    service: PoliticoService = Depends(_politico_service),
):
    """
    Retorna proposições onde o deputado figura como autor.
    O campo `proponente=true` indica autoria principal.
    """
    logger.info("Proposições | deputado id=%s limit=%s", politico_id, limit)
    return await service.get_politico_proposicoes_service(politico_id, limit=limit)


@router.get(
    "/{politico_id}/atividade-legislativa", response_model=AtividadeLegislativaResponse
)
@cache(expire=86400, key_builder=politico_key_builder)
async def atividade_legislativa(
    politico_id: DeputadoIdPath,
    ano: AnoQuery = None,
    q: Annotated[
        Optional[str],
        Query(max_length=150, description="Busca textual genérica"),
    ] = None,
    # Filtros de Votações
    q_votacao: Annotated[
        Optional[str],
        Query(max_length=150, description="Busca textual em votações"),
    ] = None,
    voto: Annotated[
        Optional[str],
        Query(max_length=50, description="Filtrar por voto (ex: Sim, Não, Abstenção, Obstrução)"),
    ] = None,
    sigla_tipo_votacao: Annotated[
        Optional[str],
        Query(max_length=20, description="Sigla do tipo de proposição na votação (ex: PL, PEC)"),
    ] = None,
    tema_votacao: Annotated[
        Optional[str],
        Query(max_length=100, description="Tema legislativo da matéria votada"),
    ] = None,
    data_inicio_votacao: Annotated[
        Optional[date],
        Query(description="Data de início das votações (AAAA-MM-DD)"),
    ] = None,
    data_fim_votacao: Annotated[
        Optional[date],
        Query(description="Data de fim das votações (AAAA-MM-DD)"),
    ] = None,
    # Filtros de Proposições
    q_proposicao: Annotated[
        Optional[str],
        Query(max_length=150, description="Busca textual em proposições"),
    ] = None,
    sigla_tipo_proposicao: Annotated[
        Optional[str],
        Query(max_length=20, description="Sigla do tipo de proposição (ex: PL, PEC, REQ)"),
    ] = None,
    proponente: Annotated[
        Optional[bool],
        Query(description="true para autor principal, false para coautor"),
    ] = None,
    data_inicio_proposicao: Annotated[
        Optional[date],
        Query(description="Data de início da apresentação (AAAA-MM-DD)"),
    ] = None,
    data_fim_proposicao: Annotated[
        Optional[date],
        Query(description="Data de fim da apresentação (AAAA-MM-DD)"),
    ] = None,
    # Paginação
    limit_votacoes: Annotated[int, Query(ge=1, le=100)] = 20,
    limit_proposicoes: Annotated[int, Query(ge=1, le=100)] = 20,
    offset_votacoes: Annotated[int, Query(ge=0)] = 0,
    offset_proposicoes: Annotated[int, Query(ge=0)] = 0,
    service: PoliticoService = Depends(_politico_service),
):
    logger.info(
        "Atividade legislativa | deputado id=%s ano=%s q=%s q_v=%s voto=%s tipo_v=%s tema_v=%s q_p=%s prop=%s lv=%s lp=%s ov=%s op=%s",
        politico_id,
        ano,
        q,
        q_votacao,
        voto,
        sigla_tipo_votacao,
        tema_votacao,
        q_proposicao,
        proponente,
        limit_votacoes,
        limit_proposicoes,
        offset_votacoes,
        offset_proposicoes,
    )

    return await service.get_politico_atividade_legislativa_service(
        deputado_id=politico_id,
        ano=ano,
        q=q,
        q_votacao=q_votacao,
        voto=voto,
        sigla_tipo_votacao=sigla_tipo_votacao,
        tema_votacao=tema_votacao,
        data_inicio_votacao=data_inicio_votacao,
        data_fim_votacao=data_fim_votacao,
        q_proposicao=q_proposicao,
        sigla_tipo_proposicao=sigla_tipo_proposicao,
        proponente=proponente,
        data_inicio_proposicao=data_inicio_proposicao,
        data_fim_proposicao=data_fim_proposicao,
        limit_votacoes=limit_votacoes,
        limit_proposicoes=limit_proposicoes,
        offset_votacoes=offset_votacoes,
        offset_proposicoes=offset_proposicoes,
    )


# ---------------------------------------------------------------------------
# SPEC-001 — Temas de Atuação Parlamentar
# ---------------------------------------------------------------------------

from backend.schemas import PoliticoTemasResponse  # noqa: E402 (import at bottom for readability)
from backend.services.tema_service import TemaService  # noqa: E402


def _tema_service(db: AsyncSession = Depends(get_db)) -> TemaService:
    return TemaService(db)


@router.get(
    "/{politico_id}/temas",
    response_model=PoliticoTemasResponse,
    summary="Temas de Atuação Parlamentar (SPEC-001)",
    description=(
        "Retorna o ranking dos temas legislativos em que o parlamentar apresentou maior "
        "concentração de atuação, calculado por similaridade semântica com pgvector "
        "(modelo BAAI/bge-m3) sobre proposições apresentadas e relatadas, "
        "ponderado por tipo de participação: autoria (peso 10), coautoria (peso 5). "
        "Fonte: pipeline tasks/classificar_temas.py (SPEC-001)."
    ),
    responses={
        404: {"description": "Parlamentar não encontrado ou pipeline não executado"},
    },
)
@cache(expire=86400, key_builder=politico_key_builder)
async def temas_atuacao(
    politico_id: DeputadoSlugPath,
    id_legislatura: Annotated[
        int,
        Query(ge=50, le=60, description="Legislatura (default: 57 — atual)"),
    ] = 57,
    limit: Annotated[
        int,
        Query(ge=1, le=20, description="Número máximo de temas a retornar"),
    ] = 10,
    service: TemaService = Depends(_tema_service),
):
    logger.info(
        "Temas de atuação | politico=%s | legislatura=%s | limit=%s",
        politico_id,
        id_legislatura,
        limit,
    )
    return await service.get_temas_atuacao_service(
        id_or_slug=politico_id,
        id_legislatura=id_legislatura,
        limit=limit,
    )
