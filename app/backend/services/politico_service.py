from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.politico_repository import PoliticoRepository
from backend.schemas import PoliticoResponse
from .ranking_service import RankingService

# Valor das cotas mensais por UF, baseado nos dados de 2025 (pode ser atualizado anualmente)
COTAS_POR_UF = {
    "AC": 50426.26, "AL": 46737.90, "AM": 49363.92, "AP": 49168.58, "BA": 44804.65,
    "CE": 48245.57, "DF": 36582.46, "ES": 43217.71, "GO": 41300.86, "MA": 47945.49,
    "MG": 41886.51, "MS": 46336.64, "MT": 45221.83, "PA": 48021.25, "PB": 47826.36,
    "PE": 47470.60, "PI": 46765.57, "PR": 44665.66, "RJ": 41553.77, "RN": 48525.79,
    "RO": 49466.29, "RR": 51406.33, "RS": 46669.70, "SC": 45671.58, "SE": 45933.06,
    "SP": 42837.33, "TO": 45297.41
}

class PoliticoService:
    def __init__(self, db: AsyncSession):
        self.repo = PoliticoRepository(db)

    async def get_politicos_service(self, limit: int = 100, q: str = None, uf: str = None, offset: int = 0):
        # rate limit
        limite_seguro = min(limit, 600)

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
    
    async def get_politico_performance_service(self, politico_id: int):
        # busca os dados brutos no repositorio
        data = await self.repo.get_politico_performance_data(politico_id)
    
        if not data:
            raise HTTPException(status_code=404, detail="Político não encontrado")

        # --- CÁLCULO DAS NOTAS (0-100) ---
        
        # 1. Assiduidade (Peso 20%)
        nota_assiduidade = (data["presencas"] / data["total_sessoes"]) * 100

        # 2. Economia (Peso 40%)
        cota_mensal = COTAS_POR_UF.get(data["uf"], 40000.0) # Fallback 40k
        cota_total_periodo = cota_mensal * data["meses_mandato"]
        # Se gastou mais que a cota (raro, mas possível), nota é 0
        economia_ratio = (cota_total_periodo - data["total_gasto"]) / cota_total_periodo
        nota_economia = max(0, economia_ratio * 100)

        # 3. Produção Legislativa (Peso 40%)
        # Referência: 5 proposições por mês é considerado alta produtividade (ajustável)
        meta_producao = data["meses_mandato"] * 2 
        nota_producao = min((data["total_proposicoes"] / meta_producao) * 100, 100) if meta_producao > 0 else 0

        # SCORE FINAL
        indice_final = (nota_assiduidade * 0.15) + (nota_economia * 0.40) + (nota_producao * 0.45)

        # Media global
        media_global = await RankingService(self.repo.db).get_media_global_cached()
        return {
            "politico_id": politico_id,
            "score_final": round(indice_final, 2),
            "media_global": round(media_global, 2),
            "detalhes": {
                "nota_assiduidade": round(nota_assiduidade, 2),
                "nota_economia": round(nota_economia, 2),
                "nota_producao": round(nota_producao, 2)
            },
            "info": {
                "valor_cota_mensal": cota_mensal,
                "total_gasto": data["total_gasto"],
                "cota_utilizada_pct": round((data["total_gasto"] / cota_total_periodo) * 100, 2)
            }
        }