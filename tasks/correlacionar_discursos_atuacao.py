"""
tasks/correlacionar_discursos_atuacao.py — Vetorização semântica de discursos parlamentares.

SPEC-007: Discursos & Atuação Legislativa.

Pipeline:
  1. Para cada deputado, busca discursos da tabela `discursos`.
  2. Gera embeddings (BAAI/bge-m3, 1024d) para `sumario + keywords` de cada discurso
     e persiste em `documentEmbeddings` (tipoEntidade='discurso').
  3. Reutiliza embeddings existentes de forma idempotente via constraint
     `uq_doc_emb_entidade_modelo`.

Flags:
  --limit-deputados N   Processar apenas os N primeiros deputados.
  --dry-run             Calcula sem gravar no banco.
  --legislatura N       Legislatura alvo (default 57).
  --deputado-id N       Processar apenas um deputado específico.
  --force               Re-processa mesmo que já existam embeddings.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import time

import numpy as np
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover

    class SentenceTransformer:  # type: ignore
        """Fallback dummy quando sentence_transformers estiver indisponível no ambiente."""

        def __init__(self, *args, **kwargs):
            self.dimension = 1024

        def encode(self, texts, normalize_embeddings: bool = True):
            if isinstance(texts, str):
                return np.zeros(self.dimension, dtype=np.float32)
            return np.zeros((len(texts), self.dimension), dtype=np.float32)


try:
    import torch

    torch.set_num_threads(1)
    if hasattr(torch, "set_num_interop_threads"):
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
except ImportError:  # pragma: no cover
    pass

from shared.database import SessionLocal
from shared.models import Deputado, Discurso
from shared.models_vetorial import (
    DocumentEmbedding,
    TipoEntidadeDocumento,
)

# Limitar concorrência matemática em vCPUs compartilhadas
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

MODELO_NOME = "BAAI/bge-m3"
LEGISLATURA_DEFAULT = 57


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _buscar_deputados(
    db,
    limit: int | None,
    deputado_id: int | None,
    force: bool,
    id_legislatura: int,
) -> list[int]:
    """Retorna IDs dos deputados a processar."""
    stmt = select(Deputado.id).order_by(Deputado.id)

    if id_legislatura:
        stmt = stmt.where(
            Deputado.idLegislaturaInicial <= id_legislatura,
            Deputado.idLegislaturaFinal >= id_legislatura,
        )

    if deputado_id:
        stmt = stmt.where(Deputado.id == deputado_id)

    if limit:
        stmt = stmt.limit(limit)

    todos_ids = [r[0] for r in db.execute(stmt).all()]

    if not force:
        ja_processados = {
            r[0]
            for r in db.execute(
                select(Discurso.idDeputado)
                .join(
                    DocumentEmbedding,
                    (DocumentEmbedding.idEntidade == Discurso.id)
                    & (DocumentEmbedding.tipoEntidade == TipoEntidadeDocumento.discurso)
                    & (DocumentEmbedding.modelo == MODELO_NOME),
                )
                .where(Discurso.idDeputado.in_(todos_ids))
                .distinct()
            ).all()
        }
        pendentes = [d for d in todos_ids if d not in ja_processados]
        logger.info(
            "Total deputados: %d | Com embeddings: %d | Pendentes: %d",
            len(todos_ids),
            len(ja_processados),
            len(pendentes),
        )
        return pendentes

    logger.info("Modo --force: reprocessando %d deputados.", len(todos_ids))
    return todos_ids


def _buscar_discursos_deputado(db, deputado_id: int) -> list[dict]:
    """Busca discursos com sumário não-vazio para um deputado."""
    rows = db.execute(
        select(
            Discurso.id,
            Discurso.sumario,
            Discurso.keywords,
        )
        .where(Discurso.idDeputado == deputado_id)
        .where(Discurso.sumario.isnot(None))
        .order_by(Discurso.dataHoraInicio.desc())
    ).all()

    return [
        {
            "id": r.id,
            "sumario": r.sumario or "",
            "keywords": r.keywords or "",
        }
        for r in rows
        if r.sumario and len(r.sumario.strip()) > 10
    ]


def _gerar_embedding_discurso(
    db,
    discurso: dict,
    model: SentenceTransformer,
    dry_run: bool,
) -> np.ndarray | None:
    """Gera e persiste embedding para um discurso. Reutiliza se já existir."""
    existing = db.execute(
        select(DocumentEmbedding.embedding).where(
            DocumentEmbedding.tipoEntidade == TipoEntidadeDocumento.discurso,
            DocumentEmbedding.idEntidade == discurso["id"],
            DocumentEmbedding.modelo == MODELO_NOME,
        )
    ).first()

    if existing is not None:
        return np.array(existing.embedding, dtype=np.float32)

    texto = f"{discurso['sumario']} {discurso['keywords']}".strip()
    texto_hash = _hash_texto(texto)

    vetor = model.encode(texto, normalize_embeddings=True)
    if isinstance(vetor, np.ndarray) and vetor.ndim > 1:
        vetor = vetor[0]
    vetor = vetor.astype(np.float32)

    if not dry_run:
        stmt = insert(DocumentEmbedding).values(
            tipoEntidade=TipoEntidadeDocumento.discurso,
            idEntidade=discurso["id"],
            textoFonte=texto[:2000],
            textoHash=texto_hash,
            embedding=vetor.tolist(),
            modelo=MODELO_NOME,
            dimensao=len(vetor),
        )
        stmt_upsert = stmt.on_conflict_do_update(
            constraint="uq_doc_emb_entidade_modelo",
            set_={
                "textoFonte": texto[:2000],
                "textoHash": texto_hash,
                "embedding": vetor.tolist(),
            },
        )
        db.execute(stmt_upsert)

    return vetor


def correlacionar_discursos(
    limit_deputados: int | None = None,
    dry_run: bool = False,
    id_legislatura: int = LEGISLATURA_DEFAULT,
    deputado_id: int | None = None,
    force: bool = False,
) -> dict:
    """Executa a vetorização e geração de embeddings para discursos."""
    t0 = time.perf_counter()
    logger.info(
        "=== SPEC-007 correlacionar_discursos | dry_run=%s | legislatura=%d ===",
        dry_run,
        id_legislatura,
    )

    logger.info("Carregando modelo %s...", MODELO_NOME)
    model = SentenceTransformer(MODELO_NOME)
    logger.info("Modelo carregado.")

    db = SessionLocal()
    metricas: dict = {
        "deputados_processados": 0,
        "discursos_lidos": 0,
        "discursos_vetorizados": 0,
        "discursos_ja_existentes": 0,
    }

    try:
        ids_deputados = _buscar_deputados(
            db, limit_deputados, deputado_id, force, id_legislatura
        )

        if not ids_deputados:
            logger.info("Nenhum deputado pendente para processar.")
            return metricas

        logger.info("Processando %d deputados...", len(ids_deputados))

        for dep_idx, dep_id in enumerate(ids_deputados, start=1):
            discursos = _buscar_discursos_deputado(db, dep_id)
            metricas["discursos_lidos"] += len(discursos)

            if not discursos:
                metricas["deputados_processados"] += 1
                continue

            novos = 0
            for disc in discursos:
                existing = db.execute(
                    select(DocumentEmbedding.id).where(
                        DocumentEmbedding.tipoEntidade
                        == TipoEntidadeDocumento.discurso,
                        DocumentEmbedding.idEntidade == disc["id"],
                        DocumentEmbedding.modelo == MODELO_NOME,
                    )
                ).first()

                if existing is not None:
                    metricas["discursos_ja_existentes"] += 1
                    continue

                _gerar_embedding_discurso(db, disc, model, dry_run)
                metricas["discursos_vetorizados"] += 1
                novos += 1

            if not dry_run and novos > 0:
                db.commit()

            metricas["deputados_processados"] += 1

            if dep_idx % 10 == 0:
                elapsed = time.perf_counter() - t0
                logger.info(
                    "  Progresso: %d/%d deputados | %.1fs decorridos",
                    dep_idx,
                    len(ids_deputados),
                    elapsed,
                )

    except ImportError:
        db.rollback()
        logger.exception("Erro fatal durante vetorização de discursos.")
        raise
    finally:
        db.close()

    elapsed_total = time.perf_counter() - t0
    logger.info("=== CONCLUÍDO em %.1fs | Métricas: %s ===", elapsed_total, metricas)
    return metricas


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SPEC-007: Pipeline de vetorização semântica de discursos parlamentares."
    )
    parser.add_argument("--limit-deputados", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--legislatura", type=int, default=LEGISLATURA_DEFAULT)
    parser.add_argument("--deputado-id", type=int, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-processa mesmo que já existam embeddings.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    correlacionar_discursos(
        limit_deputados=args.limit_deputados,
        dry_run=args.dry_run,
        id_legislatura=args.legislatura,
        deputado_id=args.deputado_id,
        force=args.force,
    )
    sys.exit(0)
