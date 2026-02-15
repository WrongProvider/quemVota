from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, or_
from backend.models import Politico

class PoliticoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_politicos_repo(self, q: str = None, uf: str = None, limit: int = 100, offset: int = 0):
        stmt = select(Politico)

        if q:
            # Busca por nome (ilike ignora maiúsculas/minúsculas)
            stmt = stmt.where(Politico.nome.ilike(f"%{q}%"))

        if uf:
            stmt = stmt.where(Politico.uf == uf)

        stmt = (
            stmt.order_by(Politico.nome)
            .limit(limit)
            .offset(offset)
        )
        
        return self.db.execute(stmt).scalars().all()