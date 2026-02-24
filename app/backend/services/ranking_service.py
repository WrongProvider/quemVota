"""
Servico de Rankings - Camada de logica de negocio.

Seguranca (OWASP):
  - A01 / Broken Access Control: limites de paginacao reforçados como segunda linha de defesa.
  - A03 / Sensitive Data Exposure: excecoes internas nao vazam stack traces para a API.
  - A04 / Insecure Design: constantes nomeadas; calculo de score isolado e testavel.
  - A06 / Vulnerable Components: logica de negocio isolada do transporte HTTP.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache import FastAPICache

from backend.repositories.ranking_repository import RankingRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cotas mensais por UF - fonte: Camara dos Deputados 2025
# ---------------------------------------------------------------------------
_COTAS_POR_UF: dict[str, float] = {
    "AC": 50426.26, "AL": 46737.90, "AM": 49363.92, "AP": 49168.58,
    "BA": 44804.65, "CE": 48245.57, "DF": 36582.46, "ES": 43217.71,
    "GO": 41300.86, "MA": 47945.49, "MG": 41886.51, "MS": 46336.64,
    "MT": 45221.83, "PA": 48021.25, "PB": 47826.36, "PE": 47470.60,
    "PI": 46765.57, "PR": 44665.66, "RJ": 41553.77, "RN": 48525.79,
    "RO": 49466.29, "RR": 51406.33, "RS": 46669.70, "SC": 45671.58,
    "SE": 45933.06, "SP": 42837.33, "TO": 45297.41,
}
_COTA_PADRAO = 40_000.0

# Pesos do score de performance
_PESO_ASSIDUIDADE = 0.15
_PESO_ECONOMIA = 0.40
_PESO_PRODUCAO = 0.45

# Meta de pontos de producao por mes para nota maxima
_META_PRODUCAO_MES = 2.0

# Limites de paginacao (segunda linha de defesa)
_MAX_LIMIT_RANKING = 100
_MAX_LIMIT_DISCURSOS = 500

# TTL do cache da media global (24h)
_CACHE_MEDIA_GLOBAL_KEY = "media_global_score"
_CACHE_MEDIA_GLOBAL_TTL = 86400


def _resolve_cota_mensal(uf: str | None) -> float:
    """Retorna a cota mensal para a UF, com fallback seguro."""
    if uf and uf.upper() in _COTAS_POR_UF:
        return _COTAS_POR_UF[uf.upper()]
    return _COTA_PADRAO


def _calcular_score(p: dict) -> dict:
    """
    Calcula o score de performance de um politico a partir dos dados brutos do repositorio.
    Retorna o dict formatado para a resposta da API.
    """
    meses = max(int(p["meses_mandato"]), 1)

    # 1. Assiduidade (0-100) - ja vem calculada do SQL
    nota_assiduidade = float(p["nota_assiduidade"])

    # 2. Producao (0-100, capped)
    meta_producao = meses * _META_PRODUCAO_MES
    nota_producao = (
        min((float(p["pontos_producao"]) / meta_producao) * 100, 100.0)
        if meta_producao > 0
        else 0.0
    )

    # 3. Economia (0-100)
    cota_mensal = _resolve_cota_mensal(p["uf"])
    cota_total = cota_mensal * meses
    gasto = float(p["total_gasto"])
    nota_economia = (
        max(0.0, ((cota_total - gasto) / cota_total) * 100)
        if cota_total > 0
        else 0.0
    )

    score_final = (
        nota_assiduidade * _PESO_ASSIDUIDADE
        + nota_economia * _PESO_ECONOMIA
        + nota_producao * _PESO_PRODUCAO
    )

    return {
        "id": p["id"],
        "nome": p["nome"],
        "uf": p["uf"],
        "partido": p["partido_sigla"],
        "foto": p["url_foto"],
        "score": round(score_final, 2),
        "notas": {
            "assiduidade": round(nota_assiduidade, 2),
            "producao": round(nota_producao, 2),
            "economia": round(nota_economia, 2),
        },
    }


class RankingService:
    """Orquestra as regras de negocio dos rankings. Nao expoe infraestrutura para a camada HTTP."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = RankingRepository(db)
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
        safe_limit = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)
        return await self._repo.get_ranking_despesas_politicos(
            q=q, uf=uf, limit=safe_limit, offset=safe_offset
        )

    # ------------------------------------------------------------------
    # Rankings de empresas
    # ------------------------------------------------------------------

    async def get_ranking_lucro_empresas(self, *, limit: int = 100, offset: int = 0):
        safe_limit = min(abs(limit), _MAX_LIMIT_RANKING)
        safe_offset = max(offset, 0)
        return await self._repo.get_ranking_lucro_empresas(limit=safe_limit, offset=safe_offset)

    # ------------------------------------------------------------------
    # Rankings de discursos
    # ------------------------------------------------------------------

    async def get_ranking_discursos_politicos(self, *, limit: int = 100, offset: int = 0):
        safe_limit = min(abs(limit), _MAX_LIMIT_DISCURSOS)
        safe_offset = max(offset, 0)
        return await self._repo.get_ranking_discursos_politicos(limit=safe_limit, offset=safe_offset)

    # ------------------------------------------------------------------
    # Rankings de performance
    # ------------------------------------------------------------------

    async def get_ranking_performance_politicos(self) -> list[dict]:
        """
        Calcula e ordena o ranking de performance de todos os politicos.
        O calculo do score e feito aqui no servico, nao no repositorio.
        """
        raw_data = await self._repo.get_ranking_performance_politicos()
        ranking = [_calcular_score(p) for p in raw_data]
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
            await self._cache.set(_CACHE_MEDIA_GLOBAL_KEY, media, expire=_CACHE_MEDIA_GLOBAL_TTL)
            logger.info("Media global recalculada: %.2f", media)

        return float(media)