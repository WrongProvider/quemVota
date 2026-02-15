from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
from backend.database import get_db
from backend.models import Politico, Voto, Votacao, Despesa, Proposicao
from backend.schemas import PoliticoEstatisticasResponse, PoliticoResponse, VotoPolitico, DespesaResumo, DespesaDetalheResponse, FornecedorRanking, VotacaoResumoItem, RankingDespesaItem, SerieDespesaItem

from fastapi_cache.decorator import cache   

router = APIRouter(
    prefix="/politicos",
    tags=["Políticos"]
)

# Cache Key Builder personalizado para as rotas de político
from fastapi.concurrency import run_in_threadpool # Importe isso
from datetime import datetime

def politico_key_builder(func, namespace, request=None, response=None, *args, **kwargs):
    # 1. Tenta pegar dos argumentos nomeados
    politico_id = kwargs.get("politico_id")
    
    # 2. Se falhar, tenta extrair direto da URL (Request)
    if politico_id is None and request:
        # Pega o ID que está na URL, ex: /politicos/59/...
        politico_id = request.path_params.get("politico_id")

    # 3. Se ainda assim falhar, tenta a posição bruta nos args
    if politico_id is None and args:
        for arg in args:
            if isinstance(arg, int):
                politico_id = arg
                break

    return f"{namespace}:{func.__name__}:{politico_id or 'unknown'}"

from backend.services.politico_service import PoliticoService

@router.get("/", response_model=list[PoliticoResponse])
async def listar_politicos(
    q: str | None = None,
    uf: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PoliticoService(db)
    return await service.listar_politicos(q=q, uf=uf, limit=limit, offset=offset)
# @router.get("/", response_model=list[PoliticoResponse])
# def listar_politicos(
#     uf: str | None = None,
#     q: str | None = None,
#     limit: int = 100,
#     offset: int = 0,
#     db: Session = Depends(get_db)
# ):
#     stmt = select(Politico)

#     if q:
#         stmt = stmt.where(Politico.nome.ilike(f"%{q}%"))

#     if uf:
#         stmt = stmt.where(Politico.uf == uf)

#     stmt = (
#         stmt
#         .order_by(Politico.nome)
#         .limit(min(limit, 100))
#         .offset(offset)
#     )

#     return db.execute(stmt).scalars().all()

@router.get(
    "/ranking/despesas",
    response_model=list[RankingDespesaItem]
)
@cache(expire=86400)
async def ranking_global_despesas(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    # Segurança contra abuso
    limit = min(limit, 50)

    def get_data():
        stmt = (
            select(
                Politico.id.label("politico_id"),
                Politico.nome,
                func.coalesce(func.sum(Despesa.valor_liquido), 0).label("total_gasto")
            )
            .join(Despesa, Despesa.politico_id == Politico.id)
            .group_by(Politico.id, Politico.nome)
            .order_by(func.sum(Despesa.valor_liquido).desc())
            .limit(limit)
        )

        return db.execute(stmt).mappings().all()

    result = await run_in_threadpool(get_data)

    return [
        RankingDespesaItem(
            politico_id=r["politico_id"],
            nome=r["nome"],
            total_gasto=float(r["total_gasto"])
        )
        for r in result
    ]


@router.get("/{politico_id}", response_model=PoliticoResponse)
def obter_politico(politico_id: int, db: Session = Depends(get_db)):
    politico = db.get(Politico, politico_id)

    if not politico:
        raise HTTPException(
            status_code=404,
            detail="Político não encontrado"
        )

    return politico


@router.get("/{politico_id}/votacoes", response_model=list[VotoPolitico])
@cache(expire=86400, key_builder=politico_key_builder)
async def ultimas_votacoes_do_politico(
    politico_id: int, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Buscando votações para o politico {politico_id}")
    
    def get_votos():
        stmt = (
                select(
                    Votacao.id.label("id_votacao"),
                    Votacao.data,
                    Proposicao.sigla_tipo.label("proposicao_sigla"),
                    Proposicao.numero.label("proposicao_numero"),
                    Proposicao.ano.label("proposicao_ano"),
                    Proposicao.ementa,
                    Voto.tipo_voto.label("voto"),
                    Votacao.descricao.label("resultado_da_votacao")
                )
                .join(Voto, Voto.votacao_id == Votacao.id)
                .join(Proposicao, Votacao.proposicao_id == Proposicao.id)
                .where(Voto.politico_id == politico_id)
                .order_by(desc(Votacao.data))
                .limit(limit)
            )

        return db.execute(stmt).mappings().all()
        
    return await run_in_threadpool(get_votos)
     
@router.get(
    "/{politico_id}/votacoes/resumo",
    response_model=list[VotacaoResumoItem]
)
@cache(expire=86400, key_builder=politico_key_builder)
async def resumo_votacoes(
    politico_id: int,
    db: Session = Depends(get_db)
):
    def get_data():
        stmt = (
            select(
                Voto.tipo_voto,
                func.count(Voto.id).label("quantidade")
            )
            .where(Voto.politico_id == politico_id)
            .group_by(Voto.tipo_voto)
        )

        return db.execute(stmt).mappings().all()

    result = await run_in_threadpool(get_data)

    return [
        VotacaoResumoItem(
            tipo_voto=r["tipo_voto"],
            quantidade=r["quantidade"]
        )
        for r in result
    ]

@router.get("/{politico_id}/despesas/resumo", response_model=list[DespesaResumo])
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def resumo_despesas_do_politico(politico_id: int, db: Session = Depends(get_db)):
    # Agora a função é ASYNC
    print(f"DEBUG: Calculando resumo no banco para o politico {politico_id} {datetime.now().time()}")
    
    # Executa a query síncrona do SQLAlchemy de forma que não trave o async
    def get_data():
        stmt = (
            select(
                Despesa.ano,
                Despesa.mes,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        )

        return db.execute(stmt).mappings().all()

    return await run_in_threadpool(get_data)

    # return [
    #     {
    #         "ano": r.ano, 
    #         "mes": r.mes, 
    #         "total_gasto": float(r.total_gasto or 0), 
    #         "qtd_despesas": r.qtd_despesas
    #     } 
    #     for r in resumo_raw
    # ]

@router.get("/{politico_id}/despesas", response_model=list[DespesaDetalheResponse])
def listar_despesas_detalhadas(
    politico_id: int,
    ano: int | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Lista as despesas individuais com paginação."""
    stmt = select(Despesa).where(Despesa.politico_id == politico_id)

    if ano:
        stmt = stmt.where(Despesa.ano == ano)

    stmt = (
        stmt
        .order_by(Despesa.data_documento.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )

    return db.execute(stmt).scalars().all()

@router.get("/{politico_id}/despesas/fornecedores", response_model=list[FornecedorRanking])
@cache(expire=86400, key_builder=politico_key_builder)
async def ranking_fornecedores_do_politico(
    politico_id: int, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Gerando ranking de fornecedores para o politico {politico_id}")
    
    def get_ranking():
        stmt = (
            select(
                Despesa.nome_fornecedor,
                func.sum(Despesa.valor_liquido).label("total_recebido"),
                func.count(Despesa.id).label("qtd_notas")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.nome_fornecedor)
            .order_by(func.sum(Despesa.valor_liquido).desc())
            .limit(limit)
        )

        return db.execute(stmt).mappings().all()

    return await run_in_threadpool(get_ranking)


@router.get(
    "/{politico_id}/estatisticas",
    response_model=PoliticoEstatisticasResponse
)
@cache(expire=86400, key_builder=politico_key_builder)
async def estatisticas_do_politico(
    politico_id: int,
    db: Session = Depends(get_db)
):
    def get_data():
        # Total votações
        stmt_votos = select(
            func.count(func.distinct(Voto.votacao_id))
        ).where(
            Voto.politico_id == politico_id
        )

        # Estatísticas despesas
        stmt_despesas = select(
            func.count(Despesa.id),
            func.coalesce(func.sum(Despesa.valor_liquido), 0),
            func.min(Despesa.ano),
            func.max(Despesa.ano)
        ).where(
            Despesa.politico_id == politico_id
        )

        total_votacoes = db.execute(stmt_votos).scalar_one()
        despesas_result = db.execute(stmt_despesas).one()

        return total_votacoes, despesas_result

    total_votacoes, despesas = await run_in_threadpool(get_data)

    total_despesas, total_gasto, primeiro_ano, ultimo_ano = despesas

    media_mensal = 0.0
    if primeiro_ano and ultimo_ano:
        total_meses = (ultimo_ano - primeiro_ano + 1) * 12
        if total_meses > 0:
            media_mensal = float(total_gasto) / total_meses

    return PoliticoEstatisticasResponse(
        total_votacoes=total_votacoes or 0,
        total_despesas=total_despesas or 0,
        total_gasto=float(total_gasto or 0),
        media_mensal=round(media_mensal, 2),
        primeiro_ano=primeiro_ano,
        ultimo_ano=ultimo_ano
    )

@router.get(
    "/{politico_id}/despesas/serie",
    response_model=list[SerieDespesaItem]
)
@cache(expire=86400, key_builder=politico_key_builder)
async def serie_despesas(
    politico_id: int,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
    db: Session = Depends(get_db)
):
    def get_data():
        stmt = (
            select(
                Despesa.ano,
                Despesa.mes,
                func.coalesce(func.sum(Despesa.valor_liquido), 0).label("total")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano, Despesa.mes)
        )

        if ano_inicio:
            stmt = stmt.where(Despesa.ano >= ano_inicio)

        if ano_fim:
            stmt = stmt.where(Despesa.ano <= ano_fim)

        return db.execute(stmt).mappings().all()

    result = await run_in_threadpool(get_data)

    return [
        SerieDespesaItem(
            ano=r["ano"],
            mes=r["mes"],
            total=float(r["total"])
        )
        for r in result
    ]
