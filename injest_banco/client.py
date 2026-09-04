"""
client.py
=========
Cliente HTTP resiliente para a API de Dados Abertos e arquivos da Câmara dos Deputados.
Implementa:
  - requests.Session com pool de conexões e retentativas automáticas
  - Backoff exponencial com jitter e respeito ao header Retry-After (HTTP 429)
  - Cache thread-safe de ETag e Last-Modified (HTTP 304 Not Modified)
  - Suporte a download de CSVs e CSVs compactados em ZIP (Cotas)
  - Métodos utilitários para a API REST v2 (/deputados, /votacoes, /proposicoes)
"""

from __future__ import annotations

import io
import json
import logging
import os
import random
import time
import zipfile
from pathlib import Path
from threading import Lock
from typing import Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("etl_camara.client")

# Configurações padrão
API_V2_BASE = "https://dadosabertos.camara.leg.br/api/v2"
BASE_ARQUIVOS_URL = "http://dadosabertos.camara.leg.br/arquivos"
COTAS_BASE_URL = "http://www.camara.leg.br/cotas"

DEFAULT_REQUEST_TIMEOUT = (10.0, 60.0)  # (connect, read)
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 3.0

CACHE_FILE_DEFAULT = Path(os.getenv("ETL_CACHE_FILE", "etl_cache.json"))
_CACHE_HIT = object()


class ETagCache:
    """Gerenciador thread-safe de cache ETag e Last-Modified."""

    def __init__(self, cache_file: Path | str = CACHE_FILE_DEFAULT):
        self.cache_file = Path(cache_file)
        self._lock = Lock()
        self._cache: dict[str, dict[str, str]] = self._load()

    def _load(self) -> dict[str, dict[str, str]]:
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception as exc:
                log.warning(
                    "Falha ao ler arquivo de cache %s: %s", self.cache_file, exc
                )
        return {}

    def save(self) -> None:
        with self._lock:
            tmp = self.cache_file.with_suffix(".tmp")
            try:
                tmp.write_text(
                    json.dumps(self._cache, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                tmp.replace(self.cache_file)
            except Exception as exc:
                log.warning(
                    "Falha ao salvar arquivo de cache %s: %s", self.cache_file, exc
                )

    def get_headers(self, url: str) -> dict[str, str]:
        with self._lock:
            entry = self._cache.get(url, {})
        headers = {}
        if entry.get("etag"):
            headers["If-None-Match"] = entry["etag"]
        elif entry.get("last_modified"):
            headers["If-Modified-Since"] = entry["last_modified"]
        return headers

    def update(self, url: str, resp_headers: Any) -> None:
        entry = {}
        if resp_headers.get("ETag"):
            entry["etag"] = resp_headers["ETag"]
        if resp_headers.get("Last-Modified"):
            entry["last_modified"] = resp_headers["Last-Modified"]
        if entry:
            with self._lock:
                self._cache[url] = entry

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            if self.cache_file.exists():
                try:
                    self.cache_file.unlink()
                except Exception:
                    pass


class CamaraClient:
    """
    Cliente HTTP unificado para dados abertos e API REST da Câmara.
    """

    def __init__(
        self,
        timeout: tuple[float, float] = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        cache: Optional[ETagCache] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache = cache or ETagCache()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=20,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(
            {
                "User-Agent": "QuemVota-ETL/2.0 (dados-publicos; contato@quemvota.org)",
                "Accept-Encoding": "gzip, deflate",
            }
        )
        return session

    def _wait_backoff(
        self, attempt: int, resp: Optional[requests.Response] = None
    ) -> None:
        """Calcula o tempo de espera respeitando Retry-After ou backoff exponencial."""
        wait = self.retry_delay * (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
        if resp is not None and resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after) + random.uniform(0.2, 1.0)
                    log.warning(
                        "HTTP 429 recebido. Aguardando Retry-After: %.2fs", wait
                    )
                except ValueError:
                    pass
            else:
                wait = max(wait, 5.0)
                log.warning("HTTP 429 sem Retry-After. Aguardando backoff: %.2fs", wait)
        time.sleep(wait)

    def download_csv(
        self,
        url: str,
        use_cache: bool = True,
    ) -> Optional[pd.DataFrame] | object:
        """
        Baixa e carrega CSV com separador ';' e codificação utf-8-sig.
        Retorna:
          - pd.DataFrame com os dados
          - _CACHE_HIT se o servidor responder 304 Not Modified
          - None se erro permanente ou 404
        """
        headers = self.cache.get_headers(url) if use_cache else {}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 304:
                    log.info("→ sem alterações (304): %s", url.split("/")[-1])
                    return _CACHE_HIT
                if resp.status_code == 404:
                    log.warning("404 — não encontrado: %s", url)
                    return None
                if resp.status_code == 429:
                    self._wait_backoff(attempt, resp)
                    continue

                resp.raise_for_status()

                if use_cache:
                    self.cache.update(url, resp.headers)

                raw_text = resp.content.decode("utf-8-sig", errors="replace")
                df = pd.read_csv(
                    io.StringIO(raw_text),
                    sep=";",
                    dtype=str,
                    low_memory=False,
                    quotechar='"',
                    doublequote=True,
                    on_bad_lines="warn",
                )
                log.info("✔ %s (%d linhas)", url.split("/")[-1], len(df))
                return df

            except Exception as exc:
                log.warning(
                    "Tentativa %d/%d falhou (%s): %s",
                    attempt,
                    self.max_retries,
                    url,
                    exc,
                )
                if attempt < self.max_retries:
                    self._wait_backoff(attempt)

        log.error("Falha permanente ao baixar CSV: %s", url)
        return None

    def download_csv_zip(
        self,
        url: str,
        use_cache: bool = True,
    ) -> Optional[pd.DataFrame] | object:
        """
        Baixa arquivo ZIP e extrai o primeiro CSV interno (ex: Cotas parlamentares).
        """
        headers = self.cache.get_headers(url) if use_cache else {}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 304:
                    log.info("→ sem alterações (304): %s", url.split("/")[-1])
                    return _CACHE_HIT
                if resp.status_code == 404:
                    log.warning("404 — não encontrado: %s", url)
                    return None
                if resp.status_code == 429:
                    self._wait_backoff(attempt, resp)
                    continue

                resp.raise_for_status()

                if use_cache:
                    self.cache.update(url, resp.headers)

                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                    if not csv_names:
                        log.error("ZIP sem arquivo CSV: %s", url)
                        return None
                    with zf.open(csv_names[0]) as f:
                        df = pd.read_csv(
                            f,
                            sep=";",
                            dtype=str,
                            low_memory=False,
                            encoding="utf-8-sig",
                            quotechar='"',
                            doublequote=True,
                            on_bad_lines="warn",
                        )
                log.info("✔ %s (%d linhas)", url.split("/")[-1], len(df))
                return df

            except Exception as exc:
                log.warning(
                    "Tentativa %d/%d falhou (%s): %s",
                    attempt,
                    self.max_retries,
                    url,
                    exc,
                )
                if attempt < self.max_retries:
                    self._wait_backoff(attempt)

        log.error("Falha permanente ao baixar ZIP: %s", url)
        return None

    def get_api(
        self, path: str, params: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        """
        Realiza requisição GET na API REST v2 com backoff automático e headers JSON.
        """
        url = f"{API_V2_BASE}{path}" if path.startswith("/") else path
        headers = {"Accept": "application/json"}

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )
                if resp.status_code == 404:
                    return None
                if resp.status_code == 429:
                    self._wait_backoff(attempt, resp)
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                log.warning(
                    "API REST tentativa %d/%d falhou (%s): %s",
                    attempt,
                    self.max_retries,
                    url,
                    exc,
                )
                if attempt < self.max_retries:
                    self._wait_backoff(attempt)

        log.error("Falha definitiva na API REST: %s", url)
        return None

    def get_deputado_detalhes(self, id_camara: int) -> Optional[dict[str, Any]]:
        """GET /deputados/{id}"""
        res = self.get_api(f"/deputados/{id_camara}")
        return res.get("dados") if res else None

    def get_votacao_detalhes(self, id_votacao: str) -> Optional[dict[str, Any]]:
        """GET /votacoes/{id}"""
        res = self.get_api(f"/votacoes/{id_votacao}")
        return res.get("dados") if res else None

    def get_proposicao_detalhes(self, id_proposicao: int) -> Optional[dict[str, Any]]:
        """GET /proposicoes/{id}"""
        res = self.get_api(f"/proposicoes/{id_proposicao}")
        return res.get("dados") if res else None
