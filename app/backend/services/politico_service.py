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
from backend.repositories.ranking_repository import RankingRepository
from backend.schemas import PoliticoResponse
from backend.services.performance_calc import calcular_score, resolve_cota_mensal
from .ranking_service import RankingService

logger = logging.getLogger(__name__)

# Limites de paginação (segunda linha de defesa)
_MAX_LIMIT_POLITICOS = 600
_MAX_LIMIT_VOTACOES  = 20
_MAX_LIMIT_DESPESAS  = 20
_MAX_LIMIT_RESUMO    = 60


class PoliticoService:
    """
    Orquestra as regras de negócio de políticos.
    Não expõe detalhes de infraestrutura (SQL, ORM) para a camada HTTP.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo         = PoliticoRepository(db)
        self._ranking_repo = RankingRepository(db)
        self._db           = db

    # ------------------------------------------------------------------
    # Listagem
    # ------------------------------------------------------------------

    async def get_politicos_service(
        self,
        *,
        limit: int = 100,
        q: str | None = None,
        uf: str | None = None,
        partido: str | None = None,
        offset: int = 0,
    ) -> list[PoliticoResponse]:
        safe_limit  = min(abs(limit), _MAX_LIMIT_POLITICOS)
        safe_offset = max(offset, 0)
        politicos   = await self._repo.get_politicos_repo(
            q=q, uf=uf, partido=partido, limit=safe_limit, offset=safe_offset
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
        self,
        politico_id: int,
        *,
        limit: int = 20,
        ano: int | None = None,
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_VOTACOES)
        return await self._repo.get_politicos_votacoes_repo(
            politico_id=politico_id, limit=safe_limit, ano=ano
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
    # Estatísticas — agora com filtro de ano
    # ------------------------------------------------------------------

    async def get_politico_estatisticas_service(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
    ):
        """
        Retorna estatísticas gerais do parlamentar.

        Args:
            politico_id: ID do parlamentar.
            ano: quando fornecido, filtra votações e despesas pelo ano,
                 permitindo comparação justa na linha do tempo.
        """
        return await self._repo.get_politicos_estatisticas_repo(
            politico_id, ano=ano
        )

    # ------------------------------------------------------------------
    # Performance — agora com filtro de ano
    # ------------------------------------------------------------------

    async def get_politico_performance_service(
        self,
        politico_id: int,
        *,
        ano: int | None = None,
    ) -> dict:
        """
        Calcula o score de performance do parlamentar.

        Usa calcular_score() de performance_calc.py — mesma função do
        RankingService — garantindo números idênticos ao ranking geral
        quando ano=None.

        Args:
            politico_id: ID do parlamentar.
            ano: quando fornecido, o score reflete apenas aquele ano,
                 possibilitando comparação justa na linha do tempo.

        Fórmula:
            score = assiduidade × 15% + economia × 40% + produção × 45%

        Lança HTTP 404 se o político não existir.
        """
        politico = await self._repo.get_politico_repo(politico_id)
        if not politico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Político não encontrado.",
            )

        raw_row = await self._ranking_repo.get_performance_data_by_id(
            politico_id, ano=ano
        )
        if not raw_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dados de performance não encontrados para este político.",
            )

        result = calcular_score(raw_row)
        meta   = result.pop("_meta")

        media_global = await RankingService(self._db).get_media_global_cached()

        return {
            "politico_id":  politico_id,
            "ano":          ano,           # None = mandato inteiro
            "score_final":  result["score"],
            "media_global": round(media_global, 2),
            "detalhes": {
                "nota_assiduidade": result["notas"]["assiduidade"],
                "nota_economia":    result["notas"]["economia"],
                "nota_producao":    result["notas"]["producao"],
            },
            "info": {
                "valor_cota_mensal":  meta["cota_mensal"],
                "meses_considerados": meta["meses_mandato"],
                "total_gasto":        meta["total_gasto"],
                "cota_utilizada_pct": meta["cota_utilizada_pct"],
            },
        }

    # ------------------------------------------------------------------
    # Timeline — série histórica anual
    # ------------------------------------------------------------------

    async def get_politico_timeline_service(self, politico_id: int) -> list[dict]:
        """
        Retorna a evolução anual de performance, estatísticas e gastos do
        parlamentar — uma entrada por ano com dados registrados no banco.

        Cada item da lista contém:
          - ano
          - score e notas detalhadas (assiduidade, economia, produção)
          - estatísticas do ano (votações, despesas, total gasto, média mensal)
          - info de cota (valor, % utilizada)

        Exemplo de resposta:
        [
          {
            "ano": 2023,
            "score": 61.4,
            "notas": { "assiduidade": 87.0, "economia": 74.2, "producao": 38.5 },
            "estatisticas": {
              "total_votacoes": 142,
              "total_despesas": 89,
              "total_gasto": 312400.0,
              "media_mensal": 26033.33
            },
            "info": {
              "valor_cota_mensal": 42837.33,
              "meses_ativos": 12,
              "cota_total": 514047.96,
              "cota_utilizada_pct": 60.73
            }
          },
          ...
        ]

        Lança HTTP 404 se o político não existir.
        """
        politico = await self._repo.get_politico_repo(politico_id)
        if not politico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Político não encontrado.",
            )

        timeline_raw = await self._ranking_repo.get_timeline_data_by_id(politico_id)
        if not timeline_raw:
            return []

        resultado = []
        for entry in timeline_raw:
            raw  = entry["raw"]
            calc = calcular_score(raw)
            meta = calc.pop("_meta")

            meses_ativos = meta["meses_mandato"]
            total_gasto  = meta["total_gasto"]

            resultado.append({
                "ano":   entry["ano"],
                "score": calc["score"],
                "notas": calc["notas"],
                "estatisticas": {
                    "total_votacoes": entry["total_votacoes"],
                    "total_despesas": entry["total_despesas"],
                    "total_gasto":    round(total_gasto, 2),
                    "media_mensal":   round(total_gasto / meses_ativos, 2) if meses_ativos else 0.0,
                },
                "info": {
                    "valor_cota_mensal":  meta["cota_mensal"],
                    "meses_ativos":       meses_ativos,
                    "cota_total":         round(meta["cota_total"], 2),
                    "cota_utilizada_pct": meta["cota_utilizada_pct"],
                },
            })

        return resultado