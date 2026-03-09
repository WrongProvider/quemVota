"""
Repositório de Rankings — Camada de acesso a dados.

Segurança (OWASP):
  - A01 / SQL Injection: todas as queries usam SQLAlchemy Core com bind parameters.
  - A03 / Sensitive Data Exposure: nenhum dado sensível é logado ou exposto.
  - A04 / Insecure Design: limites máximos aplicados como defesa em profundidade.
"""

import logging
from collections import Counter, defaultdict

from sqlalchemy import Float, Integer, Numeric, String, case, cast, desc, extract, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Despesa, Discurso, Deputado, PresencaDeputado, Proposicao, ProposicaoAutor, Voto, Votacao, Evento, VerbaGabinete
from backend.schemas import KeywordInfo, RankingDespesaPolitico, RankingDiscursoPolitico, RankingEmpresaLucro

logger = logging.getLogger(__name__)

_MAX_LIMIT_RANKING   = 100
_MAX_LIMIT_DISCURSOS = 500

_BLACKLIST_KEYWORDS: frozenset = frozenset({
    "ORIENTACAO DE BANCADA", "REQUERIMENTO DE URGENCIA", "ENCAMINHAMENTO DE VOTACAO",
    "DISCUSSAO", "QUESTAO DE ORDEM", "VOTO FAVORAVEL", "VOTO CONTRARIO",
    "FAVORAVEL", "CONTRARIO", "REQUERIMENTO DE DESTAQUE DE VOTACAO EM SEPARADO",
    "SUBSTITUTIVO", "SEGUNDO TURNO", "PAUTA (PROCESSO LEGISLATIVO)", "DISPOSITIVO LEGAL",
    "EMENDA DE PLENARIO", "PARECER (PROPOSICAO LEGISLATIVA)", "PARECER DO RELATOR",
    "RELATOR", "PROJETO DE LEI DE CONVERSAO", "REQUERIMENTO", "APROVACAO", "ALTERACAO",
    "PROPOSTA DE EMENDA A CONSTITUICAO", "PROJETO DE LEI COMPLEMENTAR",
    "PROJETO DE LEI ORDINARIA", "MEDIDA PROVISORIA", "PROJETO DE LEI DO CONGRESSO NACIONAL",
    "MPV 1095/2021", "DEPUTADO FEDERAL", "PRESIDENTE DA REPUBLICA",
    "EX-PRESIDENTE DA REPUBLICA", "GOVERNO FEDERAL", "GOVERNO", "GOVERNO ESTADUAL",
    "GOVERNADOR", "CONGRESSO NACIONAL", "SENADO FEDERAL", "SUPREMO TRIBUNAL FEDERAL (STF)",
    "PODER JUDICIARIO", "BASE DE APOIO POLITICO", "MINORIA PARLAMENTAR",
    "MAIORIA PARLAMENTAR", "OPOSICAO POLITICA", "VEREADOR",
    "PARTIDO LIBERAL (PL)", "PARTIDO DOS TRABALHADORES (PT)", "PARTIDO NOVO (NOVO)",
    "FEDERACAO PSOL REDE", "FEDERACAO BRASIL DA ESPERANCA (FE BRASIL)", "BLOCO PARLAMENTAR",
    "CRITICA", "DEFESA", "HOMENAGEM", "MANIFESTACAO", "ATUACAO",
    "ATUACAO PARLAMENTAR", "ANIVERSARIO DE EMANCIPACAO POLITICA", "CRIACAO",
})

_FORNECEDOR_DATA_FIX: dict = {
    "TAM":                     {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
    "LATAM AIRLINES BRASIL":   {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
    "LATAM LINHAS AEREAS S.A": {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
    "CIA AEREA - TAM":         {"cnpj": "02012862000160", "nome": "LATAM AIRLINES"},
    "GOL":                     {"cnpj": "07575651000159", "nome": "GOL"},
    "GOL LINHAS AEREAS":       {"cnpj": "07575651000159", "nome": "GOL"},
    "AZUL":                    {"cnpj": "09296295000160", "nome": "AZUL"},
    "AZUL LINHAS AEREAS":      {"cnpj": "09296295000160", "nome": "AZUL"},
}

# ---------------------------------------------------------------------------
# Helpers internos — subqueries reutilizáveis
# ---------------------------------------------------------------------------
def _sub_presenca(deputado_id: int, ano: int | None = None):
    """Subquery de assiduidade via participação em votações, filtrável por ano.

    Fórmula: (votações em que o deputado registrou voto) / (total de votações no período) * 100

    O denominador conta votações únicas na tabela Votacao para o período —
    representa o universo total de votações disponíveis, independente de
    qualquer deputado.
    O numerador conta as linhas em Voto para o deputado no mesmo período,
    fazendo join com Votacao para aplicar o filtro de ano de forma consistente.
    """
    # ── Denominador: IDs únicos de Votacao presentes em Voto ──────────────
    # Conta apenas votações que geraram registros em Voto — ou seja, votações
    # que de fato exigiram voto nominal dos deputados. Faz join com Votacao
    # apenas para poder aplicar o filtro de ano quando necessário.
    sub_total_votacoes = (
        select(func.count(func.distinct(Voto.idVotacao)))
        .join(Votacao, Votacao.id == Voto.idVotacao)
    )
    if ano is not None:
        sub_total_votacoes = sub_total_votacoes.where(
            extract("year", Votacao.data) == ano
        )
    sub_total_votacoes = sub_total_votacoes.scalar_subquery()

    # ── Numerador: votações em que o deputado registrou voto ───────────────
    q = (
        select(
            Voto.idDeputado,
            func.coalesce(
                func.round(
                    cast(
                        func.count(Voto.id).cast(Float)
                        / func.nullif(sub_total_votacoes, 0)
                        * 100,
                        Numeric,
                    ),
                    2,
                ),
                0,
            ).label("nota_assiduidade"),
        )
        .join(Votacao, Votacao.id == Voto.idVotacao)
        .where(Voto.idDeputado == deputado_id)
    )

    if ano is not None:
        q = q.where(extract("year", Votacao.data) == ano)

    return q.group_by(Voto.idDeputado).subquery()
def _sub_producao(deputado_id: int, ano: int | None = None):
    """Subquery de produção legislativa ponderada, filtrável por ano."""
    q = (
        select(
            ProposicaoAutor.idDeputadoAutor,
            func.sum(
                case(
                    (
                        Proposicao.siglaTipo.in_(["PEC", "PL", "PLC", "PLP"]),
                        case((ProposicaoAutor.proponente == True, 1.0), else_=0.2),
                    ),
                    (
                        Proposicao.siglaTipo.in_(["PDC", "PRC", "MPV"]),
                        case((ProposicaoAutor.proponente == True, 0.5), else_=0.1),
                    ),
                    else_=case((ProposicaoAutor.proponente == True, 0.05), else_=0.01),
                )
            ).label("pontos_producao"),
        )
        .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
        .where(ProposicaoAutor.idDeputadoAutor == deputado_id)
    )
    if ano is not None:
        q = q.where(Proposicao.ano == ano)
    return q.group_by(ProposicaoAutor.idDeputadoAutor).subquery()


def _sub_gastos(deputado_id: int, ano: int | None = None):
    """Subquery de gastos CEAP e meses ativos, filtrável por ano."""
    q = (
        select(
            Despesa.idDeputado,
            func.sum(Despesa.valorLiquido).label("total_gasto"),
            func.count(
                func.distinct(Despesa.ano.cast(String) + "-" + Despesa.mes.cast(String))
            ).label("meses_mandato"),
        )
        .where(Despesa.idDeputado == deputado_id)
    )
    if ano is not None:
        q = q.where(Despesa.ano == ano)
    return q.group_by(Despesa.idDeputado).subquery()


def _sub_gabinete(deputado_id: int, ano: int | None = None):
    """Subquery de verba de gabinete (pessoal/funcionários), filtrável por ano."""
    q = (
        select(
            VerbaGabinete.idDeputado,
            func.coalesce(func.sum(VerbaGabinete.valorGasto), 0).label("gasto_gabinete"),
        )
        .where(VerbaGabinete.idDeputado == deputado_id)
    )
    if ano is not None:
        q = q.where(VerbaGabinete.ano == ano)
    return q.group_by(VerbaGabinete.idDeputado).subquery()


class RankingRepository:
    """Acesso a dados de rankings. Todas as queries são parametrizadas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Rankings de despesas
    # ------------------------------------------------------------------

    async def get_ranking_despesas_politicos(
        self,
        *,
        q: str | None = None,
        uf: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingDespesaPolitico]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Deputado.id.label("politico_id"),
                Deputado.nome,
                func.coalesce(func.sum(Despesa.valorLiquido), 0).label("total_gasto"),
            )
            .join(Despesa, Despesa.idDeputado == Deputado.id)
        )

        if uf:
            stmt = stmt.where(Deputado.siglaUF == uf.upper()[:2])
        if q:
            stmt = stmt.where(Deputado.nome.ilike(f"%{q}%"))

        stmt = (
            stmt.group_by(Deputado.id, Deputado.nome)
            .order_by(desc("total_gasto"))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            result = await self.db.execute(stmt)
            return [
                RankingDespesaPolitico(
                    politico_id=r["politico_id"],
                    nome=r["nome"],
                    total_gasto=float(r["total_gasto"]),
                )
                for r in result.mappings()
            ]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ranking de despesas por deputado")
            raise

    # ------------------------------------------------------------------
    # Rankings de discursos
    # ------------------------------------------------------------------

    async def get_ranking_discursos_politicos(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingDiscursoPolitico]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_DISCURSOS)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Deputado.id.label("politico_id"),
                Deputado.nome.label("nome_politico"),
                Deputado.siglaPartido.label("sigla_partido"),
                Deputado.siglaUF.label("sigla_uf"),
                func.count(Discurso.id).label("total_discursos"),
            )
            .join(Discurso, Discurso.idDeputado == Deputado.id)
            .group_by(Deputado.id, Deputado.nome, Deputado.siglaPartido, Deputado.siglaUF)
            .order_by(desc("total_discursos"))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            result            = await self.db.execute(stmt)
            deputados_ranking = result.mappings().all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ranking de discursos")
            raise

        if not deputados_ranking:
            return []

        deputado_ids = [r["politico_id"] for r in deputados_ranking]
        stmt_kw = select(Discurso.idDeputado, Discurso.keywords).where(
            Discurso.idDeputado.in_(deputado_ids),
            Discurso.keywords.is_not(None),
        )

        try:
            kw_result = await self.db.execute(stmt_kw)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar keywords dos discursos")
            raise

        keywords_por_deputado: dict[int, Counter] = {pid: Counter() for pid in deputado_ids}
        for row in kw_result:
            tags = [
                t.strip().upper()
                for t in row.keywords.replace(";", ",").split(",")
                if t.strip()
            ]
            tags_limpas = [t for t in tags if t not in _BLACKLIST_KEYWORDS and len(t) > 3]
            keywords_por_deputado[row.idDeputado].update(tags_limpas)

        return [
            RankingDiscursoPolitico(
                politico_id=r["politico_id"],
                nome_politico=r["nome_politico"],
                sigla_partido=r["sigla_partido"],
                sigla_uf=r["sigla_uf"],
                total_discursos=r["total_discursos"],
                temas_mais_discutidos=[
                    KeywordInfo(keyword=kw, frequencia=count)
                    for kw, count in keywords_por_deputado[r["politico_id"]].most_common(20)
                ],
            )
            for r in deputados_ranking
        ]

    # ------------------------------------------------------------------
    # Performance — ranking geral (todos os parlamentares)
    # ------------------------------------------------------------------

    async def get_ranking_performance_politicos(self) -> list:
        """
        Retorna dados brutos de performance para todos os parlamentares.
        Sem filtro de ano — usa o mandato inteiro.
        O cálculo do score é responsabilidade do serviço (performance_calc).
        """
        # Total de eventos disponíveis (denominador da assiduidade)
        sub_total_eventos = (
            select(func.count(PresencaDeputado.id)).scalar_subquery()
        )

        sub_presenca = (
            select(
                PresencaDeputado.idDeputado,
                func.coalesce(
                    func.round(
                        cast(
                            func.count(PresencaDeputado.id).cast(Float)
                            / func.nullif(sub_total_eventos, 0)
                            * 100,
                            Numeric,
                        ),
                        2,
                    ),
                    0,
                ).label("nota_assiduidade"),
            )
            .group_by(PresencaDeputado.idDeputado)
        ).subquery()

        sub_producao = (
            select(
                ProposicaoAutor.idDeputadoAutor,
                func.sum(
                    case(
                        (
                            Proposicao.siglaTipo.in_(["PEC", "PL", "PLC", "PLP"]),
                            case((ProposicaoAutor.proponente == True, 1.0), else_=0.2),
                        ),
                        (
                            Proposicao.siglaTipo.in_(["PDC", "PRC", "MPV"]),
                            case((ProposicaoAutor.proponente == True, 0.5), else_=0.1),
                        ),
                        else_=case((ProposicaoAutor.proponente == True, 0.05), else_=0.01),
                    )
                ).label("pontos_producao"),
            )
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .group_by(ProposicaoAutor.idDeputadoAutor)
        ).subquery()

        sub_gastos = (
            select(
                Despesa.idDeputado,
                func.sum(Despesa.valorLiquido).label("total_gasto"),
                func.count(
                    func.distinct(Despesa.ano.cast(String) + "-" + Despesa.mes.cast(String))
                ).label("meses_mandato"),
            )
            .group_by(Despesa.idDeputado)
        ).subquery()

        sub_gabinete = (
            select(
                VerbaGabinete.idDeputado,
                func.coalesce(func.sum(VerbaGabinete.valorGasto), 0).label("gasto_gabinete"),
            )
            .group_by(VerbaGabinete.idDeputado)
        ).subquery()

        stmt = (
            select(
                Deputado.id,
                Deputado.nome,
                Deputado.siglaUF.label("siglaUF"),
                Deputado.siglaPartido.label("siglaPartido"),
                Deputado.urlFoto.label("urlFoto"),
                func.coalesce(sub_presenca.c.nota_assiduidade, 0).label("nota_assiduidade"),
                func.coalesce(sub_producao.c.pontos_producao,  0).label("pontos_producao"),
                func.coalesce(sub_gastos.c.total_gasto,        0).label("total_gasto"),
                func.coalesce(sub_gastos.c.meses_mandato,      1).label("meses_mandato"),
                func.coalesce(sub_gabinete.c.gasto_gabinete,   0).label("gasto_gabinete"),
            )
            .outerjoin(sub_presenca, Deputado.id == sub_presenca.c.idDeputado)
            .outerjoin(sub_producao, Deputado.id == sub_producao.c.idDeputadoAutor)
            .outerjoin(sub_gastos,   Deputado.id == sub_gastos.c.idDeputado)
            .outerjoin(sub_gabinete, Deputado.id == sub_gabinete.c.idDeputado)
        )

        try:
            result = await self.db.execute(stmt)
            return result.mappings().all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar dados de performance dos deputados")
            raise

    # ------------------------------------------------------------------
    # Performance — parlamentar individual (com ou sem filtro de ano)
    # ------------------------------------------------------------------

    async def get_performance_data_by_id(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
    ) -> dict | None:
        sub_p  = _sub_presenca(deputado_id, ano)
        sub_r  = _sub_producao(deputado_id, ano)
        sub_g  = _sub_gastos(deputado_id, ano)
        sub_gb = _sub_gabinete(deputado_id, ano)

        stmt = (
            select(
                Deputado.id,
                Deputado.nome,
                Deputado.siglaUF.label("siglaUF"),
                Deputado.siglaPartido.label("siglaPartido"),
                Deputado.urlFoto.label("urlFoto"),
                func.coalesce(sub_p.c.nota_assiduidade,  0).label("nota_assiduidade"),
                func.coalesce(sub_r.c.pontos_producao,   0).label("pontos_producao"),
                func.coalesce(sub_g.c.total_gasto,       0).label("total_gasto"),
                func.coalesce(sub_g.c.meses_mandato,     1).label("meses_mandato"),
                func.coalesce(sub_gb.c.gasto_gabinete,   0).label("gasto_gabinete"),
            )
            .where(Deputado.id == deputado_id)
            .outerjoin(sub_p,  Deputado.id == sub_p.c.idDeputado)
            .outerjoin(sub_r,  Deputado.id == sub_r.c.idDeputadoAutor)
            .outerjoin(sub_g,  Deputado.id == sub_g.c.idDeputado)
            .outerjoin(sub_gb, Deputado.id == sub_gb.c.idDeputado)
        )

        try:
            result = await self.db.execute(stmt)
            row = result.mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError:
            logger.exception("Erro ao buscar dados de performance do deputado id=%s", deputado_id)
            raise

    # ------------------------------------------------------------------
    # Timeline — série histórica anual de um parlamentar
    # ------------------------------------------------------------------

    async def get_timeline_data_by_id(self, deputado_id: int) -> list[dict]:
        # --- Anos disponíveis ---
        stmt_anos = (
            select(Despesa.ano.label("ano"))
            .where(Despesa.idDeputado == deputado_id)
            .distinct()
            .order_by(Despesa.ano)
        )

        # --- Assiduidade por ano ---
        # Denominador: total de eventos por ano (independente do deputado)
        _ano_presenca = extract("year", PresencaDeputado.dataHoraInicio).cast(Integer).label("ano")
        _ano_presenca_all = extract("year", PresencaDeputado.dataHoraInicio).cast(Integer).label("ano")
        sub_total_por_ano = (
            select(
                _ano_presenca_all,
                func.count(PresencaDeputado.id).label("total_eventos"),
            )
            .group_by(_ano_presenca_all)
        ).subquery()

        stmt_presenca = (
            select(
                _ano_presenca,
                func.coalesce(
                    func.round(
                        cast(
                            func.count(PresencaDeputado.id).cast(Float)
                            / func.nullif(sub_total_por_ano.c.total_eventos, 0)
                            * 100,
                            Numeric,
                        ),
                        2,
                    ),
                    0,
                ).label("nota_assiduidade"),
            )
            .join(
                sub_total_por_ano,
                extract("year", PresencaDeputado.dataHoraInicio).cast(Integer) == sub_total_por_ano.c.ano,
            )
            .where(PresencaDeputado.idDeputado == deputado_id)
            .group_by(_ano_presenca, sub_total_por_ano.c.total_eventos)
        )

        # --- Produção ponderada por ano ---
        stmt_producao = (
            select(
                Proposicao.ano.label("ano"),
                func.sum(
                    case(
                        (
                            Proposicao.siglaTipo.in_(["PEC", "PL", "PLC", "PLP"]),
                            case((ProposicaoAutor.proponente == True, 1.0), else_=0.2),
                        ),
                        (
                            Proposicao.siglaTipo.in_(["PDC", "PRC", "MPV"]),
                            case((ProposicaoAutor.proponente == True, 0.5), else_=0.1),
                        ),
                        else_=case((ProposicaoAutor.proponente == True, 0.05), else_=0.01),
                    )
                ).label("pontos_producao"),
            )
            .select_from(ProposicaoAutor)
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(ProposicaoAutor.idDeputadoAutor == deputado_id)
            .group_by(Proposicao.ano)
        )

        # --- Gastos, meses ativos e total de despesas por ano ---
        stmt_gastos = (
            select(
                Despesa.ano.label("ano"),
                func.sum(Despesa.valorLiquido).label("total_gasto"),
                func.count(func.distinct(Despesa.mes)).label("meses_ativos"),
                func.count(Despesa.id).label("total_despesas"),
            )
            .where(Despesa.idDeputado == deputado_id)
            .group_by(Despesa.ano)
        )

        # --- Verba de gabinete por ano ---
        stmt_gabinete = (
            select(
                VerbaGabinete.ano.label("ano"),
                func.coalesce(func.sum(VerbaGabinete.valorGasto), 0).label("gasto_gabinete"),
            )
            .where(VerbaGabinete.idDeputado == deputado_id)
            .group_by(VerbaGabinete.ano)
        )

        # --- Votações por ano ---
        _ano_voto = extract("year", Votacao.data).cast(Integer).label("ano")
        stmt_votos = (
            select(
                _ano_voto,
                func.count(Voto.id).label("total_votacoes"),
            )
            .select_from(Voto)
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .where(Voto.idDeputado == deputado_id)
            .group_by(_ano_voto)
        )

        try:
            res_anos     = await self.db.execute(stmt_anos)
            res_presenca = await self.db.execute(stmt_presenca)
            res_producao = await self.db.execute(stmt_producao)
            res_gastos   = await self.db.execute(stmt_gastos)
            res_gabinete = await self.db.execute(stmt_gabinete)
            res_votos    = await self.db.execute(stmt_votos)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar timeline do deputado id=%s", deputado_id)
            raise

        deputado = await self.db.get(Deputado, deputado_id)
        if not deputado:
            return []

        presenca_por_ano  = {int(r.ano): float(r.nota_assiduidade) for r in res_presenca}
        producao_por_ano  = {int(r.ano): float(r.pontos_producao)  for r in res_producao}
        gabinete_por_ano  = {int(r.ano): float(r.gasto_gabinete)   for r in res_gabinete}
        gastos_por_ano    = {
            int(r.ano): {
                "total_gasto":    float(r.total_gasto or 0),
                "meses_ativos":   int(r.meses_ativos or 1),
                "total_despesas": int(r.total_despesas or 0),
            }
            for r in res_gastos
        }
        votos_por_ano = {int(r.ano): int(r.total_votacoes) for r in res_votos}

        anos = sorted({int(r.ano) for r in res_anos})

        resultado = []
        for ano in anos:
            gastos    = gastos_por_ano.get(ano, {"total_gasto": 0.0, "meses_ativos": 1, "total_despesas": 0})
            raw_entry = {
                "id":               deputado.id,
                "nome":             deputado.nome,
                "siglaUF":          deputado.siglaUF,
                "siglaPartido":     deputado.siglaPartido,
                "urlFoto":          deputado.urlFoto,
                "nota_assiduidade": presenca_por_ano.get(ano, 0.0),
                "pontos_producao":  producao_por_ano.get(ano, 0.0),
                "total_gasto":      gastos["total_gasto"],
                "meses_mandato":    gastos["meses_ativos"],
                "gasto_gabinete":   gabinete_por_ano.get(ano, 0.0),
            }
            resultado.append({
                "ano":            ano,
                "raw":            raw_entry,
                "total_votacoes": votos_por_ano.get(ano, 0),
                "total_despesas": gastos["total_despesas"],
            })

        return resultado

    # ------------------------------------------------------------------
    # Performance — lista de IDs elegíveis para o ranking
    # ------------------------------------------------------------------

    async def get_todos_deputados_ids(self) -> list[dict]:
        """
        Retorna id, nome, siglaUF, siglaPartido e urlFoto de todos os
        parlamentares elegíveis para o ranking (idLegislaturaInicial >= 54).
        Query leve — sem agregações.
        """
        stmt = (
            select(
                Deputado.id,
                Deputado.nome,
                Deputado.siglaUF,
                Deputado.siglaPartido,
                Deputado.urlFoto,
            )
            .where(Deputado.idLegislaturaInicial >= 54)
            .order_by(Deputado.id)
        )
        try:
            result = await self.db.execute(stmt)
            return [dict(r) for r in result.mappings()]
        except SQLAlchemyError:
            logger.exception("Erro ao listar IDs de deputados para ranking")
            raise

    async def get_timeline_data_batch(self, deputado_ids: list[int]) -> dict[int, list[dict]]:
        """
        Busca dados de timeline para múltiplos deputados em queries únicas (sem N+1).
        Retorna dict {deputado_id: [lista de entradas anuais com raw + metadados]}.

        Cada entrada tem o mesmo formato de get_timeline_data_by_id:
          {"ano": int, "raw": {...}, "total_votacoes": int, "total_despesas": int}
        """
        if not deputado_ids:
            return {}

        ids = deputado_ids  # já validados pelo chamador

        # --- Anos disponíveis por deputado ---
        stmt_anos = (
            select(Despesa.idDeputado, Despesa.ano)
            .where(Despesa.idDeputado.in_(ids))
            .distinct()
        )

        # --- Assiduidade por deputado/ano via votações ---
        sub_total_votacoes_ano = (
            select(
                extract("year", Votacao.data).cast(Integer).label("ano"),
                func.count(func.distinct(Votacao.id)).label("total"),
            )
            .group_by(extract("year", Votacao.data).cast(Integer))
        ).subquery()

        _ano_voto_batch = extract("year", Votacao.data).cast(Integer).label("ano")
        stmt_presenca = (
            select(
                Voto.idDeputado,
                _ano_voto_batch,
                func.coalesce(
                    func.round(
                        cast(
                            func.count(Voto.id).cast(Float)
                            / func.nullif(sub_total_votacoes_ano.c.total, 0)
                            * 100,
                            Numeric,
                        ),
                        2,
                    ),
                    0,
                ).label("nota_assiduidade"),
            )
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .join(
                sub_total_votacoes_ano,
                extract("year", Votacao.data).cast(Integer) == sub_total_votacoes_ano.c.ano,
            )
            .where(Voto.idDeputado.in_(ids))
            # sub_total_votacoes_ano.c.total deve estar no GROUP BY porque
            # o PostgreSQL não permite referenciá-lo apenas na divisão sem agregação
            .group_by(Voto.idDeputado, _ano_voto_batch, sub_total_votacoes_ano.c.total)
        )

        # --- Produção por deputado/ano ---
        stmt_producao = (
            select(
                ProposicaoAutor.idDeputadoAutor,
                Proposicao.ano.label("ano"),
                func.sum(
                    case(
                        (
                            Proposicao.siglaTipo.in_(["PEC", "PL", "PLC", "PLP"]),
                            case((ProposicaoAutor.proponente == True, 1.0), else_=0.2),
                        ),
                        (
                            Proposicao.siglaTipo.in_(["PDC", "PRC", "MPV"]),
                            case((ProposicaoAutor.proponente == True, 0.5), else_=0.1),
                        ),
                        else_=case((ProposicaoAutor.proponente == True, 0.05), else_=0.01),
                    )
                ).label("pontos_producao"),
            )
            .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(ProposicaoAutor.idDeputadoAutor.in_(ids))
            .group_by(ProposicaoAutor.idDeputadoAutor, Proposicao.ano)
        )

        # --- Gastos CEAP por deputado/ano ---
        stmt_gastos = (
            select(
                Despesa.idDeputado,
                Despesa.ano.label("ano"),
                func.sum(Despesa.valorLiquido).label("total_gasto"),
                func.count(func.distinct(Despesa.mes)).label("meses_ativos"),
                func.count(Despesa.id).label("total_despesas"),
            )
            .where(Despesa.idDeputado.in_(ids))
            .group_by(Despesa.idDeputado, Despesa.ano)
        )

        # --- Verba de gabinete por deputado/ano ---
        stmt_gabinete = (
            select(
                VerbaGabinete.idDeputado,
                VerbaGabinete.ano.label("ano"),
                func.coalesce(func.sum(VerbaGabinete.valorGasto), 0).label("gasto_gabinete"),
            )
            .where(VerbaGabinete.idDeputado.in_(ids))
            .group_by(VerbaGabinete.idDeputado, VerbaGabinete.ano)
        )

        # --- Votações por deputado/ano ---
        _ano_voto2 = extract("year", Votacao.data).cast(Integer).label("ano")
        stmt_votos = (
            select(
                Voto.idDeputado,
                _ano_voto2,
                func.count(Voto.id).label("total_votacoes"),
            )
            .join(Votacao, Votacao.id == Voto.idVotacao)
            .where(Voto.idDeputado.in_(ids))
            .group_by(Voto.idDeputado, _ano_voto2)
        )

        try:
            res_anos     = await self.db.execute(stmt_anos)
            res_presenca = await self.db.execute(stmt_presenca)
            res_producao = await self.db.execute(stmt_producao)
            res_gastos   = await self.db.execute(stmt_gastos)
            res_gabinete = await self.db.execute(stmt_gabinete)
            res_votos    = await self.db.execute(stmt_votos)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar timeline batch de deputados")
            raise

        # --- Montar dicts auxiliares indexados por (deputado_id, ano) ---
        anos_por_dep: dict[int, set[int]] = defaultdict(set)
        for r in res_anos.all():
            anos_por_dep[r.idDeputado].add(int(r.ano))

        presenca: dict[tuple, float] = {}
        for r in res_presenca.mappings():
            presenca[(int(r["idDeputado"]), int(r["ano"]))] = float(r["nota_assiduidade"])

        producao: dict[tuple, float] = {}
        for r in res_producao.mappings():
            producao[(int(r["idDeputadoAutor"]), int(r["ano"]))] = float(r["pontos_producao"])

        gastos: dict[tuple, dict] = {}
        for r in res_gastos.mappings():
            gastos[(int(r["idDeputado"]), int(r["ano"]))] = {
                "total_gasto":    float(r["total_gasto"] or 0),
                "meses_ativos":   int(r["meses_ativos"] or 1),
                "total_despesas": int(r["total_despesas"] or 0),
            }

        gabinete: dict[tuple, float] = {}
        for r in res_gabinete.mappings():
            gabinete[(int(r["idDeputado"]), int(r["ano"]))] = float(r["gasto_gabinete"])

        votos: dict[tuple, int] = {}
        for r in res_votos.mappings():
            votos[(int(r["idDeputado"]), int(r["ano"]))] = int(r["total_votacoes"])

        # --- Montar resultado final ---
        resultado: dict[int, list[dict]] = {}
        for dep_id in ids:
            anos = sorted(anos_por_dep.get(dep_id, set()))
            entradas = []
            for ano in anos:
                g = gastos.get((dep_id, ano), {"total_gasto": 0.0, "meses_ativos": 1, "total_despesas": 0})
                entradas.append({
                    "ano": ano,
                    "raw": {
                        "nota_assiduidade": presenca.get((dep_id, ano), 0.0),
                        "pontos_producao":  producao.get((dep_id, ano), 0.0),
                        "total_gasto":      g["total_gasto"],
                        "meses_mandato":    g["meses_ativos"],
                        "gasto_gabinete":   gabinete.get((dep_id, ano), 0.0),
                    },
                    "total_votacoes": votos.get((dep_id, ano), 0),
                    "total_despesas": g["total_despesas"],
                })
            resultado[dep_id] = entradas

        return resultado

    # ------------------------------------------------------------------
    # Empresas
    # ------------------------------------------------------------------

    async def get_ranking_lucro_empresas(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingEmpresaLucro]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)

        # Busca um volume maior do banco para compensar o merge de fornecedores duplicados
        # (ex: TAM/LATAM). O offset real é aplicado em memória após o merge porque a
        # deduplicação muda a ordem. Para cobrir até safe_offset + safe_limit entradas
        # únicas, buscamos (safe_offset + safe_limit) * 3 do banco.
        _fetch_size = (safe_offset + safe_limit) * 3
        stmt = (
            select(
                func.coalesce(Despesa.cnpjCpfFornecedor, "").label("cnpj"),
                func.upper(func.trim(Despesa.nomeFornecedor)).label("nome_bruto"),
                func.sum(Despesa.valorLiquido).label("total"),
            )
            .group_by(text("cnpj"), text("nome_bruto"))
            .order_by(desc("total"))
            .limit(_fetch_size)
        )

        try:
            result = await self.db.execute(stmt)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ranking de empresas")
            raise

        processed_data: dict[str, float] = defaultdict(float)
        names_map: dict[str, dict]       = {}

        for r in result.mappings():
            nome_bruto: str = r["nome_bruto"]
            cnpj_db: str    = r["cnpj"]

            fix = _FORNECEDOR_DATA_FIX.get(nome_bruto)
            if fix:
                cnpj_final = fix["cnpj"]
                nome_final = fix["nome"]
            else:
                cnpj_final = cnpj_db
                nome_final = nome_bruto

            key = cnpj_final if cnpj_final else f"NOCNPJ_{nome_final}"
            processed_data[key] += float(r["total"])

            if key not in names_map:
                names_map[key] = {"cnpj": cnpj_final, "nome": nome_final}

        ranking = sorted(
            [
                RankingEmpresaLucro(
                    cnpj=info["cnpj"],
                    nome_fornecedor=info["nome"],
                    total_recebido=processed_data[key],
                )
                for key, info in names_map.items()
            ],
            key=lambda x: x.total_recebido,
            reverse=True,
        )

        return ranking[safe_offset : safe_offset + safe_limit]