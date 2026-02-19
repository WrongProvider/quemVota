# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from backend.schemas import ItemRanking, PoliticoDespesaDetalhe, PoliticoDespesaResumoCompleto, PoliticoEstatisticasResponse, PoliticoEstatisticasResponse, PoliticoVoto, PoliticoDespesaResumo
from backend.models import Politico, Votacao, Voto, Proposicao, Despesa

class PoliticoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_politicos_repo(self, q: str = None, uf: str = None, limit: int = 100, offset: int = 0):
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

        # resolve primeiro a rotina
        result = await self.db.execute(stmt)
        # se fizesse junto ele da await numa corrotina.
        return result.scalars().all()
    
    async def get_politico_repo(self, politico_id: int):
        stmt = select(Politico).where(Politico.id == politico_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

        # if uf:
        #     stmt = stmt.where(Politico.uf == uf)

        # stmt = (
        #     stmt.order_by(Politico.nome)
        #     .limit(limit)
        #     .offset(offset)
        # )

        # # resolve primeiro a rotina
        # result = await self.db.execute(stmt)
        # # se fizesse junto ele da await numa corrotina.
        # return result.scalars().all()
    
    
    async def get_politicos_votacoes_repo(self, politico_id: int, limit: int = 20):
        # Implementação para buscar as votações de um político específico
        stmt = (
                select(
                    Votacao.id.label("id_votacao"),
                    Votacao.data,
                    Proposicao.sigla_tipo.label("proposicao_sigla"),
                    Proposicao.numero.label("proposicao_numero"),
                    Proposicao.ano.label("proposicao_ano"),
                    Proposicao.ementa,
                    Voto.tipo_voto.label("voto"),
                    Votacao.descricao.label("resultado_da_votacao"),
                    Votacao.tipo_votacao.label("tipo_votacao"),
                    Votacao.uri.label("uri do evento de votação")
                )
                .join(Voto, Voto.votacao_id == Votacao.id)
                .join(Proposicao, Votacao.proposicao_id == Proposicao.id)
                .where(Voto.politico_id == politico_id)
                .order_by(desc(Votacao.data))
                .limit(limit)
            )
        
        result = await self.db.execute(stmt)

        return [
            PoliticoVoto(
                id_votacao=r["id_votacao"],
                data=r["data"],
                proposicao_sigla=r["proposicao_sigla"],
                proposicao_numero=r["proposicao_numero"],
                proposicao_ano=r["proposicao_ano"],
                ementa=r["ementa"],
                voto=r["voto"],
                resultado_da_votacao=r["resultado_da_votacao"],
                tipo_votacao=r["tipo_votacao"],
                uri=r["uri do evento de votação"]
            )
            for r in result.mappings()
        ]
    
    async def get_politicos_despesas_repo(self, politico_id: int, ano: int = None, mes: int = None, limit: int = 20, offset: int = 0):
        # Implementação para buscar as despesas de um político específico
        stmt = (
            select(
                Despesa.id,
                Despesa.data_documento,
                Despesa.valor_liquido,
                Despesa.nome_fornecedor,
                Despesa.tipo_despesa,
                Despesa.url_documento
            )
            .where(Despesa.politico_id == politico_id)
        )

        if ano:
            stmt = stmt.where(Despesa.ano == ano)

        if mes:
            stmt = stmt.where(Despesa.mes == mes)

        stmt = (
            stmt.order_by(Despesa.data_documento.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        return [
            PoliticoDespesaDetalhe(**r)
            for r in result.mappings()
        ]
    
    async def get_politicos_despesas_resumo_repo(
        self, 
        politico_id: int, 
        ano: int = None, 
        limit: int = None
    ):
        """
        Retorna o resumo de gastos. 
        - Se 'ano' for informado, filtra aquele ano e o 'limit' controla quantos meses.
        - Se 'ano' for None, traz o histórico geral e o 'limit' controla o alcance total.
        """
        stmt = (
            select(
                Despesa.ano,
                Despesa.mes,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        )

        # Filtra por um ano específico (ex: 2026)
        if ano:
            stmt = stmt.where(Despesa.ano == ano)

        # Aplica o limite (ex: 5 para pegar 5 meses ou os últimos 5 anos/meses)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        
        return [
            PoliticoDespesaResumo(
                ano=r["ano"],
                mes=r["mes"],
                total_gasto=float(r["total_gasto"] or 0),
                qtd_despesas=r["qtd_despesas"]
            )
            for r in result.mappings()
        ]
    
    async def get_politicos_despesas_resumo_completo_repo(
        self, politico_id: int, ano: int = None, limit_meses: int = None
    ):
        # 1. Busca Histórico Mensal (Sua query anterior)
        stmt_historico = (
            select(
                Despesa.ano,
                Despesa.mes,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        )
        if ano: stmt_historico = stmt_historico.where(Despesa.ano == ano)
        if limit_meses: stmt_historico = stmt_historico.limit(limit_meses)

        # 2. Top 10 Fornecedores (Empresas)
        stmt_empresas = (
            select(
                Despesa.nome_fornecedor.label("nome"),
                func.sum(Despesa.valor_liquido).label("total")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.nome_fornecedor)
            .order_by(desc("total"))
            .limit(10)
        )

        # 3. Top 10 Categorias de Gastos
        stmt_categorias = (
            select(
                Despesa.tipo_despesa.label("nome"),
                func.sum(Despesa.valor_liquido).label("total")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.tipo_despesa)
            .order_by(desc("total"))
            .limit(10)
        )

        # Execução
        res_h = await self.db.execute(stmt_historico)
        res_e = await self.db.execute(stmt_empresas)
        res_c = await self.db.execute(stmt_categorias)

        # ... (dentro de get_politicos_despesas_resumo_completo_repo)
        
        # 1. Prepare as listas primeiro
        lista_historico = [
            PoliticoDespesaResumo(
                ano=r["ano"], 
                mes=r["mes"], 
                total_gasto=float(r["total_gasto"] or 0), 
                qtd_despesas=r["qtd_despesas"]
            ) for r in res_h.mappings()
        ]

        lista_fornecedores = [
            ItemRanking(nome=r["nome"], total=float(r["total"] or 0)) 
            for r in res_e.mappings()
        ]

        lista_categorias = [
            ItemRanking(nome=r["nome"], total=float(r["total"] or 0)) 
            for r in res_c.mappings()
        ]

        # 2. Retorne o modelo passando as chaves explicitamente
        return PoliticoDespesaResumoCompleto(
            historico_mensal=lista_historico,
            top_fornecedores=lista_fornecedores,
            top_categorias=lista_categorias
        )
    
    async def get_politicos_estatisticas_repo(self, politico_id: int):
        # Total votações    
        stmt_votos = select(
            func.count(func.distinct(Voto.votacao_id))
        ).where(
            Voto.politico_id == politico_id
        )

        # Estatísticas despesas
        stmt_despesas = select(
            func.count(Despesa.id),
            func.coalesce(func.sum(Despesa.valor_liquido), 0),
            func.min(Despesa.ano),
            func.max(Despesa.ano)
        ).where(
            Despesa.politico_id == politico_id
        )

        res_votos = await self.db.execute(stmt_votos)
        res_despesas = await self.db.execute(stmt_despesas)
        
        total_votacoes = res_votos.scalar()
        total_despesas, total_gasto, primeiro_ano, ultimo_ano = res_despesas.one()

        media_mensal = 0.0
        if primeiro_ano and ultimo_ano:
            total_meses = (ultimo_ano - primeiro_ano + 1) * 12
            if total_meses > 0:
                media_mensal = float(total_gasto) / total_meses

        return PoliticoEstatisticasResponse(
            total_votacoes=total_votacoes or 0,
            total_despesas=total_despesas or 0,
            total_gasto=float(total_gasto or 0),
            media_mensal=round(media_mensal, 2),
            primeiro_ano=primeiro_ano,
            ultimo_ano=ultimo_ano
        )