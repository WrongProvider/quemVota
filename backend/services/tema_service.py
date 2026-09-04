"""
tema_service.py — Serviço de consulta dos Temas de Atuação Parlamentar (SPEC-001).

Responsabilidades:
  - Validar existência do deputado (por ID ou slug).
  - Consultar deputadoTemasAtuacao + temasAtuacao.
  - Retornar PoliticoTemasResponse com ranking normalizado.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.politico_repository import PoliticoRepository
from backend.schemas import PoliticoTemasResponse, TemaAtuacaoItemResponse
from shared.models_vetorial import DeputadoTemaAtuacao, TemaAtuacao

logger = logging.getLogger(__name__)

_MAX_LIMIT_TEMAS = 20
_LEGISLATURA_PADRAO = 57


class TemaService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = PoliticoRepository(db)

    async def _resolver_deputado(self, id_or_slug: str):
        """Resolve um deputado por ID numérico ou slug. Levanta 404 se não encontrado."""
        if id_or_slug.isdigit():
            pol = await self._repo.get_politico_repo(int(id_or_slug))
        else:
            pol = await self._repo.get_politico_by_slug_repo(id_or_slug)

        if pol is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parlamentar '{id_or_slug}' não encontrado.",
            )
        return pol

    async def get_temas_atuacao_service(
        self,
        id_or_slug: str,
        id_legislatura: int = _LEGISLATURA_PADRAO,
        limit: int = 10,
    ) -> PoliticoTemasResponse:
        """
        Retorna o ranking temático de atuação do parlamentar.

        Fonte: tabela deputadoTemasAtuacao populada pelo pipeline tasks/classificar_temas.py.
        Levanta 404 se o parlamentar não existe ou se o pipeline ainda não foi executado.
        """
        safe_limit = min(abs(limit), _MAX_LIMIT_TEMAS)
        pol = await self._resolver_deputado(id_or_slug)

        stmt = (
            select(
                DeputadoTemaAtuacao.score,
                DeputadoTemaAtuacao.pesoTotal,
                DeputadoTemaAtuacao.rank,
                TemaAtuacao.id.label("id_tema"),
                TemaAtuacao.slug,
                TemaAtuacao.nome,
            )
            .join(TemaAtuacao, TemaAtuacao.id == DeputadoTemaAtuacao.idTemaAtuacao)
            .where(DeputadoTemaAtuacao.idDeputado == pol.id)
            .where(DeputadoTemaAtuacao.idLegislatura == id_legislatura)
            .order_by(DeputadoTemaAtuacao.rank)
            .limit(safe_limit)
        )

        result = await self._db.execute(stmt)
        rows = result.all()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Dados de temas de atuação não disponíveis para o parlamentar id={pol.id} "
                    f"na legislatura {id_legislatura}. "
                    "Execute o pipeline tasks/classificar_temas.py para processar este parlamentar."
                ),
            )

        temas = [
            TemaAtuacaoItemResponse(
                id_tema=r.id_tema,
                slug=r.slug,
                nome=r.nome,
                score=float(r.score),
                percentual=round(float(r.score) * 100, 2),
                peso_total=float(r.pesoTotal),
                rank=r.rank,
            )
            for r in rows
        ]

        return PoliticoTemasResponse(
            id_deputado=pol.id,
            id_legislatura=id_legislatura,
            total_temas_identificados=len(temas),
            temas=temas,
        )
