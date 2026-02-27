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
    OrientacaoVotacao,
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

# Limites máximos — defesa em profundidade (serviço também limita)
_MAX_LIMIT_PROPOSICOES = 100
_MAX_LIMIT_VOTACOES    = 100


class ProposicaoRepository:
    """Acesso a dados de proposições e votações. Todas as queries são parametrizadas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helpers privados — constroem schemas a partir de ORM objects
    # ------------------------------------------------------------------

    @staticmethod
    def _build_proposicao_response(p: Proposicao) -> ProposicaoResponse:
        """
        Constrói ProposicaoResponse a partir de um ORM Proposicao.
        Os relacionamentos `autores` e `temas` já devem estar carregados
        via selectinload antes de chamar este método.
        """
        return ProposicaoResponse(
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
                AutorResumo(
                    politico_id=a.politico_id,
                    nome=a.nome,
                    tipo=a.tipo,
                    proponente=a.proponente,
                )
                for a in p.autores
            ],
            temas=[
                TemaResumo(id=t.id, cod_tema=t.cod_tema, tema=t.tema)
                for t in p.temas
            ],
        )

    @staticmethod
    def _build_votacao_response(row) -> VotacaoResponse:
        """
        Constrói VotacaoResponse a partir de uma linha de resultado de query.
        Recebe um mapping com os campos da votação + campos desnormalizados
        da proposição (proposicao_sigla, proposicao_numero, etc.).
        """
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
        """
        Lista proposições com filtros opcionais e paginação.

        Filtros:
          q          — busca na ementa (ilike)
          sigla_tipo — tipo da proposição: "PL", "PEC", "MPV", etc.
          ano        — ano de apresentação
          tema_id    — ID de um tema legislativo (join many-to-many)

        Os relacionamentos autores e temas são carregados em queries
        separadas pelo SQLAlchemy (selectinload), evitando o problema
        de N+1 queries sem gerar um produto cartesiano gigante com JOIN.
        """
        safe_limit  = min(abs(limit), _MAX_LIMIT_PROPOSICOES)
        safe_offset = max(offset, 0)

        stmt = (
            select(Proposicao)
            .options(
                selectinload(Proposicao.autores),
                selectinload(Proposicao.temas),
            )
            .order_by(desc(Proposicao.data_apresentacao))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        # Filtros opcionais — todos usam bind parameters internamente
        if q:
            stmt = stmt.where(Proposicao.ementa.ilike(f"%{q}%"))
        if sigla_tipo:
            stmt = stmt.where(Proposicao.sigla_tipo == sigla_tipo.upper()[:10])
        if ano:
            stmt = stmt.where(Proposicao.ano == ano)
        if tema_id:
            # Filtra por tema via relação many-to-many
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
        """
        Retorna o detalhe completo de uma proposição pelo ID interno.

        Carrega via selectinload:
          - autores     → ProposicaoAutor
          - temas       → Tema (many-to-many)
          - tramitacoes → Tramitacao (ordenadas por data_hora ASC pelo modelo)

        Retorna None se não encontrado (o serviço lança 404).
        """
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
            # Campos base (herda ProposicaoResponse)
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
                AutorResumo(
                    politico_id=a.politico_id,
                    nome=a.nome,
                    tipo=a.tipo,
                    proponente=a.proponente,
                )
                for a in p.autores
            ],
            temas=[
                TemaResumo(id=t.id, cod_tema=t.cod_tema, tema=t.tema)
                for t in p.temas
            ],
            # Campos exclusivos do detalhe
            ementa_detalhada=p.ementa_detalhada,
            justificativa=p.justificativa,
            urn_final=p.urn_final,
            tramitacoes=[
                TramitacaoItem(
                    id=t.id,
                    data_hora=t.data_hora,
                    sequencia=t.sequencia,
                    sigla_orgao=t.sigla_orgao,
                    regime=t.regime,
                    descricao_tramitacao=t.descricao_tramitacao,
                    descricao_situacao=t.descricao_situacao,
                    despacho=t.despacho,
                    ambito=t.ambito,
                    apreciacao=t.apreciacao,
                )
                for t in p.tramitacoes  # já ordenadas por data_hora (order_by no modelo)
            ],
        )

    # ------------------------------------------------------------------
    # Proposições — votações de uma proposição
    # ------------------------------------------------------------------

    async def get_votacoes_da_proposicao_repo(
        self,
        proposicao_id: int,
    ) -> list[VotacaoResponse]:
        """
        Retorna todas as votações vinculadas a uma proposição específica.

        Caso a proposição não exista ou não tenha votações, retorna lista vazia.
        O serviço é responsável por verificar se a proposição existe (404).
        """
        stmt = (
            select(
                Votacao.id,
                Votacao.id_camara,
                Votacao.data,
                Votacao.data_hora_registro,
                Votacao.tipo_votacao,
                Votacao.descricao,
                Votacao.aprovacao,
                Votacao.sigla_orgao,
                # Campos da proposição (desnormalizados para o response)
                Proposicao.id.label("proposicao_id"),
                Proposicao.sigla_tipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
            )
            .join(Proposicao, Votacao.proposicao_id == Proposicao.id)
            .where(Votacao.proposicao_id == proposicao_id)
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
        """
        Lista votações com filtros opcionais e paginação.

        Filtros:
          ano        — ano da votação
          aprovacao  — resultado: 1 (aprovada), 0 (rejeitada), -1 (indefinido)
          sigla_tipo — filtra pelo tipo da proposição vinculada ("PL", "PEC"...)

        Faz JOIN com Proposicao para desnormalizar os campos da proposição
        no response, evitando um segundo request do frontend.

        O JOIN é LEFT OUTER para não excluir votações sem proposição vinculada
        (casos onde proposicao_id é NULL no banco).
        """
        safe_limit  = min(abs(limit), _MAX_LIMIT_VOTACOES)
        safe_offset = max(offset, 0)

        stmt = (
            select(
                Votacao.id,
                Votacao.id_camara,
                Votacao.data,
                Votacao.data_hora_registro,
                Votacao.tipo_votacao,
                Votacao.descricao,
                Votacao.aprovacao,
                Votacao.sigla_orgao,
                Proposicao.id.label("proposicao_id"),
                Proposicao.sigla_tipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
            )
            .outerjoin(Proposicao, Votacao.proposicao_id == Proposicao.id)
            .order_by(desc(Votacao.data))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        if ano is not None:
            stmt = stmt.where(func.extract("year", Votacao.data) == ano)
        if aprovacao is not None:
            stmt = stmt.where(Votacao.aprovacao == aprovacao)
        if sigla_tipo:
            # Filtra pelo tipo da proposição vinculada
            stmt = stmt.where(Proposicao.sigla_tipo == sigla_tipo.upper()[:10])

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
        """
        Retorna o detalhe completo de uma votação pelo ID interno.

        Inclui:
          - Todos os campos de VotacaoResponse
          - orientacoes: como cada partido/bloco orientou o voto

        Usa duas queries separadas:
          1. SELECT na votacao + JOIN proposicao (para os campos desnormalizados)
          2. SELECT nas orientacoes_votacao (para não gerar produto cartesiano)

        Retorna None se não encontrado (o serviço lança 404).
        """
        # ── Query 1: dados da votação + proposição ──────────────────────
        stmt_votacao = (
            select(
                Votacao.id,
                Votacao.id_camara,
                Votacao.data,
                Votacao.data_hora_registro,
                Votacao.tipo_votacao,
                Votacao.descricao,
                Votacao.aprovacao,
                Votacao.sigla_orgao,
                Proposicao.id.label("proposicao_id"),
                Proposicao.sigla_tipo.label("proposicao_sigla"),
                Proposicao.numero.label("proposicao_numero"),
                Proposicao.ano.label("proposicao_ano"),
                Proposicao.ementa.label("proposicao_ementa"),
            )
            .outerjoin(Proposicao, Votacao.proposicao_id == Proposicao.id)
            .where(Votacao.id == votacao_id)
        )

        # ── Query 2: orientações por partido ────────────────────────────
        stmt_orientacoes = (
            select(
                OrientacaoVotacao.sigla_partido_bloco,
                OrientacaoVotacao.cod_tipo_lideranca,
                OrientacaoVotacao.orientacao_voto,
            )
            .where(OrientacaoVotacao.votacao_id == votacao_id)
            .order_by(OrientacaoVotacao.sigla_partido_bloco)
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
                cod_tipo_lideranca=o.cod_tipo_lideranca,
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