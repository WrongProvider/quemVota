"""
transformers.py
===============
Funções de limpeza, normalização e transformação dos datasets CSV da Câmara.
Converte DataFrames brutos em listas de dicionários padronizados para carga.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

log = logging.getLogger("etl_camara.transformers")

# ---------------------------------------------------------------------------
# Funções utilitárias de limpeza e sanitização de dados
# ---------------------------------------------------------------------------


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpeza global do DataFrame:
      - Remove BOM (\ufeff), aspas duplas e espaços nos nomes de colunas
      - Remove espaços em branco, quebras desnecessárias e aspas espúrias nos textos
      - Converte strings vazias, 'nan' e 'None' para None
    """
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "")
        .str.replace('"', "")
        .str.strip()
    )

    for col in df.select_dtypes(include="object").columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("\x00", "", regex=False)
            .str.strip()
            .str.replace(r'^"(.*)"$', r"\1", regex=True)
            .str.replace('""', '"', regex=False)
            .replace({"": None, "nan": None, "None": None, "null": None, "NULL": None})
        )
    return df


def to_date_series(s: Optional[pd.Series]) -> pd.Series:
    """Converte série para date (YYYY-MM-DD)."""
    if s is None or s.empty:
        return pd.Series(dtype="object")
    return pd.to_datetime(s, errors="coerce").dt.date


def to_datetime_series(s: Optional[pd.Series]) -> pd.Series:
    """Converte série para datetime com segurança."""
    if s is None or s.empty:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(s, errors="coerce")


def to_numeric_series(s: Optional[pd.Series]) -> pd.Series:
    """Converte série para numérico suportando vírgula como decimal."""
    if s is None or s.empty:
        return pd.Series(dtype="float64")
    return pd.to_numeric(
        s.astype(str)
        .str.replace(".", "", regex=False)  # se contiver separador de milhar
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True),
        errors="coerce",
    )


def to_boolean_series(s: Optional[pd.Series]) -> pd.Series:
    """Converte série para booleano a partir de texto."""
    if s is None or s.empty:
        return pd.Series(dtype="boolean")
    m = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
        "sim": True,
        "não": False,
        "nao": False,
    }
    return s.astype(str).str.lower().map(m)


def sanitize_val(v: Any) -> Any:
    """Converte NaT, NaN e float NaN para None compatível com drivers SQL."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def keep_columns(df: pd.DataFrame, cols: list[str]) -> list[dict[str, Any]]:
    """Filtra colunas existentes e retorna lista de dicionários sanitizados."""
    sub = df[[c for c in cols if c in df.columns]]
    return [
        {k: sanitize_val(v) for k, v in row.items()} for row in sub.to_dict("records")
    ]


# ---------------------------------------------------------------------------
# Transformações específicas por Entidade / Dataset
# ---------------------------------------------------------------------------


def t_legislaturas(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df).rename(columns={"id": "idLegislatura"})
    df["idLegislatura"] = pd.to_numeric(df["idLegislatura"], errors="coerce")
    df["dataInicio"] = to_date_series(df.get("dataInicio"))
    df["dataFim"] = to_date_series(df.get("dataFim"))
    df["anoEleicao"] = pd.to_numeric(df.get("anoEleicao"), errors="coerce")
    return keep_columns(
        df, ["idLegislatura", "uri", "dataInicio", "dataFim", "anoEleicao"]
    )


def t_legislaturas_mesas(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["dataInicio"] = to_datetime_series(df.get("dataInicio"))
    df["dataFim"] = to_datetime_series(df.get("dataFim"))
    for c in ["idLegislatura", "idOrgao", "idDeputado"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return keep_columns(
        df,
        [
            "idLegislatura",
            "idOrgao",
            "uriOrgao",
            "siglaOrgao",
            "nomeOrgao",
            "idDeputado",
            "uriDeputado",
            "nomeDeputado",
            "siglaPartido",
            "siglaUF",
            "cargo",
            "dataInicio",
            "dataFim",
        ],
    )


def t_orgaos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    if "uri" in df.columns:
        df["idCamara"] = df["uri"].astype(str).str.split("/").str[-1]
    else:
        df["idCamara"] = df.get("id")
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    for c in ["dataInicio", "dataInstalacao", "dataFim", "dataFimOriginal"]:
        df[c] = to_date_series(df.get(c, pd.Series(dtype=str)))
    for c in ["codTipoOrgao", "codSituacao"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "sigla",
            "apelido",
            "nome",
            "nomePublicacao",
            "codTipoOrgao",
            "tipoOrgao",
            "casa",
            "sala",
            "dataInicio",
            "dataInstalacao",
            "dataFim",
            "dataFimOriginal",
            "codSituacao",
            "descricaoSituacao",
            "urlWebsite",
        ],
    )


def t_orgaos_deputados(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    if "uriOrgao" in df.columns:
        df["idOrgaoCamara"] = pd.to_numeric(
            df["uriOrgao"].astype(str).str.split("/").str[-1], errors="coerce"
        )
    else:
        df["idOrgaoCamara"] = pd.to_numeric(df.get("idOrgao"), errors="coerce")

    if "uriDeputado" in df.columns:
        df["idDeputadoCamara"] = pd.to_numeric(
            df["uriDeputado"].astype(str).str.split("/").str[-1], errors="coerce"
        )
    else:
        df["idDeputadoCamara"] = pd.to_numeric(df.get("idDeputado"), errors="coerce")

    for c in ["dataInicio", "dataFim"]:
        df[c] = to_date_series(df.get(c, pd.Series(dtype=str)))
    df["codTitulo"] = pd.to_numeric(df.get("codTitulo"), errors="coerce")
    return keep_columns(
        df,
        [
            "idOrgaoCamara",
            "idDeputadoCamara",
            "nomePublicacaoOrgao",
            "uriDeputado",
            "nomeDeputado",
            "siglaPartido",
            "siglaUF",
            "cargo",
            "codTitulo",
            "dataInicio",
            "dataFim",
        ],
    )


def t_deputados(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    if "uri" in df.columns:
        df["idCamara"] = df["uri"].astype(str).str.split("/").str[-1]
    else:
        df["idCamara"] = df.get("id")
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    for c in ["idLegislaturaInicial", "idLegislaturaFinal"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["dataNascimento", "dataFalecimento"]:
        df[c] = to_datetime_series(df.get(c))
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "nome",
            "nomeCivil",
            "cpf",
            "siglaSexo",
            "idLegislaturaInicial",
            "idLegislaturaFinal",
            "dataNascimento",
            "dataFalecimento",
            "ufNascimento",
            "municipioNascimento",
            "siglaUF",
            "siglaPartido",
            "urlRedeSocial",
            "urlWebsite",
        ],
    )


def t_deputados_ocupacoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idDeputadoCamara"] = pd.to_numeric(df.get("id"), errors="coerce")
    for c in ["anoInicio", "anoFim"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
        df.loc[(df[c] > 2100) | (df[c] < 1800), c] = np.nan
        df[c] = df[c].astype(pd.Int64Dtype())

    df = df.drop_duplicates(
        subset=["idDeputadoCamara", "titulo", "anoInicio"], keep="last"
    )
    return keep_columns(
        df,
        [
            "idDeputadoCamara",
            "titulo",
            "entidade",
            "entidadeUF",
            "entidadePais",
            "anoInicio",
            "anoFim",
        ],
    )


def t_deputados_profissoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idDeputadoCamara"] = pd.to_numeric(df.get("id"), errors="coerce")
    df["codTipoProfissao"] = pd.to_numeric(df.get("codTipoProfissao"), errors="coerce")
    df["dataHora"] = to_datetime_series(df.get("dataHora"))
    return keep_columns(
        df, ["idDeputadoCamara", "dataHora", "codTipoProfissao", "titulo"]
    )


def t_eventos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df).rename(columns={"id": "idCamara"})
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    df["dataHoraInicio"] = to_datetime_series(df.get("dataHoraInicio"))
    df["dataHoraFim"] = to_datetime_series(df.get("dataHoraFim"))
    for campo, orig in [
        ("localCamaraNome", "localCamara.nome"),
        ("localCamaraPredio", "localCamara.predio"),
        ("localCamaraSala", "localCamara.sala"),
        ("localCamaraAndar", "localCamara.andar"),
    ]:
        if orig in df.columns:
            df[campo] = df[orig]
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "urlDocumentoPauta",
            "dataHoraInicio",
            "dataHoraFim",
            "situacao",
            "descricao",
            "descricaoTipo",
            "localExterno",
            "localCamaraNome",
            "localCamaraPredio",
            "localCamaraSala",
            "localCamaraAndar",
            "urlEvento",
        ],
    )


def t_eventos_orgaos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idEventoCamara"] = pd.to_numeric(df.get("idEvento"), errors="coerce")
    df["idOrgaoCamara"] = pd.to_numeric(df.get("idOrgao"), errors="coerce")
    return df[["idEventoCamara", "idOrgaoCamara"]].dropna().to_dict("records")


def t_eventos_reqs(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idEventoCamara"] = pd.to_numeric(df.get("idEvento"), errors="coerce")
    return keep_columns(df, ["idEventoCamara", "tituloRequerimento", "uriRequerimento"])


def t_presenca(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idEventoCamara"] = pd.to_numeric(df.get("idEvento"), errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("idDeputado"), errors="coerce")
    df["dataHoraInicio"] = to_datetime_series(df.get("dataHoraInicio"))
    return keep_columns(df, ["idEventoCamara", "idDeputadoCamara", "dataHoraInicio"])


def t_proposicoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df).rename(columns={"id": "idCamara"})
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    for c in [
        "codTipo",
        "numero",
        "ano",
        "ultimoStatus_idOrgao",
        "ultimoStatus_sequencia",
        "ultimoStatus_idTipoTramitacao",
        "ultimoStatus_idSituacao",
    ]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["dataApresentacao"] = to_datetime_series(df.get("dataApresentacao"))
    df["ultimoStatus_dataHora"] = to_datetime_series(df.get("ultimoStatus_dataHora"))
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "siglaTipo",
            "codTipo",
            "numero",
            "ano",
            "descricaoTipo",
            "ementa",
            "ementaDetalhada",
            "keywords",
            "dataApresentacao",
            "uriOrgaoNumerador",
            "uriPropAnterior",
            "uriPropPrincipal",
            "uriPropPosterior",
            "urlInteiroTeor",
            "urnFinal",
            "ultimoStatus_dataHora",
            "ultimoStatus_sequencia",
            "ultimoStatus_uriRelator",
            "ultimoStatus_idOrgao",
            "ultimoStatus_siglaOrgao",
            "ultimoStatus_uriOrgao",
            "ultimoStatus_regime",
            "ultimoStatus_descricaoTramitacao",
            "ultimoStatus_idTipoTramitacao",
            "ultimoStatus_descricaoSituacao",
            "ultimoStatus_idSituacao",
            "ultimoStatus_despacho",
            "ultimoStatus_apreciacao",
            "ultimoStatus_url",
        ],
    )


def t_proposicoes_autores(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idProposicaoCamara"] = pd.to_numeric(df.get("idProposicao"), errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("idDeputadoAutor"), errors="coerce")
    df["codTipoAutor"] = pd.to_numeric(df.get("codTipoAutor"), errors="coerce")
    df["ordemAssinatura"] = pd.to_numeric(df.get("ordemAssinatura"), errors="coerce")
    df["proponente"] = to_boolean_series(df.get("proponente", pd.Series(dtype=str)))
    return keep_columns(
        df,
        [
            "idProposicaoCamara",
            "idDeputadoCamara",
            "uriAutor",
            "codTipoAutor",
            "tipoAutor",
            "nomeAutor",
            "siglaPartidoAutor",
            "uriPartidoAutor",
            "siglaUFAutor",
            "ordemAssinatura",
            "proponente",
        ],
    )


def t_proposicoes_temas(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    if "uriProposicao" in df.columns:
        df["idProposicaoCamara"] = pd.to_numeric(
            df["uriProposicao"].astype(str).str.split("/").str[-1], errors="coerce"
        )
    else:
        df["idProposicaoCamara"] = pd.to_numeric(
            df.get("idProposicao"), errors="coerce"
        )
    df["codTema"] = pd.to_numeric(df.get("codTema"), errors="coerce")
    return keep_columns(df, ["idProposicaoCamara", "codTema", "tema"])


def t_votacoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df).rename(columns={"id": "idCamara"})
    df["data"] = to_date_series(df.get("data"))
    df["dataHoraRegistro"] = to_datetime_series(df.get("dataHoraRegistro"))
    df["ultimaAberturaVotacao_dataHoraRegistro"] = to_datetime_series(
        df.get("ultimaAberturaVotacao_dataHoraRegistro")
    )
    df["ultimaApresentacaoProposicao_dataHoraRegistro"] = to_datetime_series(
        df.get("ultimaApresentacaoProposicao_dataHoraRegistro")
    )
    for c in ["aprovacao", "votosSim", "votosNao", "votosOutros"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["idOrgaoCamara"] = pd.to_numeric(df.get("idOrgao"), errors="coerce")
    df["idEventoCamara"] = pd.to_numeric(df.get("idEvento"), errors="coerce")
    df["idProposicaoCamara"] = pd.to_numeric(
        df.get("idCamara").astype(str).str.split("-").str[0], errors="coerce"
    )
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "data",
            "dataHoraRegistro",
            "idOrgaoCamara",
            "uriOrgao",
            "siglaOrgao",
            "idEventoCamara",
            "uriEvento",
            "aprovacao",
            "votosSim",
            "votosNao",
            "votosOutros",
            "descricao",
            "tipoVotacao",
            "ultimaAberturaVotacao_dataHoraRegistro",
            "ultimaAberturaVotacao_descricao",
            "ultimaApresentacaoProposicao_dataHoraRegistro",
            "ultimaApresentacaoProposicao_descricao",
            "idProposicaoCamara",
            "ultimaApresentacaoProposicao_uriProposicao",
        ],
    )


def t_votacoes_votos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idVotacaoCamara"] = df.get("idVotacao")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("deputado_id"), errors="coerce")
    df["dataHoraVoto"] = to_datetime_series(df.get("dataHoraVoto"))
    df["idLegislatura"] = pd.to_numeric(
        df.get("deputado_idLegislatura"), errors="coerce"
    )
    df["siglaPartido"] = df.get("deputado_siglaPartido")
    df["uriPartido"] = df.get("deputado_uriPartido")
    df["siglaUF"] = df.get("deputado_siglaUf")
    return keep_columns(
        df,
        [
            "idVotacaoCamara",
            "idDeputadoCamara",
            "dataHoraVoto",
            "voto",
            "siglaPartido",
            "uriPartido",
            "siglaUF",
            "idLegislatura",
        ],
    )


def t_votacoes_orientacoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idVotacaoCamara"] = df.get("idVotacao")
    return keep_columns(
        df,
        ["idVotacaoCamara", "siglaOrgao", "siglaBancada", "uriBancada", "orientacao"],
    )


def t_votacoes_objetos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idVotacaoCamara"] = df.get("idVotacao")
    df["data"] = to_date_series(df.get("data"))
    for c in [
        "proposicao_codTipo",
        "proposicao_numero",
        "proposicao_ano",
        "proposicao_id",
    ]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return keep_columns(
        df,
        [
            "idVotacaoCamara",
            "data",
            "descricao",
            "proposicao_id",
            "proposicao_uri",
            "proposicao_ementa",
            "proposicao_codTipo",
            "proposicao_siglaTipo",
            "proposicao_numero",
            "proposicao_ano",
            "proposicao_titulo",
        ],
    )


def t_frentes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df).rename(columns={"id": "idCamara"})
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    df["idSituacao"] = pd.to_numeric(df.get("idSituacao"), errors="coerce")
    df["dataCriacao"] = to_date_series(df.get("dataCriacao"))
    df["coordenador_idCamara"] = pd.to_numeric(
        df.get("coordenador_id"), errors="coerce"
    )
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "titulo",
            "dataCriacao",
            "idLegislatura",
            "telefone",
            "email",
            "keywords",
            "idSituacao",
            "situacao",
            "urlWebsite",
            "urlDocumento",
            "coordenador_idCamara",
            "coordenador_uri",
            "coordenador_nome",
            "coordenador_siglaPartido",
            "coordenador_uriPartido",
            "coordenador_siglaUf",
            "coordenador_idLegislatura",
            "coordenador_urlFoto",
        ],
    )


def t_frentes_deputados(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    col_map = {
        "deputado_.id": "deputado_id",
        "deputado_.uri": "uriDeputado",
        "deputado_.uriPartido": "uriPartido",
        "deputado_.nome": "nomeDeputado",
        "deputado_.siglaUf": "siglaUf",
        "deputado_.idLegislatura": "idLegislatura",
        "deputado_.urlFoto": "urlFoto",
        "deputado_.codTitulo": "codTitulo",
        "deputado_.titulo": "titulo",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    df["idFrenteCamara"] = pd.to_numeric(df.get("id"), errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("deputado_id"), errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    df["codTitulo"] = pd.to_numeric(df.get("codTitulo"), errors="coerce")
    df["dataInicio"] = to_date_series(df.get("dataInicio"))
    df["dataFim"] = to_date_series(df.get("dataFim"))
    return keep_columns(
        df,
        [
            "idFrenteCamara",
            "idDeputadoCamara",
            "uriDeputado",
            "nomeDeputado",
            "siglaUf",
            "idLegislatura",
            "urlFoto",
            "codTitulo",
            "titulo",
            "dataInicio",
            "dataFim",
        ],
    )


def t_grupos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df).rename(columns={"idGrupo": "idCamara", "uriGrupo": "uri"})
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    df["anoCriacao"] = pd.to_numeric(df.get("anoCriacao"), errors="coerce")
    for c in ["subvencionado", "grupoMisto", "ativo"]:
        df[c] = to_boolean_series(df.get(c, pd.Series(dtype=str)))
    for c in [
        "ultimoStatus_dataStatus",
        "ultimoStatus_oficioDataApresentacao",
        "ultimoStatus_oficioDataPublicacao",
    ]:
        df[c] = to_datetime_series(df.get(c))
    return keep_columns(
        df,
        [
            "idCamara",
            "uri",
            "nomeGrupo",
            "anoCriacao",
            "projetoTitulo",
            "projetoUri",
            "resolucaoTitulo",
            "resolucaoUri",
            "subvencionado",
            "grupoMisto",
            "ativo",
            "observacao",
            "ultimoStatus_idLegislatura",
            "ultimoStatus_dataStatus",
            "ultimoStatus_presidenteNome",
            "ultimoStatus_presidenteUri",
            "ultimoStatus_documento",
            "ultimoStatus_oficioTitulo",
            "ultimoStatus_oficioUri",
            "ultimoStatus_oficioAutorTipo",
            "ultimoStatus_oficioAutorNome",
            "ultimoStatus_oficioAutorUri",
            "ultimoStatus_oficioDataApresentacao",
            "ultimoStatus_oficioDataPublicacao",
        ],
    )


def t_grupos_membros(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idGrupoCamara"] = pd.to_numeric(df.get("idGrupo"), errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("membro_id"), errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("membro_idlegislatura"), errors="coerce")
    df["ordemEntrada"] = pd.to_numeric(df.get("membro_ordem_entrada"), errors="coerce")
    df["dataInicio"] = to_datetime_series(df.get("membro_datainicio"))
    df["dataFim"] = to_datetime_series(df.get("membro_datafim"))
    df["nome"] = df.get("membro_nome")
    df["tipo"] = df.get("membro_tipo")
    df["uri"] = df.get("membro_uri")
    df["cargo"] = df.get("membro_cargo")
    return keep_columns(
        df,
        [
            "idGrupoCamara",
            "idDeputadoCamara",
            "idLegislatura",
            "ordemEntrada",
            "dataInicio",
            "dataFim",
            "nome",
            "tipo",
            "uri",
            "cargo",
        ],
    )


def t_grupos_historico(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idGrupoCamara"] = pd.to_numeric(df.get("id"), errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    for c in ["dataStatus", "oficioDataApresentacao", "oficioDataPublicacao"]:
        df[c] = to_datetime_series(df.get(c))
    return keep_columns(
        df,
        [
            "idGrupoCamara",
            "idLegislatura",
            "dataStatus",
            "documentoSgm",
            "presidente",
            "presidenteUri",
            "observacao",
            "oficioTitulo",
            "oficioAutorTipo",
            "oficioAutor",
            "oficioAutorUri",
            "oficioDataApresentacao",
            "oficioDataPublicacao",
        ],
    )


def t_funcionarios(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["codGrupo"] = pd.to_numeric(df.get("codGrupo"), errors="coerce")
    for c in ["dataNomeacao", "dataInicioHistorico", "dataPubNomeacao"]:
        df[c] = to_date_series(df.get(c, pd.Series(dtype=str)))
    df = df.drop_duplicates(subset=["ponto"], keep="last")
    return keep_columns(
        df,
        [
            "ponto",
            "codGrupo",
            "grupo",
            "nome",
            "cargo",
            "lotacao",
            "atoNomeacao",
            "dataNomeacao",
            "dataInicioHistorico",
            "dataPubNomeacao",
            "funcao",
            "uriLotacao",
        ],
    )


def t_licitacoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in [
        "numero",
        "ano",
        "numProcesso",
        "anoProcesso",
        "numItens",
        "numUnidades",
        "numPropostas",
        "numContratos",
    ]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["vlrEstimado", "vlrContratado", "vlrPago"]:
        df[c] = to_numeric_series(df.get(c, pd.Series(dtype=str)))
    for c in ["dataAutorizacao", "dataPublicacao", "dataAbertura"]:
        df[c] = to_date_series(df.get(c, pd.Series(dtype=str)))
    return keep_columns(
        df,
        [
            "idLicitacao",
            "numero",
            "ano",
            "numProcesso",
            "anoProcesso",
            "objeto",
            "modalidade",
            "tipo",
            "situacao",
            "vlrEstimado",
            "vlrContratado",
            "vlrPago",
            "dataAutorizacao",
            "dataPublicacao",
            "dataAbertura",
            "numItens",
            "numUnidades",
            "numPropostas",
            "numContratos",
        ],
    )


def t_licitacoes_pedidos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano", "numPedido", "anoPedido", "idOrgao"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["dataHoraCadastro"] = to_datetime_series(df.get("dataHoraCadastro"))
    return keep_columns(
        df,
        [
            "idLicitacao",
            "ano",
            "tipoRegistro",
            "numPedido",
            "anoPedido",
            "dataHoraCadastro",
            "idOrgao",
            "orgao",
            "objeto",
            "observacoes",
        ],
    )


def t_licitacoes_propostas(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano", "numItem", "numSubitens", "numProposta", "diasValidadeProposta"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["unidadesLicitadas", "vlrEstimado", "unidadesProposta", "vlrProposta"]:
        df[c] = to_numeric_series(df.get(c, pd.Series(dtype=str)))
    df["dataProposta"] = to_date_series(df.get("dataProposta"))
    return keep_columns(
        df,
        [
            "idLicitacao",
            "ano",
            "numItem",
            "descricao",
            "numSubitens",
            "unidadesLicitadas",
            "vlrEstimado",
            "unidadesProposta",
            "vlrProposta",
            "numProposta",
            "marcaProposta",
            "fornecedorCpfCnpj",
            "fornecedorSituacao",
            "dataProposta",
            "diasValidadeProposta",
            "observacoes",
            "urlDocumento",
        ],
    )


def t_licitacoes_itens(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano", "numItem", "numSubitem", "numContrato", "anoContrato"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in [
        "qtdLicitada",
        "vlrUnitarioEstimado",
        "qtdContratada",
        "vlrUnitarioContratado",
        "vlrTotalContratado",
    ]:
        df[c] = to_numeric_series(df.get(c, pd.Series(dtype=str)))
    return keep_columns(
        df,
        [
            "idLicitacao",
            "ano",
            "numItem",
            "numSubitem",
            "descricao",
            "especificacao",
            "unidade",
            "qtdLicitada",
            "vlrUnitarioEstimado",
            "qtdContratada",
            "vlrUnitarioContratado",
            "vlrTotalContratado",
            "fornecedorCpfCnpj",
            "fornecedorNome",
            "uriContrato",
            "numContrato",
            "anoContrato",
            "tipoContrato",
            "situacaoItem",
            "observacoes",
            "naturezaDespesa",
            "programaTrabalho",
            "codPTRES",
        ],
    )


def t_licitacoes_contratos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano", "numContrato", "anoContrato", "numSeqArquivoInstrContratual"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["vlrOriginal", "vlrTotal"]:
        df[c] = to_numeric_series(df.get(c, pd.Series(dtype=str)))
    for c in [
        "dataAssinatura",
        "dataPublicacao",
        "dataInicioVigenciaOriginal",
        "dataFimVigenciaOriginal",
        "dataFimUltimaVigencia",
    ]:
        df[c] = to_date_series(df.get(c, pd.Series(dtype=str)))
    return keep_columns(
        df,
        [
            "idLicitacao",
            "ano",
            "numContrato",
            "anoContrato",
            "tipoContrato",
            "situacaoContrato",
            "vlrOriginal",
            "vlrTotal",
            "objeto",
            "dataAssinatura",
            "dataPublicacao",
            "dataInicioVigenciaOriginal",
            "dataFimVigenciaOriginal",
            "dataFimUltimaVigencia",
            "fornecedorCpfCnpj",
            "fornecedorNome",
            "fornecedorEndereco",
            "fornecedorCidade",
            "fornecedorSiglaUF",
            "numSeqArquivoInstrContratual",
            "txtNomeArquivo",
        ],
    )


def t_tecad_categorias(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    for c in ["codCategoria", "codSubCategoria"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return keep_columns(
        df, ["codCategoria", "categoria", "codSubCategoria", "subCategoria"]
    )


def t_tecad_termos(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = clean_dataframe(df)
    df["codTermo"] = pd.to_numeric(df.get("codTermo"), errors="coerce")
    return keep_columns(
        df,
        [
            "codTermo",
            "termo",
            "categorias",
            "subcategorias",
            "notasExplicativas",
            "notasHistoricas",
            "notasAplicativas",
            "fontes",
            "use",
            "usadoPara",
            "termosEspecificos",
            "termosGenericos",
            "termosRelacionados",
        ],
    )


_COTA_COL_MAP = {
    "ideCadastro": "idDeputadoCamara",
    "numAno": "ano",
    "numMes": "mes",
    "txtDescricao": "tipoDespesa",
    "txtFornecedor": "nomeFornecedor",
    "txtCNPJCPF": "cnpjCpfFornecedor",
    "txtNumero": "numDocumento",
    "indTipoDocumento": "codTipoDocumento",
    "datEmissao": "dataDocumento",
    "vlrDocumento": "valorDocumento",
    "vlrGlosa": "valorGlosa",
    "vlrLiquido": "valorLiquido",
    "numParcela": "parcela",
    "numLote": "codLote",
    "numRessarcimento": "numRessarcimento",
    "ideDocumento": "codDocumento",
    "urlDocumento": "urlDocumento",
    "txtPassageiro": "txPassageiro",
    "txtTrecho": "txTrecho",
    "numEspecificacaoSubCota": "numEspecificacaoSubCota",
    "numSubCota": "numSubCota",
}


def t_cotas(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Transformação de Cotas Parlamentares (CEAP)."""
    df = clean_dataframe(df)
    df = df.rename(columns={k: v for k, v in _COTA_COL_MAP.items() if k in df.columns})

    for c in [
        "idDeputadoCamara",
        "ano",
        "mes",
        "parcela",
        "numSubCota",
        "numEspecificacaoSubCota",
        "codTipoDocumento",
    ]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")

    for c in ["valorDocumento", "valorGlosa", "valorLiquido"]:
        df[c] = to_numeric_series(df.get(c, pd.Series(dtype=str)))

    df["dataDocumento"] = to_datetime_series(df.get("dataDocumento"))

    df = df.dropna(subset=["codDocumento", "idDeputadoCamara"])
    df["codDocumento"] = df["codDocumento"].astype(str).str.strip()
    df = df[df["codDocumento"].str.len() > 0]

    # Despesas oficiais (ex: telefonia direta) possuem ideDocumento == '0' no open data.
    # Sintetiza uma chave única e determinística para evitar colisão e CardinalityViolation.
    mask_zero = df["codDocumento"].isin(["0", "0.0"])
    if mask_zero.any():
        num_doc = df.loc[mask_zero, "numDocumento"].fillna("").astype(str).str.strip()
        sub_cota = (
            df.loc[mask_zero, "numSubCota"]
            .fillna("0")
            .astype(int, errors="ignore")
            .astype(str)
        )
        dep_id = (
            df.loc[mask_zero, "idDeputadoCamara"]
            .astype(int, errors="ignore")
            .astype(str)
        )
        mes_val = (
            df.loc[mask_zero, "mes"]
            .fillna("0")
            .astype(int, errors="ignore")
            .astype(str)
        )
        ano_val = (
            df.loc[mask_zero, "ano"]
            .fillna("0")
            .astype(int, errors="ignore")
            .astype(str)
        )
        parc = (
            df.loc[mask_zero, "parcela"]
            .fillna("0")
            .astype(int, errors="ignore")
            .astype(str)
        )
        vlr = df.loc[mask_zero, "valorLiquido"].fillna("0").astype(str)
        df.loc[mask_zero, "codDocumento"] = (
            "0-"
            + dep_id
            + "-"
            + ano_val
            + "-"
            + mes_val
            + "-"
            + sub_cota
            + "-"
            + num_doc
            + "-"
            + parc
            + "-"
            + vlr
        ).str[:90]

    # Deduplicação determinística em memória mantendo o último registro (restituições/correções)
    df = df.drop_duplicates(subset=["codDocumento"], keep="last")

    return keep_columns(
        df,
        [
            "idDeputadoCamara",
            "codDocumento",
            "ano",
            "mes",
            "tipoDespesa",
            "numSubCota",
            "numEspecificacaoSubCota",
            "codTipoDocumento",
            "dataDocumento",
            "numDocumento",
            "valorDocumento",
            "valorGlosa",
            "valorLiquido",
            "nomeFornecedor",
            "cnpjCpfFornecedor",
            "urlDocumento",
            "parcela",
            "codLote",
            "numRessarcimento",
            "txPassageiro",
            "txTrecho",
        ],
    )


def t_partidos(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Transformação e validação de partidos políticos (partidos.csv)."""
    df = clean_dataframe(df).rename(columns={"id": "idCamara"})
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    for c in ["numeroEleitoral", "totalMembros", "totalPosse"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["idCamara", "sigla"])
    df["idCamara"] = df["idCamara"].astype(int)
    df = df.drop_duplicates(subset=["idCamara"], keep="last")

    return keep_columns(
        df,
        [
            "idCamara",
            "sigla",
            "nome",
            "uri",
            "numeroEleitoral",
            "situacao",
            "totalMembros",
            "totalPosse",
            "urlLogo",
            "urlWebsite",
            "urlFacebook",
        ],
    )


def t_proposicoes_tramitacoes(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Transformação de passos de tramitação legislativa (proposicoesTramitacoes-{ano}.csv)."""
    df = clean_dataframe(df)
    # Extrai idProposicaoCamara da uriProposicao se coluna direta não existir
    if "idProposicaoCamara" not in df.columns:
        uri_col = df["uriProposicao"].fillna("").astype(str)
        extracted = uri_col.str.extract(r"/proposicoes/(\d+)")
        df["idProposicaoCamara"] = pd.to_numeric(extracted[0], errors="coerce")
    else:
        df["idProposicaoCamara"] = pd.to_numeric(
            df["idProposicaoCamara"], errors="coerce"
        )

    df["sequencia"] = pd.to_numeric(df.get("sequencia"), errors="coerce")
    df["dataHora"] = to_datetime_series(df.get("dataHora"))
    df["codTipoTramitacao"] = pd.to_numeric(
        df.get("codTipoTramitacao"), errors="coerce"
    )
    df["codSituacao"] = pd.to_numeric(df.get("codSituacao"), errors="coerce")

    df = df.dropna(subset=["idProposicaoCamara", "sequencia", "dataHora"])
    df["idProposicaoCamara"] = df["idProposicaoCamara"].astype(int)
    df["sequencia"] = df["sequencia"].astype(int)

    # Deduplicação determinística em memória
    df = df.drop_duplicates(
        subset=["idProposicaoCamara", "sequencia", "dataHora"], keep="last"
    )

    return keep_columns(
        df,
        [
            "idProposicaoCamara",
            "sequencia",
            "dataHora",
            "siglaOrgao",
            "uriOrgao",
            "uriUltimoRelator",
            "regime",
            "descricaoTramitacao",
            "codTipoTramitacao",
            "descricaoSituacao",
            "codSituacao",
            "despacho",
            "url",
            "ambito",
            "apreciacao",
        ],
    )


def t_deputados_historico(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Transformação de histórico parlamentar, suplências e licenças (deputadosHistorico.csv)."""
    df = clean_dataframe(df).rename(
        columns={"id": "idDeputadoCamara", "siglaUf": "siglaUF"}
    )
    df["idDeputadoCamara"] = pd.to_numeric(df["idDeputadoCamara"], errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    df["idPartido"] = pd.to_numeric(df.get("idPartido"), errors="coerce")
    df["dataInicio"] = to_datetime_series(df.get("dataInicio"))
    df["dataFim"] = to_datetime_series(df.get("dataFim"))

    df = df.dropna(subset=["idDeputadoCamara", "dataInicio"])
    df["idDeputadoCamara"] = df["idDeputadoCamara"].astype(int)

    df = df.drop_duplicates(
        subset=["idDeputadoCamara", "idLegislatura", "dataInicio", "descricao"],
        keep="last",
    )

    return keep_columns(
        df,
        [
            "idDeputadoCamara",
            "idLegislatura",
            "dataInicio",
            "dataFim",
            "nome",
            "siglaPartido",
            "siglaUF",
            "idPartido",
            "condicao",
            "situacao",
            "descricao",
        ],
    )


def t_deputados_mandatos_externos(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Transformação de cargos eletivos anteriores fora da Câmara (deputadosMandatosExternos.csv)."""
    df = clean_dataframe(df).rename(
        columns={"id": "idDeputadoCamara", "siglaUf": "siglaUF"}
    )
    df["idDeputadoCamara"] = pd.to_numeric(df["idDeputadoCamara"], errors="coerce")
    df["anoInicio"] = pd.to_numeric(df.get("anoInicio"), errors="coerce")
    df["anoFim"] = pd.to_numeric(df.get("anoFim"), errors="coerce")

    df = df.dropna(subset=["idDeputadoCamara", "cargo"])
    df["idDeputadoCamara"] = df["idDeputadoCamara"].astype(int)

    df = df.drop_duplicates(
        subset=["idDeputadoCamara", "cargo", "siglaUF", "anoInicio"],
        keep="last",
    )

    return keep_columns(
        df,
        [
            "idDeputadoCamara",
            "cargo",
            "siglaUF",
            "municipio",
            "anoInicio",
            "anoFim",
            "siglaPartidoEleicao",
            "uriPartidoEleicao",
        ],
    )
