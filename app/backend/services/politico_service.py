"""
Serviço de Deputados — Camada de lógica de negócio.

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
from backend.schemas import PoliticoResponse, AtividadeLegislativaResponse
from backend.services.performance_calc import calcular_score, resolve_cota_mensal
from .ranking_service import RankingService
import asyncio

logger = logging.getLogger(__name__)

# Limites de paginação (segunda linha de defesa)
_MAX_LIMIT_DEPUTADOS   = 600
_MAX_LIMIT_VOTACOES    = 20
_MAX_LIMIT_DESPESAS    = 20
_MAX_LIMIT_RESUMO      = 60
_MAX_LIMIT_ATIVIDADE   = 100


class PoliticoService:
    """
    Orquestra as regras de negócio de deputados.
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
        safe_limit  = min(abs(limit), _MAX_LIMIT_DEPUTADOS)
        safe_offset = max(offset, 0)
        deputados   = await self._repo.get_politicos_repo(
            q=q, uf=uf, partido=partido, limit=safe_limit, offset=safe_offset
        )
        return [PoliticoResponse.model_validate(p) for p in deputados]

    # ------------------------------------------------------------------
    # Detalhe
    # ------------------------------------------------------------------

    async def get_politicos_detalhe_service(self, deputado_id: int) -> PoliticoResponse:
        deputado = await self._repo.get_politico_repo(deputado_id)
        if not deputado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deputado não encontrado.",
            )
        return PoliticoResponse.model_validate(deputado)

    async def get_politico_by_slug_service(self, slug: str) -> PoliticoResponse:
        deputado = await self._repo.get_politico_by_slug_repo(slug)
        if not deputado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deputado não encontrado.",
            )
        return PoliticoResponse.model_validate(deputado)

    async def get_politico_by_id_or_slug_service(self, id_or_slug: str) -> PoliticoResponse:
        """
        Resolve um deputado por ID numérico ou slug de nome.

        Usado pelo endpoint unificado GET /politicos/{id_or_slug} para suportar
        tanto URLs legadas (/politicos/1047) quanto URLs com slug (/politicos/joao-silva).
        """
        if id_or_slug.isdigit():
            return await self.get_politicos_detalhe_service(int(id_or_slug))
        return await self.get_politico_by_slug_service(id_or_slug)

    # ------------------------------------------------------------------
    # Votações
    # ------------------------------------------------------------------

    async def get_politicos_votacoes_service(
        self,
        deputado_id: int,
        *,
        limit: int = 20,
        ano: int | None = None,
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_VOTACOES)
        return await self._repo.get_politicos_votacoes_repo(
            politico_id=deputado_id, limit=safe_limit, ano=ano
        )

    # ------------------------------------------------------------------
    # Despesas
    # ------------------------------------------------------------------

    async def get_politicos_despesas_services(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
        mes: int | None = None,
        limit: int = 20,
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_DESPESAS)
        return await self._repo.get_politicos_despesas_repo(
            politico_id=deputado_id, ano=ano, mes=mes, limit=safe_limit
        )

    async def get_politicos_despesas_resumo_services(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
        limit: int = 60,
    ):
        safe_limit = min(abs(limit), _MAX_LIMIT_RESUMO)
        return await self._repo.get_politicos_despesas_resumo_repo(
            politico_id=deputado_id, ano=ano, limit=safe_limit
        )

    async def get_politicos_despesas_resumo_completo_services(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
        limit_meses: int = 60,
    ):
        safe_limit = min(abs(limit_meses), _MAX_LIMIT_RESUMO)
        return await self._repo.get_politicos_despesas_resumo_completo_repo(
            politico_id=deputado_id, ano=ano, limit_meses=safe_limit
        )

    # ------------------------------------------------------------------
    # Estatísticas — com filtro de ano
    # ------------------------------------------------------------------

    async def get_politico_estatisticas_service(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
    ):
        """
        Retorna estatísticas gerais do parlamentar.

        Args:
            deputado_id: ID do parlamentar.
            ano: quando fornecido, filtra votações e despesas pelo ano,
                 permitindo comparação justa na linha do tempo.
        """
        return await self._repo.get_politicos_estatisticas_repo(
            deputado_id, ano=ano
        )

    # ------------------------------------------------------------------
    # Performance — com filtro de ano
    # ------------------------------------------------------------------

    async def get_politico_performance_service(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
    ) -> dict:
        """
        Calcula o score de performance do parlamentar.

        Usa calcular_score() de performance_calc.py — mesma função do
        RankingService — garantindo números idênticos ao ranking geral
        quando ano=None.

        Args:
            deputado_id: ID do parlamentar.
            ano: quando fornecido, o score reflete apenas aquele ano,
                 possibilitando comparação justa na linha do tempo.

        Fórmula:
            score = assiduidade × 15% + economia × 40% + produção × 45%

        Lança HTTP 404 se o deputado não existir.
        """
        deputado = await self._repo.get_politico_repo(deputado_id)
        if not deputado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deputado não encontrado.",
            )

        raw_row = await self._ranking_repo.get_performance_data_by_id(
            deputado_id, ano=ano
        )
        if not raw_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dados de performance não encontrados para este deputado.",
            )

        result = calcular_score(raw_row)
        meta   = result.pop("_meta")

        media_global = await RankingService(self._db).get_media_global_cached()

        return {
            "politico_id":  deputado_id,
            "ano":          ano,
            "score_final":  result["score"],
            "media_global": round(media_global, 2),
            "detalhes": {
                "nota_assiduidade": result["notas"]["assiduidade"],
                "nota_economia":    result["notas"]["economia"],
                "nota_producao":    result["notas"]["producao"],
            },
            "info": {
                "valor_cota_mensal":       meta["cota_mensal"],
                "meses_considerados":      meta["meses_mandato"],
                # Breakdown de gastos — apos inclusao da verba de gabinete
                "total_gasto":             meta["gasto_ceap"],
                "gasto_gabinete":          meta["gasto_gabinete"],
                "gasto_total":             meta["gasto_total"],
                "orcamento_total":         meta["orcamento_total"],
                "orcamento_utilizado_pct": meta["orcamento_utilizado_pct"],
                # Mantido por retrocompatibilidade
                "cota_utilizada_pct":      meta["orcamento_utilizado_pct"],
            },
        }

    # ------------------------------------------------------------------
    # Timeline — série histórica anual
    # ------------------------------------------------------------------

    async def get_politico_timeline_service(self, deputado_id: int) -> list[dict]:
        """
        Retorna a evolução anual de performance, estatísticas e gastos do
        parlamentar — uma entrada por ano com dados registrados no banco.

        Lança HTTP 404 se o deputado não existir.
        """
        deputado = await self._repo.get_politico_repo(deputado_id)
        if not deputado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deputado não encontrado.",
            )

        timeline_raw = await self._ranking_repo.get_timeline_data_by_id(deputado_id)
        if not timeline_raw:
            return []

        resultado = []
        for entry in timeline_raw:
            raw  = entry["raw"]
            calc = calcular_score(raw)
            meta = calc.pop("_meta")

            meses_ativos   = meta["meses_mandato"]
            gasto_ceap     = meta["gasto_ceap"]
            gasto_gabinete = meta["gasto_gabinete"]
            gasto_total    = meta["gasto_total"]

            resultado.append({
                "ano":   entry["ano"],
                "score": calc["score"],
                "notas": calc["notas"],
                "estatisticas": {
                    "total_votacoes": entry["total_votacoes"],
                    "total_despesas": entry["total_despesas"],
                    "total_gasto":    round(gasto_ceap, 2),
                    "media_mensal":   round(gasto_ceap / meses_ativos, 2) if meses_ativos else 0.0,
                },
                "info": {
                    "valor_cota_mensal":       meta["cota_mensal"],
                    "meses_ativos":            meses_ativos,
                    "cota_total":              round(meta["cota_total"], 2),
                    # Breakdown de gastos — apos inclusao da verba de gabinete
                    "gasto_ceap":              round(gasto_ceap, 2),
                    "gasto_gabinete":          round(gasto_gabinete, 2),
                    "gasto_total":             round(gasto_total, 2),
                    "verba_gabinete_total":    round(meta["verba_gabinete_total"], 2),
                    "orcamento_total":         round(meta["orcamento_total"], 2),
                    "orcamento_utilizado_pct": meta["orcamento_utilizado_pct"],
                    # Mantido por retrocompatibilidade
                    "cota_utilizada_pct":      meta["orcamento_utilizado_pct"],
                },
            })

        return resultado

    async def get_politico_proposicoes_service(
        self,
        deputado_id: int,
        *,
        limit: int = 100,
    ):
        safe_limit = min(abs(limit), 100)
        return await self._repo.get_politico_proposicoes_repo(
            politico_id=deputado_id, limit=safe_limit
        )

    async def get_politico_atividade_legislativa_service(
        self,
        deputado_id: int,
        *,
        ano: int | None = None,
        limit_votacoes: int = 20,
        limit_proposicoes: int = 20,
        offset_votacoes: int = 0,
        offset_proposicoes: int = 0,
    ) -> "AtividadeLegislativaResponse":
        """
        Retorna em uma única chamada as votações nominais e as proposições
        em que o parlamentar é autor ou coautor.

        As duas queries ao banco são disparadas em paralelo via asyncio.gather,
        reduzindo a latência total ao tempo da query mais lenta (não à soma).

        Lança HTTP 404 se o deputado não existir.
        """
        deputado = await self._repo.get_politico_repo(deputado_id)
        if not deputado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deputado não encontrado.",
            )

        safe_lv  = min(abs(limit_votacoes),    100)
        safe_lp  = min(abs(limit_proposicoes), 100)
        safe_ov  = max(offset_votacoes, 0)
        safe_op  = max(offset_proposicoes, 0)

        # Queries paralelas — reduz latência
        (votacoes, total_v), (proposicoes, total_p) = await asyncio.gather(
            self._repo.get_atividade_votacoes_repo(
                deputado_id,
                ano=ano,
                limit=safe_lv,
                offset=safe_ov,
            ),
            self._repo.get_atividade_proposicoes_repo(
                deputado_id,
                ano=ano,
                limit=safe_lp,
                offset=safe_op,
            ),
        )

        return AtividadeLegislativaResponse(
            votacoes=votacoes,
            proposicoes=proposicoes,
            total_votacoes=total_v,
            total_proposicoes=total_p,
            limit_votacoes=safe_lv,
            limit_proposicoes=safe_lp,
            offset_votacoes=safe_ov,
            offset_proposicoes=safe_op,
            ano=ano,
        )