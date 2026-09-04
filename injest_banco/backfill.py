"""
backfill.py
===========
Rotinas de enriquecimento de detalhes de deputados via API REST (GET /deputados/{id}).
Preenche dados que não constam na listagem básica de deputados:
  - nomeCivil, escolaridade, situacao, condicaoEleitoral, urlFoto,
  - emailGabinete, telefoneGabinete, slug único e cpf.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import logging
import re
from threading import Lock, Semaphore
import time
import unicodedata
from typing import Any, Optional

from sqlalchemy import text

from injest_banco.client import CamaraClient

log = logging.getLogger("etl_camara.backfill")

DEFAULT_BACKFILL_WORKERS = 4
BACKFILL_SLEEP = 0.25  # segundos entre requisições por thread
BACKFILL_COMMIT_BATCH = 50


def parse_iso_date(valor: Optional[str]) -> Optional[date]:
    """Converte string ISO para date (YYYY-MM-DD)."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def generate_slug(text_val: Optional[str]) -> Optional[str]:
    """Gera slug limpo a partir de texto (ASCII em minúsculas e hífens)."""
    if not text_val:
        return None
    normalized = (
        unicodedata.normalize("NFKD", text_val)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
    )
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def is_deputado_incompleto(row: dict[str, Any]) -> bool:
    """Verifica se o deputado precisa de enriquecimento via API REST."""
    return any(
        [
            not row.get("urlFoto"),
            not row.get("nomeCivil"),
            not row.get("escolaridade"),
            not row.get("situacao"),
            not row.get("emailGabinete"),
            not row.get("slug"),
            not row.get("cpf"),
        ]
    )


def build_deputado_updates(dados: dict[str, Any]) -> dict[str, Any]:
    """Monta o dict de atualizações a partir da resposta da API REST (/deputados/{id})."""
    status = dados.get("ultimoStatus") or {}
    gabinete = status.get("gabinete") or {}
    nome_display = status.get("nome") or dados.get("nomeCivil")

    return {
        "nomeCivil": dados.get("nomeCivil"),
        "dataNascimento": parse_iso_date(dados.get("dataNascimento")),
        "siglaSexo": dados.get("sexo"),
        "escolaridade": dados.get("escolaridade"),
        "situacao": status.get("situacao"),
        "condicaoEleitoral": status.get("condicaoEleitoral"),
        "siglaUF": status.get("siglaUf"),
        "siglaPartido": status.get("siglaPartido"),
        "urlFoto": status.get("urlFoto"),
        "emailGabinete": gabinete.get("email") or status.get("email"),
        "telefoneGabinete": gabinete.get("telefone"),
        "slug": generate_slug(nome_display),
        "cpf": dados.get("cpf"),
    }


def resolve_unique_slug(slug_base: str, id_camara: int, slugs_em_uso: set[str]) -> str:
    """Garante unicidade do slug: se duplicado, adiciona o idCamara como sufixo."""
    slug = slug_base
    if slug in slugs_em_uso:
        slug = f"{slug_base}-{id_camara}"
        log.warning("⚠️  Slug duplicado — usando sufixo: %s", slug)
    slugs_em_uso.add(slug)
    return slug


def run_backfill_deputados(
    engine: Any,
    *,
    force: bool = False,
    slug_only: bool = False,
    workers: int = DEFAULT_BACKFILL_WORKERS,
    client: Optional[CamaraClient] = None,
) -> None:
    """
    Percorre todos os deputados na tabela e preenche os campos de detalhe
    via GET /deputados/{idCamara} em paralelo com respeito ao rate-limit.
    """
    client = client or CamaraClient()
    semaphore = Semaphore(workers)

    log.info(
        "🚀 Backfill de deputados iniciado [force=%s | slug_only=%s | workers=%d]",
        force,
        slug_only,
        workers,
    )

    with engine.begin() as conn:
        rows = (
            conn.execute(
                text(
                    'SELECT id, "idCamara", nome, "nomeCivil", "urlFoto", "escolaridade", '
                    '"situacao", "emailGabinete", slug, cpf FROM deputados ORDER BY "idCamara"'
                )
            )
            .mappings()
            .all()
        )

    todos = [dict(r) for r in rows]
    log.info("📋 Total de deputados no banco: %d", len(todos))

    slugs_lock = Lock()
    slugs_em_uso: set[str] = {d["slug"] for d in todos if d.get("slug")}

    # ── Modo slug_only ────────────────────────────────────────────────────────
    if slug_only:
        log.info("⚡ Modo slug_only: gerando slugs sem chamar a API")
        slugs_em_uso.clear()
        updates: list[dict[str, Any]] = []
        for dep in todos:
            slug_base = generate_slug(dep.get("nome")) or f"deputado-{dep['idCamara']}"
            slug = resolve_unique_slug(slug_base, dep["idCamara"], slugs_em_uso)
            updates.append({"id": dep["id"], "slug": slug})

        with engine.begin() as conn:
            for u in updates:
                conn.execute(
                    text("UPDATE deputados SET slug = :slug WHERE id = :id"),
                    u,
                )
        log.info("✔ %d slugs atualizados com sucesso.", len(updates))
        return

    # ── Modo normal ou force ──────────────────────────────────────────────────
    alvos = todos if force else [d for d in todos if is_deputado_incompleto(d)]
    log.info(
        "🎯 Deputados a processar: %d (%d já estavam completos)",
        len(alvos),
        len(todos) - len(alvos),
    )
    if not alvos:
        log.info("✔ Nenhum deputado incompleto — nada a fazer.")
        return

    def _process_one(
        dep: dict[str, Any],
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        with semaphore:
            time.sleep(BACKFILL_SLEEP)
            dados = client.get_deputado_detalhes(dep["idCamara"])
            return dep, dados

    total = len(alvos)
    sucesso = 0
    erros = 0
    buffer_updates: list[dict[str, Any]] = []

    def _flush_buffer(conn, buf: list[dict[str, Any]]) -> None:
        if not buf:
            return
        for u in buf:
            conn.execute(
                text(
                    "UPDATE deputados SET "
                    '"nomeCivil" = COALESCE(:nomeCivil, "nomeCivil"), '
                    '"dataNascimento" = COALESCE(:dataNascimento, "dataNascimento"), '
                    '"siglaSexo" = COALESCE(:siglaSexo, "siglaSexo"), '
                    "escolaridade = COALESCE(:escolaridade, escolaridade), "
                    "situacao = COALESCE(:situacao, situacao), "
                    '"condicaoEleitoral" = COALESCE(:condicaoEleitoral, "condicaoEleitoral"), '
                    '"siglaUF" = COALESCE(:siglaUF, "siglaUF"), '
                    '"siglaPartido" = COALESCE(:siglaPartido, "siglaPartido"), '
                    '"urlFoto" = COALESCE(:urlFoto, "urlFoto"), '
                    '"emailGabinete" = COALESCE(:emailGabinete, "emailGabinete"), '
                    '"telefoneGabinete" = COALESCE(:telefoneGabinete, "telefoneGabinete"), '
                    "slug = COALESCE(:slug, slug), "
                    "cpf = COALESCE(:cpf, cpf) "
                    "WHERE id = :id"
                ),
                u,
            )
        buf.clear()

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="bf-dep") as pool:
        futures = {pool.submit(_process_one, dep): dep for dep in alvos}

        for future in as_completed(futures):
            dep, dados = future.result()
            if not dados:
                log.warning(
                    "Sem dados na API para idCamara=%d (%s)",
                    dep["idCamara"],
                    dep["nome"],
                )
                erros += 1
                continue

            u = build_deputado_updates(dados)
            u["id"] = dep["id"]

            slug_base = (
                u["slug"] or generate_slug(dep["nome"]) or f"deputado-{dep['idCamara']}"
            )
            with slugs_lock:
                u["slug"] = resolve_unique_slug(
                    slug_base, dep["idCamara"], slugs_em_uso
                )

            buffer_updates.append(u)
            sucesso += 1

            if len(buffer_updates) >= BACKFILL_COMMIT_BATCH:
                with engine.begin() as conn:
                    _flush_buffer(conn, buffer_updates)
                log.info(
                    "💾 Progresso backfill: %d/%d deputados gravados...", sucesso, total
                )

    if buffer_updates:
        with engine.begin() as conn:
            _flush_buffer(conn, buffer_updates)

    log.info(
        "🏁 Backfill concluído — processados: %d | sucesso: %d | erros: %d",
        total,
        sucesso,
        erros,
    )
