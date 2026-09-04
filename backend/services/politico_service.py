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

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.politico_repository import PoliticoRepository
from backend.repositories.ranking_repository import RankingRepository
from backend.schemas import (
    AtividadeLegislativaResponse,
    ComparacaoPoliticosGrafoResponse,
    PoliticoResumoComparacao,
    PoliticoResponse,
    TemaComparadoResumo,
    VotoComparado,
)
from backend.services.performance_calc import calcular_score

from .ranking_service import RankingService

logger = logging.getLogger(__name__)

# Limites de paginação (segunda linha de defesa)
_MAX_LIMIT_DEPUTADOS = 600
_MAX_LIMIT_VOTACOES = 20
_MAX_LIMIT_DESPESAS = 20
_MAX_LIMIT_RESUMO = 60
_MAX_LIMIT_ATIVIDADE = 100


class PoliticoService:
    """
    Orquestra as regras de negócio de deputados.
    Não expõe detalhes de infraestrutura (SQL, ORM) para a camada HTTP.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = PoliticoRepository(db)
        self._ranking_repo = RankingRepository(db)
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
        partido: str | None = None,
        offset: int = 0,
    ) -> list[PoliticoResponse]:
        safe_limit = min(abs(limit), _MAX_LIMIT_DEPUTADOS)
        safe_offset = max(offset, 0)
        deputados = await self._repo.get_politicos_repo(
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

    async def get_politico_by_id_or_slug_service(
        self, id_or_slug: str
    ) -> PoliticoResponse:
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
        return await self._repo.get_politicos_estatisticas_repo(deputado_id, ano=ano)

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
        meta = result.pop("_meta")

        media_global = await RankingService(self._db).get_media_global_cached()

        return {
            "politico_id": deputado_id,
            "ano": ano,
            "score_final": result["score"],
            "media_global": round(media_global, 2),
            "detalhes": {
                "nota_assiduidade": result["notas"]["assiduidade"],
                "nota_economia": result["notas"]["economia"],
                "nota_producao": result["notas"]["producao"],
            },
            "info": {
                "valor_cota_mensal": meta["cota_mensal"],
                "meses_considerados": meta["meses_mandato"],
                # Breakdown de gastos — apos inclusao da verba de gabinete
                "total_gasto": meta["gasto_ceap"],
                "gasto_gabinete": meta["gasto_gabinete"],
                "gasto_total": meta["gasto_total"],
                "orcamento_total": meta["orcamento_total"],
                "orcamento_utilizado_pct": meta["orcamento_utilizado_pct"],
                # Mantido por retrocompatibilidade
                "cota_utilizada_pct": meta["orcamento_utilizado_pct"],
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
            raw = entry["raw"]
            calc = calcular_score(raw)
            meta = calc.pop("_meta")

            meses_ativos = meta["meses_mandato"]
            gasto_ceap = meta["gasto_ceap"]
            gasto_gabinete = meta["gasto_gabinete"]
            gasto_total = meta["gasto_total"]

            resultado.append(
                {
                    "ano": entry["ano"],
                    "score": calc["score"],
                    "notas": calc["notas"],
                    "estatisticas": {
                        "total_votacoes": entry["total_votacoes"],
                        "total_despesas": entry["total_despesas"],
                        "total_gasto": round(gasto_ceap, 2),
                        "media_mensal": round(gasto_ceap / meses_ativos, 2)
                        if meses_ativos
                        else 0.0,
                    },
                    "info": {
                        "valor_cota_mensal": meta["cota_mensal"],
                        "meses_ativos": meses_ativos,
                        "cota_total": round(meta["cota_total"], 2),
                        # Breakdown de gastos — apos inclusao da verba de gabinete
                        "gasto_ceap": round(gasto_ceap, 2),
                        "gasto_gabinete": round(gasto_gabinete, 2),
                        "gasto_total": round(gasto_total, 2),
                        "verba_gabinete_total": round(meta["verba_gabinete_total"], 2),
                        "orcamento_total": round(meta["orcamento_total"], 2),
                        "orcamento_utilizado_pct": meta["orcamento_utilizado_pct"],
                        # Mantido por retrocompatibilidade
                        "cota_utilizada_pct": meta["orcamento_utilizado_pct"],
                    },
                }
            )

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
        q: str | None = None,
        offset_votacoes: int = 0,
        offset_proposicoes: int = 0,
    ) -> "AtividadeLegislativaResponse":
        """
        Retorna em uma única chamada as votações nominais e as proposições
        em que o parlamentar é autor ou coautor.

        As duas queries ao banco são disparadas em sequência na mesma sessão:
        o asyncpg não suporta operações concorrentes numa única conexão, e
        essa abordagem mantém o consumo em 1 conexão por requisição (relevante
        sob carga com múltiplos usuários simultâneos). O resultado combinado
        é cacheado via fastapi-cache2/Valkey para absorver o custo repetido.

        Lança HTTP 404 se o deputado não existir.
        """
        deputado = await self._repo.get_politico_repo(deputado_id)
        if not deputado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deputado não encontrado.",
            )

        safe_lv = min(abs(limit_votacoes), 100)
        safe_lp = min(abs(limit_proposicoes), 100)
        safe_ov = max(offset_votacoes, 0)
        safe_op = max(offset_proposicoes, 0)

        # Queries sequenciais na mesma sessão — evita concorrência na mesma
        # conexão asyncpg (InterfaceError: "another operation is in progress")
        votacoes, total_v = await self._repo.get_atividade_votacoes_repo(
            deputado_id,
            q=q,
            ano=ano,
            limit=safe_lv,
            offset=safe_ov,
        )
        proposicoes, total_p = await self._repo.get_atividade_proposicoes_repo(
            deputado_id,
            ano=ano,
            q=q,
            limit=safe_lp,
            offset=safe_op,
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

    # ------------------------------------------------------------------
    # Comparador de 2 Políticos (Apache AGE openCypher + Fallback Relacional)
    # ------------------------------------------------------------------

    async def comparar_politicos_service(
        self,
        id_or_slug1: str,
        id_or_slug2: str,
        tema: str | None = None,
        limit_divergencias: int = 50,
        limit_alinhamentos: int = 20,
    ) -> ComparacaoPoliticosGrafoResponse:
        """
        Compara o posicionamento e alinhamento de votações entre dois parlamentares.

        Prioriza a travessia de grafo no Apache AGE:
            (p1:Politico)-[:VOTED_IN]->(vt:Votacao)<-[:VOTED_IN]-(p2:Politico)
        Caso os nós ainda não estejam sincronizados no grafo, realiza fallback transparente
        para o PostgreSQL relacional.
        """
        if str(id_or_slug1).strip().lower() == str(id_or_slug2).strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível comparar um parlamentar consigo mesmo.",
            )

        # 1. Resolve os dois políticos
        pol1 = await self.get_politico_by_id_or_slug_service(str(id_or_slug1))
        pol2 = await self.get_politico_by_id_or_slug_service(str(id_or_slug2))

        # 2. Resumo de temas disponíveis para filtro (sempre de todo o histórico comum)
        temas_resumo_raw = await self._repo.get_resumo_temas_comparacao_repo(
            pol1.id, pol2.id
        )
        temas_disponiveis = [TemaComparadoResumo(**t) for t in temas_resumo_raw]

        # 3. Executa a comparação via Apache AGE
        votos_comparados = []
        fonte = "apache_age_graph"
        try:
            from shared.graph import cypher_sample_alinhamento_votos_async

            votos_comparados = await cypher_sample_alinhamento_votos_async(
                self._db, pol1.id, pol2.id, tema=tema
            )
        except Exception as e:
            logger.warning(
                "Falha ao consultar alinhamento no Apache AGE (%s vs %s, tema=%s): %s",
                pol1.id,
                pol2.id,
                tema,
                e,
            )
            votos_comparados = []

        # 4. Fallback relacional se o grafo não retornou dados para este par
        if not votos_comparados:
            fonte = "relacional"
            votos_comparados = await self._repo.get_comparacao_votos_relacional_repo(
                pol1.id, pol2.id, tema=tema
            )

        # 5. Agrega estatísticas e divide em alinhamentos e divergências
        divergencias_list: list[VotoComparado] = []
        alinhamentos_list: list[VotoComparado] = []

        for v in votos_comparados:
            item = VotoComparado(
                id_votacao=v["id_votacao"],
                data=v.get("data"),
                descricao=v.get("descricao"),
                proposicao=v.get("proposicao"),
                ementa=v.get("ementa"),
                voto_politico1=v["voto_politico1"],
                voto_politico2=v["voto_politico2"],
                alinhados=v["alinhados"],
                tema=v.get("tema"),
                temas=v.get("temas", []),
            )
            if item.alinhados:
                alinhamentos_list.append(item)
            else:
                divergencias_list.append(item)

        total_comuns = len(votos_comparados)
        total_alinhados = len(alinhamentos_list)
        total_divergentes = len(divergencias_list)
        taxa = (
            round((total_alinhados / total_comuns) * 100.0, 1)
            if total_comuns > 0
            else 0.0
        )

        safe_lim_div = min(abs(limit_divergencias), 100)
        safe_lim_aln = min(abs(limit_alinhamentos), 100)

        return ComparacaoPoliticosGrafoResponse(
            politico1=PoliticoResumoComparacao(
                id=pol1.id,
                nome=pol1.nome,
                slug=pol1.slug,
                sigla_partido=pol1.sigla_partido,
                sigla_uf=pol1.sigla_uf,
                url_foto=pol1.url_foto,
            ),
            politico2=PoliticoResumoComparacao(
                id=pol2.id,
                nome=pol2.nome,
                slug=pol2.slug,
                sigla_partido=pol2.sigla_partido,
                sigla_uf=pol2.sigla_uf,
                url_foto=pol2.url_foto,
            ),
            total_votacoes_comuns=total_comuns,
            votos_alinhados=total_alinhados,
            votos_divergentes=total_divergentes,
            taxa_alinhamento=taxa,
            divergencias=divergencias_list[:safe_lim_div],
            alinhamentos=alinhamentos_list[:safe_lim_aln],
            fonte_dados=fonte,
            tema_filtrado=tema,
            temas_disponiveis=temas_disponiveis,
        )
