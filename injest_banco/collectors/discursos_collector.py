"""
injest_banco/collectors/discursos_collector.py — Coletor modular de Discursos da Câmara (SPEC-007).

Encapsula a lógica de requisição paginada ao endpoint
``GET /deputados/{id}/discursos`` da API de Dados Abertos,
com backoff exponencial, respeito a rate-limits (HTTP 429) e
sanitização básica de strings.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

BASE_API_URL = "https://dadosabertos.camara.leg.br/api/v2"
DEFAULT_TIMEOUT = (10.0, 30.0)
_NULL_BYTE_RE = re.compile(r"\x00")


def _sanitize_string(value: str | None) -> str | None:
    """Remove null-bytes, espaços extras e quebras de linha espúrias."""
    if value is None:
        return None
    cleaned = _NULL_BYTE_RE.sub("", value)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip() or None


class DiscursosCollector:
    """Coletor resiliente de discursos via API da Câmara dos Deputados.

    Attributes:
        session: Sessão HTTP reutilizável com retry e backoff.
        base_url: URL base da API de Dados Abertos.
    """

    def __init__(
        self,
        *,
        base_url: str = BASE_API_URL,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
        max_retries: int = 4,
        backoff_factor: float = 1.5,
        user_agent: str = "QuemVota-ETL/1.0 (transparencia@quemvota.com.br)",
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = self._build_session(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            user_agent=user_agent,
        )

    @staticmethod
    def _build_session(
        *,
        max_retries: int,
        backoff_factor: float,
        user_agent: str,
    ) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": user_agent,
            }
        )
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def coletar(
        self,
        id_camara: int,
        *,
        legislatura: int = 57,
        max_paginas: int = 10,
        delay_entre_paginas: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Coleta discursos de um deputado na legislatura especificada.

        Args:
            id_camara: ID do deputado na API da Câmara (``Deputado.idCamara``).
            legislatura: ID da legislatura alvo.
            max_paginas: Limite de páginas a percorrer (segurança).
            delay_entre_paginas: Intervalo em segundos entre páginas (rate-limit).

        Returns:
            Lista de dicts crus vindos da API, sanitizados nas strings.
        """
        url: str | None = f"{self.base_url}/deputados/{id_camara}/discursos"
        params: dict[str, Any] | None = {
            "idLegislatura": legislatura,
            "ordenarPor": "dataHoraInicio",
            "ordem": "DESC",
            "itens": 100,
        }

        todos: list[dict[str, Any]] = []
        pagina = 1

        while url and pagina <= max_paginas:
            try:
                resp = self.session.get(
                    url,
                    params=params if pagina == 1 else None,
                    timeout=self.timeout,
                )
                if resp.status_code == 404:
                    logger.debug(
                        "Deputado idCamara=%s não encontrado na API (404).", id_camara
                    )
                    break

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    logger.warning(
                        "Rate-limit (429) para deputado %s. Aguardando %ss.",
                        id_camara,
                        retry_after,
                    )
                    time.sleep(retry_after)
                    continue

                if resp.status_code != 200:
                    logger.warning(
                        "HTTP %s para deputado %s: %s",
                        resp.status_code,
                        id_camara,
                        resp.text[:200],
                    )
                    break

                data = resp.json()
                itens = data.get("dados", [])
                if not itens:
                    break

                # Sanitização de strings
                for item in itens:
                    for campo in (
                        "tipoDiscurso",
                        "sumario",
                        "transcricao",
                        "keywords",
                        "urlTexto",
                        "urlAudio",
                        "urlVideo",
                    ):
                        if campo in item and isinstance(item[campo], str):
                            item[campo] = _sanitize_string(item[campo])

                todos.extend(itens)

                # Próxima página via rel='next'
                next_url: str | None = None
                for link in data.get("links", []):
                    if link.get("rel") == "next":
                        next_url = link.get("href")
                        break

                url = next_url
                pagina += 1

                if delay_entre_paginas > 0:
                    time.sleep(delay_entre_paginas)

            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Erro de rede ao coletar discursos para idCamara=%s (página %s): %s",
                    id_camara,
                    pagina,
                    exc,
                )
                break

        logger.debug(
            "Coletados %d discursos para deputado idCamara=%s (legislatura %s).",
            len(todos),
            id_camara,
            legislatura,
        )
        return todos
