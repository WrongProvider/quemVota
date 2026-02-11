from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Politico, Voto, Votacao, Despesa
from backend.schemas import PoliticoResponse, VotoPoliticoResponse, DespesaResumo, DespesaDetalheResponse

router = APIRouter(
    prefix="/politicos",
    tags=["Políticos"]
)

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


@router.get(
    "/{politico_id}/votacoes",
    response_model=list[VotoPoliticoResponse]
)
def listar_votacoes_do_politico(
    politico_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    politico = db.get(Politico, politico_id)

    if not politico:
        raise HTTPException(
            status_code=404,
            detail="Político não encontrado"
        )

    query = (
        db.query(
            Votacao.id.label("votacao_id"),
            Votacao.titulo,
            Votacao.data,
            Voto.voto
        )
        .join(Voto, Voto.votacao_id == Votacao.id)
        .filter(Voto.politico_id == politico_id)
        .order_by(Votacao.data.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )

    return query.all()


@router.get("/{politico_id}/despesas/resumo", response_model=list[DespesaResumo])
def resumo_despesas_do_politico(politico_id: int, db: Session = Depends(get_db)):
    """Retorna o total gasto por mês/ano para alimentar gráficos."""
    resumo = (
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
    return resumo

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