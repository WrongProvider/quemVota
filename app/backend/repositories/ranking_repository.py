# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from collections import defaultdict
from backend.schemas import RankingDespesaPolitico, RankingEmpresaLucro, RankingDiscursoPolitico 
from backend.models import Politico, Despesa, Discurso

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
    
    async def get_ranking_discursos_politicos(self, limit: int = 100, offset: int = 0):
        """
        Retorna os políticos que mais realizaram discursos/pronunciamentos.
        """
        # Contamos quantos discursos cada político tem
        stmt = (
            select(
                Politico.id.label("politico_id"),
                Politico.nome.label("nome_politico"),
                Politico.partido_sigla.label("sigla_partido"),
                Politico.uf.label("sigla_uf"),
                func.count(Discurso.id).label("total_discursos")
            )
            .join(Discurso, Discurso.politico_id == Politico.id)
            # Filtramos discursos vazios ou nulos se necessário
            .group_by(Politico.id)
            .order_by(desc("total_discursos"))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        
        return [
            RankingDiscursoPolitico(
                politico_id=r["politico_id"],
                nome_politico=r["nome_politico"],
                sigla_partido=r["sigla_partido"],
                sigla_uf=r["sigla_uf"],
                total_discursos=r["total_discursos"]
            )
            for r in result.mappings()
        ]
    
    async def get_ranking_lucro_empresas(self, limit: int = 100, offset: int = 0):
        # 1. Dicionário de "Cura de Dados" (Aumentado)
        # Aqui você mapeia qualquer variação de nome para o CNPJ e Nome Padrão
        DATA_FIX = {
            "TAM": {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
            "LATAM AIRLINES BRASIL": {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
            "LATAM LINHAS AÉREAS S.A": {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
            "CIA AÉREA - TAM": {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
            "GOL": {"cnpj": "07575651000159", "nome": "GOL"},
            "GOL LINHAS AÉREAS": {"cnpj": "07575651000159", "nome": "GOL"},
            "AZUL": {"cnpj": "09296295000160", "nome": "AZUL"},
            "AZUL LINHAS AÉREAS": {"cnpj": "09296295000160", "nome": "AZUL"},
        }

        # 2. Busca um volume maior para garantir o ranking após o merge
        stmt = (
            select(
                func.coalesce(Despesa.cnpj_cpf_fornecedor, "").label("cnpj"),
                func.upper(func.trim(Despesa.nome_fornecedor)).label("nome_bruto"),
                func.sum(Despesa.valor_liquido).label("total")
            )
            .group_by(text("cnpj"), text("nome_bruto"))
            .order_by(desc("total"))
            .limit(limit * 3) 
        )

        result = await self.db.execute(stmt)
        
        processed_data = defaultdict(float)
        names_map = {} 

        for r in result.mappings():
            nome_bruto = r["nome_bruto"]
            cnpj_db = r["cnpj"]
            
            # --- O PULO DO GATO ---
            # Se o nome existe no DATA_FIX, ignoramos o CNPJ do banco e usamos o fixo
            if nome_bruto in DATA_FIX:
                cnpj_final = DATA_FIX[nome_bruto]["cnpj"]
                nome_final = DATA_FIX[nome_bruto]["nome"]
            else:
                cnpj_final = cnpj_db
                nome_final = nome_bruto

            # A chave de soma agora é SEMPRE o CNPJ se ele existir (mesmo vindo do DATA_FIX)
            # Se não tiver CNPJ de jeito nenhum, usamos o nome
            key = cnpj_final if cnpj_final else f"NOCNPJ_{nome_final}"
            
            # Somamos o valor
            processed_data[key] += float(r["total"])
            
            # Guardamos a referência de exibição (CNPJ e Nome Bonito)
            if key not in names_map:
                names_map[key] = {"cnpj": cnpj_final, "nome": nome_final}

        # 4. Converte para a lista de objetos final
        ranking = [
            RankingEmpresaLucro(
                cnpj=info["cnpj"],
                nome_fornecedor=info["nome"],
                total_recebido=processed_data[key]
            )
            for key, info in names_map.items()
        ]

        # Re-ordena pelo total somado (essencial!)
        ranking.sort(key=lambda x: x.total_recebido, reverse=True)
        
        return ranking[offset : offset + limit]
    

    