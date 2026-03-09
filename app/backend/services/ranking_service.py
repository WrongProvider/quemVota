"""
Servico de Rankings - Camada de logica de negocio.

Seguranca (OWASP):
  - A01 / Broken Access Control: limites de paginacao reforçados como segunda linha de defesa.
  - A03 / Sensitive Data Exposure: excecoes internas nao vazam stack traces para a API.
  - A04 / Insecure Design: constantes nomeadas; calculo de score isolado em performance_calc.py.
  - A06 / Vulnerable Components: logica de negocio isolada do transporte HTTP.
"""

import asyncio
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
        self._repo = RankingRepository(db)

    @property
    def _cache(self):
        # Lazy: obtém o backend somente quando necessário, evitando falha
        # se FastAPICache ainda não estiver inicializado (ex: testes, startup).
        return FastAPICache.get_backend()

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
        Calcula e ordena o ranking de performance com normalização por ano.

        Para cada parlamentar:
          1. Busca a timeline anual (via get_timeline_data_batch — sem N+1).
          2. Calcula calcular_score() para cada ano individualmente.
          3. O score final é a média dos scores anuais — comparação justa
             independente do tamanho do mandato.

        Campos adicionais por parlamentar:
          - anos_com_dados : int  — quantos anos têm dados de despesas
          - confianca      : str  — "baixa" (1 ano) | "media" (2-3) | "alta" (4+)
        """
        # 1. Busca todos os deputados elegíveis (query leve)
        deputados = await self._repo.get_todos_deputados_ids()
        if not deputados:
            return []

        dep_map = {d["id"]: d for d in deputados}
        ids     = list(dep_map.keys())

        # 2. Busca timelines em batch (6 queries no total, independente do nº de deputados)
        timelines = await self._repo.get_timeline_data_batch(ids)

        # 3. Calcula score médio por parlamentar
        ranking = []
        for dep_id, entradas in timelines.items():
            if not entradas:
                continue

            dep  = dep_map[dep_id]
            anos = len(entradas)

            scores_anuais = []
            notas_por_dim: dict[str, list[float]] = {
                "assiduidade": [], "economia": [], "producao": []
            }

            for entrada in entradas:
                raw = {**entrada["raw"], **dep}
                calc = calcular_score(raw)
                scores_anuais.append(calc["score"])
                notas_por_dim["assiduidade"].append(calc["notas"]["assiduidade"])
                notas_por_dim["economia"].append(calc["notas"]["economia"])
                notas_por_dim["producao"].append(calc["notas"]["producao"])

            score_medio = round(sum(scores_anuais) / anos, 2)

            if anos >= 4:
                confianca = "alta"
            elif anos >= 2:
                confianca = "media"
            else:
                confianca = "baixa"

            ranking.append({
                "id":      dep_id,
                "nome":    dep["nome"],
                "uf":      dep["siglaUF"],
                "partido": dep["siglaPartido"],
                "foto":    dep["urlFoto"],
                "score":   score_medio,
                "notas": {
                    "assiduidade": round(sum(notas_por_dim["assiduidade"]) / anos, 2),
                    "economia":    round(sum(notas_por_dim["economia"])    / anos, 2),
                    "producao":    round(sum(notas_por_dim["producao"])    / anos, 2),
                },
                "anos_com_dados": anos,
                "confianca":      confianca,
            })

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