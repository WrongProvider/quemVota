from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Politico, Voto, Votacao, Despesa
from backend.schemas import PoliticoResponse, VotoPolitico, DespesaResumo, DespesaDetalheResponse, FornecedorRanking

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


@router.get("/", response_model=list[PoliticoResponse])
def listar_politicos(
    uf: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Politico)

    if q:
        return query.filter(
            Politico.nome.ilike(f"%{q}%")
        ).all()
    if uf:
        query = query.filter(Politico.uf == uf)

    return (
        query
        .order_by(Politico.nome)
        .limit(min(limit, 100))
        .offset(offset)
        .all()
    )

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
        return (
            db.query(
                Votacao.id.label("id_votacao"),
                Votacao.data,
                Proposicao.sigla_tipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa,
                Voto.tipo_voto.label("voto"),
                Votacao.ultima_apresentacao_proposicao_descricao.label("resultado_da_votacao")
            )
            .join(Voto, Voto.votacao_id == Votacao.id)
            .join(Proposicao, Votacao.proposicao_id == Proposicao.id)
            .filter(Voto.politico_id == politico_id)
            .order_by(desc(Votacao.data))
            .limit(limit)
            .all()
        )

    votos_raw = await run_in_threadpool(get_votos)
    return votos_raw

@router.get("/{politico_id}/despesas/resumo", response_model=list[DespesaResumo])
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def resumo_despesas_do_politico(politico_id: int, db: Session = Depends(get_db)):
    # Agora a função é ASYNC
    print(f"DEBUG: Calculando resumo no banco para o politico {politico_id} {datetime.now().time()}")
    
    # Executa a query síncrona do SQLAlchemy de forma que não trave o async
    def get_data():
        return (
            db.query(
                Despesa.ano,
                Despesa.mes,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas")
            )
            .filter(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
            .all()
        )

    resumo_raw = await run_in_threadpool(get_data)

    return [
        {
            "ano": r.ano, 
            "mes": r.mes, 
            "total_gasto": float(r.total_gasto or 0), 
            "qtd_despesas": r.qtd_despesas
        } 
        for r in resumo_raw
    ]

@router.get("/{politico_id}/despesas", response_model=list[DespesaDetalheResponse])
def listar_despesas_detalhadas(
    politico_id: int,
    ano: int | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Lista as despesas individuais com paginação."""
    query = db.query(Despesa).filter(Despesa.politico_id == politico_id)

    if ano:
        query = query.filter(Despesa.ano == ano)

    return (
        query.order_by(Despesa.data_documento.desc())
        .limit(min(limit, 100))
        .offset(offset)
        .all()
    )


@router.get("/{politico_id}/despesas/fornecedores", response_model=list[FornecedorRanking])
@cache(expire=86400, key_builder=politico_key_builder)
async def ranking_fornecedores_do_politico(
    politico_id: int, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Gerando ranking de fornecedores para o politico {politico_id}")
    
    def get_ranking():
        return (
            db.query(
                Despesa.nome_fornecedor,
                func.sum(Despesa.valor_liquido).label("total_recebido"),
                func.count(Despesa.id).label("qtd_notas")
            )
            .filter(Despesa.politico_id == politico_id)
            .group_by(Despesa.nome_fornecedor)
            .order_by(func.sum(Despesa.valor_liquido).desc())
            .limit(limit)
            .all()
        )

    ranking_raw = await run_in_threadpool(get_ranking)

    return [
        {
            "nome_fornecedor": r.nome_fornecedor,
            "total_recebido": float(r.total_recebido or 0),
            "qtd_notas": r.qtd_notas
        }
        for r in ranking_raw
    ]