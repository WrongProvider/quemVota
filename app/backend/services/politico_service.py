"""
Serviço de Políticos — Camada de lógica de negócio.

Segurança (OWASP):
  - A01 / Broken Access Control: IDs são validados antes de qualquer operação.
  - A03 / Sensitive Data Exposure: exceções internas não vazam stack traces para
    a API; apenas mensagens controladas chegam ao cliente.
  - A04 / Insecure Design: limites de paginação são reforçados aqui como segunda
    linha de defesa (o repositório também os aplica).
  - A06 / Vulnerable Components: nenhuma dependência desnecessária; lógica de
    negócio isolada do transporte HTTP.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.repositories.politico_repository import PoliticoRepository
from backend.schemas import PoliticoResponse
from .ranking_service import RankingService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cotas mensais por UF — fonte: Câmara dos Deputados 2025
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
_COTA_PADRAO = 40_000.0  # fallback conservador

# Pesos do score de performance
_PESO_ASSIDUIDADE = 0.15
_PESO_ECONOMIA = 0.40
_PESO_PRODUCAO = 0.45

# Meta de proposições por mês para nota máxima
_META_PROPOSICOES_MES = 2

# Limites de paginação (segunda linha de defesa)
_MAX_LIMIT_POLITICOS = 600
_MAX_LIMIT_VOTACOES = 20
_MAX_LIMIT_DESPESAS = 20
_MAX_LIMIT_RESUMO = 60


def _resolve_cota_mensal(uf: str | None) -> float:
    """Retorna a cota mensal para a UF, com fallback seguro."""
    if uf and uf.upper() in _COTAS_POR_UF:
        return _COTAS_POR_UF[uf.upper()]
    return _COTA_PADRAO


class PoliticoService:
    """
    Orquestra as regras de negócio de políticos.

    Não expõe detalhes de infraestrutura (SQL, ORM) para a camada HTTP.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = PoliticoRepository(db)
        self._db = db

    # ------------------------------------------------------------------
    # Listagem
    # ------------------------------------------------------------------

    async def get_politicos_service(
        self,
        *,
        limit: int = 100,
        q: str | None = None,
        uf: str | None = None,
        offset: int = 0,
    ) -> list[PoliticoResponse]:
        safe_limit = min(abs(limit), _MAX_LIMIT_POLITICOS)
        safe_offset = max(offset, 0)

        politicos = await self._repo.get_politicos_repo(
            q=q, uf=uf, limit=safe_limit, offset=safe_offset
        )
        return [PoliticoResponse.model_validate(p) for p in politicos]

    # ------------------------------------------------------------------
    # Detalhe
    # ------------------------------------------------------------------

    async def get_politicos_detalhe_service(self, politico_id: int) -> PoliticoResponse:
        politico = await self._repo.get_politico_repo(politico_id)
        if not politico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Político não encontrado.",
            )
        return PoliticoResponse.model_validate(politico)

    # ------------------------------------------------------------------
    # Votações
    # ------------------------------------------------------------------

    async def get_politicos_votacoes_service(
        self, politico_id: int, limit: int = 20
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_VOTACOES)
        return await self._repo.get_politicos_votacoes_repo(
            politico_id=politico_id, limit=safe_limit
        )

    # ------------------------------------------------------------------
    # Despesas
    # ------------------------------------------------------------------

    async def get_politicos_despesas_services(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        mes: int | None = None,
        limit: int = 20,
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_DESPESAS)
        return await self._repo.get_politicos_despesas_repo(
            politico_id=politico_id, ano=ano, mes=mes, limit=safe_limit
        )

    async def get_politicos_despesas_resumo_services(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit: int = 60,
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_RESUMO)
        return await self._repo.get_politicos_despesas_resumo_repo(
            politico_id=politico_id, ano=ano, limit=safe_limit
        )

    async def get_politicos_despesas_resumo_completo_services(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
        limit_meses: int = 60,
    ):
        safe_limit = min(abs(limit_meses), _MAX_LIMIT_RESUMO)
        return await self._repo.get_politicos_despesas_resumo_completo_repo(
            politico_id=politico_id, ano=ano, limit_meses=safe_limit
        )

    # ------------------------------------------------------------------
    # Estatísticas
    # ------------------------------------------------------------------

    async def get_politico_estatisticas_service(self, politico_id: int):
        return await self._repo.get_politicos_estatisticas_repo(politico_id)

    # ------------------------------------------------------------------
    # Performance
    # ------------------------------------------------------------------

    async def get_politico_performance_service(self, politico_id: int) -> dict:
        """
        Calcula o score de performance do parlamentar.

        Fórmula:
          score = assiduidade × 15% + economia × 40% + produção × 45%

        Lança HTTP 404 se o político não existir.
        """
        data = await self._repo.get_politico_performance_data(politico_id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Político não encontrado.",
            )

        # 1. Assiduidade (0–100)
        nota_assiduidade = (data["presencas"] / data["total_sessoes"]) * 100

        # 2. Economia (0–100)
        cota_mensal = _resolve_cota_mensal(data.get("uf"))
        cota_total = cota_mensal * data["meses_mandato"]
        economia_ratio = (cota_total - data["total_gasto"]) / cota_total
        nota_economia = max(0.0, economia_ratio * 100)

        # 3. Produção (0–100, capped)
        meta_producao = data["meses_mandato"] * _META_PROPOSICOES_MES
        nota_producao = (
            min((data["total_proposicoes"] / meta_producao) * 100, 100.0)
            if meta_producao > 0
            else 0.0
        )

        score_final = (
            nota_assiduidade * _PESO_ASSIDUIDADE
            + nota_economia * _PESO_ECONOMIA
            + nota_producao * _PESO_PRODUCAO
        )

        media_global = await RankingService(self._db).get_media_global_cached()

        return {
            "politico_id": politico_id,
            "score_final": round(score_final, 2),
            "media_global": round(media_global, 2),
            "detalhes": {
                "nota_assiduidade": round(nota_assiduidade, 2),
                "nota_economia": round(nota_economia, 2),
                "nota_producao": round(nota_producao, 2),
            },
            "info": {
                "valor_cota_mensal": cota_mensal,
                "total_gasto": data["total_gasto"],
                "cota_utilizada_pct": round(
                    (data["total_gasto"] / cota_total) * 100, 2
                ),
            },
        }
