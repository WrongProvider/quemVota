"""
classificar_temas.py — Pipeline de classificação semântica de temas de atuação parlamentar.

SPEC-001: Classificação de Temas de Atuação Parlamentar.

Etapas:
  1. Carrega os 20 vetores de TemaAtuacao em memória (numpy 20×1024).
  2. Busca proposições por autor em batches (default 500).
  3. Para cada proposição: encoda ementa+keywords com BAAI/bge-m3,
     salva em documentEmbeddings (idempotente). Calcula dot product
     contra os 20 temas (L2-normalizados → equivale a cosseno).
  4. Filtra sim >= 0.40, top 3 por item. Grava em itensTemasAtuacao.
  5. Agrega por deputado+legislatura: peso_ponderado = Σ(peso × score).
     Normaliza em proporção e grava em deputadoTemasAtuacao.

Flags:
  --limit-deputados N   Processar apenas os N primeiros deputados.
  --limit-proposicoes N Máximo de proposições por deputado (debug).
  --dry-run             Calcula sem gravar no banco.
  --legislatura N       Legislatura alvo (default 57).
  --deputado-id N       Processar apenas um deputado específico.
  --force               Re-processa mesmo que já exista entrada prévia.
"""

import argparse
import hashlib
import logging
import os
import sys
import time
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
import torch

from shared.database import SessionLocal
from shared.models import Deputado, Proposicao, ProposicaoAutor
from shared.models_vetorial import (
    DeputadoTemaAtuacao,
    DocumentEmbedding,
    ItemTemaAtuacao,
    TemaAtuacao,
    TipoEntidadeDocumento,
    TipoParticipacao,
)

# Limitar concorrência de threads matemáticas (PyTorch/BLAS/OpenMP) para não estrangular vCPUs
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

torch.set_num_threads(1)
if hasattr(torch, "set_num_interop_threads"):
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Pesos por tipo de participação (SPEC-001, etapa 2)
PESOS: dict[str, float] = {
    TipoParticipacao.autoria: 10.0,
    TipoParticipacao.coautoria: 5.0,
    TipoParticipacao.relatoria: 8.0,
    TipoParticipacao.discurso: 2.0,
    TipoParticipacao.evento: 1.0,
}

MODELO_NOME = "BAAI/bge-m3"
SIM_LIMIAR = 0.40
TOP_K = 3
LEGISLATURA_DEFAULT = 57
BATCH_PROPOSICOES = 500


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _tipo_participacao(proponente: bool, ordem: Optional[int]) -> TipoParticipacao:
    """Determina o tipo de participação a partir de flags do ProposicaoAutor."""
    if proponente and (ordem == 1 or ordem is None):
        return TipoParticipacao.autoria
    return TipoParticipacao.coautoria


def _carregar_vetores_temas(db) -> tuple[list[dict], np.ndarray]:
    """Carrega os 20 temas e seus vetores da tabela temasAtuacao."""
    rows = db.execute(
        select(
            TemaAtuacao.id,
            TemaAtuacao.slug,
            TemaAtuacao.nome,
            TemaAtuacao.embedding,
        ).where(TemaAtuacao.ativo.is_(True))
    ).all()

    if not rows:
        raise RuntimeError(
            "Tabela temasAtuacao está vazia. Execute tasks/seed_temas_atuacao.py primeiro."
        )

    temas_meta = [{"id": r.id, "slug": r.slug, "nome": r.nome} for r in rows]
    matriz = np.array([r.embedding for r in rows], dtype=np.float32)  # (N_temas, 1024)
    logger.info("Carregados %d temas em memória.", len(temas_meta))
    return temas_meta, matriz


def _buscar_deputados(
    db,
    limit: Optional[int],
    deputado_id: Optional[int],
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
        # Filtrar deputados que já têm entrada em deputadoTemasAtuacao para esta legislatura
        ja_processados = set(
            r[0]
            for r in db.execute(
                select(DeputadoTemaAtuacao.idDeputado)
                .where(DeputadoTemaAtuacao.idLegislatura == id_legislatura)
                .distinct()
            ).all()
        )
        pendentes = [d for d in todos_ids if d not in ja_processados]
        logger.info(
            "Total deputados: %d | Já processados: %d | Pendentes: %d",
            len(todos_ids),
            len(ja_processados),
            len(pendentes),
        )
        return pendentes

    logger.info("Modo --force: reprocessando %d deputados.", len(todos_ids))
    return todos_ids


def _buscar_proposicoes_deputado(
    db, deputado_id: int, limit_prop: Optional[int]
) -> list[dict]:
    """
    Retorna as proposições em que o deputado é autor, com flags de participação.
    """
    stmt = (
        select(
            Proposicao.id,
            Proposicao.ementa,
            Proposicao.keywords,
            ProposicaoAutor.proponente,
            ProposicaoAutor.ordemAssinatura,
        )
        .join(ProposicaoAutor, ProposicaoAutor.idProposicao == Proposicao.id)
        .where(ProposicaoAutor.idDeputadoAutor == deputado_id)
        .where(Proposicao.ementa.isnot(None))
    )
    if limit_prop:
        stmt = stmt.limit(limit_prop)

    return [
        {
            "id": r.id,
            "ementa": r.ementa or "",
            "keywords": r.keywords or "",
            "proponente": r.proponente,
            "ordem": r.ordemAssinatura,
        }
        for r in db.execute(stmt).all()
        if r.ementa and len(r.ementa.strip()) > 20
    ]


def _obter_ou_criar_embedding(
    db,
    prop: dict,
    model: SentenceTransformer,
    dry_run: bool,
) -> Optional[np.ndarray]:
    """
    Retorna o vetor da proposição. Se já existe em documentEmbeddings,
    reutiliza. Caso contrário, computa e persiste.
    """
    texto = f"{prop['ementa']} {prop['keywords']}".strip()
    texto_hash = _hash_texto(texto)

    row = db.execute(
        select(DocumentEmbedding.embedding).where(
            DocumentEmbedding.tipoEntidade == TipoEntidadeDocumento.proposicao,
            DocumentEmbedding.idEntidade == prop["id"],
            DocumentEmbedding.modelo == MODELO_NOME,
        )
    ).first()

    if row is not None:
        return np.array(row.embedding, dtype=np.float32)

    # Computar embedding
    vetor = model.encode(texto, normalize_embeddings=True).astype(np.float32)

    if not dry_run:
        stmt = insert(DocumentEmbedding).values(
            tipoEntidade=TipoEntidadeDocumento.proposicao,
            idEntidade=prop["id"],
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


def _classificar_item(
    vetor_doc: np.ndarray,
    temas_meta: list[dict],
    matriz_temas: np.ndarray,
) -> list[dict]:
    """
    Compara o vetor do documento com os 20 temas.
    Retorna lista [{id_tema, score, rank}] com top K acima do limiar.
    """
    scores = (matriz_temas @ vetor_doc).tolist()  # dot product, já L2-norm

    resultados = sorted(
        [
            {"id_tema": temas_meta[i]["id"], "score": float(s), "rank": 0}
            for i, s in enumerate(scores)
            if s >= SIM_LIMIAR
        ],
        key=lambda x: x["score"],
        reverse=True,
    )[:TOP_K]

    for rank_idx, item in enumerate(resultados, start=1):
        item["rank"] = rank_idx

    return resultados


def _gravar_itens(
    db,
    deputado_id: int,
    prop: dict,
    classificacoes: list[dict],
    tipo_participacao: TipoParticipacao,
    peso: float,
    dry_run: bool,
) -> int:
    """Grava ItemTemaAtuacao para cada tema classificado."""
    gravados = 0
    for cls in classificacoes:
        if not dry_run:
            stmt = insert(ItemTemaAtuacao).values(
                tipoEntidade=TipoEntidadeDocumento.proposicao,
                idEntidade=prop["id"],
                idDeputado=deputado_id,
                idTemaAtuacao=cls["id_tema"],
                tipoParticipacao=tipo_participacao,
                peso=peso,
                scoreClassificacao=round(cls["score"], 4),
                rankNoItem=cls["rank"],
                modelo=MODELO_NOME,
            )
            stmt_upsert = stmt.on_conflict_do_update(
                constraint="uq_item_tema_entidade_modelo",
                set_={
                    "tipoParticipacao": tipo_participacao,
                    "peso": peso,
                    "scoreClassificacao": round(cls["score"], 4),
                    "rankNoItem": cls["rank"],
                },
            )
            db.execute(stmt_upsert)
        gravados += 1
    return gravados


def _agregar_e_persistir_deputado(
    db,
    deputado_id: int,
    id_legislatura: int,
    dry_run: bool,
) -> int:
    """
    Agrega itensTemasAtuacao por deputado → normaliza → grava deputadoTemasAtuacao.
    Retorna número de temas gravados.
    """
    rows = db.execute(
        text(
            """
            SELECT ita."idTemaAtuacao",
                   SUM(ita.peso * ita."scoreClassificacao") AS peso_ponderado
            FROM "itensTemasAtuacao" ita
            WHERE ita."idDeputado" = :dep_id
              AND ita.modelo = :modelo
            GROUP BY ita."idTemaAtuacao"
            HAVING SUM(ita.peso * ita."scoreClassificacao") > 0
            ORDER BY peso_ponderado DESC
            """
        ),
        {"dep_id": deputado_id, "modelo": MODELO_NOME},
    ).all()

    if not rows:
        return 0

    total_peso = sum(float(r.peso_ponderado) for r in rows)
    gravados = 0

    for rank_idx, r in enumerate(rows, start=1):
        score = round(float(r.peso_ponderado) / total_peso, 4)

        if not dry_run:
            stmt = insert(DeputadoTemaAtuacao).values(
                idDeputado=deputado_id,
                idTemaAtuacao=r.idTemaAtuacao,
                idLegislatura=id_legislatura,
                score=score,
                pesoTotal=round(float(r.peso_ponderado), 2),
                rank=rank_idx,
            )
            stmt_upsert = stmt.on_conflict_do_update(
                constraint="uq_dep_tema_legislatura",
                set_={
                    "score": score,
                    "pesoTotal": round(float(r.peso_ponderado), 2),
                    "rank": rank_idx,
                },
            )
            db.execute(stmt_upsert)
        gravados += 1

    return gravados


def classificar_temas(
    limit_deputados: Optional[int] = None,
    limit_proposicoes: Optional[int] = None,
    dry_run: bool = False,
    id_legislatura: int = LEGISLATURA_DEFAULT,
    deputado_id: Optional[int] = None,
    force: bool = False,
) -> dict:
    """
    Executa o pipeline completo de classificação semântica de temas.
    Retorna métricas de execução.
    """
    t0 = time.perf_counter()
    logger.info(
        "=== SPEC-001 classificar_temas | dry_run=%s | legislatura=%d ===",
        dry_run,
        id_legislatura,
    )

    logger.info("Carregando modelo %s...", MODELO_NOME)
    model = SentenceTransformer(MODELO_NOME)
    logger.info("Modelo carregado.")

    db = SessionLocal()
    metricas: dict = {
        "deputados_processados": 0,
        "proposicoes_lidas": 0,
        "proposicoes_vetorizadas": 0,
        "proposicoes_sem_embedding": 0,
        "itens_classificados": 0,
        "deputados_agregados": 0,
    }

    try:
        temas_meta, matriz_temas = _carregar_vetores_temas(db)
        ids_deputados = _buscar_deputados(
            db, limit_deputados, deputado_id, force, id_legislatura
        )

        if not ids_deputados:
            logger.info("Nenhum deputado pendente para processar.")
            return metricas

        logger.info("Processando %d deputados...", len(ids_deputados))

        for dep_idx, dep_id in enumerate(ids_deputados, start=1):
            logger.info("[%d/%d] Deputado id=%d", dep_idx, len(ids_deputados), dep_id)

            proposicoes = _buscar_proposicoes_deputado(db, dep_id, limit_proposicoes)
            metricas["proposicoes_lidas"] += len(proposicoes)

            if not proposicoes:
                logger.info("  Sem proposições com ementa. Pulando.")
                metricas["deputados_processados"] += 1
                continue

            for prop in proposicoes:
                vetor = _obter_ou_criar_embedding(db, prop, model, dry_run)
                if vetor is None:
                    metricas["proposicoes_sem_embedding"] += 1
                    continue

                metricas["proposicoes_vetorizadas"] += 1

                tipo_part = _tipo_participacao(bool(prop["proponente"]), prop["ordem"])
                peso = PESOS[tipo_part]

                classificacoes = _classificar_item(vetor, temas_meta, matriz_temas)
                itens_gravados = _gravar_itens(
                    db, dep_id, prop, classificacoes, tipo_part, peso, dry_run
                )
                metricas["itens_classificados"] += itens_gravados

            # Commit parcial por deputado
            if not dry_run:
                db.commit()

            temas_gravados = _agregar_e_persistir_deputado(
                db, dep_id, id_legislatura, dry_run
            )
            if not dry_run:
                db.commit()

            if temas_gravados > 0:
                metricas["deputados_agregados"] += 1

            metricas["deputados_processados"] += 1

            if dep_idx % 10 == 0:
                elapsed = time.perf_counter() - t0
                logger.info(
                    "  Progresso: %d/%d deputados | %.1fs decorridos",
                    dep_idx,
                    len(ids_deputados),
                    elapsed,
                )

    except Exception:
        db.rollback()
        logger.exception("Erro fatal durante classificação de temas.")
        raise
    finally:
        db.close()

    elapsed_total = time.perf_counter() - t0
    logger.info("=== CONCLUÍDO em %.1fs | Métricas: %s ===", elapsed_total, metricas)
    return metricas


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SPEC-001: Pipeline de classificação semântica de temas de atuação."
    )
    parser.add_argument("--limit-deputados", type=int, default=None)
    parser.add_argument("--limit-proposicoes", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--legislatura", type=int, default=LEGISLATURA_DEFAULT)
    parser.add_argument("--deputado-id", type=int, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocessa mesmo que já exista entrada prévia.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    classificar_temas(
        limit_deputados=args.limit_deputados,
        limit_proposicoes=args.limit_proposicoes,
        dry_run=args.dry_run,
        id_legislatura=args.legislatura,
        deputado_id=args.deputado_id,
        force=args.force,
    )
    sys.exit(0)
