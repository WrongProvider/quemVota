"""
Repositório de Deputados — Camada de acesso a dados.

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
    Deputado,
    ProposicaoAutor,
    Proposicao,
    Votacao,
    Voto,
    VerbaGabinete,
)

logger = logging.getLogger(__name__)

_MAX_LIMIT_DEPUTADOS = 600
_MAX_LIMIT_VOTACOES  = 20
_MAX_LIMIT_DESPESAS  = 20
_MAX_LIMIT_RESUMO    = 60


class PoliticoRepository:
    """Acesso a dados de deputados. Todas as queries são parametrizadas."""

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
    ) -> list[Deputado]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_DEPUTADOS)
        safe_offset = max(offset, 0)

        stmt = select(Deputado)

        if q:
            stmt = stmt.where(Deputado.nome.ilike(f"%{q}%"))
        if uf:
            stmt = stmt.where(Deputado.siglaUF == uf.upper()[:2])
        if partido:
            stmt = stmt.where(Deputado.siglaPartido == partido.upper()[:10])

        stmt = stmt.order_by(Deputado.nome).limit(safe_limit).offset(safe_offset)

        try:
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError:
            logger.exception("Erro ao listar deputados")
            raise

    # ------------------------------------------------------------------
    # Detalhe
    # ------------------------------------------------------------------

    async def get_politico_repo(self, deputado_id: int) -> Deputado | None:
        stmt = select(Deputado).where(Deputado.id == deputado_id)
        try:
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar deputado id=%s", deputado_id)
            raise

    async def get_politico_by_slug_repo(self, slug: str) -> Deputado | None:
        stmt = select(Deputado).where(Deputado.slug == slug)
        try:
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar deputado slug=%s", slug)
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
                Proposicao.siglaTipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa,
                Voto.voto.label("voto"),
                Votacao.descricao.label("resultado_da_votacao"),
                Votacao.tipoVotacao.label("tipo_votacao"),
                Votacao.uri,
            )
            .join(Voto, Voto.idVotacao == Votacao.id)
            .join(Proposicao, Votacao.idProposicao == Proposicao.id)
            .where(Voto.idDeputado == politico_id)
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
            logger.exception("Erro ao buscar votações do deputado id=%s", politico_id)
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
                Despesa.dataDocumento,
                Despesa.valorLiquido,
                Despesa.nomeFornecedor,
                Despesa.tipoDespesa,
                Despesa.urlDocumento,
            )
            .where(Despesa.idDeputado == politico_id)
        )

        if ano is not None:
            stmt = stmt.where(Despesa.ano == ano)
        if mes is not None:
            stmt = stmt.where(Despesa.mes == mes)

        stmt = stmt.order_by(Despesa.dataDocumento.desc()).limit(safe_limit).offset(safe_offset)

        try:
            result = await self.db.execute(stmt)
            return [PoliticoDespesaDetalhe(**row) for row in result.mappings()]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar despesas do deputado id=%s", politico_id)
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
                func.sum(Despesa.valorLiquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas"),
            )
            .where(Despesa.idDeputado == politico_id)
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
            logger.exception("Erro ao buscar resumo de despesas do deputado id=%s", politico_id)
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
                func.sum(Despesa.valorLiquido).label("total_gasto"),
                func.count(Despesa.id).label("qtd_despesas"),
            )
            .where(Despesa.idDeputado == politico_id)
            .group_by(Despesa.ano, Despesa.mes)
            .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        )
        if ano is not None:
            stmt_historico = stmt_historico.where(Despesa.ano == ano)
        if safe_limit:
            stmt_historico = stmt_historico.limit(safe_limit)

        # ── Top fornecedores ─────────────────────────────────────────
        fornecedor_rank_sq = (
            select(
                Despesa.nomeFornecedor,
                Despesa.tipoDespesa,
                func.count(Despesa.id).label("qtd"),
                func.rank()
                .over(
                    partition_by=Despesa.nomeFornecedor,
                    order_by=func.count(Despesa.id).desc(),
                )
                .label("rnk"),
            )
            .where(Despesa.idDeputado == politico_id)
            .group_by(Despesa.nomeFornecedor, Despesa.tipoDespesa)
        )
        if ano is not None:
            fornecedor_rank_sq = fornecedor_rank_sq.where(Despesa.ano == ano)
        fornecedor_rank_sq = fornecedor_rank_sq.subquery("fornecedor_rank")

        categoria_principal_sq = (
            select(
                fornecedor_rank_sq.c.nomeFornecedor,
                fornecedor_rank_sq.c.tipoDespesa.label("categoria_principal"),
            )
            .where(fornecedor_rank_sq.c.rnk == 1)
            .subquery("categoria_principal")
        )

        stmt_empresas = (
            select(
                Despesa.nomeFornecedor.label("nome"),
                func.sum(Despesa.valorLiquido).label("total"),
                categoria_principal_sq.c.categoria_principal,
            )
            .join(
                categoria_principal_sq,
                Despesa.nomeFornecedor == categoria_principal_sq.c.nomeFornecedor,
            )
            .where(Despesa.idDeputado == politico_id)
            .group_by(
                Despesa.nomeFornecedor,
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
                Despesa.tipoDespesa.label("nome"),
                func.sum(Despesa.valorLiquido).label("total"),
            )
            .where(Despesa.idDeputado == politico_id)
            .group_by(Despesa.tipoDespesa)
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
            logger.exception("Erro ao buscar resumo completo do deputado id=%s", politico_id)
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
    # Estatísticas — com filtro de ano
    # ------------------------------------------------------------------

    async def get_politicos_estatisticas_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
    ) -> PoliticoEstatisticasResponse:
        # --- Votações ---
        stmt_votos = select(func.count(func.distinct(Voto.idVotacao))).where(
            Voto.idDeputado == politico_id
        )
        if ano is not None:
            stmt_votos = (
                stmt_votos
                .join(Votacao, Votacao.id == Voto.idVotacao)
                .where(func.extract("year", Votacao.data) == ano)
            )

        # --- Despesas ---
        stmt_despesas = select(
            func.count(Despesa.id),
            func.coalesce(func.sum(Despesa.valorLiquido), 0),
            func.min(Despesa.ano),
            func.max(Despesa.ano),
        ).where(Despesa.idDeputado == politico_id)

        if ano is not None:
            stmt_despesas = stmt_despesas.where(Despesa.ano == ano)

        # --- Verba de gabinete ---
        stmt_gabinete = select(
            func.coalesce(func.sum(VerbaGabinete.valorGasto), 0)
        ).where(VerbaGabinete.idDeputado == politico_id)
        if ano is not None:
            stmt_gabinete = stmt_gabinete.where(VerbaGabinete.ano == ano)

        try:
            res_votos    = await self.db.execute(stmt_votos)
            res_despesas = await self.db.execute(stmt_despesas)
            res_gabinete = await self.db.execute(stmt_gabinete)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar estatísticas do deputado id=%s", politico_id)
            raise

        total_votacoes = res_votos.scalar() or 0
        total_despesas, total_gasto, primeiro_ano, ultimo_ano = res_despesas.one()
        total_gasto_gabinete = float(res_gabinete.scalar() or 0)

        if ano is not None:
            stmt_meses = select(
                func.count(func.distinct(Despesa.mes))
            ).where(Despesa.idDeputado == politico_id, Despesa.ano == ano)
            try:
                res_meses   = await self.db.execute(stmt_meses)
                total_meses = res_meses.scalar() or 1
            except SQLAlchemyError:
                logger.exception("Erro ao buscar meses ativos do deputado id=%s", politico_id)
                raise
        else:
            total_meses = (
                (ultimo_ano - primeiro_ano + 1) * 12
                if primeiro_ano and ultimo_ano
                else 1
            )

        gasto_ceap     = float(total_gasto or 0)
        gasto_combinado = round(gasto_ceap + total_gasto_gabinete, 2)

        media_mensal = (
            round(gasto_ceap / total_meses, 2)
            if total_meses > 0 and gasto_ceap
            else 0.0
        )

        return PoliticoEstatisticasResponse(
            total_votacoes=total_votacoes,
            total_despesas=total_despesas or 0,
            total_gasto=gasto_ceap,
            total_gasto_gabinete=total_gasto_gabinete,
            total_gasto_combinado=gasto_combinado,
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
        Retorna todas as proposições em que o deputado é autor
        (principal ou coautor), ordenadas por data de apresentação desc.
        """
        safe_limit = min(abs(limit), 100)

        stmt_ids = (
            select(ProposicaoAutor.idProposicao)
            .where(ProposicaoAutor.idDeputadoAutor == politico_id)
            .distinct()
        )

        try:
            result_ids = await self.db.execute(stmt_ids)
            proposicao_ids = [row[0] for row in result_ids.all()]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ids de proposições do deputado id=%s", politico_id)
            raise

        if not proposicao_ids:
            return []

        stmt = (
            select(Proposicao)
            .where(Proposicao.id.in_(proposicao_ids))
            .options(
                selectinload(Proposicao.autores),
                selectinload(Proposicao.temas),
            )
            .order_by(desc(Proposicao.dataApresentacao))
            .limit(safe_limit)
        )

        try:
            result = await self.db.execute(stmt)
            proposicoes = result.scalars().all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar proposições do deputado id=%s", politico_id)
            raise

        return [
            ProposicaoParaPolitico(
                id=p.id,
                id_camara=p.idCamara,
                sigla_tipo=p.siglaTipo,
                numero=p.numero,
                ano=p.ano,
                descricao_tipo=p.descricaoTipo,
                ementa=p.ementa,
                keywords=p.keywords,
                data_apresentacao=p.dataApresentacao,
                url_inteiro_teor=p.urlInteiroTeor,
                autores=[
                    ProposicaoAutorResumo(
                        politico_id=a.idDeputadoAutor,
                        nome=a.nomeAutor,
                        tipo=a.tipoAutor,
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
        stmt = select(func.coalesce(func.sum(VerbaGabinete.valorGasto), 0)).where(
            VerbaGabinete.idDeputado == politico_id,
        )
        if ano is not None:
            stmt = stmt.where(VerbaGabinete.ano == ano)
        if mes is not None:
            stmt = stmt.where(VerbaGabinete.mes == mes)

        try:
            result = await self.db.execute(stmt)
            return float(result.scalar() or 0)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar verba de gabinete do deputado id=%s", politico_id)
            raise

    # ------------------------------------------------------------------
    # Atividade legislativa — votações paginadas
    # ------------------------------------------------------------------

    async def get_atividade_votacoes_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list, int]:
        safe_limit  = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        base_filter = [Voto.idDeputado == politico_id]
        if ano is not None:
            base_filter.append(func.extract("year", Votacao.data) == ano)

        stmt_count = (
            select(func.count())
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .where(*base_filter)
        )

        stmt_data = (
            select(
                Votacao.id.label("id_votacao"),
                Votacao.data,
                Votacao.idProposicao.label("proposicao_id"),
                Proposicao.siglaTipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
                Voto.voto.label("voto"),
                Votacao.aprovacao,
                Votacao.tipoVotacao.label("tipo_votacao"),
                Votacao.siglaOrgao.label("sigla_orgao"),
            )
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .outerjoin(Proposicao, Proposicao.id == Votacao.idProposicao)
            .where(*base_filter)
            .order_by(desc(Votacao.data))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            res_count = await self.db.execute(stmt_count)
            res_data  = await self.db.execute(stmt_data)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar votações (atividade) do deputado id=%s", politico_id)
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

    # ------------------------------------------------------------------
    # Atividade legislativa — proposições paginadas
    # ------------------------------------------------------------------

    async def get_atividade_proposicoes_repo(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list, int]:
        from backend.schemas import ProposicaoResumida  # import local evita circular

        safe_limit  = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        base_filter = [ProposicaoAutor.idDeputadoAutor == politico_id]
        if ano is not None:
            base_filter.append(Proposicao.ano == ano)

        stmt_count = (
            select(func.count(func.distinct(ProposicaoAutor.idProposicao)))
            .select_from(ProposicaoAutor)
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(*base_filter)
        )

        stmt_ids = (
            select(
                ProposicaoAutor.idProposicao,
                ProposicaoAutor.proponente,
                ProposicaoAutor.tipoAutor.label("tipo_autoria"),
            )
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(*base_filter)
            .order_by(desc(Proposicao.dataApresentacao))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            res_count = await self.db.execute(stmt_count)
            res_ids   = await self.db.execute(stmt_ids)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar proposições (atividade) do deputado id=%s", politico_id)
            raise

        total        = res_count.scalar() or 0
        autoria_rows = res_ids.mappings().all()

        if not autoria_rows:
            return [], total

        autoria_map: dict[int, dict] = {
            row["idProposicao"]: {
                "proponente":   bool(row["proponente"]),
                "tipo_autoria": row["tipo_autoria"],
            }
            for row in autoria_rows
        }
        ids_paginados = list(autoria_map.keys())

        stmt_props = (
            select(Proposicao)
            .where(Proposicao.id.in_(ids_paginados))
            .options(selectinload(Proposicao.temas))
            .order_by(desc(Proposicao.dataApresentacao))
        )

        try:
            res_props = await self.db.execute(stmt_props)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar detalhes de proposições do deputado id=%s", politico_id)
            raise

        proposicoes_orm = res_props.scalars().all()

        proposicoes = [
            ProposicaoResumida(
                id=p.id,
                id_camara=p.idCamara,
                sigla_tipo=p.siglaTipo,
                numero=p.numero,
                ano=p.ano,
                descricao_tipo=p.descricaoTipo,
                ementa=p.ementa,
                keywords=p.keywords,
                data_apresentacao=p.dataApresentacao,
                url_inteiro_teor=p.urlInteiroTeor,
                proponente=autoria_map[p.id]["proponente"],
                tipo_autoria=autoria_map[p.id]["tipo_autoria"],
                temas=[t.tema for t in p.temas],
            )
            for p in proposicoes_orm
        ]

        return proposicoes, total