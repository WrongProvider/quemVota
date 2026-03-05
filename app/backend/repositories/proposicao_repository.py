"""
Repositório de Proposições e Votações — Camada de acesso a dados.

Segurança (OWASP):
  - A01 / SQL Injection: todas as queries usam SQLAlchemy Core com bind
    parameters; nenhuma concatenação ou interpolação de strings em SQL.
  - A03 / Sensitive Data Exposure: nenhum dado sensível é logado ou exposto
    nas exceções; stack traces não chegam à camada HTTP.
  - A04 / Insecure Design: limites máximos aplicados aqui como segunda linha
    de defesa (o serviço também os aplica).
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from backend.models import (
    VotacaoOrientacao,
    Proposicao,
    ProposicaoAutor,
    Tema,
    Tramitacao,
    Votacao,
)
from backend.schemas import (
    AutorResumo,
    OrientacaoPartido,
    ProposicaoDetalhe,
    ProposicaoResponse,
    TemaResumo,
    TramitacaoItem,
    VotacaoDetalhe,
    VotacaoResponse,
)

logger = logging.getLogger(__name__)

_MAX_LIMIT_PROPOSICOES = 100
_MAX_LIMIT_VOTACOES    = 100


class ProposicaoRepository:
    """Acesso a dados de proposições e votações. Todas as queries são parametrizadas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _build_proposicao_response(p: Proposicao) -> ProposicaoResponse:
        return ProposicaoResponse(
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
                AutorResumo(
                    politico_id=a.idDeputadoAutor,
                    nome=a.nomeAutor,
                    tipo=a.tipoAutor,
                    proponente=a.proponente,
                )
                for a in p.autores
            ],
            temas=[
                TemaResumo(id=t.id, cod_tema=t.codTema, tema=t.tema)
                for t in p.temas
            ],
        )

    @staticmethod
    def _build_votacao_response(row) -> VotacaoResponse:
        return VotacaoResponse(
            id=row.id,
            id_camara=row.id_camara,
            data=row.data,
            data_hora_registro=row.data_hora_registro,
            tipo_votacao=row.tipo_votacao,
            descricao=row.descricao,
            aprovacao=row.aprovacao,
            sigla_orgao=row.sigla_orgao,
            proposicao_id=row.proposicao_id,
            proposicao_sigla=row.proposicao_sigla,
            proposicao_numero=row.proposicao_numero,
            proposicao_ano=row.proposicao_ano,
            proposicao_ementa=row.proposicao_ementa,
        )

    # ------------------------------------------------------------------
    # Proposições — listagem
    # ------------------------------------------------------------------

    async def listar_proposicoes_repo(
        self,
        *,
        q: str | None = None,
        sigla_tipo: str | None = None,
        ano: int | None = None,
        tema_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProposicaoResponse]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_PROPOSICOES)
        safe_offset = max(offset, 0)

        stmt = (
            select(Proposicao)
            .options(
                selectinload(Proposicao.autores),
                selectinload(Proposicao.temas),
            )
            .order_by(desc(Proposicao.dataApresentacao))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        if q:
            stmt = stmt.where(Proposicao.ementa.ilike(f"%{q}%"))
        if sigla_tipo:
            stmt = stmt.where(Proposicao.siglaTipo == sigla_tipo.upper()[:10])
        if ano:
            stmt = stmt.where(Proposicao.ano == ano)
        if tema_id:
            stmt = stmt.where(Proposicao.temas.any(Tema.id == tema_id))

        try:
            result = await self.db.execute(stmt)
            proposicoes = result.scalars().all()
            return [self._build_proposicao_response(p) for p in proposicoes]
        except SQLAlchemyError:
            logger.exception(
                "Erro ao listar proposições | q=%s sigla_tipo=%s ano=%s tema_id=%s",
                q, sigla_tipo, ano, tema_id,
            )
            raise

    # ------------------------------------------------------------------
    # Proposições — detalhe
    # ------------------------------------------------------------------

    async def get_proposicao_repo(self, proposicao_id: int) -> ProposicaoDetalhe | None:
        stmt = (
            select(Proposicao)
            .options(
                selectinload(Proposicao.autores),
                selectinload(Proposicao.temas),
                selectinload(Proposicao.tramitacoes),
            )
            .where(Proposicao.id == proposicao_id)
        )

        try:
            result = await self.db.execute(stmt)
            p = result.scalars().first()
        except SQLAlchemyError:
            logger.exception("Erro ao buscar proposição id=%s", proposicao_id)
            raise

        if p is None:
            return None

        return ProposicaoDetalhe(
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
                AutorResumo(
                    politico_id=a.idDeputadoAutor,
                    nome=a.nomeAutor,
                    tipo=a.tipoAutor,
                    proponente=a.proponente,
                )
                for a in p.autores
            ],
            temas=[
                TemaResumo(id=t.id, cod_tema=t.codTema, tema=t.tema)
                for t in p.temas
            ],
            ementa_detalhada=p.ementaDetalhada,
            justificativa=p.justificativa,
            urn_final=p.urnFinal,
            tramitacoes=[
                TramitacaoItem(
                    id=t.id,
                    data_hora=t.dataHora,
                    sequencia=t.sequencia,
                    sigla_orgao=t.siglaOrgao,
                    regime=t.regime,
                    descricao_tramitacao=t.descricaoTramitacao,
                    descricao_situacao=t.descricaoSituacao,
                    despacho=t.despacho,
                    ambito=t.ambito,
                    apreciacao=t.apreciacao,
                )
                for t in p.tramitacoes
            ],
        )

    # ------------------------------------------------------------------
    # Proposições — votações de uma proposição
    # ------------------------------------------------------------------

    async def get_votacoes_da_proposicao_repo(
        self,
        proposicao_id: int,
    ) -> list[VotacaoResponse]:
        stmt = (
            select(
                Votacao.id,
                Votacao.idCamara.label("id_camara"),
                Votacao.data,
                Votacao.dataHoraRegistro.label("data_hora_registro"),
                Votacao.tipoVotacao.label("tipo_votacao"),
                Votacao.descricao,
                Votacao.aprovacao,
                Votacao.siglaOrgao.label("sigla_orgao"),
                Proposicao.id.label("proposicao_id"),
                Proposicao.siglaTipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
            )
            .join(Proposicao, Votacao.idProposicao == Proposicao.id)
            .where(Votacao.idProposicao == proposicao_id)
            .order_by(desc(Votacao.data))
        )

        try:
            result = await self.db.execute(stmt)
            return [self._build_votacao_response(row) for row in result.mappings()]
        except SQLAlchemyError:
            logger.exception("Erro ao buscar votações da proposição id=%s", proposicao_id)
            raise

    # ------------------------------------------------------------------
    # Votações — listagem
    # ------------------------------------------------------------------

    async def listar_votacoes_repo(
        self,
        *,
        ano: int | None = None,
        aprovacao: int | None = None,
        sigla_tipo: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[VotacaoResponse]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_VOTACOES)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Votacao.id,
                Votacao.idCamara.label("id_camara"),
                Votacao.data,
                Votacao.dataHoraRegistro.label("data_hora_registro"),
                Votacao.tipoVotacao.label("tipo_votacao"),
                Votacao.descricao,
                Votacao.aprovacao,
                Votacao.siglaOrgao.label("sigla_orgao"),
                Proposicao.id.label("proposicao_id"),
                Proposicao.siglaTipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
            )
            .outerjoin(Proposicao, Votacao.idProposicao == Proposicao.id)
            .order_by(desc(Votacao.data))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        if ano is not None:
            stmt = stmt.where(func.extract("year", Votacao.data) == ano)
        if aprovacao is not None:
            stmt = stmt.where(Votacao.aprovacao == aprovacao)
        if sigla_tipo:
            stmt = stmt.where(Proposicao.siglaTipo == sigla_tipo.upper()[:10])

        try:
            result = await self.db.execute(stmt)
            return [self._build_votacao_response(row) for row in result.mappings()]
        except SQLAlchemyError:
            logger.exception(
                "Erro ao listar votações | ano=%s aprovacao=%s sigla_tipo=%s",
                ano, aprovacao, sigla_tipo,
            )
            raise

    # ------------------------------------------------------------------
    # Votações — detalhe
    # ------------------------------------------------------------------

    async def get_votacao_repo(self, votacao_id: int) -> VotacaoDetalhe | None:
        stmt_votacao = (
            select(
                Votacao.id,
                Votacao.idCamara.label("id_camara"),
                Votacao.data,
                Votacao.dataHoraRegistro.label("data_hora_registro"),
                Votacao.tipoVotacao.label("tipo_votacao"),
                Votacao.descricao,
                Votacao.aprovacao,
                Votacao.siglaOrgao.label("sigla_orgao"),
                Proposicao.id.label("proposicao_id"),
                Proposicao.siglaTipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
            )
            .outerjoin(Proposicao, Votacao.idProposicao == Proposicao.id)
            .where(Votacao.id == votacao_id)
        )

        stmt_orientacoes = (
            select(
                VotacaoOrientacao.siglaBancada.label("sigla_partido_bloco"),
                VotacaoOrientacao.orientacao.label("orientacao_voto"),
            )
            .where(VotacaoOrientacao.idVotacao == votacao_id)
            .order_by(VotacaoOrientacao.siglaBancada)
        )

        try:
            res_v = await self.db.execute(stmt_votacao)
            res_o = await self.db.execute(stmt_orientacoes)
        except SQLAlchemyError:
            logger.exception("Erro ao buscar votação id=%s", votacao_id)
            raise

        row = res_v.mappings().first()
        if row is None:
            return None

        orientacoes = [
            OrientacaoPartido(
                sigla_partido_bloco=o.sigla_partido_bloco,
                orientacao_voto=o.orientacao_voto,
            )
            for o in res_o.mappings()
        ]

        return VotacaoDetalhe(
            id=row.id,
            id_camara=row.id_camara,
            data=row.data,
            data_hora_registro=row.data_hora_registro,
            tipo_votacao=row.tipo_votacao,
            descricao=row.descricao,
            aprovacao=row.aprovacao,
            sigla_orgao=row.sigla_orgao,
            proposicao_id=row.proposicao_id,
            proposicao_sigla=row.proposicao_sigla,
            proposicao_numero=row.proposicao_numero,
            proposicao_ano=row.proposicao_ano,
            proposicao_ementa=row.proposicao_ementa,
            orientacoes=orientacoes,
        )