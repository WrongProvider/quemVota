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

    async def get_ranking_performance_politicos(
        self,
        *,
        ano: int | None = None,
        q: str | None = None,
        uf: str | None = None,
        partido: str | None = None,
    ) -> list[dict]:
        """
        Calcula e ordena o ranking de performance com normalização por ano.

        Quando `ano` é fornecido, o ranking é calculado **exclusivamente** para
        aquele ano — todos os parlamentares são comparados no mesmo período,
        eliminando a vantagem de deputados com mandatos mais longos.

        Quando `ano` é None, o comportamento padrão é mantido: score médio
        sobre todos os anos com dados (média de mandato).

        Para cada parlamentar:
          1. Busca a timeline anual filtrada por ano se fornecido.
          2. Calcula calcular_score() para cada entrada anual.
          3. O score final é a média dos scores anuais — ou o score do ano
             específico quando `ano` é passado.

        Filtros disponíveis:
          - ano     : restringe o ranking a um único ano calendário
          - q       : busca parcial por nome (case-insensitive)
          - uf      : sigla do estado (ex: "SP", "RJ")
          - partido : sigla do partido (ex: "PT", "PL")
        """
        # 1. Busca todos os deputados elegíveis — com filtros aplicados
        deputados = await self._repo.get_todos_deputados_ids(
            q=q, uf=uf, partido=partido, ano=ano
        )
        if not deputados:
            return []

        dep_map = {d["id"]: d for d in deputados}
        ids     = list(dep_map.keys())

        # 2. Busca timelines em batch, restringindo ao ano se fornecido
        timelines = await self._repo.get_timeline_data_batch(ids, ano=ano)

        # 3. Calcula score médio (ou do ano específico) por parlamentar
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

            entry: dict = {
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
            }

            # Quando o ranking é filtrado por ano, expõe o ano de referência
            # para que o cliente saiba exatamente qual período está sendo exibido.
            if ano is not None:
                entry["ano_referencia"] = ano

            ranking.append(entry)

        ranking.sort(key=lambda x: x["score"], reverse=True)
        return ranking

    # ------------------------------------------------------------------
    # Media global (com cache manual)
    # ------------------------------------------------------------------

    async def get_media_global_cached(self, *, ano: int | None = None) -> float:
        """
        Retorna a media global dos scores com cache de 24h.
        Evita recalcular o ranking completo a cada requisicao de performance individual.
        A chave de cache é diferenciada por ano para evitar colisão entre períodos.
        """
        cache_key = f"{_CACHE_MEDIA_GLOBAL_KEY}:{ano}" if ano is not None else _CACHE_MEDIA_GLOBAL_KEY
        media = await self._cache.get(cache_key)

        if media is None:
            ranking = await self.get_ranking_performance_politicos(ano=ano)
            if not ranking:
                return 0.0
            media = sum(p["score"] for p in ranking) / len(ranking)
            await self._cache.set(cache_key, media, expire=_CACHE_MEDIA_GLOBAL_TTL)
            logger.info("Media global recalculada (ano=%s): %.2f", ano, media)

        return float(media)