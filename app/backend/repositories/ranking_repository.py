# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import case, cast, select, func, desc, text, Float, Numeric
from collections import defaultdict, Counter
from backend.schemas import KeywordInfo, RankingDespesaPolitico, RankingEmpresaLucro, RankingDiscursoPolitico 
from backend.models import Politico, Despesa, Discurso, Presenca, Proposicao, ProposicaoAutor

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
        # Defina os termos burocráticos que devem ser ignorados
        BLACKLIST_KEYWORDS = {
        # --- PROCESSUAL E RITUALÍSTICO ---
        "ORIENTAÇÃO DE BANCADA", "REQUERIMENTO DE URGÊNCIA", "ENCAMINHAMENTO DE VOTAÇÃO",
        "DISCUSSÃO", "QUESTÃO DE ORDEM", "VOTO FAVORÁVEL", "VOTO CONTRÁRIO", 
        "VOTO FAVORAVEL.", "VOTO CONTRÁRIO.", "FAVORÁVEL", "CONTRÁRIO",
        "REQUERIMENTO DE DESTAQUE DE VOTAÇÃO EM SEPARADO", "SUBSTITUTIVO",
        "REQUERIMENTO DE RETIRADA DE PROPOSIÇÃO DA ORDEM DO DIA", "SEGUNDO TURNO",
        "PAUTA (PROCESSO LEGISLATIVO)", "DISPOSITIVO LEGAL", "EMENDA DE PLENÁRIO",
        "PARECER (PROPOSIÇÃO LEGISLATIVA)", "PARECER DO RELATOR", "RELATOR",
        "PROJETO DE LEI DE CONVERSÃO", "REQUERIMENTO", "APROVAÇÃO", "ALTERAÇÃO",

        # --- TIPOS DE PROPOSIÇÃO (O "VEÍCULO") ---
        "PROPOSTA DE EMENDA À CONSTITUIÇÃO", "PROJETO DE LEI COMPLEMENTAR",
        "PROJETO DE LEI ORDINARIA", "PROJETO DE LEI ORDINÁRIA", "MEDIDA PROVISORIA", 
        "MEDIDA PROVISÓRIA", "PROJETO DE LEI DO CONGRESSO NACIONAL", "MPV 1095/2021",

        # --- AGENTES E INSTITUIÇÕES (GENÉRICOS) ---
        "DEPUTADO FEDERAL", "PRESIDENTE DA REPÚBLICA", "EX-PRESIDENTE DA REPÚBLICA",
        "GOVERNO FEDERAL", "GOVERNO", "GOVERNO ESTADUAL", "GOVERNADOR",
        "CONGRESSO NACIONAL", "SENADO FEDERAL", "SUPREMO TRIBUNAL FEDERAL (STF)",
        "MINISTRO DO SUPREMO TRIBUNAL FEDERAL", "PODER JUDICIÁRIO", "BASE DE APOIO POLÍTICO",
        "MINORIA PARLAMENTAR", "MAIORIA PARLAMENTAR", "OPOSIÇÃO POLÍTICA", "VEREADOR",

        # --- PARTIDOS E FEDERAÇÕES ---
        "PARTIDO LIBERAL (PL)", "PARTIDO DOS TRABALHADORES (PT)", "PARTIDO NOVO (NOVO)",
        "PARTIDO SOCIAL DEMOCRÁTICO (PSD) (2011)", "PARTIDO VERDE (PV)", 
        "PARTIDO DEMOCRÁTICO TRABALHISTA (PDT)", "PARTIDO DEMOCRATICO TRABALHISTA (PDT)",
        "PARTIDO SOCIALISTA BRASILEIRO (PSB) (1987)", "PARTIDO SOCIAL LIBERAL (PSL)",
        "PARTIDO PROGRESSISTA (PP) (2003)", "CIDADANIA (PARTIDO POLÍTICO)", "PODEMOS (PODE) (2016)",
        "FEDERAÇÃO PSOL REDE", "FEDERAÇÃO BRASIL DA ESPERANÇA (FE BRASIL)", "BLOCO PARLAMENTAR",

        # --- SENTIMENTOS E AÇÕES ABSTRATAS ---
        "CRÍTICA", "DEFESA", "HOMENAGEM", "MANIFESTAÇÃO", "ATUAÇÃO", 
        "ATUAÇÃO PARLAMENTAR", "ANIVERSÁRIO DE EMANCIPAÇÃO POLÍTICA", "CRIAÇÃO"
    }
        
        # 1. Busca o Ranking (Query Principal)
        stmt = (
            select(
                Politico.id.label("politico_id"),
                Politico.nome.label("nome_politico"),
                Politico.partido_sigla.label("sigla_partido"),
                Politico.uf.label("sigla_uf"),
                func.count(Discurso.id).label("total_discursos")
            )
            .join(Discurso, Discurso.politico_id == Politico.id)
            .group_by(Politico.id, Politico.nome, Politico.partido_sigla, Politico.uf)
            .order_by(desc("total_discursos"))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        politicos_ranking = result.mappings().all()

        # 2. Coleta IDs e busca Keywords
        politico_ids = [r["politico_id"] for r in politicos_ranking]
        stmt_kw = select(Discurso.politico_id, Discurso.keywords).where(
            Discurso.politico_id.in_(politico_ids),
            Discurso.keywords != None
        )
        kw_result = await self.db.execute(stmt_kw)
        
        # 3. Processamento com Counter
        keywords_por_politico = {pid: Counter() for pid in politico_ids}
        for row in kw_result:
            # 1. Transforma em lista
            tags_sujas = [t.strip().upper() for t in row.keywords.replace(";", ",").split(",") if t.strip()]
            
            # 2. Filtra: só entra o que NÃO estiver na blacklist e tiver mais de 3 letras
            tags_limpas = [
                t for t in tags_sujas 
                if t not in BLACKLIST_KEYWORDS and len(t) > 3
            ]
            
            keywords_por_politico[row.politico_id].update(tags_limpas)
        # 4. Montagem do Resultado Final
        final_ranking = []
        for r in politicos_ranking:
            pid = r["politico_id"]
            # Criamos a lista de KeywordInfo com a palavra e a frequência
            top_10_data = [
                KeywordInfo(keyword=kw, frequencia=count) 
                for kw, count in keywords_por_politico[pid].most_common(20)
            ]
            
            final_ranking.append(
                RankingDiscursoPolitico(
                    politico_id=pid,
                    nome_politico=r["nome_politico"],
                    sigla_partido=r["sigla_partido"],
                    sigla_uf=r["sigla_uf"],
                    total_discursos=r["total_discursos"],
                    temas_mais_discutidos=top_10_data
                )
            )

        return final_ranking
    

    async def get_ranking_performance_politicos(self):
        # Dicionário de cotas para o SQL (simplificado para o exemplo)
        # Em produção, você pode passar isso via parâmetros ou JOIN com uma tabela de cotas
        
        stmt = (
            select(
                Politico.id,
                Politico.nome,
                Politico.uf,
                Politico.partido_sigla,
                Politico.url_foto,
                # 1. Cálculo de Assiduidade com Cast para Numeric
                func.coalesce(
                    func.round(
                        cast(
                            (func.count(Presenca.id).filter(Presenca.frequencia_sessao == "Presença").cast(Float) / 
                            func.nullif(func.count(Presenca.id), 0)) * 100,
                            Numeric
                        ), 
                        2
                    ),
                    0 # Valor padrão se for nulo
                ).label("nota_assiduidade"),
                # 2. Cálculo de Produção Ponderada (Simplificado para o ranking)
                func.coalesce(func.sum(
                    case(
                        (Proposicao.sigla_tipo.in_(['PEC', 'PL', 'PLC', 'PLP']), 1.0),
                        (Proposicao.sigla_tipo.in_(['PDC', 'PRC', 'MPV']), 0.5),
                        else_=0.05
                    )
                ), 0).label("pontos_producao")
            )
            .select_from(Politico)
            .outerjoin(Presenca, Presenca.politico_id == Politico.id)
            .outerjoin(ProposicaoAutor, ProposicaoAutor.politico_id == Politico.id)
            .outerjoin(Proposicao, Proposicao.id == ProposicaoAutor.proposicao_id)
            .group_by(Politico.id)
            .order_by(desc("nota_assiduidade")) # Ordenação inicial
        )
        
        result = await self.db.execute(stmt)
        return result.mappings().all()
    

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
    

    