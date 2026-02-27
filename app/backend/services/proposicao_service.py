"""
Serviço de Proposições e Votações — Camada de lógica de negócio.

Responsabilidades desta camada:
  - Aplicar limites de paginação como segunda linha de defesa
    (o repositório também limita, mas o serviço garante que valores
    inválidos nunca chegam ao banco)
  - Converter ausência de dado (None) em HTTP 404 — o repositório
    retorna None, o serviço lança HTTPException
  - Sanitizar e normalizar parâmetros de entrada antes de repassar
    ao repositório (ex: sigla_tipo sempre em maiúsculas)
  - Isolar a camada HTTP de qualquer detalhe de infraestrutura

Segurança (OWASP):
  - A01 / Broken Access Control: somente leitura; nenhuma operação
    de escrita exposta.
  - A03 / Sensitive Data Exposure: exceções internas não vazam stack
    traces para a API; apenas mensagens controladas chegam ao cliente.
  - A04 / Insecure Design: limites de paginação reforçados aqui como
    segunda linha de defesa — o repositório também os aplica.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.proposicao_repository import ProposicaoRepository
from backend.schemas import (
    ProposicaoDetalhe,
    ProposicaoResponse,
    VotacaoDetalhe,
    VotacaoResponse,
)

logger = logging.getLogger(__name__)

# Limites máximos — segunda linha de defesa (repositório também limita)
_MAX_LIMIT_PROPOSICOES = 100
_MAX_LIMIT_VOTACOES    = 100


class ProposicaoService:
    """
    Orquestra as regras de negócio de proposições e votações.

    Não expõe detalhes de infraestrutura (SQL, ORM) para a camada HTTP.
    Recebe AsyncSession via injeção de dependência do FastAPI.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = ProposicaoRepository(db)

    # ------------------------------------------------------------------
    # Proposições — listagem
    # ------------------------------------------------------------------

    async def listar_proposicoes_service(
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
        Lista proposições com filtros e paginação.

        Parâmetros:
          q          — texto livre buscado na ementa
          sigla_tipo — tipo da proposição ("PL", "PEC", "MPV", etc.)
                       normalizado para maiúsculas antes do repasse
          ano        — ano de apresentação da proposição
          tema_id    — filtra por tema legislativo (ID interno)
          limit      — máximo de itens (cap: 100)
          offset     — deslocamento para paginação

        Retorna lista vazia se nenhum resultado for encontrado
        (não lança 404 — ausência de resultados é válida em listagens).
        """
        safe_limit  = min(abs(limit), _MAX_LIMIT_PROPOSICOES)
        safe_offset = max(offset, 0)

        # Normaliza sigla para maiúsculas — evita bypass de filtro
        sigla_normalizada = sigla_tipo.upper().strip() if sigla_tipo else None

        logger.info(
            "Listando proposições | q=%s sigla_tipo=%s ano=%s tema_id=%s limit=%s offset=%s",
            q, sigla_normalizada, ano, tema_id, safe_limit, safe_offset,
        )

        return await self._repo.listar_proposicoes_repo(
            q=q,
            sigla_tipo=sigla_normalizada,
            ano=ano,
            tema_id=tema_id,
            limit=safe_limit,
            offset=safe_offset,
        )

    # ------------------------------------------------------------------
    # Proposições — detalhe
    # ------------------------------------------------------------------

    async def get_proposicao_service(self, proposicao_id: int) -> ProposicaoDetalhe:
        """
        Retorna o detalhe completo de uma proposição.

        Inclui tramitação, autores e temas.
        Lança HTTP 404 se a proposição não existir.
        """
        logger.info("Detalhe da proposição id=%s", proposicao_id)

        proposicao = await self._repo.get_proposicao_repo(proposicao_id)

        if proposicao is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposição não encontrada.",
            )

        return proposicao

    # ------------------------------------------------------------------
    # Proposições — votações de uma proposição
    # ------------------------------------------------------------------

    async def get_votacoes_da_proposicao_service(
        self, proposicao_id: int
    ) -> list[VotacaoResponse]:
        """
        Retorna todas as votações vinculadas a uma proposição.

        Primeiro verifica se a proposição existe (404 se não).
        Retorna lista vazia se a proposição existe mas não tem votações —
        isso é válido (proposição em tramitação, por exemplo).
        """
        logger.info("Votações da proposição id=%s", proposicao_id)

        # Garante que a proposição existe antes de buscar votações
        # Reutiliza o método de detalhe — lança 404 automaticamente
        await self.get_proposicao_service(proposicao_id)

        return await self._repo.get_votacoes_da_proposicao_repo(proposicao_id)

    # ------------------------------------------------------------------
    # Votações — listagem
    # ------------------------------------------------------------------

    async def listar_votacoes_service(
        self,
        *,
        ano: int | None = None,
        aprovacao: int | None = None,
        sigla_tipo: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[VotacaoResponse]:
        """
        Lista votações com filtros e paginação.

        Parâmetros:
          ano        — ano da votação
          aprovacao  — resultado: 1 (aprovada), 0 (rejeitada), -1 (indefinido)
          sigla_tipo — tipo da proposição vinculada ("PL", "PEC"...)
          limit      — máximo de itens (cap: 100)
          offset     — deslocamento para paginação

        Valida o campo `aprovacao` — aceita apenas 1, 0 ou -1.
        Retorna lista vazia se nenhum resultado for encontrado.
        """
        safe_limit  = min(abs(limit), _MAX_LIMIT_VOTACOES)
        safe_offset = max(offset, 0)

        # Valida aprovacao — valor fora do domínio causa confusão silenciosa
        if aprovacao is not None and aprovacao not in (1, 0, -1):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="O parâmetro 'aprovacao' deve ser 1 (aprovada), 0 (rejeitada) ou -1 (indefinido).",
            )

        sigla_normalizada = sigla_tipo.upper().strip() if sigla_tipo else None

        logger.info(
            "Listando votações | ano=%s aprovacao=%s sigla_tipo=%s limit=%s offset=%s",
            ano, aprovacao, sigla_normalizada, safe_limit, safe_offset,
        )

        return await self._repo.listar_votacoes_repo(
            ano=ano,
            aprovacao=aprovacao,
            sigla_tipo=sigla_normalizada,
            limit=safe_limit,
            offset=safe_offset,
        )

    # ------------------------------------------------------------------
    # Votações — detalhe
    # ------------------------------------------------------------------

    async def get_votacao_service(self, votacao_id: int) -> VotacaoDetalhe:
        """
        Retorna o detalhe completo de uma votação.

        Inclui orientações por partido/bloco.
        Lança HTTP 404 se a votação não existir.
        """
        logger.info("Detalhe da votação id=%s", votacao_id)

        votacao = await self._repo.get_votacao_repo(votacao_id)

        if votacao is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Votação não encontrada.",
            )

        return votacao