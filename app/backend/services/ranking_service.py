"""
Servico de Rankings - Camada de logica de negocio.

Seguranca (OWASP):
  - A01 / Broken Access Control: limites de paginacao reforçados como segunda linha de defesa.
  - A03 / Sensitive Data Exposure: excecoes internas nao vazam stack traces para a API.
  - A04 / Insecure Design: constantes nomeadas; calculo de score isolado em performance_calc.py.
  - A06 / Vulnerable Components: logica de negocio isolada do transporte HTTP.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache import FastAPICache

from backend.repositories.ranking_repository import RankingRepository
from backend.services.performance_calc import calcular_score  # ← fonte única da verdade

logger = logging.getLogger(__name__)

# Limites de paginacao (segunda linha de defesa)
_MAX_LIMIT_RANKING   = 100
_MAX_LIMIT_DISCURSOS = 500

# TTL do cache da media global (24h)
_CACHE_MEDIA_GLOBAL_KEY = "media_global_score"
_CACHE_MEDIA_GLOBAL_TTL = 86_400


class RankingService:
    """Orquestra as regras de negocio dos rankings. Nao expoe infraestrutura para a camada HTTP."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo  = RankingRepository(db)
        self._cache = FastAPICache.get_backend()

    # ------------------------------------------------------------------
    # Rankings de despesas
    # ------------------------------------------------------------------

    async def get_ranking_despesas_politicos(
        self,
        *,
        limit: int = 100,
        q: str | None = None,
        uf: str | None = None,
        offset: int = 0,
    ):
        safe_limit  = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)
        return await self._repo.get_ranking_despesas_politicos(
            q=q, uf=uf, limit=safe_limit, offset=safe_offset
        )

    # ------------------------------------------------------------------
    # Rankings de empresas
    # ------------------------------------------------------------------

    async def get_ranking_lucro_empresas(self, *, limit: int = 100, offset: int = 0):
        safe_limit  = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)
        return await self._repo.get_ranking_lucro_empresas(limit=safe_limit, offset=safe_offset)

    # ------------------------------------------------------------------
    # Rankings de discursos
    # ------------------------------------------------------------------

    async def get_ranking_discursos_politicos(self, *, limit: int = 100, offset: int = 0):
        safe_limit  = min(abs(limit), _MAX_LIMIT_DISCURSOS)
        safe_offset = max(offset, 0)
        return await self._repo.get_ranking_discursos_politicos(limit=safe_limit, offset=safe_offset)

    # ------------------------------------------------------------------
    # Rankings de performance
    # ------------------------------------------------------------------

    async def get_ranking_performance_politicos(self) -> list[dict]:
        """
        Calcula e ordena o ranking de performance de todos os politicos.
        O calculo do score usa performance_calc.calcular_score — mesma logica
        que o endpoint individual /politicos/{id}/performance.
        """
        raw_data = await self._repo.get_ranking_performance_politicos()
        ranking  = [calcular_score(dict(p)) for p in raw_data]
        ranking.sort(key=lambda x: x["score"], reverse=True)
        return ranking

    # ------------------------------------------------------------------
    # Media global (com cache manual)
    # ------------------------------------------------------------------

    async def get_media_global_cached(self) -> float:
        """
        Retorna a media global dos scores com cache de 24h.
        Evita recalcular o ranking completo a cada requisicao de performance individual.
        """
        media = await self._cache.get(_CACHE_MEDIA_GLOBAL_KEY)

        if media is None:
            ranking = await self.get_ranking_performance_politicos()
            if not ranking:
                return 0.0
            media = sum(p["score"] for p in ranking) / len(ranking)
            await self._cache.set(
                _CACHE_MEDIA_GLOBAL_KEY, media, expire=_CACHE_MEDIA_GLOBAL_TTL
            )
            logger.info("Media global recalculada: %.2f", media)

        return float(media)