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
from sqlalchemy.orm import selectinload

from backend.schemas import (
    ItemRanking,
    ItemRankingFornecedor,
    PoliticoDespesaDetalhe,
    PoliticoDespesaResumo,
    PoliticoDespesaResumoCompleto,
    PoliticoEstatisticasResponse,
    PoliticoVoto,
    ProposicaoAutorResumo,
    ProposicaoParaPolitico,
    TemaResumoSimples,
    VotacaoResumida
)
from backend.models import (
    Despesa,
    Politico,
    Presenca,
    ProposicaoAutor,
    Proposicao,
    Votacao,
    Voto,
    VerbaGabinete,
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

        # ── Histórico mensal ──────────────────────────────────────────
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

        # ── Top fornecedores ─────────────────────────────────────────
        #
        # Para cada fornecedor, além do total gasto, buscamos a
        # `categoria_principal` — o tipo_despesa mais frequente nas
        # notas fiscais daquele fornecedor para este parlamentar.
        #
        # Estratégia: subquery que ranqueia cada (fornecedor, tipo_despesa)
        # por contagem decrescente e filtra apenas o rank = 1 (modo).
        #
        # Compatível com PostgreSQL, SQLite e MySQL via window function.
        #
        fornecedor_rank_sq = (
            select(
                Despesa.nome_fornecedor,
                Despesa.tipo_despesa,
                func.count(Despesa.id).label("qtd"),
                func.rank()
                .over(
                    partition_by=Despesa.nome_fornecedor,
                    order_by=func.count(Despesa.id).desc(),
                )
                .label("rnk"),
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.nome_fornecedor, Despesa.tipo_despesa)
        )
        if ano is not None:
            fornecedor_rank_sq = fornecedor_rank_sq.where(Despesa.ano == ano)
        fornecedor_rank_sq = fornecedor_rank_sq.subquery("fornecedor_rank")

        # Categoria predominante por fornecedor (rank = 1)
        categoria_principal_sq = (
            select(
                fornecedor_rank_sq.c.nome_fornecedor,
                fornecedor_rank_sq.c.tipo_despesa.label("categoria_principal"),
            )
            .where(fornecedor_rank_sq.c.rnk == 1)
            .subquery("categoria_principal")
        )

        stmt_empresas = (
            select(
                Despesa.nome_fornecedor.label("nome"),
                func.sum(Despesa.valor_liquido).label("total"),
                categoria_principal_sq.c.categoria_principal,
            )
            .join(
                categoria_principal_sq,
                Despesa.nome_fornecedor == categoria_principal_sq.c.nome_fornecedor,
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(
                Despesa.nome_fornecedor,
                categoria_principal_sq.c.categoria_principal,
            )
            .order_by(desc("total"))
            .limit(10)
        )
        if ano is not None:
            stmt_empresas = stmt_empresas.where(Despesa.ano == ano)

        # ── Top categorias ────────────────────────────────────────────
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
                ItemRankingFornecedor(
                    nome=row.nome,
                    total=float(row.total or 0),
                    categoria_principal=row.categoria_principal,
                )
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

        total_votacoes = res_votos.scalar() or 0
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
    
    async def get_politico_proposicoes_repo(
        self,
        politico_id: int,
        *,
        limit: int = 100,
    ) -> list:
        """
        Retorna todas as proposições em que o político é autor
        (principal ou coautor), ordenadas por data de apresentação desc.

        Usa selectinload para autores e temas — evita produto cartesiano
        com múltiplos relacionamentos carregados via JOIN.
        """

        safe_limit = min(abs(limit), 100)

        # Busca IDs de proposições onde o político é autor
        stmt_ids = (
            select(ProposicaoAutor.proposicao_id)
            .where(ProposicaoAutor.politico_id == politico_id)
            .distinct()
        )

        try:
            result_ids = await self.db.execute(stmt_ids)
            proposicao_ids = [row[0] for row in result_ids.all()]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ids de proposições do político id=%s", politico_id)
            raise

        if not proposicao_ids:
            return []

        # Busca as proposições com autores e temas já carregados
        stmt = (
            select(Proposicao)
            .where(Proposicao.id.in_(proposicao_ids))
            .options(
                selectinload(Proposicao.autores),
                selectinload(Proposicao.temas),
            )
            .order_by(desc(Proposicao.data_apresentacao))
            .limit(safe_limit)
        )

        try:
            result = await self.db.execute(stmt)
            proposicoes = result.scalars().all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar proposições do político id=%s", politico_id)
            raise

        return [
            ProposicaoParaPolitico(
                id=p.id,
                id_camara=p.id_camara,
                sigla_tipo=p.sigla_tipo,
                numero=p.numero,
                ano=p.ano,
                descricao_tipo=p.descricao_tipo,
                ementa=p.ementa,
                keywords=p.keywords,
                data_apresentacao=p.data_apresentacao,
                url_inteiro_teor=p.url_inteiro_teor,
                autores=[
                    ProposicaoAutorResumo(
                        politico_id=a.politico_id,
                        nome=a.nome,
                        tipo=a.tipo,
                        proponente=bool(a.proponente),
                    )
                    for a in p.autores
                ],
                temas=[
                    TemaResumoSimples(id=t.id, tema=t.tema)
                    for t in p.temas
                ],
            )
            for p in proposicoes
        ]
    
    async def get_politico_verba_gabinete_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        mes: int | None = None,
    ) -> float:
        stmt = select(func.coalesce(func.sum(VerbaGabinete.valor_liquido), 0)).where(
            VerbaGabinete.politico_id == politico_id,
        )
        if ano is not None:
            stmt = stmt.where(VerbaGabinete.ano == ano)
        if mes is not None:
            stmt = stmt.where(VerbaGabinete.mes == mes)

        try:
            result = await self.db.execute(stmt)
            return float(result.scalar() or 0)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar verba de gabinete do político id=%s", politico_id)
            raise

    # Dois métodos novos:
    #   - get_atividade_votacoes_repo   → votações nominais do político
    #   - get_atividade_proposicoes_repo → proposições onde é autor/coautor
    #
    # Ambos aceitam paginação e filtro por ano independentes,
    # consumidos pelo serviço via asyncio.gather (queries paralelas).
    # =============================================================================

    async def get_atividade_votacoes_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list, int]:
        """
        Retorna (lista_de_votações, total_count) para o político.

        O total_count é calculado numa subquery separada para suportar
        paginação correta sem carregar todos os registros em memória.

        Args:
            politico_id: ID interno do parlamentar.
            ano:         Quando fornecido, filtra pelo ano da votação.
            limit:       Máximo de itens retornados (cap: 100).
            offset:      Deslocamento para paginação.

        Returns:
            Tupla (votações, total) onde votações é lista de VotacaoResumida
            e total é o count sem paginação aplicada.
        """

        safe_limit  = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        # ── Query base compartilhada por dados e count ─────────────────────
        base_filter = [Voto.politico_id == politico_id]
        if ano is not None:
            base_filter.append(func.extract("year", Votacao.data) == ano)

        # ── Count total (sem limit/offset) ─────────────────────────────────
        stmt_count = (
            select(func.count())
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.votacao_id)
            .where(*base_filter)
        )

        # ── Dados paginados ────────────────────────────────────────────────
        stmt_data = (
            select(
                Votacao.id.label("id_votacao"),
                Votacao.data,
                Votacao.proposicao_id,
                Proposicao.sigla_tipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
                Voto.tipo_voto.label("voto"),
                Votacao.aprovacao,
                Votacao.tipo_votacao,
                Votacao.sigla_orgao,
            )
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.votacao_id)
            .outerjoin(Proposicao, Proposicao.id == Votacao.proposicao_id)
            .where(*base_filter)
            .order_by(desc(Votacao.data))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            res_count = await self.db.execute(stmt_count)
            res_data  = await self.db.execute(stmt_data)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar votações (atividade) do político id=%s", politico_id
            )
            raise

        total = res_count.scalar() or 0
        rows  = res_data.mappings().all()

        votacoes = [
            VotacaoResumida(
                id_votacao=row["id_votacao"],
                data=row["data"],
                proposicao_id=row["proposicao_id"],
                proposicao_sigla=row["proposicao_sigla"],
                proposicao_numero=row["proposicao_numero"],
                proposicao_ano=row["proposicao_ano"],
                proposicao_ementa=row["proposicao_ementa"],
                voto=row["voto"],
                aprovacao=row["aprovacao"],
                tipo_votacao=row["tipo_votacao"],
                sigla_orgao=row["sigla_orgao"],
            )
            for row in rows
        ]

        return votacoes, total

    async def get_atividade_proposicoes_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list, int]:
        """
        Retorna (lista_de_proposições, total_count) para proposições em que
        o político é autor ou coautor.

        Usa selectinload para temas e carrega dados de autoria (proponente,
        tipo_autoria) a partir de ProposicaoAutor — sem produto cartesiano.

        Args:
            politico_id: ID interno do parlamentar.
            ano:         Quando fornecido, filtra pelo ano de apresentação.
            limit:       Máximo de itens retornados (cap: 100).
            offset:      Deslocamento para paginação.

        Returns:
            Tupla (proposições, total) onde proposições é lista de
            ProposicaoResumida e total é o count sem paginação aplicada.
        """
        from backend.schemas import ProposicaoResumida  # import local evita circular

        safe_limit  = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        # ── Filtro base na tabela de autores ───────────────────────────────
        base_filter = [ProposicaoAutor.politico_id == politico_id]
        if ano is not None:
            base_filter.append(Proposicao.ano == ano)

        # ── Count total ────────────────────────────────────────────────────
        stmt_count = (
            select(func.count(func.distinct(ProposicaoAutor.proposicao_id)))
            .select_from(ProposicaoAutor)
            .join(Proposicao, Proposicao.id == ProposicaoAutor.proposicao_id)
            .where(*base_filter)
        )

        # ── IDs paginados (evita subquery com selectinload) ────────────────
        stmt_ids = (
            select(
                ProposicaoAutor.proposicao_id,
                ProposicaoAutor.proponente,
                ProposicaoAutor.tipo.label("tipo_autoria"),
            )
            .join(Proposicao, Proposicao.id == ProposicaoAutor.proposicao_id)
            .where(*base_filter)
            .order_by(desc(Proposicao.data_apresentacao))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            res_count = await self.db.execute(stmt_count)
            res_ids   = await self.db.execute(stmt_ids)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar proposições (atividade) do político id=%s", politico_id
            )
            raise

        total     = res_count.scalar() or 0
        autoria_rows = res_ids.mappings().all()

        if not autoria_rows:
            return [], total

        # Mapa auxiliar: proposicao_id → metadados de autoria
        autoria_map: dict[int, dict] = {
            row["proposicao_id"]: {
                "proponente":   bool(row["proponente"]),
                "tipo_autoria": row["tipo_autoria"],
            }
            for row in autoria_rows
        }
        ids_paginados = list(autoria_map.keys())

        # ── Busca proposições com temas já carregados ──────────────────────
        stmt_props = (
            select(Proposicao)
            .where(Proposicao.id.in_(ids_paginados))
            .options(selectinload(Proposicao.temas))
            .order_by(desc(Proposicao.data_apresentacao))
        )

        try:
            res_props = await self.db.execute(stmt_props)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar detalhes de proposições do político id=%s", politico_id
            )
            raise

        proposicoes_orm = res_props.scalars().all()

        proposicoes = [
            ProposicaoResumida(
                id=p.id,
                id_camara=p.id_camara,
                sigla_tipo=p.sigla_tipo,
                numero=p.numero,
                ano=p.ano,
                descricao_tipo=p.descricao_tipo,
                ementa=p.ementa,
                keywords=p.keywords,
                data_apresentacao=p.data_apresentacao,
                url_inteiro_teor=p.url_inteiro_teor,
                proponente=autoria_map[p.id]["proponente"],
                tipo_autoria=autoria_map[p.id]["tipo_autoria"],
                temas=[t.tema for t in p.temas],
            )
            for p in proposicoes_orm
        ]

        return proposicoes, total