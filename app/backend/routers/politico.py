from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Politico
from backend.schemas import PoliticoResponse

router = APIRouter(
    prefix="/politicos",
    tags=["Políticos"]
)

@router.get("/", response_model=list[PoliticoResponse])
def listar_politicos(
    uf: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Politico)

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

