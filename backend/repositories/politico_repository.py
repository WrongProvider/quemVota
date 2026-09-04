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

from shared.models import (
    Deputado,
    Despesa,
    Proposicao,
    ProposicaoAutor,
    Tema,
    VerbaGabinete,
    Votacao,
    Voto,
    proposicoesTemas,
)
from sqlalchemy import case, desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

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
    VotacaoResumida,
    ProposicaoResumida,
)

logger = logging.getLogger(__name__)

_MAX_LIMIT_DEPUTADOS = 600
_MAX_LIMIT_VOTACOES = 20
_MAX_LIMIT_DESPESAS = 20
_MAX_LIMIT_RESUMO = 60


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
        safe_limit = min(abs(limit), _MAX_LIMIT_DEPUTADOS)
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
            dep = result.scalars().first()
            if dep:
                return dep

            # Fallback resiliente: se não encontrar slug exato, tenta prefixo com sufixo (ex: homônimos com idCamara)
            stmt_fallback = (
                select(Deputado)
                .where(Deputado.slug.like(f"{slug}-%"))
                .order_by(
                    Deputado.idLegislaturaFinal.desc().nulls_last(),
                    Deputado.id.asc(),
                )
            )
            result_fallback = await self.db.execute(stmt_fallback)
            return result_fallback.scalars().first()
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
        safe_limit = min(abs(limit), _MAX_LIMIT_DESPESAS)
        safe_offset = max(offset, 0)

        stmt = select(
            Despesa.id,
            Despesa.dataDocumento,
            Despesa.valorLiquido,
            Despesa.nomeFornecedor,
            Despesa.tipoDespesa,
            Despesa.urlDocumento,
        ).where(Despesa.idDeputado == politico_id)

        if ano is not None:
            stmt = stmt.where(Despesa.ano == ano)
        if mes is not None:
            stmt = stmt.where(Despesa.mes == mes)

        stmt = (
            stmt.order_by(Despesa.dataDocumento.desc())
            .limit(safe_limit)
            .offset(safe_offset)
        )

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
            logger.exception(
                "Erro ao buscar resumo de despesas do deputado id=%s", politico_id
            )
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
            logger.exception(
                "Erro ao buscar resumo completo do deputado id=%s", politico_id
            )
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
            stmt_votos = stmt_votos.join(Votacao, Votacao.id == Voto.idVotacao).where(
                func.extract("year", Votacao.data) == ano
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
            res_votos = await self.db.execute(stmt_votos)
            res_despesas = await self.db.execute(stmt_despesas)
            res_gabinete = await self.db.execute(stmt_gabinete)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar estatísticas do deputado id=%s", politico_id
            )
            raise

        total_votacoes = res_votos.scalar() or 0
        total_despesas, total_gasto, primeiro_ano, ultimo_ano = res_despesas.one()
        total_gasto_gabinete = float(res_gabinete.scalar() or 0)

        if ano is not None:
            stmt_meses = select(func.count(func.distinct(Despesa.mes))).where(
                Despesa.idDeputado == politico_id, Despesa.ano == ano
            )
            try:
                res_meses = await self.db.execute(stmt_meses)
                total_meses = res_meses.scalar() or 1
            except SQLAlchemyError:
                logger.exception(
                    "Erro ao buscar meses ativos do deputado id=%s", politico_id
                )
                raise
        else:
            total_meses = (
                (ultimo_ano - primeiro_ano + 1) * 12
                if primeiro_ano and ultimo_ano
                else 1
            )

        gasto_ceap = float(total_gasto or 0)
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
            logger.exception(
                "Erro ao buscar ids de proposições do deputado id=%s", politico_id
            )
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
            logger.exception(
                "Erro ao buscar proposições do deputado id=%s", politico_id
            )
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
                temas=[TemaResumoSimples(id=t.id, tema=t.tema) for t in p.temas],
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
            logger.exception(
                "Erro ao buscar verba de gabinete do deputado id=%s", politico_id
            )
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
        q: str | None = None,
    ) -> tuple[list, int]:
        safe_limit = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        base_filter = [Voto.idDeputado == politico_id]
        if ano is not None:
            base_filter.append(func.extract("year", Votacao.data) == ano)

        # if q:
        #     termo = f"%{q}%"
        #     stmt = stmt.where(
        #         or_(
        #             Votacao.ementa.ilike(termo),
        #             Votacao.proposicao_sigla.ilike(termo) # Se houver campos em comum
        #         )
        #     )
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
            res_data = await self.db.execute(stmt_data)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar votações (atividade) do deputado id=%s", politico_id
            )
            raise

        total = res_count.scalar() or 0
        rows = res_data.mappings().all()

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
        q: str | None = None,
    ) -> tuple[list, int]:

        safe_limit = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        base_filter = [ProposicaoAutor.idDeputadoAutor == politico_id]
        if ano is not None:
            base_filter.append(Proposicao.ano == ano)

        # if q:
        #     termo = f"%{q}%"
        #     stmt = stmt.where(
        #         or_(
        #             Votacao.ementa.ilike(termo),
        #             Votacao.proposicao_sigla.ilike(termo) # Se houver campos em comum
        #         )
        #     )
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
            res_ids = await self.db.execute(stmt_ids)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar proposições (atividade) do deputado id=%s", politico_id
            )
            raise

        total = res_count.scalar() or 0
        autoria_rows = res_ids.mappings().all()

        if not autoria_rows:
            return [], total

        autoria_map: dict[int, dict] = {
            row["idProposicao"]: {
                "proponente": bool(row["proponente"]),
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
            logger.exception(
                "Erro ao buscar detalhes de proposições do deputado id=%s", politico_id
            )
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

    # ------------------------------------------------------------------
    # Comparação de Votações (Relacional)
    # ------------------------------------------------------------------

    async def get_comparacao_votos_relacional_repo(
        self, id_dep1: int, id_dep2: int, tema: str | None = None
    ) -> list[dict]:
        """
        Busca comparativa de todas as votações comuns entre dois deputados via PostgreSQL relacional,
        com suporte a agregação e filtro por tema legislativo.
        """
        v2 = aliased(Voto)
        stmt = (
            select(
                Voto.idVotacao,
                Votacao.descricao,
                Votacao.data,
                Voto.voto.label("voto1"),
                v2.voto.label("voto2"),
                Proposicao.siglaTipo,
                Proposicao.numero,
                Proposicao.ano,
                Proposicao.ementa,
                func.string_agg(Tema.tema, ", ").label("temas_str"),
            )
            .join(v2, (Voto.idVotacao == v2.idVotacao) & (v2.idDeputado == id_dep2))
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .outerjoin(Proposicao, Proposicao.id == Votacao.idProposicao)
            .outerjoin(
                proposicoesTemas, proposicoesTemas.c.idProposicao == Proposicao.id
            )
            .outerjoin(Tema, Tema.id == proposicoesTemas.c.idTema)
            .where(Voto.idDeputado == id_dep1)
        )

        if tema:
            stmt = stmt.where(
                Proposicao.temas.any(Tema.tema.ilike(f"%{tema.strip()}%"))
            )

        stmt = stmt.group_by(
            Voto.idVotacao,
            Votacao.descricao,
            Votacao.data,
            Voto.voto,
            v2.voto,
            Proposicao.siglaTipo,
            Proposicao.numero,
            Proposicao.ano,
            Proposicao.ementa,
        ).order_by(desc(Votacao.data).nullslast(), desc(Voto.idVotacao))

        try:
            result = await self.db.execute(stmt)
            rows = result.all()
        except SQLAlchemyError:
            logger.exception(
                "Erro ao comparar votações relacionais entre deputados %s e %s (tema=%s)",
                id_dep1,
                id_dep2,
                tema,
            )
            raise

        results = []
        for r in rows:
            voto1 = (r.voto1 or "").strip()
            voto2 = (r.voto2 or "").strip()
            prop_str = f"{r.siglaTipo} {r.numero}/{r.ano}" if r.siglaTipo else None
            temas_lista = (
                [t.strip() for t in r.temas_str.split(",")] if r.temas_str else []
            )
            tema_principal = temas_lista[0] if temas_lista else None
            results.append(
                {
                    "id_votacao": r.idVotacao,
                    "data": r.data,
                    "descricao": r.descricao,
                    "voto_politico1": voto1,
                    "voto_politico2": voto2,
                    "alinhados": (voto1.lower() == voto2.lower() and voto1 != ""),
                    "proposicao": prop_str,
                    "ementa": r.ementa,
                    "tema": tema_principal,
                    "temas": temas_lista,
                }
            )
        return results

    async def get_resumo_temas_comparacao_repo(
        self, id_dep1: int, id_dep2: int
    ) -> list[dict]:
        """
        Retorna o agrupamento temático de todas as votações em comum entre dois deputados,
        incluindo contagem de votações, votos alinhados, divergentes e taxa percentual de alinhamento.
        """
        v2 = aliased(Voto)
        stmt = (
            select(
                Tema.tema,
                func.count(func.distinct(Voto.idVotacao)).label("total"),
                func.count(
                    func.distinct(
                        case(
                            (
                                func.lower(Voto.voto) == func.lower(v2.voto),
                                Voto.idVotacao,
                            ),
                            else_=None,
                        )
                    )
                ).label("alinhados"),
            )
            .join(v2, (Voto.idVotacao == v2.idVotacao) & (v2.idDeputado == id_dep2))
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .join(Proposicao, Proposicao.id == Votacao.idProposicao)
            .join(proposicoesTemas, proposicoesTemas.c.idProposicao == Proposicao.id)
            .join(Tema, Tema.id == proposicoesTemas.c.idTema)
            .where(Voto.idDeputado == id_dep1)
            .group_by(Tema.tema)
            .order_by(desc("total"))
        )
        try:
            res = await self.db.execute(stmt)
            rows = res.all()
            temas = []
            for r in rows:
                tot = r.total
                aln = r.alinhados
                div = tot - aln
                taxa = round((aln / tot) * 100.0, 1) if tot > 0 else 0.0
                temas.append(
                    {
                        "tema": r.tema,
                        "total_votacoes": tot,
                        "votos_alinhados": aln,
                        "votos_divergentes": div,
                        "taxa_alinhamento": taxa,
                    }
                )
            return temas
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar resumo de temas entre deputados %s e %s",
                id_dep1,
                id_dep2,
            )
            return []
