from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.ranking_repository import RankingRepository
from backend.schemas import RankingDespesaItem

class RankingService:
    def __init__(self, db: AsyncSession):
        self.repo = RankingRepository(db)

    async def get_ranking_despesas(self, limit: int = 100, q: str = None, uf: str = None, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 100)

        # busca os dados brutos no repositorio
        return await self.repo.get_ranking_despesas(limit=limite_seguro, q=q, uf=uf, offset=offset)
    
    