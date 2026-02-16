from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.ranking_repository import RankingRepository

class RankingService:
    def __init__(self, db: AsyncSession):
        self.repo = RankingRepository(db)

    async def get_ranking_despesas_politicos(self, limit: int = 100, q: str = None, uf: str = None, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 100)

        # busca os dados brutos no repositorio
        return await self.repo.get_ranking_despesas_politicos(limit=limite_seguro, q=q, uf=uf, offset=offset)
    
    async def get_ranking_lucro_empresas(self, limit: int = 100, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 100)

        # busca os dados brutos no repositorio
        return await self.repo.get_ranking_lucro_empresas(limit=limite_seguro, offset=offset)

    async def get_ranking_discursos_politicos(self, limit: int = 100, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 100)

        # busca os dados brutos no repositorio
        return await self.repo.get_ranking_discursos_politicos(limit=limite_seguro, offset=offset)  