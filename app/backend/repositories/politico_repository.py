"""
Repositório de Políticos — Camada de acesso a dados.

Segurança (OWASP):
  - A01 / SQL Injection: todas as queries usam SQLAlchemy Core com bind parameters;
    nenhuma concatenação ou interpolação de strings em SQL.
  - A03 / Sensitive Data Exposure: nenhum dado sensível é logado ou exposto nas exceções.
  - A04 / Insecure Design: limites máximos aplicados aqui (não só no serviço) como
    defesa em profundidade.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import case, desc, func, select, String
from sqlalchemy.exc import SQLAlchemyError

from backend.schemas import (
    ItemRanking,
    PoliticoDespesaDetalhe,
    PoliticoDespesaResumo,
    PoliticoDespesaResumoCompleto,
    PoliticoEstatisticasResponse,
    PoliticoVoto,
)
from backend.models import (
    Despesa,
    Politico,
    Presenca,
    ProposicaoAutor,
    Proposicao,
    Votacao,
    Voto,
)

logger = logging.getLogger(__name__)

_MAX_LIMIT_POLITICOS = 600
_MAX_LIMIT_VOTACOES  = 20
_MAX_LIMIT_DESPESAS  = 20
_MAX_LIMIT_RESUMO    = 60


class PoliticoRepository:
    """Acesso a dados de políticos. Todas as queries são parametrizadas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Listagem / busca
    # ------------------------------------------------------------------

    async def get_politicos_repo(
        self,
        *,
        q: str | None = None,
        uf: str | None = None,
        partido: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Politico]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_POLITICOS)
        safe_offset = max(offset, 0)

        stmt = select(Politico)

        if q:
            stmt = stmt.where(Politico.nome.ilike(f"%{q}%"))
        if uf:
            stmt = stmt.where(Politico.uf == uf.upper()[:2])
        if partido:
            stmt = stmt.where(Politico.partido_sigla == partido.upper()[:10])

        stmt = stmt.order_by(Politico.nome).limit(safe_limit).offset(safe_offset)

        try:
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError:
            logger.exception("Erro ao listar políticos")
            raise

    # ------------------------------------------------------------------
    # Detalhe
    # ------------------------------------------------------------------

    async def get_politico_repo(self, politico_id: int) -> Politico | None:
        stmt = select(Politico).where(Politico.id == politico_id)
        try:
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar político id=%s", politico_id)
            raise

    # ------------------------------------------------------------------
    # Votações
    # ------------------------------------------------------------------

    async def get_politicos_votacoes_repo(
        self,
        politico_id: int,
        *,
        limit: int = 20,
        ano: int | None = None,
    ) -> list[PoliticoVoto]:
        safe_limit = min(abs(limit), _MAX_LIMIT_VOTACOES)

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
                Votacao.tipo_votacao,
                Votacao.uri,
            )
            .join(Voto, Voto.votacao_id == Votacao.id)
            .join(Proposicao, Votacao.proposicao_id == Proposicao.id)
            .where(Voto.politico_id == politico_id)
            .order_by(desc(Votacao.data))
            .limit(safe_limit)
        )
        if ano is not None:
            stmt = stmt.where(Proposicao.ano == ano)

        try:
            result = await self.db.execute(stmt)
            return [
                PoliticoVoto(
                    id_votacao=row.id_votacao,
                    data=row.data,
                    proposicao_sigla=row.proposicao_sigla,
                    proposicao_numero=row.proposicao_numero,
                    proposicao_ano=row.proposicao_ano,
                    ementa=row.ementa,
                    voto=row.voto,
                    resultado_da_votacao=row.resultado_da_votacao,
                    tipo_votacao=row.tipo_votacao,
                    uri=row.uri,
                )
                for row in result.mappings()
            ]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar votações do político id=%s", politico_id)
            raise

    # ------------------------------------------------------------------
    # Despesas — detalhe
    # ------------------------------------------------------------------

    async def get_politicos_despesas_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        mes: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PoliticoDespesaDetalhe]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_DESPESAS)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Despesa.id,
                Despesa.data_documento,
                Despesa.valor_liquido,
                Despesa.nome_fornecedor,
                Despesa.tipo_despesa,
                Despesa.url_documento,
            )
            .where(Despesa.politico_id == politico_id)
        )

        if ano is not None:
            stmt = stmt.where(Despesa.ano == ano)
        if mes is not None:
            stmt = stmt.where(Despesa.mes == mes)

        stmt = stmt.order_by(Despesa.data_documento.desc()).limit(safe_limit).offset(safe_offset)

        try:
            result = await self.db.execute(stmt)
            return [PoliticoDespesaDetalhe(**row) for row in result.mappings()]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar despesas do político id=%s", politico_id)
            raise

    # ------------------------------------------------------------------
    # Despesas — resumo mensal
    # ------------------------------------------------------------------

    async def get_politicos_despesas_resumo_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit: int | None = None,
    ) -> list[PoliticoDespesaResumo]:
        stmt = (
            select(
                Despesa.ano,
                Despesa.mes,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas"),
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        )

        if ano is not None:
            stmt = stmt.where(Despesa.ano == ano)
        if limit is not None:
            stmt = stmt.limit(min(abs(limit), _MAX_LIMIT_RESUMO))

        try:
            result = await self.db.execute(stmt)
            return [
                PoliticoDespesaResumo(
                    ano=row.ano,
                    mes=row.mes,
                    total_gasto=float(row.total_gasto or 0),
                    qtd_despesas=row.qtd_despesas,
                )
                for row in result.mappings()
            ]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar resumo de despesas do político id=%s", politico_id)
            raise

    # ------------------------------------------------------------------
    # Despesas — resumo completo
    # ------------------------------------------------------------------

    async def get_politicos_despesas_resumo_completo_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit_meses: int | None = None,
    ) -> PoliticoDespesaResumoCompleto:
        safe_limit = min(abs(limit_meses), _MAX_LIMIT_RESUMO) if limit_meses else None

        stmt_historico = (
            select(
                Despesa.ano,
                Despesa.mes,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas"),
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        )
        if ano is not None:
            stmt_historico = stmt_historico.where(Despesa.ano == ano)
        if safe_limit:
            stmt_historico = stmt_historico.limit(safe_limit)

        stmt_empresas = (
            select(
                Despesa.nome_fornecedor.label("nome"),
                func.sum(Despesa.valor_liquido).label("total"),
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.nome_fornecedor)
            .order_by(desc("total"))
            .limit(10)
        )
        if ano is not None:
            stmt_empresas = stmt_empresas.where(Despesa.ano == ano)

        stmt_categorias = (
            select(
                Despesa.tipo_despesa.label("nome"),
                func.sum(Despesa.valor_liquido).label("total"),
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.tipo_despesa)
            .order_by(desc("total"))
            .limit(10)
        )
        if ano is not None:
            stmt_categorias = stmt_categorias.where(Despesa.ano == ano)

        try:
            res_h = await self.db.execute(stmt_historico)
            res_e = await self.db.execute(stmt_empresas)
            res_c = await self.db.execute(stmt_categorias)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar resumo completo do político id=%s", politico_id)
            raise

        return PoliticoDespesaResumoCompleto(
            historico_mensal=[
                PoliticoDespesaResumo(
                    ano=row.ano,
                    mes=row.mes,
                    total_gasto=float(row.total_gasto or 0),
                    qtd_despesas=row.qtd_despesas,
                )
                for row in res_h.mappings()
            ],
            top_fornecedores=[
                ItemRanking(nome=row.nome, total=float(row.total or 0))
                for row in res_e.mappings()
            ],
            top_categorias=[
                ItemRanking(nome=row.nome, total=float(row.total or 0))
                for row in res_c.mappings()
            ],
        )

    # ------------------------------------------------------------------
    # Estatísticas — agora com filtro de ano
    # ------------------------------------------------------------------

    async def get_politicos_estatisticas_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
    ) -> PoliticoEstatisticasResponse:
        """
        Retorna estatísticas agregadas do parlamentar.

        Args:
            politico_id: ID do parlamentar.
            ano: quando fornecido, filtra votações e despesas pelo ano,
                 permitindo comparação justa na linha do tempo.
        """
        # --- Votações ---
        stmt_votos = select(func.count(func.distinct(Voto.votacao_id))).where(
            Voto.politico_id == politico_id
        )
        if ano is not None:
            stmt_votos = (
                stmt_votos
                .join(Votacao, Votacao.id == Voto.votacao_id)
                .where(func.extract("year", Votacao.data) == ano)
            )

        # --- Despesas ---
        stmt_despesas = select(
            func.count(Despesa.id),
            func.coalesce(func.sum(Despesa.valor_liquido), 0),
            func.min(Despesa.ano),
            func.max(Despesa.ano),
        ).where(Despesa.politico_id == politico_id)

        if ano is not None:
            stmt_despesas = stmt_despesas.where(Despesa.ano == ano)

        try:
            res_votos    = await self.db.execute(stmt_votos)
            res_despesas = await self.db.execute(stmt_despesas)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar estatísticas do político id=%s", politico_id)
            raise

        total_votacoes                                          = res_votos.scalar() or 0
        total_despesas, total_gasto, primeiro_ano, ultimo_ano  = res_despesas.one()

        # Quando filtrado por ano, meses = meses distintos com despesa naquele ano
        if ano is not None:
            stmt_meses = select(
                func.count(func.distinct(Despesa.mes))
            ).where(Despesa.politico_id == politico_id, Despesa.ano == ano)
            try:
                res_meses    = await self.db.execute(stmt_meses)
                total_meses  = res_meses.scalar() or 1
            except SQLAlchemyError:
                logger.exception("Erro ao buscar meses ativos do político id=%s", politico_id)
                raise
        else:
            # Mandato inteiro: (anos de diferença + 1) × 12
            total_meses = (
                (ultimo_ano - primeiro_ano + 1) * 12
                if primeiro_ano and ultimo_ano
                else 1
            )

        media_mensal = (
            round(float(total_gasto) / total_meses, 2)
            if total_meses > 0 and total_gasto
            else 0.0
        )

        return PoliticoEstatisticasResponse(
            total_votacoes=total_votacoes,
            total_despesas=total_despesas or 0,
            total_gasto=float(total_gasto or 0),
            media_mensal=media_mensal,
            primeiro_ano=primeiro_ano,
            ultimo_ano=ultimo_ano,
        )