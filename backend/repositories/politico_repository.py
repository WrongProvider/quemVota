"""
Repositório de Deputados — Camada de acesso a dados.

Segurança (OWASP):
  - A01 / SQL Injection: todas as queries usam SQLAlchemy Core com bind parameters;
    nenhuma concatenação ou interpolação de strings em SQL.
  - A03 / Sensitive Data Exposure: nenhum dado sensível é logado ou exposto nas exceções.
  - A04 / Insecure Design: limites máximos aplicados aqui (não só no serviço) como
    defesa em profundidade.
"""

from datetime import date
import logging

from shared.models import (
    Deputado,
    Despesa,
    Proposicao,
    ProposicaoAutor,
    Tema,
    VerbaGabinete,
    Votacao,
    VotacaoOrientacao,
    Voto,
    proposicoesTemas,
)
from sqlalchemy import String, case, cast, desc, func, or_, select
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

POPULAR_TOPIC_SYNONYMS: dict[str, list[str]] = {
    "6x1": ["jornada de trabalho", "36 horas", "escala 6x1", "PEC 221", "221/2019"],
    "escala 6x1": ["jornada de trabalho", "36 horas", "escala 6x1", "PEC 221", "221/2019"],
    "escala 6 por 1": ["jornada de trabalho", "36 horas", "PEC 221"],
    "fim da escala 6x1": ["jornada de trabalho", "36 horas", "PEC 221"],
    "reforma tributaria": ["tributária", "tributario", "PLP 68", "PEC 45/2019", "IBS", "CBS"],
    "tributaria": ["tributária", "tributario", "impostos"],
    "marco temporal": ["terras indígenas", "indígena", "demarcação", "PL 2903", "14701"],
    "aborto": ["interrupção de gravidez", "gestação", "PL 1904"],
    "pl do aborto": ["interrupção de gravidez", "PL 1904"],
    "bets": ["apostas", "quota fixa", "jogos de azar", "cassino", "PL 3626"],
    "apostas": ["apostas esportivas", "quota fixa", "bets", "PL 3626"],
    "armas": ["porte de arma", "posse de arma", "CAC", "desarmamento", "arma de fogo"],
    "porte de armas": ["porte de arma", "posse de arma", "arma de fogo"],
    "drogas": ["entorpecentes", "maconha", "porte de drogas", "PEC 45/2023"],
    "maconha": ["entorpecentes", "drogas", "porte de drogas"],
    "desoneracao": ["desoneração", "folha de pagamento", "PL 334/2023"],
    "desoneracao da folha": ["desoneração", "folha de pagamento", "PL 334/2023"],
    "combustiveis": ["gasolina", "diesel", "etanol", "combustíveis", "PLP 18"],
}


def expand_popular_query(q: str | None) -> list[str]:
    if not q or not q.strip():
        return []
    cleaned = q.strip().lower()
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", cleaned)
    unaccented = "".join([c for c in nfkd if not unicodedata.combining(c)])

    terms: set[str] = {q.strip()}
    for key, syns in POPULAR_TOPIC_SYNONYMS.items():
        if key in unaccented or unaccented in key:
            for s in syns:
                terms.add(s)
    return list(terms)


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
        voto: str | None = None,
        sigla_tipo: str | None = None,
        tema: str | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> tuple[list[VotacaoResumida], int, int, int, int]:
        safe_limit = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        base_filter = [Voto.idDeputado == politico_id]
        if ano is not None:
            base_filter.append(func.extract("year", Votacao.data) == ano)
        if voto and voto.strip():
            base_filter.append(Voto.voto.ilike(voto.strip()))
        if sigla_tipo and sigla_tipo.strip():
            base_filter.append(Proposicao.siglaTipo.ilike(sigla_tipo.strip()))
        if tema and tema.strip():
            base_filter.append(Proposicao.temas.any(Tema.tema.ilike(f"%{tema.strip()}%")))
        if data_inicio is not None:
            base_filter.append(Votacao.data >= data_inicio)
        if data_fim is not None:
            base_filter.append(Votacao.data <= data_fim)
        if q and q.strip():
            termos_expandidos = expand_popular_query(q)
            or_conditions = []
            for t_str in termos_expandidos:
                termo = f"%{t_str.strip()}%"
                or_conditions.extend(
                    [
                        Proposicao.ementa.ilike(termo),
                        Proposicao.siglaTipo.ilike(termo),
                        cast(Proposicao.numero, String).ilike(termo),
                        Votacao.descricao.ilike(termo),
                        Votacao.tipoVotacao.ilike(termo),
                    ]
                )
            base_filter.append(or_(*or_conditions))

        stmt_counts = (
            select(
                func.count().label("total"),
                func.count(
                    case((Voto.voto.ilike("Sim"), 1), else_=None)
                ).label("total_sim"),
                func.count(
                    case((Voto.voto.ilike("Não"), 1), else_=None)
                ).label("total_nao"),
                func.count(
                    case(
                        (~Voto.voto.ilike("Sim") & ~Voto.voto.ilike("Não"), 1),
                        else_=None,
                    )
                ).label("total_outros"),
            )
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .outerjoin(Proposicao, Proposicao.id == Votacao.idProposicao)
            .where(*base_filter)
        )

        stmt_data = (
            select(
                Votacao.id.label("id_votacao"),
                Votacao.data,
                Votacao.idProposicao.label("proposicao_id"),
                Proposicao.idCamara.label("proposicao_id_camara"),
                Proposicao.siglaTipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
                Proposicao.descricaoTipo.label("proposicao_descricao_tipo"),
                Proposicao.urlInteiroTeor.label("proposicao_url_inteiro_teor"),
                Voto.voto.label("voto"),
                Votacao.aprovacao,
                Votacao.tipoVotacao.label("tipo_votacao"),
                Votacao.siglaOrgao.label("sigla_orgao"),
            )
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .outerjoin(Proposicao, Proposicao.id == Votacao.idProposicao)
            .where(*base_filter)
            .order_by(desc(Votacao.data), desc(Votacao.id))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            res_counts = await self.db.execute(stmt_counts)
            res_data = await self.db.execute(stmt_data)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar votações (atividade) do deputado id=%s", politico_id
            )
            raise

        row_counts = res_counts.mappings().one()
        total = row_counts["total"] or 0
        total_sim = row_counts["total_sim"] or 0
        total_nao = row_counts["total_nao"] or 0
        total_outros = row_counts["total_outros"] or 0

        rows = res_data.mappings().all()

        prop_ids = [r["proposicao_id"] for r in rows if r["proposicao_id"]]
        temas_by_prop_id: dict[int, list[str]] = {}
        if prop_ids:
            stmt_temas = (
                select(Proposicao)
                .where(Proposicao.id.in_(prop_ids))
                .options(selectinload(Proposicao.temas))
            )
            try:
                res_temas = await self.db.execute(stmt_temas)
                for p in res_temas.scalars().all():
                    temas_by_prop_id[p.id] = [t.tema for t in p.temas if t.tema]
            except SQLAlchemyError:
                logger.warning(
                    "Falha ao carregar temas das proposições nas votações do deputado id=%s",
                    politico_id,
                )

        votacoes = [
            VotacaoResumida(
                id_votacao=row["id_votacao"],
                data=row["data"],
                proposicao_id=row["proposicao_id"],
                proposicao_id_camara=row["proposicao_id_camara"],
                proposicao_sigla=row["proposicao_sigla"],
                proposicao_numero=row["proposicao_numero"],
                proposicao_ano=row["proposicao_ano"],
                proposicao_ementa=row["proposicao_ementa"],
                proposicao_descricao_tipo=row["proposicao_descricao_tipo"],
                proposicao_url_inteiro_teor=row["proposicao_url_inteiro_teor"],
                voto=row["voto"],
                aprovacao=row["aprovacao"],
                tipo_votacao=row["tipo_votacao"],
                sigla_orgao=row["sigla_orgao"],
                temas=temas_by_prop_id.get(row["proposicao_id"], []),
            )
            for row in rows
        ]

        return votacoes, total, total_sim, total_nao, total_outros

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
        proponente: bool | None = None,
        sigla_tipo: str | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> tuple[list[ProposicaoResumida], int, int, int]:
        safe_limit = min(abs(limit), 100)
        safe_offset = max(offset, 0)

        base_filter_common = [ProposicaoAutor.idDeputadoAutor == politico_id]
        if ano is not None:
            base_filter_common.append(Proposicao.ano == ano)
        if sigla_tipo and sigla_tipo.strip():
            base_filter_common.append(Proposicao.siglaTipo.ilike(sigla_tipo.strip()))
        if data_inicio is not None:
            base_filter_common.append(func.date(Proposicao.dataApresentacao) >= data_inicio)
        if data_fim is not None:
            base_filter_common.append(func.date(Proposicao.dataApresentacao) <= data_fim)
        if q and q.strip():
            termos_expandidos = expand_popular_query(q)
            or_conditions = []
            for t_str in termos_expandidos:
                termo = f"%{t_str.strip()}%"
                or_conditions.extend(
                    [
                        Proposicao.ementa.ilike(termo),
                        Proposicao.siglaTipo.ilike(termo),
                        cast(Proposicao.numero, String).ilike(termo),
                        Proposicao.keywords.ilike(termo),
                    ]
                )
            base_filter_common.append(or_(*or_conditions))

        stmt_counts = (
            select(
                func.count(func.distinct(ProposicaoAutor.idProposicao)).label("total"),
                func.count(
                    func.distinct(
                        case(
                            (ProposicaoAutor.proponente.is_(True), ProposicaoAutor.idProposicao),
                            else_=None,
                        )
                    )
                ).label("total_proponente"),
                func.count(
                    func.distinct(
                        case(
                            (ProposicaoAutor.proponente.is_(False), ProposicaoAutor.idProposicao),
                            else_=None,
                        )
                    )
                ).label("total_coautor"),
            )
            .select_from(ProposicaoAutor)
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(*base_filter_common)
        )

        base_filter_data = list(base_filter_common)
        if proponente is not None:
            base_filter_data.append(ProposicaoAutor.proponente.is_(proponente))

        stmt_ids = (
            select(
                ProposicaoAutor.idProposicao,
                ProposicaoAutor.proponente,
                ProposicaoAutor.tipoAutor.label("tipo_autoria"),
            )
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(*base_filter_data)
            .order_by(desc(Proposicao.dataApresentacao), desc(Proposicao.id))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            res_counts = await self.db.execute(stmt_counts)
            res_ids = await self.db.execute(stmt_ids)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar proposições (atividade) do deputado id=%s", politico_id
            )
            raise

        row_counts = res_counts.mappings().one()
        total_proponente = row_counts["total_proponente"] or 0
        total_coautor = row_counts["total_coautor"] or 0
        if proponente is True:
            total = total_proponente
        elif proponente is False:
            total = total_coautor
        else:
            total = row_counts["total"] or 0

        autoria_rows = res_ids.mappings().all()
        if not autoria_rows:
            return [], total, total_proponente, total_coautor

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
        )

        try:
            res_props = await self.db.execute(stmt_props)
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar detalhes de proposições do deputado id=%s", politico_id
            )
            raise

        proposicoes_orm = res_props.scalars().all()
        proposicoes_by_id = {p.id: p for p in proposicoes_orm}

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
                temas=[t.tema for t in p.temas] if p.temas else [],
                ultimo_status_situacao=p.ultimoStatus_descricaoSituacao,
                ultimo_status_orgao=p.ultimoStatus_siglaOrgao,
            )
            for pid in ids_paginados
            if (p := proposicoes_by_id.get(pid)) is not None
        ]

        return proposicoes, total, total_proponente, total_coautor

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

    # ------------------------------------------------------------------
    # Rede de Coautoria (Relacional)
    # ------------------------------------------------------------------

    async def get_rede_coautoria_relacional_repo(
        self, politico_id: int, limit: int = 20
    ) -> list[dict]:
        """
        Retorna a lista dos deputados que mais coautoram proposições com o parlamentar informado,
        com métricas de autoria principal, coautoria e amostra de matérias.
        """
        pa1 = aliased(ProposicaoAutor)
        pa2 = aliased(ProposicaoAutor)
        d2 = aliased(Deputado)
        d1 = aliased(Deputado)

        stmt = (
            select(
                d2.id.label("parceiro_id"),
                d2.idCamara.label("parceiro_id_camara"),
                d2.nome.label("parceiro_nome"),
                d2.slug.label("parceiro_slug"),
                func.coalesce(d2.siglaPartido, pa2.siglaPartidoAutor).label(
                    "parceiro_partido"
                ),
                func.coalesce(d2.siglaUF, pa2.siglaUFAutor).label("parceiro_uf"),
                d2.urlFoto.label("parceiro_url_foto"),
                func.coalesce(d1.siglaPartido, pa1.siglaPartidoAutor).label(
                    "base_partido"
                ),
                func.count(func.distinct(pa1.idProposicao)).label("total_juntos"),
                func.count(
                    func.distinct(
                        case((pa1.proponente.is_(True), pa1.idProposicao), else_=None)
                    )
                ).label("como_principal"),
                func.count(
                    func.distinct(
                        case(
                            (
                                pa2.proponente.is_(True) & pa1.proponente.is_(False),
                                pa1.idProposicao,
                            ),
                            else_=None,
                        )
                    )
                ).label("como_coautor"),
            )
            .join(
                pa2,
                (pa1.idProposicao == pa2.idProposicao)
                & (pa2.idDeputadoAutor != politico_id),
            )
            .join(d2, d2.id == pa2.idDeputadoAutor)
            .join(d1, d1.id == politico_id)
            .where(pa1.idDeputadoAutor == politico_id)
            .group_by(
                d2.id,
                d2.idCamara,
                d2.nome,
                d2.slug,
                d2.siglaPartido,
                pa2.siglaPartidoAutor,
                d2.siglaUF,
                pa2.siglaUFAutor,
                d2.urlFoto,
                d1.siglaPartido,
                pa1.siglaPartidoAutor,
            )
            .order_by(desc("total_juntos"))
            .limit(limit)
        )

        try:
            res = await self.db.execute(stmt)
            rows = res.all()
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar rede de coautoria do deputado id=%s", politico_id
            )
            return []

        if not rows:
            return []

        resultados = []
        for r in rows:
            mesmo_partido = bool(
                r.base_partido
                and r.parceiro_partido
                and r.base_partido.upper() == r.parceiro_partido.upper()
            )

            stmt_props = (
                select(Proposicao)
                .join(
                    pa1,
                    (pa1.idProposicao == Proposicao.id)
                    & (pa1.idDeputadoAutor == politico_id),
                )
                .join(
                    pa2,
                    (pa2.idProposicao == Proposicao.id)
                    & (pa2.idDeputadoAutor == r.parceiro_id),
                )
                .options(selectinload(Proposicao.temas))
                .order_by(desc(Proposicao.dataApresentacao))
                .limit(5)
            )
            res_props = await self.db.execute(stmt_props)
            props_orm = res_props.scalars().all()

            temas_cont: dict[str, int] = {}
            amostra = []
            for p in props_orm:
                for t in p.temas:
                    temas_cont[t.tema] = temas_cont.get(t.tema, 0) + 1
                amostra.append(
                    {
                        "id": p.id,
                        "sigla_tipo": p.siglaTipo,
                        "numero": p.numero,
                        "ano": p.ano,
                        "ementa": p.ementa,
                        "proponente_principal_id": (
                            politico_id if r.como_principal > 0 else r.parceiro_id
                        ),
                    }
                )

            temas_ordenados = sorted(
                temas_cont.keys(), key=lambda t: temas_cont[t], reverse=True
            )

            parceiro_url_foto = r.parceiro_url_foto or (
                f"https://www.camara.leg.br/internet/deputado/bandep/{r.parceiro_id_camara}.jpg"
                if r.parceiro_id_camara
                else None
            )

            resultados.append(
                {
                    "politico": {
                        "id": r.parceiro_id,
                        "nome": r.parceiro_nome,
                        "slug": r.parceiro_slug,
                        "sigla_partido": r.parceiro_partido,
                        "sigla_uf": r.parceiro_uf,
                        "url_foto": parceiro_url_foto,
                    },
                    "total_proposicoes_juntos": r.total_juntos,
                    "proposicoes_como_autor_principal": r.como_principal,
                    "proposicoes_como_coautor": r.como_coautor,
                    "mesmo_partido": mesmo_partido,
                    "temas_comuns": temas_ordenados[:5],
                    "amostra_proposicoes": amostra,
                }
            )

        return resultados

    # ------------------------------------------------------------------
    # Afinidades e Oposições de Voto (Relacional)
    # ------------------------------------------------------------------

    async def get_afinidades_voto_relacional_repo(
        self,
        politico_id: int,
        min_comuns: int = 10,
        apenas_outros_partidos: bool = False,
        limit: int = 10,
    ) -> dict:
        """
        Calcula as afinidades e divergências de votações com todos os demais parlamentares,
        além do alinhamento agregado por bancada partidária.
        """
        v1 = aliased(Voto)
        v2 = aliased(Voto)
        d2 = aliased(Deputado)
        d1 = aliased(Deputado)

        stmt = (
            select(
                d2.id.label("outro_id"),
                d2.idCamara.label("outro_id_camara"),
                d2.nome.label("outro_nome"),
                d2.slug.label("outro_slug"),
                func.coalesce(d2.siglaPartido, v2.siglaPartido).label("outro_partido"),
                func.coalesce(d2.siglaUF, v2.siglaUF).label("outro_uf"),
                d2.urlFoto.label("outro_url_foto"),
                func.coalesce(d1.siglaPartido, v1.siglaPartido).label("base_partido"),
                func.count(func.distinct(v1.idVotacao)).label("total_comuns"),
                func.count(
                    func.distinct(
                        case(
                            (
                                (func.lower(v1.voto) == func.lower(v2.voto))
                                & (v1.voto != ""),
                                v1.idVotacao,
                            ),
                            else_=None,
                        )
                    )
                ).label("alinhados"),
            )
            .join(v2, (v1.idVotacao == v2.idVotacao) & (v2.idDeputado != politico_id))
            .join(d2, d2.id == v2.idDeputado)
            .join(d1, d1.id == politico_id)
            .where(v1.idDeputado == politico_id)
            .group_by(
                d2.id,
                d2.idCamara,
                d2.nome,
                d2.slug,
                d2.siglaPartido,
                v2.siglaPartido,
                d2.siglaUF,
                v2.siglaUF,
                d2.urlFoto,
                d1.siglaPartido,
                v1.siglaPartido,
            )
            .having(func.count(func.distinct(v1.idVotacao)) >= min_comuns)
        )

        try:
            res = await self.db.execute(stmt)
            rows = res.all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar afinidades do deputado id=%s", politico_id)
            return {
                "min_votacoes_comuns": min_comuns,
                "mais_alinhados": [],
                "mais_divergentes": [],
                "alinhamento_por_bancada": [],
            }

        itens = []
        bancadas: dict[str, dict[str, int]] = {}

        for r in rows:
            mesmo_partido = bool(
                r.base_partido
                and r.outro_partido
                and r.base_partido.upper() == r.outro_partido.upper()
            )
            if apenas_outros_partidos and mesmo_partido:
                continue

            tot = r.total_comuns
            aln = r.alinhados
            div = tot - aln
            taxa = round((aln / tot) * 100.0, 1) if tot > 0 else 0.0

            outro_url_foto = r.outro_url_foto or (
                f"https://www.camara.leg.br/internet/deputado/bandep/{r.outro_id_camara}.jpg"
                if r.outro_id_camara
                else None
            )

            itens.append(
                {
                    "politico": {
                        "id": r.outro_id,
                        "nome": r.outro_nome,
                        "slug": r.outro_slug,
                        "sigla_partido": r.outro_partido,
                        "sigla_uf": r.outro_uf,
                        "url_foto": outro_url_foto,
                    },
                    "total_votacoes_comuns": tot,
                    "votos_alinhados": aln,
                    "votos_divergentes": div,
                    "taxa_alinhamento": taxa,
                    "mesmo_partido": mesmo_partido,
                }
            )

            if r.outro_partido:
                sigla = r.outro_partido.upper()
                if sigla not in bancadas:
                    bancadas[sigla] = {"total": 0, "alinhados": 0}
                bancadas[sigla]["total"] += tot
                bancadas[sigla]["alinhados"] += aln

        mais_alinhados = sorted(
            itens,
            key=lambda x: (x["taxa_alinhamento"], x["total_votacoes_comuns"]),
            reverse=True,
        )[:limit]
        mais_divergentes = sorted(
            itens, key=lambda x: (x["taxa_alinhamento"], -x["total_votacoes_comuns"])
        )[:limit]

        bancadas_resumo = []
        for sigla, bdata in bancadas.items():
            btot = bdata["total"]
            baln = bdata["alinhados"]
            if btot >= 5:
                btaxa = round((baln / btot) * 100.0, 1)
                bancadas_resumo.append(
                    {
                        "sigla_partido": sigla,
                        "total_votacoes": btot,
                        "votos_alinhados": baln,
                        "taxa_alinhamento": btaxa,
                    }
                )
        bancadas_resumo.sort(key=lambda x: x["taxa_alinhamento"], reverse=True)

        return {
            "min_votacoes_comuns": min_comuns,
            "mais_alinhados": mais_alinhados,
            "mais_divergentes": mais_divergentes,
            "alinhamento_por_bancada": bancadas_resumo,
        }

    # ------------------------------------------------------------------
    # Fidelidade Partidária (Relacional)
    # ------------------------------------------------------------------

    # Mapeamento oficial de partidos para siglas de bancadas e federações na Câmara
    MAPA_BANCADAS_PARTIDO: dict[str, list[str]] = {
        "PSOL": ["PSOL", "Fdr PSOL-REDE"],
        "REDE": ["REDE", "Fdr PSOL-REDE"],
        "PT": ["PT", "Fdr PT-PCdoB-PV"],
        "PCDOB": ["PCDOB", "Fdr PT-PCdoB-PV"],
        "PV": ["PV", "Fdr PT-PCdoB-PV"],
        "PSDB": ["PSDB", "Fdr PSDB-CIDADANIA", "Fdr PSDB-CIDADAN"],
        "CIDADANIA": ["CIDADANIA", "Fdr PSDB-CIDADANIA", "Fdr PSDB-CIDADAN", "PPS"],
        "SOLIDARIEDADE": ["SOLIDARIEDADE", "SOLIDARIED", "SD", "SDD"],
        "PODE": ["PODE", "PODEMOS", "PTN"],
        "PODEMOS": ["PODE", "PODEMOS", "PTN"],
        "REPUBLICANOS": ["REPUBLICANOS", "REPUBLICAN", "PRB"],
        "UNIÃO": ["UNIÃO", "UNIAO"],
        "UNIAO": ["UNIÃO", "UNIAO"],
        "PRD": ["PRD", "PATRIOTA", "PATRI", "PTB"],
        "PATRIOTA": ["PATRIOTA", "PATRI", "PRD"],
        "MDB": ["MDB", "PMDB"],
        "PL": ["PL", "PR"],
        "NOVO": ["NOVO"],
        "AVANTE": ["AVANTE"],
        "PDT": ["PDT"],
        "PSB": ["PSB"],
        "PP": ["PP"],
        "PSD": ["PSD"],
    }

    @classmethod
    def _obter_bancadas_equivalentes(cls, partido_sigla: str) -> list[str]:
        norm = (partido_sigla or "").strip().upper()
        bancadas = cls.MAPA_BANCADAS_PARTIDO.get(norm, [norm])
        s = {b.upper() for b in bancadas}
        if norm:
            s.add(norm)
        return list(s)

    async def get_fidelidade_partidaria_relacional_repo(
        self, politico_id: int, partido_sigla: str, limit_divergencias: int = 50
    ) -> dict:
        """
        Compara cada voto do deputado com a orientação oficial da bancada do seu partido
        ou da federação partidária a que pertence na Câmara dos Deputados.
        """
        bancadas_upper = self._obter_bancadas_equivalentes(partido_sigla)

        # Subquery deduplicada: agrupa por votação para evitar duplicações de órgãos/registros
        sub_orient = (
            select(
                VotacaoOrientacao.idVotacao,
                func.max(VotacaoOrientacao.orientacao).label("orientacao_partido"),
            )
            .where(
                func.upper(VotacaoOrientacao.siglaBancada).in_(bancadas_upper),
                VotacaoOrientacao.orientacao.isnot(None),
                ~func.lower(VotacaoOrientacao.orientacao).in_(
                    ["libera", "liberado", ""]
                ),
            )
            .group_by(VotacaoOrientacao.idVotacao)
            .subquery("vo_dedup")
        )

        stmt = (
            select(
                Voto.idVotacao,
                Votacao.data,
                Votacao.descricao,
                Voto.voto.label("voto_politico"),
                sub_orient.c.orientacao_partido,
                Proposicao.siglaTipo,
                Proposicao.numero,
                Proposicao.ano,
                Proposicao.ementa,
            )
            .join(
                sub_orient,
                sub_orient.c.idVotacao == Voto.idVotacao,
            )
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .outerjoin(Proposicao, Proposicao.id == Votacao.idProposicao)
            .where(
                Voto.idDeputado == politico_id,
            )
            .order_by(desc(Votacao.data).nullslast(), desc(Voto.idVotacao))
        )

        try:
            res = await self.db.execute(stmt)
            rows = res.all()
        except SQLAlchemyError:
            logger.exception(
                "Erro ao buscar fidelidade partidária do deputado id=%s", politico_id
            )
            return {
                "total_votacoes_orientadas": 0,
                "votos_com_bancada": 0,
                "votos_contra_bancada": 0,
                "taxa_fidelidade": 0.0,
                "divergencias": [],
            }

        total = len(rows)
        alinhados = 0
        divergencias = []

        for r in rows:
            v_dep = (r.voto_politico or "").strip()
            v_orient = (r.orientacao_partido or "").strip()
            if v_dep.lower() == v_orient.lower():
                alinhados += 1
            else:
                prop_str = f"{r.siglaTipo} {r.numero}/{r.ano}" if r.siglaTipo else None
                divergencias.append(
                    {
                        "id_votacao": r.idVotacao,
                        "data": r.data,
                        "proposicao": prop_str,
                        "ementa": r.ementa or r.descricao,
                        "voto_politico": v_dep,
                        "orientacao_partido": v_orient,
                    }
                )

        contra = total - alinhados
        taxa = round((alinhados / total) * 100.0, 1) if total > 0 else 0.0

        return {
            "total_votacoes_orientadas": total,
            "votos_com_bancada": alinhados,
            "votos_contra_bancada": contra,
            "taxa_fidelidade": taxa,
            "divergencias": divergencias[:limit_divergencias],
        }

    # ------------------------------------------------------------------
    # Grafo da Proposição (Relacional)
    # ------------------------------------------------------------------

    async def get_grafo_proposicao_relacional_repo(
        self, proposicao_id: int
    ) -> dict | None:
        """
        Retorna o ecossistema completo de uma proposição via joins relacionais:
        autor principal, coautores, temas e votações.
        """
        stmt = (
            select(Proposicao)
            .where(Proposicao.id == proposicao_id)
            .options(
                selectinload(Proposicao.autores).selectinload(ProposicaoAutor.deputado),
                selectinload(Proposicao.temas),
                selectinload(Proposicao.votacoes).selectinload(Votacao.orientacoes),
            )
        )
        try:
            res = await self.db.execute(stmt)
            p = res.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar grafo da proposicao id=%s", proposicao_id)
            return None

        if not p:
            return None

        autor_proponente = None
        coautores = []
        for a in p.autores:
            dep = a.deputado
            url_foto = (dep.urlFoto if dep else None) or (
                f"https://www.camara.leg.br/internet/deputado/bandep/{dep.idCamara}.jpg"
                if dep and dep.idCamara
                else None
            )
            p_dict = {
                "id": a.idDeputadoAutor,
                "nome": a.nomeAutor,
                "slug": dep.slug if dep else None,
                "sigla_partido": (dep.siglaPartido if dep else None)
                or a.siglaPartidoAutor,
                "sigla_uf": (dep.siglaUF if dep else None) or a.siglaUFAutor,
                "url_foto": url_foto,
            }
            if a.proponente and not autor_proponente:
                autor_proponente = p_dict
            else:
                coautores.append(p_dict)

        temas = [t.tema for t in p.temas]

        votacoes = []
        for vt in p.votacoes:
            orientacoes = [
                {
                    "sigla_partido": o.siglaBancada or "",
                    "orientacao_voto": o.orientacao or "",
                }
                for o in vt.orientacoes
                if o.siglaBancada and o.orientacao
            ]
            votacoes.append(
                {
                    "id_votacao": vt.id,
                    "data": vt.data,
                    "descricao": vt.descricao,
                    "aprovacao": vt.aprovacao,
                    "votos_sim": vt.votosSim,
                    "votos_nao": vt.votosNao,
                    "votos_outros": vt.votosOutros,
                    "orientacoes": orientacoes,
                }
            )

        prop_str = (
            f"{p.siglaTipo} {p.numero}/{p.ano}"
            if p.siglaTipo
            else f"Proposição #{p.id}"
        )
        return {
            "id_proposicao": p.id,
            "proposicao": prop_str,
            "ementa": p.ementa,
            "autor_proponente": autor_proponente,
            "coautores": coautores,
            "temas": temas,
            "votacoes": votacoes,
        }
