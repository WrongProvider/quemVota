"""
injest_banco/injest_discursos.py — Ingestão de Discursos da Câmara dos Deputados (SPEC-007)

Coleta pronunciamentos e discursos de tribuna via API de Dados Abertos da Câmara:
GET /deputados/{id}/discursos

Valida com Pydantic V2 (DiscursoCamaraSchema) e persiste de forma idempotente
via PostgreSQL ON CONFLICT na tabela 'discursos'.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert

from injest_banco.collectors.discursos_collector import DiscursosCollector
from injest_banco.schemas_camara import DiscursoCamaraSchema
from shared.database import SYNC_URL
from shared.models import Deputado, Discurso

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("injest_discursos")


def sincronizar_discursos(
    engine: Any,
    legislatura: int = 57,
    deputado_id_filtro: Optional[int] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    max_paginas: int = 10,
) -> dict[str, int]:
    """Coordena a ingestão dos discursos para os deputados selecionados."""
    collector = DiscursosCollector()

    # 1. Carregar deputados alvo
    with engine.connect() as conn:
        stmt = (
            select(Deputado.id, Deputado.idCamara, Deputado.nome)
            .where(
                (Deputado.idLegislaturaFinal >= legislatura)
                & (Deputado.idLegislaturaInicial <= legislatura)
            )
            .order_by(Deputado.nome)
        )
        if deputado_id_filtro:
            stmt = stmt.where(
                (Deputado.id == deputado_id_filtro)
                | (Deputado.idCamara == deputado_id_filtro)
            )
        if limit:
            stmt = stmt.limit(limit)

        deputados = conn.execute(stmt).all()

    total_deputados = len(deputados)
    logger.info(
        "Iniciando ingestão de discursos para %s deputados (Legislatura %s)...",
        total_deputados,
        legislatura,
    )

    metricas = {
        "deputados_processados": 0,
        "discursos_coletados": 0,
        "discursos_validados": 0,
        "discursos_inseridos": 0,
        "descartados": 0,
    }

    for idx, dep in enumerate(deputados, start=1):
        dep_id = dep[0]
        id_camara = dep[1]
        _nome = dep[2]

        raw_items = collector.coletar(
            id_camara, legislatura=legislatura, max_paginas=max_paginas
        )
        metricas["deputados_processados"] += 1
        metricas["discursos_coletados"] += len(raw_items)

        registros_validos: list[dict[str, Any]] = []

        for item in raw_items:
            try:
                validado = DiscursoCamaraSchema(idDeputadoCamara=id_camara, **item)
                registros_validos.append(
                    {
                        "idDeputado": dep_id,
                        "dataHoraInicio": validado.dataHoraInicio,
                        "dataHoraFim": validado.dataHoraFim,
                        "tipoDiscurso": validado.tipoDiscurso or "",
                        "faseEventoTitulo": validado.faseEventoTitulo,
                        "sumario": validado.sumario,
                        "transcricao": validado.transcricao,
                        "keywords": validado.keywords,
                        "urlTexto": validado.urlTexto,
                        "urlAudio": validado.urlAudio,
                        "urlVideo": validado.urlVideo,
                    }
                )
            except Exception as e:
                metricas["descartados"] += 1
                logger.debug(
                    "Item descartado por validação (deputado %s): %s", dep_id, e
                )

        metricas["discursos_validados"] += len(registros_validos)

        if registros_validos and not dry_run:
            with engine.begin() as conn:
                insert_stmt = insert(Discurso).values(registros_validos)
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    constraint="uq_discursos_dep_inicio_tipo",
                    set_={
                        "dataHoraFim": insert_stmt.excluded.dataHoraFim,
                        "faseEventoTitulo": insert_stmt.excluded.faseEventoTitulo,
                        "sumario": insert_stmt.excluded.sumario,
                        "transcricao": insert_stmt.excluded.transcricao,
                        "keywords": insert_stmt.excluded.keywords,
                        "urlTexto": insert_stmt.excluded.urlTexto,
                        "urlAudio": insert_stmt.excluded.urlAudio,
                        "urlVideo": insert_stmt.excluded.urlVideo,
                    },
                )
                conn.execute(upsert_stmt)
            metricas["discursos_inseridos"] += len(registros_validos)

        if idx % 10 == 0 or idx == total_deputados:
            logger.info(
                "Progresso: %s/%s deputados | Discursos validados: %s",
                idx,
                total_deputados,
                metricas["discursos_validados"],
            )

    logger.info("✔ Ingestão concluída com sucesso! Métricas: %s", metricas)
    return metricas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingestão de discursos da Câmara dos Deputados."
    )
    parser.add_argument(
        "--legislatura", type=int, default=57, help="ID da Legislatura (padrão: 57)"
    )
    parser.add_argument(
        "--deputado-id",
        type=int,
        default=None,
        help="Filtrar por ID interno ou idCamara do deputado",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limite máximo de deputados a processar"
    )
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=10,
        help="Máximo de páginas de discursos por deputado",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Executa sem persistir no banco"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_engine(SYNC_URL, pool_pre_ping=True)
    try:
        sincronizar_discursos(
            engine,
            legislatura=args.legislatura,
            deputado_id_filtro=args.deputado_id,
            limit=args.limit,
            dry_run=args.dry_run,
            max_paginas=args.max_paginas,
        )
    except Exception as exc:
        logger.exception("Erro crítico no processo de ingestão de discursos: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
