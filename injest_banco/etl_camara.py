"""
etl_camara.py
=============
Orquestrador modular e ponto de entrada da esteira de ETL da Câmara dos Deputados.
Fonte: dadosabertos.camara.leg.br

Uso:
    # Carga incremental / ano corrente
    python -m injest_banco.etl_camara --update

    # Carga histórica completa
    python -m injest_banco.etl_camara --full

    # Dry-run para testes e validação rápida
    python -m injest_banco.etl_camara --dry-run --limit 5

    # Dataset específico
    python -m injest_banco.etl_camara --dataset votacoes --anos 2023 2024
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import os
from pathlib import Path
import sys

from sqlalchemy import create_engine, text
from tqdm import tqdm

# Garante resolução de imports tanto executado como módulo (-m) quanto script direto
_current_dir = Path(__file__).resolve().parent
_repo_root = _current_dir.parent
for _p in [str(_repo_root), str(_current_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from injest_banco.backfill import run_backfill_deputados  # noqa: E402
    from injest_banco.catalog import Dataset, build_catalog  # noqa: E402
    from injest_banco.client import CamaraClient, ETagCache, _CACHE_HIT  # noqa: E402
    from injest_banco.loaders import bulk_resolve_and_insert, bulk_upsert  # noqa: E402
    from injest_banco.reconciler import reconcile_orphan_votacoes  # noqa: E402
except ImportError:
    from backfill import run_backfill_deputados  # noqa: E402
    from catalog import Dataset, build_catalog  # noqa: E402
    from client import CamaraClient, ETagCache, _CACHE_HIT  # noqa: E402
    from loaders import bulk_resolve_and_insert, bulk_upsert  # noqa: E402
    from reconciler import reconcile_orphan_votacoes  # noqa: E402

from shared.database import SYNC_URL  # noqa: E402


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
# Constantes padrão
# ---------------------------------------------------------------------------
ANO_ATUAL = datetime.now().year
ANOS_HISTORICO = list(range(2008, ANO_ATUAL + 1))
DEFAULT_DOWNLOAD_WORKERS = int(os.getenv("ETL_DOWNLOAD_WORKERS", "8"))
DEFAULT_BACKFILL_WORKERS = int(os.getenv("ETL_BACKFILL_WORKERS", "4"))


def get_legislaturas_disponiveis(engine) -> list[int]:
    """Obtém as legislaturas registradas no banco ou fallback para as mais recentes."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text('SELECT "idLegislatura" FROM legislaturas ORDER BY 1')
            ).fetchall()
            return [r[0] for r in rows] or [56, 57]
    except Exception:
        return [56, 57]


def process_dataset(
    ds: Dataset,
    client: CamaraClient,
    engine,
    skip_historical: bool,
    dry_run: bool = False,
) -> tuple[str, str, int]:
    """
    Processa um único dataset: download -> transformação -> persistência.
    Retorna (nome_dataset, status, total_registros).
    Status: "ok" | "304" | "skip_hist" | "error"
    """
    if skip_historical and ds.ano_ref is not None and ds.ano_ref < ANO_ATUAL:
        log.debug("⏭ histórico imutável, pulando: %s", ds.nome)
        return ds.nome, "skip_hist", 0

    url = ds.url_fn()

    if ds.nome.startswith("cotas_"):
        df = client.download_csv_zip(url)
    else:
        df = client.download_csv(url)

    if df is _CACHE_HIT:
        return ds.nome, "304", 0
    if df is None:
        return ds.nome, "error", 0

    try:
        records = ds.transform_fn(df)
    except Exception as exc:
        log.error("Erro na transformação de [%s]: %s", ds.nome, exc)
        return ds.nome, "error", 0

    if dry_run:
        log.info(
            "🔍 [Dry-Run] %s -> %d registros validados (sem escrita)",
            ds.nome,
            len(records),
        )
        return ds.nome, "ok", len(records)

    try:
        if ds.table_name.startswith("_raw_"):
            n = bulk_resolve_and_insert(engine, ds.table_name, records)
            log.info("  FK-insert %s -> %d registros gravados", ds.nome, n)
        else:
            n = bulk_upsert(
                engine, ds.table_name, ds.preserve_cols, records, ds.conflict_cols
            )
            log.info("  upsert %s -> %d registros gravados", ds.nome, n)
    except Exception as exc:
        log.error("Erro na carga de [%s]: %s", ds.nome, exc)
        return ds.nome, "error", 0

    return ds.nome, "ok", len(records)


def run_etl(
    datasets: list[Dataset],
    engine,
    client: CamaraClient,
    *,
    force: bool = False,
    skip_historical: bool = False,
    dry_run: bool = False,
    backfill_deputados: bool = False,
    backfill_force: bool = False,
    backfill_slug_only: bool = False,
    workers: int = DEFAULT_DOWNLOAD_WORKERS,
    backfill_workers: int = DEFAULT_BACKFILL_WORKERS,
) -> list[str]:
    """
    Executa o pipeline de ETL particionado nas ondas de dependência (dep_group).
    """
    erros: list[str] = []
    pulados_historico = 0
    pulados_304 = 0
    processados = 0
    total_linhas_processadas = 0

    grupos: dict[int, list[Dataset]] = {}
    for ds in datasets:
        grupos.setdefault(ds.dep_group, []).append(ds)

    deputados_processado = False

    for group_id in sorted(grupos.keys()):
        grupo_datasets = grupos[group_id]
        log.info("━" * 60)
        log.info(
            "🌊 Onda %d — %d datasets | workers=%d | dry_run=%s",
            group_id,
            len(grupo_datasets),
            workers,
            dry_run,
        )

        futures_map = {}
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix=f"etl-g{group_id}"
        ) as pool:
            for ds in grupo_datasets:
                future = pool.submit(
                    process_dataset, ds, client, engine, skip_historical, dry_run
                )
                futures_map[future] = ds

            with tqdm(
                total=len(grupo_datasets), desc=f"Grupo {group_id}", unit="ds"
            ) as pbar:
                for future in as_completed(futures_map):
                    ds = futures_map[future]
                    try:
                        nome, status, n_rows = future.result()
                    except Exception as exc:
                        log.error("Exceção não tratada em [%s]: %s", ds.nome, exc)
                        erros.append(ds.nome)
                        pbar.update(1)
                        continue

                    if status == "ok":
                        processados += 1
                        total_linhas_processadas += n_rows
                        if not force and processados % 20 == 0:
                            client.cache.save()
                        if nome == "deputados":
                            deputados_processado = True
                    elif status == "304":
                        pulados_304 += 1
                    elif status == "skip_hist":
                        pulados_historico += 1
                    elif status == "error":
                        erros.append(nome)

                    pbar.update(1)

        if (
            deputados_processado
            and not dry_run
            and (backfill_deputados or backfill_force or backfill_slug_only)
        ):
            deputados_processado = False
            if not force:
                client.cache.save()
            run_backfill_deputados(
                engine,
                force=backfill_force,
                slug_only=backfill_slug_only,
                workers=backfill_workers,
                client=client,
            )

    if not force:
        client.cache.save()

    total = len(datasets)
    log.info("━" * 60)
    log.info(
        "🏁 ETL concluído — datasets processados: %d (%d registros) | 304: %d | "
        "histórico pulado: %d | erros: %d | total datasets: %d",
        processados,
        total_linhas_processadas,
        pulados_304,
        pulados_historico,
        len(erros),
        total,
    )
    if erros:
        log.warning("⚠️  Datasets com falha (%d): %s", len(erros), erros)

    return erros


def main():
    parser = argparse.ArgumentParser(
        description="ETL Modular — Dados Abertos da Câmara dos Deputados"
    )
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        "--full", action="store_true", help="Carga histórica completa (2008–hoje)"
    )
    mode.add_argument(
        "--update",
        action="store_true",
        help="Apenas o ano corrente (pula histórico automaticamente)",
    )
    mode.add_argument(
        "--dataset", type=str, help="Prefixo do dataset (ex: votacoes, eventos)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa download e validação sem gravar no banco de dados",
    )

    parser.add_argument("--anos", type=int, nargs="+", help="Anos específicos")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignora cache de ETag e reprocessa tudo",
    )
    parser.add_argument(
        "--cache-file",
        type=str,
        default=None,
        help="Caminho do arquivo de cache ETag",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_DOWNLOAD_WORKERS,
        help=f"Threads para download/processamento (padrão: {DEFAULT_DOWNLOAD_WORKERS})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita o número de datasets processados (útil para testes)",
    )
    parser.add_argument(
        "--reconcile-orfas",
        action="store_true",
        help="Executa rotina de reconciliação de votações órfãs após o ETL",
    )

    # ── Backfill de deputados ────────────────────────────────────────────────
    backfill_grp = parser.add_argument_group(
        "backfill", "Enriquecimento de deputados via API REST"
    )
    backfill_grp.add_argument(
        "--backfill-deputados",
        action="store_true",
        default=False,
        help="Preenche detalhes dos deputados incompletos",
    )
    backfill_grp.add_argument(
        "--backfill-force",
        action="store_true",
        default=False,
        help="Reprocessa todos os deputados (implica --backfill-deputados)",
    )
    backfill_grp.add_argument(
        "--backfill-slug-only",
        action="store_true",
        default=False,
        help="Apenas regera slugs a partir do nome sem chamar a API REST",
    )
    backfill_grp.add_argument(
        "--backfill-workers",
        type=int,
        default=DEFAULT_BACKFILL_WORKERS,
        help=f"Threads do backfill (padrão: {DEFAULT_BACKFILL_WORKERS})",
    )

    args = parser.parse_args()

    has_mode = any([args.full, args.update, args.dataset, args.dry_run])
    has_standalone_action = any(
        [
            args.reconcile_orfas,
            args.backfill_deputados,
            args.backfill_force,
            args.backfill_slug_only,
        ]
    )
    if not has_mode and not has_standalone_action:
        parser.error(
            "Informe um modo de execução (--full, --update, --dataset, --dry-run) "
            "ou uma ação autônoma (--reconcile-orfas, --backfill-deputados, --backfill-slug-only)."
        )

    cache_file = Path(args.cache_file) if args.cache_file else None
    cache = ETagCache(cache_file) if cache_file else ETagCache()
    if args.force:
        cache.clear()

    client = CamaraClient(cache=cache)

    engine = None
    if not args.dry_run:
        engine = create_engine(
            SYNC_URL,
            pool_pre_ping=True,
            pool_size=max(args.workers, args.backfill_workers) + 4,
            max_overflow=4,
        )
        log.info("Banco: conectado")

    # Ação autônoma: executa diretamente sem baixar todos os datasets
    if not has_mode:
        if args.backfill_deputados or args.backfill_force or args.backfill_slug_only:
            if engine is None:
                log.error("Banco de dados não disponível para backfill.")
                sys.exit(1)
            run_backfill_deputados(
                engine,
                force=args.backfill_force,
                slug_only=args.backfill_slug_only,
                workers=args.backfill_workers,
                client=client,
            )

        if args.reconcile_orfas:
            if engine is None:
                log.error("Banco de dados não disponível para reconciliação.")
                sys.exit(1)
            reconcile_orphan_votacoes(engine, client=client)

        sys.exit(0)

    if args.full:
        anos = ANOS_HISTORICO
        skip_historical = False
    elif args.update:
        anos = args.anos or [ANO_ATUAL]
        skip_historical = not args.force
    else:
        anos = args.anos or [ANO_ATUAL]
        skip_historical = False

    legislaturas = [56, 57] if args.dry_run else get_legislaturas_disponiveis(engine)
    catalog = build_catalog(anos, legislaturas)

    if args.dataset:
        catalog = [ds for ds in catalog if ds.nome.startswith(args.dataset)]
        if not catalog:
            log.error("Nenhum dataset encontrado com prefixo '%s'", args.dataset)
            sys.exit(1)

    if args.limit:
        catalog = catalog[: args.limit]

    log.info(
        "Iniciando ETL: %d datasets selecionados | anos=%s | legislaturas=%s",
        len(catalog),
        anos,
        legislaturas,
    )

    erros = run_etl(
        catalog,
        engine,
        client,
        force=args.force,
        skip_historical=skip_historical,
        dry_run=args.dry_run,
        backfill_deputados=args.backfill_deputados,
        backfill_force=args.backfill_force,
        backfill_slug_only=args.backfill_slug_only,
        workers=args.workers,
        backfill_workers=args.backfill_workers,
    )

    if args.reconcile_orfas and not args.dry_run and engine is not None:
        reconcile_orphan_votacoes(engine, client=client)

    if erros:
        log.error(
            "ETL finalizado com %d dataset(s) em erro — saindo com código 1", len(erros)
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
