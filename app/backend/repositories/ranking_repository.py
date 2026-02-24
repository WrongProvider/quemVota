"""
Repositório de Rankings — Camada de acesso a dados.

Segurança (OWASP):
  - A01 / SQL Injection: todas as queries usam SQLAlchemy Core com bind parameters.
  - A03 / Sensitive Data Exposure: nenhum dado sensível é logado ou exposto.
  - A04 / Insecure Design: limites máximos aplicados como defesa em profundidade.
"""

import logging
from collections import Counter, defaultdict

from sqlalchemy import Float, Numeric, String, case, cast, desc, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Despesa, Discurso, Politico, Presenca, Proposicao, ProposicaoAutor
from backend.schemas import KeywordInfo, RankingDespesaPolitico, RankingDiscursoPolitico, RankingEmpresaLucro

logger = logging.getLogger(__name__)

_MAX_LIMIT_RANKING = 100
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


class RankingRepository:
    """Acesso a dados de rankings. Todas as queries sao parametrizadas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_ranking_despesas_politicos(
        self,
        *,
        q: str | None = None,
        uf: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingDespesaPolitico]:
        safe_limit = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Politico.id.label("politico_id"),
                Politico.nome,
                func.coalesce(func.sum(Despesa.valor_liquido), 0).label("total_gasto"),
            )
            .join(Despesa, Despesa.politico_id == Politico.id)
        )

        if uf:
            stmt = stmt.where(Politico.uf == uf.upper()[:2])
        if q:
            stmt = stmt.where(Politico.nome.ilike(f"%{q}%"))

        stmt = (
            stmt.group_by(Politico.id, Politico.nome)
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
            logger.exception("Erro ao buscar ranking de despesas por politico")
            raise

    async def get_ranking_discursos_politicos(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingDiscursoPolitico]:
        safe_limit = min(abs(limit), _MAX_LIMIT_DISCURSOS)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Politico.id.label("politico_id"),
                Politico.nome.label("nome_politico"),
                Politico.partido_sigla.label("sigla_partido"),
                Politico.uf.label("sigla_uf"),
                func.count(Discurso.id).label("total_discursos"),
            )
            .join(Discurso, Discurso.politico_id == Politico.id)
            .group_by(Politico.id, Politico.nome, Politico.partido_sigla, Politico.uf)
            .order_by(desc("total_discursos"))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        try:
            result = await self.db.execute(stmt)
            politicos_ranking = result.mappings().all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ranking de discursos")
            raise

        if not politicos_ranking:
            return []

        politico_ids = [r["politico_id"] for r in politicos_ranking]
        stmt_kw = select(Discurso.politico_id, Discurso.keywords).where(
            Discurso.politico_id.in_(politico_ids),
            Discurso.keywords.is_not(None),
        )

        try:
            kw_result = await self.db.execute(stmt_kw)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar keywords dos discursos")
            raise

        keywords_por_politico: dict[int, Counter] = {pid: Counter() for pid in politico_ids}
        for row in kw_result:
            tags = [
                t.strip().upper()
                for t in row.keywords.replace(";", ",").split(",")
                if t.strip()
            ]
            tags_limpas = [
                t for t in tags
                if t not in _BLACKLIST_KEYWORDS and len(t) > 3
            ]
            keywords_por_politico[row.politico_id].update(tags_limpas)

        return [
            RankingDiscursoPolitico(
                politico_id=r["politico_id"],
                nome_politico=r["nome_politico"],
                sigla_partido=r["sigla_partido"],
                sigla_uf=r["sigla_uf"],
                total_discursos=r["total_discursos"],
                temas_mais_discutidos=[
                    KeywordInfo(keyword=kw, frequencia=count)
                    for kw, count in keywords_por_politico[r["politico_id"]].most_common(20)
                ],
            )
            for r in politicos_ranking
        ]

    async def get_ranking_performance_politicos(self) -> list:
        """Retorna dados brutos de performance. O calculo do score e responsabilidade do servico."""
        sub_presenca = (
            select(
                Presenca.politico_id,
                func.coalesce(
                    func.round(
                        cast(
                            (
                                func.count(Presenca.id)
                                .filter(Presenca.frequencia_sessao == "Presenca")
                                .cast(Float)
                                / func.nullif(func.count(Presenca.id), 0)
                            )
                            * 100,
                            Numeric,
                        ),
                        2,
                    ),
                    0,
                ).label("nota_assiduidade"),
            )
            .group_by(Presenca.politico_id)
        ).subquery()

        sub_producao = (
            select(
                ProposicaoAutor.politico_id,
                func.sum(
                    case(
                        (
                            Proposicao.sigla_tipo.in_(["PEC", "PL", "PLC", "PLP"]),
                            case((ProposicaoAutor.proponente == True, 1.0), else_=0.2),
                        ),
                        (
                            Proposicao.sigla_tipo.in_(["PDC", "PRC", "MPV"]),
                            case((ProposicaoAutor.proponente == True, 0.5), else_=0.1),
                        ),
                        else_=case((ProposicaoAutor.proponente == True, 0.05), else_=0.01),
                    )
                ).label("pontos_producao"),
            )
            .join(Proposicao, Proposicao.id == ProposicaoAutor.proposicao_id)
            .group_by(ProposicaoAutor.politico_id)
        ).subquery()

        sub_gastos = (
            select(
                Despesa.politico_id,
                func.sum(Despesa.valor_liquido).label("total_gasto"),
                func.count(
                    func.distinct(Despesa.ano.cast(String) + "-" + Despesa.mes.cast(String))
                ).label("meses_mandato"),
            )
            .group_by(Despesa.politico_id)
        ).subquery()

        stmt = (
            select(
                Politico.id,
                Politico.nome,
                Politico.uf,
                Politico.partido_sigla,
                Politico.url_foto,
                func.coalesce(sub_presenca.c.nota_assiduidade, 0).label("nota_assiduidade"),
                func.coalesce(sub_producao.c.pontos_producao, 0).label("pontos_producao"),
                func.coalesce(sub_gastos.c.total_gasto, 0).label("total_gasto"),
                func.coalesce(sub_gastos.c.meses_mandato, 0).label("meses_mandato"),
            )
            .outerjoin(sub_presenca, Politico.id == sub_presenca.c.politico_id)
            .outerjoin(sub_producao, Politico.id == sub_producao.c.politico_id)
            .outerjoin(sub_gastos, Politico.id == sub_gastos.c.politico_id)
        )

        try:
            result = await self.db.execute(stmt)
            return result.mappings().all()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar dados de performance dos politicos")
            raise

    async def get_ranking_lucro_empresas(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RankingEmpresaLucro]:
        safe_limit = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                func.coalesce(Despesa.cnpj_cpf_fornecedor, "").label("cnpj"),
                func.upper(func.trim(Despesa.nome_fornecedor)).label("nome_bruto"),
                func.sum(Despesa.valor_liquido).label("total"),
            )
            .group_by(text("cnpj"), text("nome_bruto"))
            .order_by(desc("total"))
            .limit(safe_limit * 3)
        )

        try:
            result = await self.db.execute(stmt)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar ranking de empresas")
            raise

        processed_data: dict[str, float] = defaultdict(float)
        names_map: dict[str, dict] = {}

        for r in result.mappings():
            nome_bruto: str = r["nome_bruto"]
            cnpj_db: str = r["cnpj"]

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