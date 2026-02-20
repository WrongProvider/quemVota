from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.ranking_repository import RankingRepository
from fastapi_cache import FastAPICache 

# Valor das cotas mensais por UF, baseado nos dados de 2025 (pode ser atualizado anualmente)
COTAS_POR_UF = {
    "AC": 50426.26, "AL": 46737.90, "AM": 49363.92, "AP": 49168.58, "BA": 44804.65,
    "CE": 48245.57, "DF": 36582.46, "ES": 43217.71, "GO": 41300.86, "MA": 47945.49,
    "MG": 41886.51, "MS": 46336.64, "MT": 45221.83, "PA": 48021.25, "PB": 47826.36,
    "PE": 47470.60, "PI": 46765.57, "PR": 44665.66, "RJ": 41553.77, "RN": 48525.79,
    "RO": 49466.29, "RR": 51406.33, "RS": 46669.70, "SC": 45671.58, "SE": 45933.06,
    "SP": 42837.33, "TO": 45297.41
}

class RankingService:
    def __init__(self, db: AsyncSession):
        self.repo = RankingRepository(db)
        self.cache_backend = FastAPICache.get_backend()

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
    
    async def get_ranking_performance_politicos(self):
        raw_data = await self.repo.get_ranking_performance_politicos()
        ranking = []

        for p in raw_data:
            # 1. Notas de Assiduidade (já vem do SQL como Decimal/Float)
            nota_assiduidade = float(p["nota_assiduidade"])

            # 2. Nota de Produção (Meta: 2 pontos ponderados por mês)
            meses = max(p["meses_mandato"], 1)
            meta_producao = meses * 2.0
            nota_producao = min((float(p["pontos_producao"]) / meta_producao) * 100, 100) if meta_producao > 0 else 0

            # 3. Nota de Economia (Baseada na cota do estado)
            cota_mensal = COTAS_POR_UF.get(p["uf"], 40000)
            cota_total_periodo = cota_mensal * meses
            gasto = float(p["total_gasto"])
            nota_economia = max(0, ((cota_total_periodo - gasto) / cota_total_periodo) * 100) if cota_total_periodo > 0 else 0

            # PESOS UNIFICADOS (Ass: 15%, Eco: 40%, Prod: 45%)
            score_final = (float(p["nota_assiduidade"]) * 0.15) + (nota_economia * 0.40) + (nota_producao * 0.45)

            ranking.append({
                "id": p["id"],
                "nome": p["nome"],
                "uf": p["uf"],
                "partido": p["partido_sigla"],
                "foto": p["url_foto"],
                "score": round(score_final, 2),
                "notas": {
                    "assiduidade": round(nota_assiduidade, 2),
                    "producao": round(nota_producao, 2),
                    "economia": round(nota_economia, 2)
                }
            })

        # Ordena pelo melhor score
        ranking.sort(key=lambda x: x["score"], reverse=True)
        return ranking
    
    async def get_media_global_cached(self):
        cache_key = "media_global_score"
        
        # 1. Tenta buscar o valor já calculado
        media = await self.cache_backend.get(cache_key)
        
        if media is None:
            # 2. Se não existir (cache expirou), calcula e guarda
            # Aqui você chama a lógica do ranking que já temos
            ranking = await self.get_ranking_performance_politicos()
            media = sum(p["score"] for p in ranking) / len(ranking)
            
            # 3. Salva por 24h para ninguém mais ter que calcular hoje
            await self.cache_backend.set(cache_key, media, expire=86400)
        
        return float(media)