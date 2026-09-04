"""
catalog.py
==========
Descritor de datasets e catálogo de ingestão da Câmara dos Deputados.
Organiza os datasets em ondas paralelas de dependência (dep_group 0, 1, 2)
para garantir que tabelas pai existam antes da carga de tabelas filhas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from injest_banco.client import BASE_ARQUIVOS_URL, COTAS_BASE_URL
from injest_banco.transformers import (
    t_cotas,
    t_deputados,
    t_deputados_ocupacoes,
    t_deputados_profissoes,
    t_eventos,
    t_eventos_orgaos,
    t_eventos_reqs,
    t_frentes,
    t_frentes_deputados,
    t_funcionarios,
    t_grupos,
    t_grupos_historico,
    t_grupos_membros,
    t_legislaturas,
    t_legislaturas_mesas,
    t_licitacoes,
    t_licitacoes_contratos,
    t_licitacoes_itens,
    t_licitacoes_pedidos,
    t_licitacoes_propostas,
    t_orgaos,
    t_orgaos_deputados,
    t_presenca,
    t_proposicoes,
    t_proposicoes_autores,
    t_proposicoes_temas,
    t_tecad_categorias,
    t_tecad_termos,
    t_votacoes,
    t_votacoes_objetos,
    t_votacoes_orientacoes,
    t_votacoes_votos,
)


@dataclass
class Dataset:
    nome: str
    url_fn: Callable[[], str]
    transform_fn: Callable
    table_name: (
        str  # prefixo "_raw_" indica que requer resolução de FKs antes de inserir
    )
    conflict_cols: list[str]
    ano_ref: Optional[int] = None  # ano dos dados; None = dataset atemporal
    preserve_cols: Optional[list[str]] = None  # colunas a não sobrescrever no upsert
    dep_group: int = 0  # onda de dependência de execução (0 -> 1 -> 2)


def url_simples(dataset: str) -> str:
    return f"{BASE_ARQUIVOS_URL}/{dataset}/csv/{dataset}.csv"


def url_anual(dataset: str, ano: int) -> str:
    return f"{BASE_ARQUIVOS_URL}/{dataset}/csv/{dataset}-{ano}.csv"


def url_legislatura(dataset: str, leg: int) -> str:
    return f"{BASE_ARQUIVOS_URL}/{dataset}/csv/{dataset}-L{leg}.csv"


def url_cota_anual(ano: int) -> str:
    return f"{COTAS_BASE_URL}/Ano-{ano}.csv.zip"


def build_catalog(anos: list[int], legislaturas: list[int]) -> list[Dataset]:
    """
    Constrói o catálogo completo de datasets ordenados por dep_group:
      0: tabelas base sem chave estrangeira para outras tabelas
      1: tabelas dependentes do grupo 0 (eventos, proposicoes, votacoes, frentes, grupos)
      2: tabelas dependentes do grupo 1 (votos, orientacoes, membros de frentes/grupos)
    """
    A, L = anos, legislaturas

    # ── Datasets simples (sem partição anual) ──────────────────────────────────
    simple = [
        # Grupo 0: Tabelas raiz
        Dataset(
            "legislaturas",
            lambda: url_simples("legislaturas"),
            t_legislaturas,
            "legislaturas",
            ["idLegislatura"],
            dep_group=0,
        ),
        Dataset(
            "orgaos",
            lambda: url_simples("orgaos"),
            t_orgaos,
            "orgaos",
            ["idCamara"],
            dep_group=0,
        ),
        Dataset(
            "deputados",
            lambda: url_simples("deputados"),
            t_deputados,
            "deputados",
            ["idCamara"],
            preserve_cols=[
                "urlFoto",
                "escolaridade",
                "emailGabinete",
                "nomeCivil",
                "condicaoEleitoral",
                "telefoneGabinete",
            ],
            dep_group=0,
        ),
        Dataset(
            "tecadCategorias",
            lambda: url_simples("tecadCategorias"),
            t_tecad_categorias,
            "tecadCategorias",
            ["codCategoria", "codSubCategoria"],
            dep_group=0,
        ),
        Dataset(
            "tecadTermos",
            lambda: url_simples("tecadTermos"),
            t_tecad_termos,
            "tecadTermos",
            ["codTermo"],
            dep_group=0,
        ),
        Dataset(
            "funcionarios",
            lambda: url_simples("funcionarios"),
            t_funcionarios,
            "funcionarios",
            ["ponto"],
            dep_group=0,
        ),
        # Grupo 1: dependem de deputados / orgaos / legislaturas
        Dataset(
            "deputadosOcupacoes",
            lambda: url_simples("deputadosOcupacoes"),
            t_deputados_ocupacoes,
            "_raw_deputadosOcupacoes",
            [],
            dep_group=1,
        ),
        Dataset(
            "deputadosProfissoes",
            lambda: url_simples("deputadosProfissoes"),
            t_deputados_profissoes,
            "_raw_deputadosProfissoes",
            [],
            dep_group=1,
        ),
        Dataset(
            "frentes",
            lambda: url_simples("frentes"),
            t_frentes,
            "_raw_frentes",
            [],
            dep_group=1,
        ),
        Dataset(
            "grupos",
            lambda: url_simples("grupos"),
            t_grupos,
            "grupos",
            ["idCamara"],
            dep_group=1,
        ),
        Dataset(
            "legislaturasMesas",
            lambda: url_simples("legislaturasMesas"),
            t_legislaturas_mesas,
            "legislaturasMesas",
            ["idLegislatura", "idDeputado", "cargo", "dataInicio"],
            dep_group=1,
        ),
        # Grupo 2: dependem de frentes / grupos
        Dataset(
            "frentesDeputados",
            lambda: url_simples("frentesDeputados"),
            t_frentes_deputados,
            "_raw_frentesDeputados",
            [],
            dep_group=2,
        ),
        Dataset(
            "gruposMembros",
            lambda: url_simples("gruposMembros"),
            t_grupos_membros,
            "_raw_gruposMembros",
            [],
            dep_group=2,
        ),
        Dataset(
            "gruposHistorico",
            lambda: url_simples("gruposHistorico"),
            t_grupos_historico,
            "_raw_gruposHistorico",
            [],
            dep_group=2,
        ),
    ]

    # ── Datasets com partição anual ────────────────────────────────────────────
    anual = []
    for a in A:
        anual += [
            # Grupo 0: eventos, proposicoes e licitacoes raiz
            Dataset(
                f"eventos_{a}",
                lambda ano=a: url_anual("eventos", ano),
                t_eventos,
                "eventos",
                ["idCamara"],
                ano_ref=a,
                dep_group=0,
            ),
            Dataset(
                f"proposicoes_{a}",
                lambda ano=a: url_anual("proposicoes", ano),
                t_proposicoes,
                "proposicoes",
                ["idCamara"],
                ano_ref=a,
                dep_group=0,
            ),
            Dataset(
                f"licitacoes_{a}",
                lambda ano=a: url_anual("licitacoes", ano),
                t_licitacoes,
                "licitacoes",
                ["idLicitacao"],
                ano_ref=a,
                dep_group=0,
            ),
            # Grupo 1: dependem de eventos / proposicoes / licitacoes / deputados
            Dataset(
                f"eventosOrgaos_{a}",
                lambda ano=a: url_anual("eventosOrgaos", ano),
                t_eventos_orgaos,
                "_raw_eventosOrgaos",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"eventosRequerimentos_{a}",
                lambda ano=a: url_anual("eventosRequerimentos", ano),
                t_eventos_reqs,
                "_raw_eventosRequerimentos",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"eventosPresenca_{a}",
                lambda ano=a: url_anual("eventosPresencaDeputados", ano),
                t_presenca,
                "_raw_eventosPresenca",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"proposicoesAutores_{a}",
                lambda ano=a: url_anual("proposicoesAutores", ano),
                t_proposicoes_autores,
                "_raw_proposicoesAutores",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"proposicoesTemas_{a}",
                lambda ano=a: url_anual("proposicoesTemas", ano),
                t_proposicoes_temas,
                "_raw_proposicoesTemas",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"votacoes_{a}",
                lambda ano=a: url_anual("votacoes", ano),
                t_votacoes,
                "_raw_votacoes",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"licitacoesPedidos_{a}",
                lambda ano=a: url_anual("licitacoesPedidos", ano),
                t_licitacoes_pedidos,
                "_raw_licitacoesPedidos",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"licitacoesPropostas_{a}",
                lambda ano=a: url_anual("licitacoesPropostas", ano),
                t_licitacoes_propostas,
                "_raw_licitacoesPropostas",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"licitacoesItens_{a}",
                lambda ano=a: url_anual("licitacoesItens", ano),
                t_licitacoes_itens,
                "_raw_licitacoesItens",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            Dataset(
                f"licitacoesContratos_{a}",
                lambda ano=a: url_anual("licitacoesContratos", ano),
                t_licitacoes_contratos,
                "_raw_licitacoesContratos",
                [],
                ano_ref=a,
                dep_group=1,
            ),
            # Grupo 2: votos e orientações dependem de votações (grupo 1)
            Dataset(
                f"votacoesVotos_{a}",
                lambda ano=a: url_anual("votacoesVotos", ano),
                t_votacoes_votos,
                "_raw_votacoesVotos",
                [],
                ano_ref=a,
                dep_group=2,
            ),
            Dataset(
                f"votacoesOrientacoes_{a}",
                lambda ano=a: url_anual("votacoesOrientacoes", ano),
                t_votacoes_orientacoes,
                "_raw_votacoesOrientacoes",
                [],
                ano_ref=a,
                dep_group=2,
            ),
            Dataset(
                f"votacoesObjetos_{a}",
                lambda ano=a: url_anual("votacoesProposicoes", ano),
                t_votacoes_objetos,
                "_raw_votacoesObjetos",
                [],
                ano_ref=a,
                dep_group=2,
            ),
        ]

    # ── Datasets por legislatura ──────────────────────────────────────────────
    leg_datasets = [
        Dataset(
            f"orgaosDeputados_L{leg}",
            lambda leg=leg: url_legislatura("orgaosDeputados", leg),
            t_orgaos_deputados,
            "_raw_orgaosDeputados",
            [],
            dep_group=1,
        )
        for leg in L
    ]

    # ── Cotas parlamentares (CEAP) ────────────────────────────────────────────
    cotas_datasets = [
        Dataset(
            f"cotas_{a}",
            lambda ano=a: url_cota_anual(ano),
            t_cotas,
            "_raw_cotas",
            [],
            ano_ref=a,
            dep_group=1,
        )
        for a in A
    ]

    return simple + anual + leg_datasets + cotas_datasets
