from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.politico_repository import PoliticoRepository
from backend.schemas import PoliticoResponse

class PoliticoService:
    def __init__(self, db: AsyncSession):
        self.repo = PoliticoRepository(db)

    async def get_politicos_service(self, limit: int = 100, q: str = None, uf: str = None, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 100)

        # busca os dados brutos no repositorio
        db_politicos = await self.repo.get_politicos_repo(limit=limite_seguro, q=q, uf=uf, offset=offset)
        return [PoliticoResponse.model_validate(p) for p in db_politicos]
    
    async def get_politicos_detalhe_service(self, politico_id: int):
        db_politico = await self.repo.get_politico_repo(politico_id=politico_id)
        return PoliticoResponse.model_validate(db_politico)
    
    async def get_politicos_votacoes_service(self, politico_id: int, limit: int = 20):
        # rate limit
        limite_seguro = min(limit, 20)

        # busca os dados brutos no repositorio
        return await self.repo.get_politicos_votacoes_repo(politico_id=politico_id, limit=limite_seguro)    
    
    async def get_politicos_despesas_services(self, politico_id: int, ano: int | None = None, mes: int | None = None, limit: int = 20):
        # rate limit
        limite_seguro = min(limit, 20)


        # busca os dados brutos no repositorio
        return await self.repo.get_politicos_despesas_repo(politico_id=politico_id, ano=ano, mes=mes, limit=limite_seguro)
    
    async def get_politicos_despesas_resumo_services(self, politico_id: int, ano: int | None = None, limit: int = 60):
        # rate limit
        limite_seguro = min(limit, 60)
        # busca os dados brutos no repositorio
        return await self.repo.get_politicos_despesas_resumo_repo(politico_id=politico_id, ano=ano, limit=limite_seguro)    
    
    async def get_politicos_despesas_resumo_completo_services(self, politico_id: int, ano: int | None = None, limit_meses: int = 60):
        # rate limit
        limite_seguro = min(limit_meses, 60)
        # busca os dados brutos no repositorio
        return await self.repo.get_politicos_despesas_resumo_completo_repo(politico_id=politico_id, ano=ano, limit_meses=limite_seguro)
    
    async def get_politico_estatisticas_service(self, politico_id: int):
        # busca os dados brutos no repositorio
        return await self.repo.get_politicos_estatisticas_repo(politico_id=politico_id)