# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from backend.schemas import RankingDespesaPolitico  
from backend.models import Politico, Despesa

class RankingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ranking_despesas_politicos(self, q: str = None, uf: str = None, limit: int = 100, offset: int = 0):
        stmt = (
            select(
                Politico.id.label("politico_id"),
                Politico.nome,
                func.coalesce(func.sum(Despesa.valor_liquido), 0).label("total_gasto")
            )
            .join(Despesa, Despesa.politico_id == Politico.id)
        )

        # --- FILTROS ADICIONADOS ---
        if uf:
            stmt = stmt.where(Politico.uf == uf.upper())
        if q:
            stmt = stmt.where(Politico.nome.ilike(f"%{q}%"))
        # ---------------------------

        stmt = (
            stmt.group_by(Politico.id, Politico.nome)
            .order_by(desc("total_gasto")) # Usa o label para ordenar
            .limit(limit)
            .offset(offset)
        )

        # resolve primeiro a rotina
        result = await self.db.execute(stmt)
        # se fizesse junto ele da await numa corrotina.
        return [
            RankingDespesaPolitico(
                politico_id=r["politico_id"],
                nome=r["nome"],
                total_gasto=float(r["total_gasto"])
            )
            for r in result.mappings()
        ]
    
    async def get_ranking_lucro_empresas(self, q: str = None, limit: int = 100, offset: int = 0):
        pass
        # return result.scalars().all()