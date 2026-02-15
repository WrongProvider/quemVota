from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.politico_repository import PoliticoRepository
from backend.schemas import PoliticoResponse

class PoliticoService:
    def __init__(self, db: AsyncSession):
        self.repo = PoliticoRepository(db)

    async def listar_politicos(self, limit: int = 100, q: str = None, uf: str = None, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 100)

        # busca os dados brutos no repositorio
        db_politicos = await self.repo.get_politicos_repo(limit=limite_seguro, q=q, uf=uf, offset=offset)
        return [PoliticoResponse.model_validate(p) for p in db_politicos]