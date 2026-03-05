"""
etl_camara.py
=============
Download + ETL para o banco de dados da Câmara dos Deputados.
Fonte: dadosabertos.camara.leg.br

Uso:
    # Carga inicial completa (anos 2019–corrente)
    python etl_camara.py --full

    # Atualizar apenas o ano corrente
    python etl_camara.py --update

    # Dataset específico + anos
    python etl_camara.py --dataset votacoes --anos 2023 2024

Dependências:
    pip install requests pandas sqlalchemy psycopg2-binary tqdm python-dotenv
"""

from __future__ import annotations
import numpy as np
import argparse
import io
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("etl_camara.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("etl_camara")

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
load_dotenv()
DATABASE_URL   = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/quemvota_teste")
BASE_URL       = "http://dadosabertos.camara.leg.br/arquivos"
FORMATO        = "csv"
ANO_ATUAL      = datetime.now().year
ANOS_HISTORICO = list(range(2008, ANO_ATUAL + 1))
REQUEST_TIMEOUT = 60
CHUNK_SIZE      = 5_000
MAX_RETRIES     = 3
RETRY_DELAY     = 5


# ===========================================================================
# Cache de ETag / Last-Modified
# ===========================================================================

CACHE_FILE = Path(os.getenv("ETL_CACHE_FILE", "etl_cache.json"))


def _cache_load() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _cache_save(cache: dict) -> None:
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CACHE_FILE)


# Sentinel retornado quando o servidor confirma 304 Not Modified
_CACHE_HIT = object()


# ===========================================================================
# Helpers de download
# ===========================================================================

def _download_csv(url: str, cache: Optional[dict] = None) -> Optional[pd.DataFrame]:
    headers = {}
    if cache is not None:
        entry = cache.get(url, {})
        if entry.get("etag"):
            headers["If-None-Match"] = entry["etag"]
        elif entry.get("last_modified"):
            headers["If-Modified-Since"] = entry["last_modified"]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 304:
                log.info("→ sem alterações (304): %s", url.split("/")[-1])
                return _CACHE_HIT
            if resp.status_code == 404:
                log.warning("404 — não encontrado: %s", url)
                return None
            resp.raise_for_status()
            if cache is not None:
                entry = {}
                if resp.headers.get("ETag"):
                    entry["etag"] = resp.headers["ETag"]
                if resp.headers.get("Last-Modified"):
                    entry["last_modified"] = resp.headers["Last-Modified"]
                if entry:
                    cache[url] = entry
            df = pd.read_csv(
                io.StringIO(resp.content.decode("utf-8-sig", errors="replace")),
                sep=";", dtype=str, low_memory=False,
            )
            log.info("✔ %s (%d linhas)", url.split("/")[-1], len(df))
            return df
        except Exception as exc:
            log.warning("Tentativa %d/%d falhou (%s): %s", attempt, MAX_RETRIES, url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    log.error("Falha permanente: %s", url)
    return None

def url_simples(dataset: str) -> str:
    return f"{BASE_URL}/{dataset}/{FORMATO}/{dataset}.{FORMATO}"

def url_anual(dataset: str, ano: int) -> str:
    return f"{BASE_URL}/{dataset}/{FORMATO}/{dataset}-{ano}.{FORMATO}"

def url_legislatura(dataset: str, leg: int) -> str:
    return f"{BASE_URL}/{dataset}/{FORMATO}/{dataset}-L{leg}.{FORMATO}"

# Cotas parlamentares — fonte: camara.leg.br (não dadosabertos)
COTAS_BASE_URL = "http://www.camara.leg.br/cotas"

def url_cota_anual(ano: int) -> str:
    """http://www.camara.leg.br/cotas/Ano-{ano}.csv.zip"""
    return f"{COTAS_BASE_URL}/Ano-{ano}.csv.zip"


# ===========================================================================
# Helpers de transformação
# ===========================================================================

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # 1. LIMPEZA GLOBAL: Remove o BOM (\ufeff), aspas duplas e espaços de TODAS as colunas
    df.columns = df.columns.str.replace('\ufeff', '').str.replace('"', '').str.strip()
    
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip().replace({"": None, "nan": None, "None": None})
    return df

def _date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.date

def _dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")

def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(",", ".").str.replace(r"[^\d.\-]", "", regex=True),
        errors="coerce",
    )

def _bool(s: pd.Series) -> pd.Series:
    m = {"true": True, "false": False, "1": True, "0": False, "sim": True, "não": False}
    return s.astype(str).str.lower().map(m)

def _sanitize(v):
    """Converte NaT, NaN e float NaN para None — psycopg2 não aceita esses tipos."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    # pandas Timestamp → deixa passar (psycopg2 aceita); NaT já capturado acima
    return v


def _keep(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    sub = df[[c for c in cols if c in df.columns]]
    return [
        {k: _sanitize(v) for k, v in row.items()}
        for row in sub.to_dict("records")
    ]


# ===========================================================================
# Upsert em lotes via ON CONFLICT DO UPDATE
# ===========================================================================

def upsert(engine, table_name: str, preserve_cols: list[str], records: list[dict], conflict_cols: list[str]) -> int:
    if not records:
        return 0
    from sqlalchemy import Table, MetaData
    meta = MetaData()
    meta.reflect(bind=engine, only=[table_name])
    table = meta.tables[table_name]
    _preserve = set(preserve_cols or [])
    total = 0
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i : i + CHUNK_SIZE]
        stmt = pg_insert(table).values(chunk)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in table.columns
            if c.name not in conflict_cols
            and c.name != "id"
            and c.name not in _preserve
        }
        if update_cols:
            stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
        with engine.begin() as conn:
            conn.execute(stmt)
        total += len(chunk)
    return total


# ===========================================================================
# Transformações por entidade
# ===========================================================================

def t_legislaturas(df):
    df = _clean(df).rename(columns={"id": "idLegislatura"})
    df["idLegislatura"] = pd.to_numeric(df["idLegislatura"], errors="coerce")
    df["dataInicio"] = _date(df.get("dataInicio"))
    df["dataFim"]    = _date(df.get("dataFim"))
    df["anoEleicao"] = pd.to_numeric(df.get("anoEleicao"), errors="coerce")
    return _keep(df, ["idLegislatura","uri","dataInicio","dataFim","anoEleicao"])


def t_legislaturas_mesas(df):
    df = _clean(df)
    df["dataInicio"]    = _dt(df.get("dataInicio"))
    df["dataFim"]       = _dt(df.get("dataFim"))
    for c in ["idLegislatura","idOrgao","idDeputado"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return _keep(df, ["idLegislatura","idOrgao","uriOrgao","siglaOrgao","nomeOrgao",
                       "idDeputado","uriDeputado","nomeDeputado","siglaPartido",
                       "siglaUF","cargo","dataInicio","dataFim"])


def t_orgaos(df):
    df = _clean(df)

    # Se existe a coluna URI, divide o texto pela barra '/' e pega o último elemento ([-1])
    if "uri" in df.columns:
        df["idCamara"] = df["uri"].astype(str).str.split("/").str[-1]
    else:
        # Fallback de segurança
        df["idCamara"] = df.get("id")
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    for c in ["dataInicio","dataInstalacao","dataFim","dataFimOriginal"]:
        df[c] = _date(df.get(c, pd.Series(dtype=str)))
    for c in ["codTipoOrgao","codSituacao"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return _keep(df, ["idCamara","uri","sigla","apelido","nome","nomePublicacao",
                       "codTipoOrgao","tipoOrgao","casa","sala","dataInicio","dataInstalacao",
                       "dataFim","dataFimOriginal","codSituacao","descricaoSituacao","urlWebsite"])


def t_orgaos_deputados(df):
    df = _clean(df)
    # CSV não tem idOrgao/idDeputado diretamente — extrai o id do final da URI
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

    for c in ["dataInicio","dataFim"]:
        df[c] = _date(df.get(c, pd.Series(dtype=str)))
    df["codTitulo"] = pd.to_numeric(df.get("codTitulo"), errors="coerce")
    return _keep(df, ["idOrgaoCamara","idDeputadoCamara","nomePublicacaoOrgao",
                       "uriDeputado","nomeDeputado","siglaPartido","siglaUF",
                       "cargo","codTitulo","dataInicio","dataFim"])


def t_deputados(df):
    df = _clean(df)
    
    # --- A MÁGICA ACONTECE AQUI ---
    # Se existe a coluna URI, divide o texto pela barra '/' e pega o último elemento ([-1])
    if "uri" in df.columns:
        df["idCamara"] = df["uri"].astype(str).str.split("/").str[-1]
    else:
        # Fallback de segurança
        df["idCamara"] = df.get("id")
        
    # Converte o texto extraído (ex: "220593") para número
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    
    # Processa os outros campos
    for c in ["idLegislaturaInicial","idLegislaturaFinal"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["dataNascimento","dataFalecimento"]:
        df[c] = pd.to_datetime(df.get(c), errors="coerce")
        
    return _keep(df, ["idCamara","uri","nome","nomeCivil","cpf","siglaSexo",
                       "idLegislaturaInicial","idLegislaturaFinal",
                       "dataNascimento","dataFalecimento","ufNascimento","municipioNascimento",
                       "siglaUF","siglaPartido","urlRedeSocial","urlWebsite"])

def t_deputados_ocupacoes(df):
    df = _clean(df)

    # CSV: coluna "id" = idCamara do deputado (não o PK interno).
    # Guardamos como "idDeputadoCamara" para resolução FK no _resolve_and_insert.
    df["idDeputadoCamara"] = pd.to_numeric(df.get("id"), errors="coerce")

    # Processar as colunas de ano
    for c in ["anoInicio", "anoFim"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
        df.loc[(df[c] > 2100) | (df[c] < 1800), c] = np.nan
        df[c] = df[c].astype(pd.Int64Dtype())

    df = df.drop_duplicates(subset=["idDeputadoCamara", "titulo", "anoInicio"], keep="last")

    return _keep(df, ["idDeputadoCamara", "titulo", "entidade", "entidadeUF", "entidadePais", "anoInicio", "anoFim"])

def t_deputados_profissoes(df):
    df = _clean(df)
    # CSV: coluna "id" = idCamara do deputado (não o PK interno).
    # Guardamos como "idDeputadoCamara" para resolução FK no _resolve_and_insert.
    df["idDeputadoCamara"] = pd.to_numeric(df.get("id"), errors="coerce")
    df["codTipoProfissao"] = pd.to_numeric(df.get("codTipoProfissao"), errors="coerce")
    df["dataHora"]         = _dt(df.get("dataHora"))
    return _keep(df, ["idDeputadoCamara","dataHora","codTipoProfissao","titulo"])


def t_eventos(df):
    df = _clean(df).rename(columns={"id": "idCamara"})
    df["idCamara"]       = pd.to_numeric(df["idCamara"], errors="coerce")
    df["dataHoraInicio"] = _dt(df.get("dataHoraInicio"))
    df["dataHoraFim"]    = _dt(df.get("dataHoraFim"))
    for campo, orig in [("localCamaraNome","localCamara.nome"), ("localCamaraPredio","localCamara.predio"),
                         ("localCamaraSala","localCamara.sala"), ("localCamaraAndar","localCamara.andar")]:
        if orig in df.columns:
            df[campo] = df[orig]
    return _keep(df, ["idCamara","uri","urlDocumentoPauta","dataHoraInicio","dataHoraFim",
                       "situacao","descricao","descricaoTipo","localExterno",
                       "localCamaraNome","localCamaraPredio","localCamaraSala","localCamaraAndar","urlEvento"])


def t_eventos_orgaos(df):
    df = _clean(df)
    df["idEventoCamara"] = pd.to_numeric(df.get("idEvento"), errors="coerce")
    df["idOrgaoCamara"]  = pd.to_numeric(df.get("idOrgao"),  errors="coerce")
    return df[["idEventoCamara","idOrgaoCamara"]].dropna().to_dict("records")


def t_eventos_reqs(df):
    df = _clean(df)
    df["idEventoCamara"] = pd.to_numeric(df.get("idEvento"), errors="coerce")
    return _keep(df, ["idEventoCamara","tituloRequerimento","uriRequerimento"])


def t_presenca(df):
    df = _clean(df)
    df["idEventoCamara"]   = pd.to_numeric(df.get("idEvento"),   errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("idDeputado"), errors="coerce")
    df["dataHoraInicio"]   = _dt(df.get("dataHoraInicio"))
    return _keep(df, ["idEventoCamara","idDeputadoCamara","dataHoraInicio"])


def t_proposicoes(df):
    df = _clean(df).rename(columns={"id": "idCamara"})
    df["idCamara"] = pd.to_numeric(df["idCamara"], errors="coerce")
    for c in ["codTipo","numero","ano","ultimoStatus_idOrgao","ultimoStatus_sequencia",
              "ultimoStatus_idTipoTramitacao","ultimoStatus_idSituacao"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["dataApresentacao"]      = _dt(df.get("dataApresentacao"))
    df["ultimoStatus_dataHora"] = _dt(df.get("ultimoStatus_dataHora"))
    return _keep(df, [
        "idCamara","uri","siglaTipo","codTipo","numero","ano","descricaoTipo",
        "ementa","ementaDetalhada","keywords","dataApresentacao",
        "uriOrgaoNumerador","uriPropAnterior","uriPropPrincipal","uriPropPosterior",
        "urlInteiroTeor","urnFinal",
        "ultimoStatus_dataHora","ultimoStatus_sequencia","ultimoStatus_uriRelator",
        "ultimoStatus_idOrgao","ultimoStatus_siglaOrgao","ultimoStatus_uriOrgao",
        "ultimoStatus_regime","ultimoStatus_descricaoTramitacao",
        "ultimoStatus_idTipoTramitacao","ultimoStatus_descricaoSituacao",
        "ultimoStatus_idSituacao","ultimoStatus_despacho",
        "ultimoStatus_apreciacao","ultimoStatus_url",
    ])


def t_proposicoes_autores(df):
    df = _clean(df)
    df["idProposicaoCamara"] = pd.to_numeric(df.get("idProposicao"),    errors="coerce")
    df["idDeputadoCamara"]   = pd.to_numeric(df.get("idDeputadoAutor"), errors="coerce")
    df["codTipoAutor"]       = pd.to_numeric(df.get("codTipoAutor"),    errors="coerce")
    df["ordemAssinatura"]    = pd.to_numeric(df.get("ordemAssinatura"), errors="coerce")
    df["proponente"]         = _bool(df.get("proponente", pd.Series(dtype=str)))
    return _keep(df, ["idProposicaoCamara","idDeputadoCamara","uriAutor","codTipoAutor",
                       "tipoAutor","nomeAutor","siglaPartidoAutor","uriPartidoAutor",
                       "siglaUFAutor","ordemAssinatura","proponente"])


def t_proposicoes_temas(df):
    df = _clean(df)
    # CSV não tem "idProposicao" — extrai o id do final de "uriProposicao"
    if "uriProposicao" in df.columns:
        df["idProposicaoCamara"] = pd.to_numeric(
            df["uriProposicao"].astype(str).str.split("/").str[-1], errors="coerce"
        )
    else:
        df["idProposicaoCamara"] = pd.to_numeric(df.get("idProposicao"), errors="coerce")
    df["codTema"] = pd.to_numeric(df.get("codTema"), errors="coerce")
    return _keep(df, ["idProposicaoCamara","codTema","tema"])


def t_votacoes(df):
    df = _clean(df).rename(columns={"id": "idCamara"})
    df["data"]             = _date(df.get("data"))
    df["dataHoraRegistro"] = _dt(df.get("dataHoraRegistro"))
    df["ultimaAberturaVotacao_dataHoraRegistro"] = _dt(df.get("ultimaAberturaVotacao_dataHoraRegistro"))
    df["ultimaApresentacaoProposicao_dataHoraRegistro"] = _dt(df.get("ultimaApresentacaoProposicao_dataHoraRegistro"))
    for c in ["aprovacao","votosSim","votosNao","votosOutros"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["idOrgaoCamara"]      = pd.to_numeric(df.get("idOrgao"),  errors="coerce")
    df["idEventoCamara"]     = pd.to_numeric(df.get("idEvento"), errors="coerce")
    df["idProposicaoCamara"] = pd.to_numeric(df.get("ultimaApresentacaoProposicao_idProposicao"), errors="coerce")
    return _keep(df, [
        "idCamara","uri","data","dataHoraRegistro",
        "idOrgaoCamara","uriOrgao","siglaOrgao","idEventoCamara","uriEvento",
        "aprovacao","votosSim","votosNao","votosOutros","descricao","tipoVotacao",
        "ultimaAberturaVotacao_dataHoraRegistro","ultimaAberturaVotacao_descricao",
        "ultimaApresentacaoProposicao_dataHoraRegistro","ultimaApresentacaoProposicao_descricao",
        "idProposicaoCamara","ultimaApresentacaoProposicao_uriProposicao",
    ])


def t_votacoes_votos(df):
    df = _clean(df)
    df["idVotacaoCamara"]  = df.get("idVotacao")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("deputado_id"), errors="coerce")
    df["dataHoraVoto"]     = _dt(df.get("dataHoraVoto"))
    df["idLegislatura"]    = pd.to_numeric(df.get("deputado_idLegislatura"), errors="coerce")
    df["siglaPartido"]     = df.get("deputado_siglaPartido")
    df["uriPartido"]       = df.get("deputado_uriPartido")
    df["siglaUF"]          = df.get("deputado_siglaUf")
    return _keep(df, ["idVotacaoCamara","idDeputadoCamara","dataHoraVoto","voto",
                       "siglaPartido","uriPartido","siglaUF","idLegislatura"])


def t_votacoes_orientacoes(df):
    df = _clean(df)
    df["idVotacaoCamara"] = df.get("idVotacao")
    return _keep(df, ["idVotacaoCamara","siglaOrgao","siglaBancada","uriBancada","orientacao"])


def t_votacoes_objetos(df):
    df = _clean(df)
    # O arquivo do governo chama-se "votacoesProposicoes-AAAA.csv";
    # a coluna de ID da votação é "idVotacao" em ambos os casos.
    df["idVotacaoCamara"] = df.get("idVotacao")
    df["data"]            = _date(df.get("data"))
    for c in ["proposicao_codTipo","proposicao_numero","proposicao_ano","proposicao_id"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return _keep(df, ["idVotacaoCamara","data","descricao",
                       "proposicao_id","proposicao_uri","proposicao_ementa",
                       "proposicao_codTipo","proposicao_siglaTipo",
                       "proposicao_numero","proposicao_ano","proposicao_titulo"])


def t_frentes(df):
    df = _clean(df).rename(columns={"id": "idCamara"})
    df["idCamara"]      = pd.to_numeric(df["idCamara"], errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    df["idSituacao"]    = pd.to_numeric(df.get("idSituacao"),    errors="coerce")
    df["dataCriacao"]   = _date(df.get("dataCriacao"))
    # coordenador_id no CSV = idCamara do deputado; FK interna é resolvida via _raw_
    df["coordenador_idCamara"] = pd.to_numeric(df.get("coordenador_id"), errors="coerce")
    return _keep(df, ["idCamara","uri","titulo","dataCriacao","idLegislatura",
                       "telefone","email","keywords","idSituacao","situacao",
                       "urlWebsite","urlDocumento",
                       "coordenador_idCamara","coordenador_uri","coordenador_nome",
                       "coordenador_siglaPartido","coordenador_uriPartido",
                       "coordenador_siglaUf","coordenador_idLegislatura","coordenador_urlFoto"])


def t_frentes_deputados(df):
    df = _clean(df)
    # CSV usa "deputado_.id", "deputado_.uri", etc. — renomear para nomes limpos
    col_map = {
        "deputado_.id":           "deputado_id",
        "deputado_.uri":          "uriDeputado",
        "deputado_.uriPartido":   "uriPartido",
        "deputado_.nome":         "nomeDeputado",
        "deputado_.siglaUf":      "siglaUf",
        "deputado_.idLegislatura":"idLegislatura",
        "deputado_.urlFoto":      "urlFoto",
        "deputado_.codTitulo":    "codTitulo",
        "deputado_.titulo":       "titulo",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # "id" no CSV = idCamara da frente; "deputado_id" = idCamara do deputado
    df["idFrenteCamara"]   = pd.to_numeric(df.get("id"),         errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("deputado_id"),errors="coerce")
    df["idLegislatura"]    = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    df["codTitulo"]        = pd.to_numeric(df.get("codTitulo"), errors="coerce")
    df["dataInicio"]       = _date(df.get("dataInicio"))
    df["dataFim"]          = _date(df.get("dataFim"))
    return _keep(df, ["idFrenteCamara","idDeputadoCamara","uriDeputado","nomeDeputado",
                       "siglaUf","idLegislatura","urlFoto","codTitulo","titulo","dataInicio","dataFim"])


def t_grupos(df):
    df = _clean(df).rename(columns={"idGrupo": "idCamara", "uriGrupo": "uri"})
    df["idCamara"]   = pd.to_numeric(df["idCamara"],   errors="coerce")
    df["anoCriacao"] = pd.to_numeric(df.get("anoCriacao"), errors="coerce")
    for c in ["subvencionado","grupoMisto","ativo"]:
        df[c] = _bool(df.get(c, pd.Series(dtype=str)))
    for c in ["ultimoStatus_dataStatus","ultimoStatus_oficioDataApresentacao","ultimoStatus_oficioDataPublicacao"]:
        df[c] = _dt(df.get(c))
    return _keep(df, [
        "idCamara","uri","nomeGrupo","anoCriacao",
        "projetoTitulo","projetoUri","resolucaoTitulo","resolucaoUri",
        "subvencionado","grupoMisto","ativo","observacao",
        "ultimoStatus_idLegislatura","ultimoStatus_dataStatus",
        "ultimoStatus_presidenteNome","ultimoStatus_presidenteUri",
        "ultimoStatus_documento","ultimoStatus_oficioTitulo","ultimoStatus_oficioUri",
        "ultimoStatus_oficioAutorTipo","ultimoStatus_oficioAutorNome","ultimoStatus_oficioAutorUri",
        "ultimoStatus_oficioDataApresentacao","ultimoStatus_oficioDataPublicacao",
    ])


def t_grupos_membros(df):
    df = _clean(df)
    df["idGrupoCamara"]    = pd.to_numeric(df.get("idGrupo"),              errors="coerce")
    df["idDeputadoCamara"] = pd.to_numeric(df.get("membro_id"),            errors="coerce")
    df["idLegislatura"]    = pd.to_numeric(df.get("membro_idlegislatura"), errors="coerce")
    df["ordemEntrada"]     = pd.to_numeric(df.get("membro_ordem_entrada"), errors="coerce")
    df["dataInicio"]       = _dt(df.get("membro_datainicio"))
    df["dataFim"]          = _dt(df.get("membro_datafim"))
    df["nome"]  = df.get("membro_nome")
    df["tipo"]  = df.get("membro_tipo")
    df["uri"]   = df.get("membro_uri")
    df["cargo"] = df.get("membro_cargo")
    return _keep(df, ["idGrupoCamara","idDeputadoCamara","idLegislatura","ordemEntrada",
                       "dataInicio","dataFim","nome","tipo","uri","cargo"])


def t_grupos_historico(df):
    df = _clean(df)
    # CSV: coluna "id" = idCamara do grupo (não o PK interno)
    df["idGrupoCamara"] = pd.to_numeric(df.get("id"), errors="coerce")
    df["idLegislatura"] = pd.to_numeric(df.get("idLegislatura"), errors="coerce")
    for c in ["dataStatus","oficioDataApresentacao","oficioDataPublicacao"]:
        df[c] = _dt(df.get(c))
    return _keep(df, ["idGrupoCamara","idLegislatura","dataStatus","documentoSgm",
                       "presidente","presidenteUri","observacao","oficioTitulo",
                       "oficioAutorTipo","oficioAutor","oficioAutorUri",
                       "oficioDataApresentacao","oficioDataPublicacao"])


def t_funcionarios(df):
    df = _clean(df)
    df["codGrupo"] = pd.to_numeric(df.get("codGrupo"), errors="coerce")
    for c in ["dataNomeacao","dataInicioHistorico","dataPubNomeacao"]:
        df[c] = _date(df.get(c, pd.Series(dtype=str)))
    df = df.drop_duplicates(subset=["ponto"], keep="last") 
    return _keep(df, ["ponto","codGrupo","grupo","nome","cargo","lotacao",
                       "atoNomeacao","dataNomeacao","dataInicioHistorico",
                       "dataPubNomeacao","funcao","uriLotacao"])


def t_licitacoes(df):
    df = _clean(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["numero","ano","numProcesso","anoProcesso","numItens","numUnidades","numPropostas","numContratos"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["vlrEstimado","vlrContratado","vlrPago"]:
        df[c] = _num(df.get(c, pd.Series(dtype=str)))
    for c in ["dataAutorizacao","dataPublicacao","dataAbertura"]:
        df[c] = _date(df.get(c, pd.Series(dtype=str)))
    return _keep(df, ["idLicitacao","numero","ano","numProcesso","anoProcesso",
                       "objeto","modalidade","tipo","situacao",
                       "vlrEstimado","vlrContratado","vlrPago",
                       "dataAutorizacao","dataPublicacao","dataAbertura",
                       "numItens","numUnidades","numPropostas","numContratos"])


def t_licitacoes_pedidos(df):
    df = _clean(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano","numPedido","anoPedido","idOrgao"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["dataHoraCadastro"] = _dt(df.get("dataHoraCadastro"))
    return _keep(df, ["idLicitacao","ano","tipoRegistro","numPedido","anoPedido",
                       "dataHoraCadastro","idOrgao","orgao","objeto","observacoes"])


def t_licitacoes_propostas(df):
    df = _clean(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano","numItem","numSubitens","numProposta","diasValidadeProposta"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["unidadesLicitadas","vlrEstimado","unidadesProposta","vlrProposta"]:
        df[c] = _num(df.get(c, pd.Series(dtype=str)))
    df["dataProposta"] = _date(df.get("dataProposta"))
    return _keep(df, ["idLicitacao","ano","numItem","descricao","numSubitens",
                       "unidadesLicitadas","vlrEstimado","unidadesProposta","vlrProposta",
                       "numProposta","marcaProposta","fornecedorCpfCnpj","fornecedorSituacao",
                       "dataProposta","diasValidadeProposta","observacoes","urlDocumento"])


def t_licitacoes_itens(df):
    df = _clean(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano","numItem","numSubitem","numContrato","anoContrato"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["qtdLicitada","vlrUnitarioEstimado","qtdContratada","vlrUnitarioContratado","vlrTotalContratado"]:
        df[c] = _num(df.get(c, pd.Series(dtype=str)))
    return _keep(df, ["idLicitacao","ano","numItem","numSubitem","descricao","especificacao",
                       "unidade","qtdLicitada","vlrUnitarioEstimado","qtdContratada",
                       "vlrUnitarioContratado","vlrTotalContratado",
                       "fornecedorCpfCnpj","fornecedorNome","uriContrato",
                       "numContrato","anoContrato","tipoContrato","situacaoItem",
                       "observacoes","naturezaDespesa","programaTrabalho","codPTRES"])


def t_licitacoes_contratos(df):
    df = _clean(df)
    df["idLicitacao"] = pd.to_numeric(df.get("idLicitacao"), errors="coerce")
    for c in ["ano","numContrato","anoContrato","numSeqArquivoInstrContratual"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    for c in ["vlrOriginal","vlrTotal"]:
        df[c] = _num(df.get(c, pd.Series(dtype=str)))
    for c in ["dataAssinatura","dataPublicacao","dataInicioVigenciaOriginal","dataFimVigenciaOriginal","dataFimUltimaVigencia"]:
        df[c] = _date(df.get(c, pd.Series(dtype=str)))
    return _keep(df, ["idLicitacao","ano","numContrato","anoContrato","tipoContrato",
                       "situacaoContrato","vlrOriginal","vlrTotal","objeto",
                       "dataAssinatura","dataPublicacao","dataInicioVigenciaOriginal",
                       "dataFimVigenciaOriginal","dataFimUltimaVigencia",
                       "fornecedorCpfCnpj","fornecedorNome","fornecedorEndereco",
                       "fornecedorCidade","fornecedorSiglaUF",
                       "numSeqArquivoInstrContratual","txtNomeArquivo"])


def t_tecad_categorias(df):
    df = _clean(df)
    for c in ["codCategoria","codSubCategoria"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    return _keep(df, ["codCategoria","categoria","codSubCategoria","subCategoria"])


def t_tecad_termos(df):
    df = _clean(df)
    df["codTermo"] = pd.to_numeric(df.get("codTermo"), errors="coerce")
    return _keep(df, ["codTermo","termo","categorias","subcategorias",
                       "notasExplicativas","notasHistoricas","notasAplicativas",
                       "fontes","use","usadoPara","termosEspecificos","termosGenericos","termosRelacionados"])


# ===========================================================================
# Download de CSV zipado — cotas parlamentares
# ===========================================================================

def _download_csv_zip(url: str, cache: Optional[dict] = None) -> Optional[pd.DataFrame]:
    import zipfile
    headers = {}
    if cache is not None:
        entry = cache.get(url, {})
        if entry.get("etag"):
            headers["If-None-Match"] = entry["etag"]
        elif entry.get("last_modified"):
            headers["If-Modified-Since"] = entry["last_modified"]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 304:
                log.info("→ sem alterações (304): %s", url.split("/")[-1])
                return _CACHE_HIT
            if resp.status_code == 404:
                log.warning("404 — não encontrado: %s", url)
                return None
            resp.raise_for_status()
            if cache is not None:
                entry = {}
                if resp.headers.get("ETag"):
                    entry["etag"] = resp.headers["ETag"]
                if resp.headers.get("Last-Modified"):
                    entry["last_modified"] = resp.headers["Last-Modified"]
                if entry:
                    cache[url] = entry
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if not csv_names:
                    log.error("ZIP sem arquivo CSV: %s", url)
                    return None
                with zf.open(csv_names[0]) as f:
                    df = pd.read_csv(f, sep=";", dtype=str, low_memory=False, encoding="utf-8-sig")
            log.info("✔ %s (%d linhas)", url.split("/")[-1], len(df))
            return df
        except Exception as exc:
            log.warning("Tentativa %d/%d falhou (%s): %s", attempt, MAX_RETRIES, url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    log.error("Falha permanente: %s", url)
    return None

# ===========================================================================
# Transformação — Cotas Parlamentares (CEAP)
# ===========================================================================

# Mapeamento colunas CSV → campos do modelo Despesa
# Colunas do CSV (em ordem):
#   txNomeParlamentar | cpf | ideCadastro | nuCarteiraParlamentar | nuLegislatura
#   sgUF | sgPartido | codLegislatura | numSubCota | txtDescricao
#   numEspecificacaoSubCota | txtDescricaoEspecificacao | txtFornecedor | txtCNPJCPF
#   txtNumero | indTipoDocumento | datEmissao | vlrDocumento | vlrGlosa | vlrLiquido
#   numMes | numAno | numParcela | txtPassageiro | txtTrecho | numLote
#   numRessarcimento | datPagamentoRestituicao | vlrRestituicao
#   nuDeputadoId | ideDocumento | urlDocumento
_COTA_COL_MAP = {
    "nuDeputadoId":            "idDeputadoCamara",   # FK resolvida em _resolve_and_insert
    "numAno":                  "ano",
    "numMes":                  "mes",
    "txtDescricao":            "tipoDespesa",
    "txtFornecedor":           "nomeFornecedor",
    "txtCNPJCPF":              "cnpjCpfFornecedor",
    "txtNumero":               "numDocumento",
    "indTipoDocumento":        "codTipoDocumento",
    "datEmissao":              "dataDocumento",
    "vlrDocumento":            "valorDocumento",
    "vlrGlosa":                "valorGlosa",
    "vlrLiquido":              "valorLiquido",
    "numParcela":              "parcela",
    "numLote":                 "codLote",
    "numRessarcimento":        "numRessarcimento",
    "ideDocumento":            "codDocumento",       # chave de upsert
    "urlDocumento":            "urlDocumento",
    "txtPassageiro":           "txPassageiro",
    "txtTrecho":               "txTrecho",
    "numEspecificacaoSubCota": "numEspecificacaoSubCota",
    "numSubCota":              "numSubCota",
}

def t_cotas(df: pd.DataFrame) -> list[dict]:
    """
    Transforma o CSV de Cota Parlamentar para a tabela `despesas`.

    Chave de upsert: codDocumento (ideDocumento no CSV).
    Linhas sem codDocumento ou sem deputado identificável são descartadas
    (ex: linhas de lideranças como "LID.GOV-CD" sem nuDeputadoId válido).

    Campos principais (CSV → modelo):
        nuDeputadoId  → idDeputadoCamara  (temporário; substituído por idDeputado no resolve)
        ideDocumento  → codDocumento
        datEmissao    → dataDocumento
        vlrLiquido    → valorLiquido
        txtDescricao  → tipoDespesa
        txtFornecedor → nomeFornecedor
        txtCNPJCPF    → cnpjCpfFornecedor
    """
    df = _clean(df)
    df = df.rename(columns={k: v for k, v in _COTA_COL_MAP.items() if k in df.columns})

    # Inteiros
    for c in ["idDeputadoCamara", "ano", "mes", "parcela",
              "numSubCota", "numEspecificacaoSubCota", "codTipoDocumento"]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")

    # Monetários
    for c in ["valorDocumento", "valorGlosa", "valorLiquido"]:
        df[c] = _num(df.get(c, pd.Series(dtype=str)))

    # Data/hora de emissão
    df["dataDocumento"] = _dt(df.get("dataDocumento"))

    # Descarta linhas sem chave de upsert ou sem deputado
    df = df.dropna(subset=["codDocumento", "idDeputadoCamara"])
    df["codDocumento"] = df["codDocumento"].astype(str).str.strip()
    df = df[df["codDocumento"].str.len() > 0]

    return _keep(df, [
        "idDeputadoCamara",
        "codDocumento",
        "ano", "mes",
        "tipoDespesa", "numSubCota", "numEspecificacaoSubCota",
        "codTipoDocumento",
        "dataDocumento", "numDocumento",
        "valorDocumento", "valorGlosa", "valorLiquido",
        "nomeFornecedor", "cnpjCpfFornecedor",
        "urlDocumento",
        "parcela", "codLote", "numRessarcimento",
        "txPassageiro", "txTrecho",
    ])


# ===========================================================================
# Dataset descriptor
# ===========================================================================

@dataclass
class Dataset:
    nome: str
    url_fn: Callable
    transform_fn: Callable
    table_name: str          # prefixo "_raw_" → resolve FK antes de inserir
    conflict_cols: list[str]
    ano_ref: Optional[int] = None  # ano dos dados; None = dataset atemporal
    preserve_cols: list[str] = None # colunas a preservar no upsert (além de conflict_cols); None = todas

# ===========================================================================
# Catálogo — ordenado por dependência de FK
# ===========================================================================

def build_catalog(anos: list[int], legislaturas: list[int]) -> list[Dataset]:
    A, L = anos, legislaturas
    simple = [
        Dataset("legislaturas",        lambda: url_simples("legislaturas"),
                t_legislaturas,        "legislaturas",       ["idLegislatura"]),
        Dataset("orgaos",              lambda: url_simples("orgaos"),
                t_orgaos,              "orgaos",             ["idCamara"]),
        Dataset("deputados",           lambda: url_simples("deputados"),
                t_deputados,           "deputados",          ["idCamara"],
                preserve_cols=["urlFoto", "escolaridade", "emailGabinete", "nomeCivil", "condicaoEleitoral", "telefoneGabinete"]),
        Dataset("deputadosOcupacoes",  lambda: url_simples("deputadosOcupacoes"),
                t_deputados_ocupacoes, "_raw_deputadosOcupacoes", []),
        Dataset("deputadosProfissoes", lambda: url_simples("deputadosProfissoes"),
                t_deputados_profissoes,"_raw_deputadosProfissoes",[]),
        Dataset("frentes",             lambda: url_simples("frentes"),
                t_frentes,             "_raw_frentes",            []),
        Dataset("frentesDeputados",    lambda: url_simples("frentesDeputados"),
                t_frentes_deputados,   "_raw_frentesDeputados", []),
        Dataset("legislaturasMesas", lambda: url_simples("legislaturasMesas"), t_legislaturas_mesas, "legislaturasMesas", ["idLegislatura","idDeputado","cargo","dataInicio"]),
        Dataset("grupos",              lambda: url_simples("grupos"),
                t_grupos,              "grupos",             ["idCamara"]),
        Dataset("gruposMembros",       lambda: url_simples("gruposMembros"),
                t_grupos_membros,      "_raw_gruposMembros", []),
        Dataset("gruposHistorico",     lambda: url_simples("gruposHistorico"),
                t_grupos_historico,    "_raw_gruposHistorico", []),
        Dataset("funcionarios",        lambda: url_simples("funcionarios"),
                t_funcionarios,        "funcionarios",       ["ponto"]),
        Dataset("tecadCategorias",     lambda: url_simples("tecadCategorias"),
                t_tecad_categorias,    "tecadCategorias",    ["codCategoria","codSubCategoria"]),
        Dataset("tecadTermos",         lambda: url_simples("tecadTermos"),
                t_tecad_termos,        "tecadTermos",        ["codTermo"]),
    ]

    anual = []
    for a in A:
        anual += [
            Dataset(f"eventos_{a}",                 lambda ano=a: url_anual("eventos", ano),
                    t_eventos,              "eventos",                    ["idCamara"]),
            Dataset(f"eventosOrgaos_{a}",           lambda ano=a: url_anual("eventosOrgaos", ano),
                    t_eventos_orgaos,       "_raw_eventosOrgaos",         []),
            Dataset(f"eventosRequerimentos_{a}",    lambda ano=a: url_anual("eventosRequerimentos", ano),
                    t_eventos_reqs,         "_raw_eventosRequerimentos",  []),
            Dataset(f"eventosPresenca_{a}",         lambda ano=a: url_anual("eventosPresencaDeputados", ano),
                    t_presenca,             "_raw_eventosPresenca",       []),
            Dataset(f"proposicoes_{a}",             lambda ano=a: url_anual("proposicoes", ano),
                    t_proposicoes,          "proposicoes",                ["idCamara"]),
            Dataset(f"proposicoesAutores_{a}",      lambda ano=a: url_anual("proposicoesAutores", ano),
                    t_proposicoes_autores,  "_raw_proposicoesAutores",    []),
            Dataset(f"proposicoesTemas_{a}",        lambda ano=a: url_anual("proposicoesTemas", ano),
                    t_proposicoes_temas,    "_raw_proposicoesTemas",      []),
            Dataset(f"votacoes_{a}",                lambda ano=a: url_anual("votacoes", ano),
                    t_votacoes,             "_raw_votacoes",              []),
            Dataset(f"votacoesVotos_{a}",           lambda ano=a: url_anual("votacoesVotos", ano),
                    t_votacoes_votos,       "_raw_votacoesVotos",         []),
            Dataset(f"votacoesOrientacoes_{a}",     lambda ano=a: url_anual("votacoesOrientacoes", ano),
                    t_votacoes_orientacoes, "_raw_votacoesOrientacoes",   []),
            Dataset(f"votacoesObjetos_{a}",         lambda ano=a: url_anual("votacoesProposicoes", ano),
                    t_votacoes_objetos,     "_raw_votacoesObjetos",       []),
            Dataset(f"licitacoes_{a}",              lambda ano=a: url_anual("licitacoes", ano),
                    t_licitacoes,           "licitacoes",                 ["idLicitacao"]),
            Dataset(f"licitacoesPedidos_{a}",       lambda ano=a: url_anual("licitacoesPedidos", ano),
                    t_licitacoes_pedidos,   "_raw_licitacoesPedidos",     []),
            Dataset(f"licitacoesPropostas_{a}",     lambda ano=a: url_anual("licitacoesPropostas", ano),
                    t_licitacoes_propostas, "_raw_licitacoesPropostas",   []),
            Dataset(f"licitacoesItens_{a}",         lambda ano=a: url_anual("licitacoesItens", ano),
                    t_licitacoes_itens,     "_raw_licitacoesItens",       []),
            Dataset(f"licitacoesContratos_{a}",     lambda ano=a: url_anual("licitacoesContratos", ano),
                    t_licitacoes_contratos, "_raw_licitacoesContratos",   []),
        ]

    leg_datasets = [
        Dataset(f"orgaosDeputados_L{l}", lambda leg=l: url_legislatura("orgaosDeputados", leg),
                t_orgaos_deputados, "_raw_orgaosDeputados", []) for l in L
    ]

    # Cotas parlamentares (CEAP) — camara.leg.br/cotas/Ano-{ano}.csv.zip
    cotas_datasets = [
        Dataset(f"cotas_{a}", lambda ano=a: url_cota_anual(ano),
                t_cotas, "_raw_cotas", [], ano_ref=a)
        for a in A
    ]

    return simple + anual + leg_datasets + cotas_datasets


# ===========================================================================
# Resolução de FK para tabelas "_raw_*"
# ===========================================================================

def _scalar(conn, sql: str, val) -> Optional[int]:
    return conn.execute(text(sql), {"v": val}).scalar()


def _resolve_and_insert(engine, raw_table: str, records: list[dict]):
    """Resolve idCamara → id interno e insere nas tabelas definitivas."""
    if not records:
        return

    def _s(v):
        """Sanitiza NaT/NaN para None antes de enviar ao banco."""
        if v is None:
            return None
        try:
            if pd.isna(v):
                return None
        except (TypeError, ValueError):
            pass
        return v

    def _row_clean(r: dict) -> dict:
        return {k: _s(v) for k, v in r.items()}

    with engine.begin() as conn:

        if raw_table == "_raw_deputadosOcupacoes":
            for r in records:
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara"))
                if dep:
                    row = {k: v for k, v in r.items() if k != "idDeputadoCamara"}
                    row["idDeputado"] = dep
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    # Usa o nome exato da constraint declarada no model (uq_deputado_ocupacao)
                    conn.execute(text(
                        f'INSERT INTO "deputadosOcupacoes"({cols}) VALUES({vals}) '
                        f'ON CONFLICT ON CONSTRAINT uq_deputado_ocupacao DO NOTHING'
                    ), row)

        elif raw_table == "_raw_deputadosProfissoes":
            for r in records:
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara"))
                if dep:
                    row = {k: v for k, v in r.items() if k != "idDeputadoCamara"}
                    row["idDeputado"] = dep
                    row = _row_clean(row)
                    # deputadosProfissoes não tem unique constraint além da PK:
                    # evitar duplicatas verificando existência antes de inserir.
                    exists = conn.execute(
                        text('SELECT 1 FROM "deputadosProfissoes" '
                             'WHERE "idDeputado"=:dep AND "codTipoProfissao"=:cod LIMIT 1'),
                        {"dep": dep, "cod": row.get("codTipoProfissao")}
                    ).scalar()
                    if not exists:
                        cols = ",".join(f'"{c}"' for c in row)
                        vals = ",".join(f":{c}" for c in row)
                        conn.execute(text(
                            f'INSERT INTO "deputadosProfissoes"({cols}) VALUES({vals})'
                        ), row)

        elif raw_table == "_raw_eventosOrgaos":
            for r in records:
                ev = _scalar(conn, 'SELECT id FROM eventos WHERE "idCamara"=:v', r["idEventoCamara"])
                og = _scalar(conn, 'SELECT id FROM orgaos  WHERE "idCamara"=:v', r["idOrgaoCamara"])
                if ev and og:
                    conn.execute(text(
                        'INSERT INTO "eventosOrgaos"("idEvento","idOrgao") VALUES(:e,:o) ON CONFLICT DO NOTHING'),
                        {"e": ev, "o": og})

        elif raw_table == "_raw_eventosRequerimentos":
            for r in records:
                ev = _scalar(conn, 'SELECT id FROM eventos WHERE "idCamara"=:v', r.get("idEventoCamara"))
                if ev:
                    conn.execute(text(
                        'INSERT INTO "eventosRequerimentos"("idEvento","tituloRequerimento","uriRequerimento") '
                        'VALUES(:e,:t,:u) ON CONFLICT DO NOTHING'),
                        {"e": ev, "t": r.get("tituloRequerimento"), "u": r.get("uriRequerimento")})

        elif raw_table == "_raw_eventosPresenca":
            for r in records:
                ev  = _scalar(conn, 'SELECT id FROM eventos   WHERE "idCamara"=:v', r.get("idEventoCamara"))
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara"))
                if ev and dep:
                    conn.execute(text(
                        'INSERT INTO "eventosPresencaDeputados"("idEvento","idDeputado","dataHoraInicio") '
                        'VALUES(:e,:d,:h) ON CONFLICT DO NOTHING'),
                        {"e": ev, "d": dep, "h": r.get("dataHoraInicio")})

        elif raw_table == "_raw_proposicoesAutores":
            for r in records:
                prop = _scalar(conn, 'SELECT id FROM proposicoes WHERE "idCamara"=:v', r.get("idProposicaoCamara"))
                dep  = _scalar(conn, 'SELECT id FROM deputados   WHERE "idCamara"=:v', r.get("idDeputadoCamara")) if r.get("idDeputadoCamara") else None
                if prop:
                    row = {k: v for k, v in r.items() if k not in ("idProposicaoCamara","idDeputadoCamara")}
                    row["idProposicao"] = prop; row["idDeputadoAutor"] = dep
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "proposicoesAutores"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_proposicoesTemas":
            for r in records:
                conn.execute(text('INSERT INTO temas("codTema","tema") VALUES(:c,:t) ON CONFLICT("codTema") DO NOTHING'),
                             {"c": r.get("codTema"), "t": r.get("tema")})
                prop  = _scalar(conn, 'SELECT id FROM proposicoes WHERE "idCamara"=:v', r.get("idProposicaoCamara"))
                tema  = _scalar(conn, 'SELECT id FROM temas WHERE "codTema"=:v',         r.get("codTema"))
                if prop and tema:
                    conn.execute(text(
                        'INSERT INTO "proposicoesTemas"("idProposicao","idTema") VALUES(:p,:t) ON CONFLICT DO NOTHING'),
                        {"p": prop, "t": tema})

        elif raw_table == "_raw_votacoes":
            for r in records:
                og   = _scalar(conn, 'SELECT id FROM orgaos    WHERE "idCamara"=:v', r.get("idOrgaoCamara"))      if r.get("idOrgaoCamara")      else None
                ev   = _scalar(conn, 'SELECT id FROM eventos   WHERE "idCamara"=:v', r.get("idEventoCamara"))     if r.get("idEventoCamara")     else None
                prop = _scalar(conn, 'SELECT id FROM proposicoes WHERE "idCamara"=:v', r.get("idProposicaoCamara")) if r.get("idProposicaoCamara") else None
                row = {k: v for k, v in r.items() if k not in ("idOrgaoCamara","idEventoCamara","idProposicaoCamara")}
                row["idOrgao"] = og; row["idEvento"] = ev; row["idProposicao"] = prop
                row = _row_clean(row)
                cols = ",".join(f'"{c}"' for c in row)
                vals = ",".join(f":{c}" for c in row)
                conn.execute(text(f'INSERT INTO votacoes({cols}) VALUES({vals}) ON CONFLICT("idCamara") DO NOTHING'), row)

        elif raw_table == "_raw_votacoesVotos":
            for r in records:
                vot = _scalar(conn, 'SELECT id FROM votacoes  WHERE "idCamara"=:v', r.get("idVotacaoCamara"))
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara"))
                if vot and dep:
                    row = {k: v for k, v in r.items() if k not in ("idVotacaoCamara","idDeputadoCamara")}
                    row["idVotacao"] = vot; row["idDeputado"] = dep
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "votacoesVotos"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_votacoesOrientacoes":
            for r in records:
                vot = _scalar(conn, 'SELECT id FROM votacoes WHERE "idCamara"=:v', r.get("idVotacaoCamara"))
                if vot:
                    conn.execute(text(
                        'INSERT INTO "votacoesOrientacoes"("idVotacao","siglaOrgao","siglaBancada","uriBancada","orientacao") '
                        'VALUES(:v,:so,:sb,:ub,:o) ON CONFLICT DO NOTHING'),
                        {"v": vot, "so": r.get("siglaOrgao"), "sb": r.get("siglaBancada"),
                         "ub": r.get("uriBancada"), "o": r.get("orientacao")})

        elif raw_table == "_raw_votacoesObjetos":
            for r in records:
                vot = _scalar(conn, 'SELECT id FROM votacoes WHERE "idCamara"=:v', r.get("idVotacaoCamara"))
                if vot:
                    row = {k: v for k, v in r.items() if k != "idVotacaoCamara"}
                    row["idVotacao"] = vot
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "votacoesObjetos"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table in ("_raw_licitacoesPedidos","_raw_licitacoesPropostas",
                           "_raw_licitacoesItens","_raw_licitacoesContratos"):
            tbl = raw_table.replace("_raw_", "")
            for r in records:
                # Verifica se a licitação pai existe no banco
                lic_id = r.get("idLicitacao")
                if not lic_id:
                    continue
                exists = conn.execute(
                    text('SELECT 1 FROM licitacoes WHERE "idLicitacao"=:v LIMIT 1'),
                    {"v": int(lic_id)}
                ).scalar()
                if not exists:
                    continue
                row = _row_clean(r)
                # Converte colunas inteiras que podem chegar como float
                for int_col in ("ano","numPedido","anoPedido","idOrgao","numItem","numSubitem",
                                "numSubitens","numProposta","diasValidadeProposta",
                                "numContrato","anoContrato","numSeqArquivoInstrContratual"):
                    if int_col in row and row[int_col] is not None:
                        try:
                            row[int_col] = int(float(row[int_col]))
                        except (ValueError, TypeError):
                            row[int_col] = None
                cols = ",".join(f'"{c}"' for c in row)
                vals = ",".join(f":{c}" for c in row)
                conn.execute(text(f'INSERT INTO "{tbl}"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_orgaosDeputados":
            for r in records:
                og  = _scalar(conn, 'SELECT id FROM orgaos    WHERE "idCamara"=:v', r.get("idOrgaoCamara"))
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara")) if r.get("idDeputadoCamara") else None
                if og:
                    row = {k: v for k, v in r.items() if k not in ("idOrgaoCamara","idDeputadoCamara")}
                    row["idOrgao"] = og; row["idDeputado"] = dep
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "orgaosDeputados"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_frentes":
            from sqlalchemy import Table, MetaData
            meta = MetaData()
            meta.reflect(bind=engine, only=["frentes"])
            tbl = meta.tables["frentes"]
            for r in records:
                dep_id = None
                if r.get("coordenador_idCamara"):
                    dep_id = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r["coordenador_idCamara"])
                row = {k: v for k, v in r.items() if k != "coordenador_idCamara"}
                row["coordenador_id"] = dep_id
                row = _row_clean(row)
                stmt = pg_insert(tbl).values([row])
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in tbl.columns
                    if c.name not in ("id", "idCamara")
                }
                stmt = stmt.on_conflict_do_update(index_elements=["idCamara"], set_=update_cols)
                conn.execute(stmt)

        elif raw_table == "_raw_frentesDeputados":
            for r in records:
                fr  = _scalar(conn, 'SELECT id FROM frentes   WHERE "idCamara"=:v', r.get("idFrenteCamara"))
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara")) if r.get("idDeputadoCamara") else None
                if fr:
                    row = {k: v for k, v in r.items() if k not in ("idFrenteCamara","idDeputadoCamara")}
                    row["idFrente"] = fr; row["idDeputado"] = dep
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "frentesDeputados"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_gruposMembros":
            for r in records:
                gr  = _scalar(conn, 'SELECT id FROM grupos    WHERE "idCamara"=:v', r.get("idGrupoCamara"))
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara")) if r.get("idDeputadoCamara") else None
                if gr:
                    row = {k: v for k, v in r.items() if k not in ("idGrupoCamara","idDeputadoCamara")}
                    row["idGrupo"] = gr; row["idDeputado"] = dep
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "gruposMembros"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_gruposHistorico":
            for r in records:
                gr = _scalar(conn, 'SELECT id FROM grupos WHERE "idCamara"=:v', r.get("idGrupoCamara"))
                if gr:
                    row = {k: v for k, v in r.items() if k != "idGrupoCamara"}
                    row["idGrupo"] = gr
                    row = _row_clean(row)
                    cols = ",".join(f'"{c}"' for c in row)
                    vals = ",".join(f":{c}" for c in row)
                    conn.execute(text(f'INSERT INTO "gruposHistorico"({cols}) VALUES({vals}) ON CONFLICT DO NOTHING'), row)

        elif raw_table == "_raw_cotas":
            # Resolve idDeputadoCamara → id interno e faz upsert em despesas.
            # ON CONFLICT em codDocumento: atualiza todos os campos monetários
            # (o valor líquido pode ser corrigido em publicações posteriores).
            _INT_COLS_COTA = ("ano", "mes", "parcela", "numSubCota",
                              "numEspecificacaoSubCota", "codTipoDocumento")
            for r in records:
                dep = _scalar(conn, 'SELECT id FROM deputados WHERE "idCamara"=:v', r.get("idDeputadoCamara"))
                if not dep:
                    continue  # liderança/externo sem cadastro — ignora
                row = {k: v for k, v in r.items() if k != "idDeputadoCamara"}
                row["idDeputado"] = dep
                row = _row_clean(row)
                # Garante inteiros — pandas pode serializar como float
                for int_col in _INT_COLS_COTA:
                    if int_col in row and row[int_col] is not None:
                        try:
                            row[int_col] = int(float(row[int_col]))
                        except (ValueError, TypeError):
                            row[int_col] = None
                cols = ",".join(f'"{c}"' for c in row)
                vals = ",".join(f":{c}" for c in row)
                update_set = ", ".join(
                    f'"{c}"=EXCLUDED."{c}"' for c in row if c != "codDocumento"
                )
                conn.execute(text(
                    f'INSERT INTO despesas({cols}) VALUES({vals}) '
                    f'ON CONFLICT("codDocumento") DO UPDATE SET {update_set}'
                ), row)


# ===========================================================================
# Pipeline
# ===========================================================================

def run_etl(datasets: list[Dataset], engine, *, force: bool = False, skip_historical: bool = False):
    cache = {} if force else _cache_load()
    erros = []
    pulados_historico = 0
    pulados_304 = 0

    for ds in tqdm(datasets, desc="ETL Câmara"):
        # Estratégia 1: pula anos históricos fechados sem fazer request
        if skip_historical and ds.ano_ref is not None and ds.ano_ref < ANO_ATUAL:
            log.debug("⏭ histórico imutável, pulando: %s", ds.nome)
            pulados_historico += 1
            continue

        url = ds.url_fn()

        # Estratégia 2: download com ETag/Last-Modified
        if ds.nome.startswith("cotas_"):
            df = _download_csv_zip(url, cache=cache)
        else:
            df = _download_csv(url, cache=cache)

        if df is _CACHE_HIT:
            pulados_304 += 1
            continue
        if df is None:
            erros.append(ds.nome)
            continue

        try:
            records = ds.transform_fn(df)
        except Exception as exc:
            log.error("Transform error [%s]: %s", ds.nome, exc)
            erros.append(ds.nome)
            continue

        if ds.table_name.startswith("_raw_"):
            try:
                _resolve_and_insert(engine, ds.table_name, records)
                log.info("  FK-insert %s → %d registros", ds.table_name, len(records))
            except Exception as exc:
                log.error("FK-insert error [%s]: %s", ds.nome, exc)
                erros.append(ds.nome)
        else:
            try:
                n = upsert(engine, ds.table_name, ds.preserve_cols, records, ds.conflict_cols)
                log.info("  upsert %s → %d registros", ds.table_name, n)
            except Exception as exc:
                log.error("Upsert error [%s]: %s", ds.nome, exc)
                erros.append(ds.nome)

    if not force:
        _cache_save(cache)

    processados = len(datasets) - pulados_historico - pulados_304 - len(erros)
    log.info(
        "ETL concluído — processados: %d | sem alteração (304): %d | histórico pulado: %d | erros: %d",
        processados, pulados_304, pulados_historico, len(erros),
    )
    if erros:
        log.warning("Datasets com falha (%d): %s", len(erros), erros)


# ===========================================================================
# CLI
# ===========================================================================

def _get_legislaturas(engine) -> list[int]:
    try:
        with engine.connect() as conn:
            rows = conn.execute(text('SELECT "idLegislatura" FROM legislaturas ORDER BY 1')).fetchall()
            return [r[0] for r in rows] or [56, 57]
    except Exception:
        return [56, 57]


def main():
    parser = argparse.ArgumentParser(description="ETL — Dados Abertos da Câmara dos Deputados")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full",    action="store_true", help="Carga histórica completa (2019–hoje)")
    mode.add_argument("--update",  action="store_true", help="Apenas o ano corrente (pula histórico automaticamente)")
    mode.add_argument("--dataset", type=str,            help="Prefixo do dataset (ex: votacoes, eventos)")
    parser.add_argument("--anos",  type=int, nargs="+", help="Anos específicos")
    parser.add_argument("--force", action="store_true",
                        help="Ignora cache de ETag e reprocessa tudo (inclui anos históricos)")
    parser.add_argument("--cache-file", type=str, default=None,
                        help="Caminho do arquivo de cache (padrão: etl_cache.json)")
    args = parser.parse_args()

    if args.cache_file:
        global CACHE_FILE
        CACHE_FILE = Path(args.cache_file)

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    log.info("Banco: %s", DATABASE_URL.split("@")[-1])
    log.info("Cache: %s%s", CACHE_FILE, " (desativado via --force)" if args.force else "")

    if args.full:
        anos = ANOS_HISTORICO
        skip_historical = False
    elif args.update:
        anos = args.anos or [ANO_ATUAL]
        skip_historical = not args.force
    else:
        anos = args.anos or [ANO_ATUAL]
        skip_historical = False

    legislaturas = _get_legislaturas(engine)
    catalog = build_catalog(anos, legislaturas)

    if args.dataset:
        catalog = [ds for ds in catalog if ds.nome.startswith(args.dataset)]
        if not catalog:
            log.error("Nenhum dataset encontrado para prefixo '%s'", args.dataset)
            sys.exit(1)

    log.info("Iniciando ETL: %d datasets | anos=%s | legislaturas=%s",
             len(catalog), anos, legislaturas)
    run_etl(catalog, engine, force=args.force, skip_historical=skip_historical)


if __name__ == "__main__":
    main()