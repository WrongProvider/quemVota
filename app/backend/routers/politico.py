from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Politico, Voto, Votacao
from backend.schemas import PoliticoResponse, VotoPoliticoResponse

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
        return Politico.query.filter(
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


