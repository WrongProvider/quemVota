"""
gerar_embeddings.py — Pipeline de geração de vetores semânticos com pgvector.

Processa proposições legislativas e gera embeddings de 1024 dimensões com BAAI/bge-m3,
gravando na tabela `documentEmbeddings` com índices HNSW.
Otimizado para alto throughput: inferência em lotes (batch inference) e upsert em chunks.
"""

import argparse
import hashlib
import logging
import os
from typing import List, Optional

from sentence_transformers import SentenceTransformer
from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
import torch
from tqdm import tqdm

from shared.database import SessionLocal
from shared.models import Proposicao, Votacao
from shared.models_vetorial import DocumentEmbedding, TipoEntidadeDocumento

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
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def montar_texto_proposicao(p: Proposicao) -> str:
    """Monta o texto representativo da proposição para geração do embedding semântico."""
    partes: List[str] = []

    cabecalho = f"{p.siglaTipo or 'PROPOSICAO'} {p.numero or ''}/{p.ano or ''}".strip()
    if cabecalho:
        partes.append(cabecalho)

    if p.ementa and p.ementa.strip():
        partes.append(p.ementa.strip())

    if (
        p.ementaDetalhada
        and p.ementaDetalhada.strip()
        and p.ementaDetalhada.strip() != p.ementa.strip()
    ):
        partes.append(p.ementaDetalhada.strip())

    if p.justificativa and p.justificativa.strip():
        # Limita a justificativa para evitar estouro desnecessário de contexto
        partes.append(p.justificativa.strip()[:1000])

    texto_final = "\n".join(partes).strip()
    return texto_final or f"Proposição {p.id}"


def processar_lote_proposicoes(
    session,
    model: SentenceTransformer,
    proposicoes: List[Proposicao],
    model_name: str = "BAAI/bge-m3",
    embedding_dim: int = 1024,
    batch_encode_size: int = 64,
) -> int:
    """Gera embeddings em lote e executa bulk upsert no PostgreSQL."""
    if not proposicoes:
        return 0

    textos: List[str] = [montar_texto_proposicao(p) for p in proposicoes]
    hashes: List[str] = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in textos]

    # Inferência vetorial em lote acelerada
    embeddings = model.encode(
        textos,
        batch_size=batch_encode_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    records = []
    for p, texto, h, emb in zip(proposicoes, textos, hashes, embeddings):
        records.append(
            {
                "tipoEntidade": TipoEntidadeDocumento.proposicao,
                "idEntidade": p.id,
                "idDeputado": None,
                "textoFonte": texto,
                "textoHash": h,
                "embedding": emb.tolist(),
                "modelo": model_name,
                "dimensao": embedding_dim,
            }
        )

    stmt = insert(DocumentEmbedding).values(records)
    stmt_upsert = stmt.on_conflict_do_update(
        index_elements=["tipoEntidade", "idEntidade", "modelo"],
        set_={
            "textoFonte": stmt.excluded.textoFonte,
            "textoHash": stmt.excluded.textoHash,
            "embedding": stmt.excluded.embedding,
            "dimensao": stmt.excluded.dimensao,
            "updatedAt": stmt.excluded.updatedAt,
        },
    )

    session.execute(stmt_upsert)
    session.commit()
    return len(records)


def executar_geracao_embeddings(
    ano_inicio: Optional[int] = None,
    ano_fim: Optional[int] = None,
    apenas_votadas: bool = False,
    chunk_size: int = 500,
    batch_encode_size: int = 64,
    limite_total: Optional[int] = None,
    model_name: str = "BAAI/bge-m3",
    embedding_dim: int = 1024,
) -> int:
    """Executa a rotina principal de busca e vetorização em chunks resilientes."""
    logger.info("Inicializando modelo de linguagem %s...", model_name)
    model = SentenceTransformer(model_name)

    session = SessionLocal()
    total_processado = 0

    try:
        # Monta a query base buscando proposições que ainda NÃO possuem embedding para este modelo
        subquery_existente = select(DocumentEmbedding.id).where(
            (DocumentEmbedding.idEntidade == Proposicao.id)
            & (DocumentEmbedding.tipoEntidade == TipoEntidadeDocumento.proposicao)
            & (DocumentEmbedding.modelo == model_name)
        )

        query = session.query(Proposicao).filter(~exists(subquery_existente))

        if ano_inicio:
            query = query.filter(Proposicao.ano >= ano_inicio)
        if ano_fim:
            query = query.filter(Proposicao.ano <= ano_fim)

        if apenas_votadas:
            # Filtra apenas proposições que possuem registro na tabela votacoes
            query = query.filter(exists().where(Votacao.idProposicao == Proposicao.id))

        query = query.order_by(Proposicao.ano.desc().nullslast(), Proposicao.id.desc())

        # Contagem estimada
        total_elegivel = query.count()
        if limite_total:
            total_elegivel = min(total_elegivel, limite_total)

        logger.info("Proposições elegíveis para vetorização: %d", total_elegivel)
        if total_elegivel == 0:
            logger.info(
                "Nenhuma proposição pendente encontrada com os filtros fornecidos."
            )
            return 0

        pbar = tqdm(total=total_elegivel, desc="Vetorizando proposições", unit="prop")

        while True:
            tamanho_lote = chunk_size
            if limite_total:
                restante = limite_total - total_processado
                if restante <= 0:
                    break
                tamanho_lote = min(chunk_size, restante)

            # Busca o próximo lote de proposições ainda não processadas
            lote = query.limit(tamanho_lote).all()
            if not lote:
                break

            qtd = processar_lote_proposicoes(
                session=session,
                model=model,
                proposicoes=lote,
                model_name=model_name,
                embedding_dim=embedding_dim,
                batch_encode_size=batch_encode_size,
            )

            total_processado += qtd
            pbar.update(qtd)

            if limite_total and total_processado >= limite_total:
                break

        pbar.close()
        logger.info(
            "Concluído! Total de %d proposições vetorizadas com sucesso.",
            total_processado,
        )
        return total_processado

    except Exception as e:
        session.rollback()
        logger.error("Erro durante pipeline de vetorização: %s", e)
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Gera embeddings de proposições com pgvector"
    )
    parser.add_argument(
        "--ano-inicio", type=int, default=None, help="Ano inicial (ex: 2023)"
    )
    parser.add_argument(
        "--ano-fim", type=int, default=None, help="Ano final (ex: 2026)"
    )
    parser.add_argument(
        "--legislatura",
        type=int,
        default=None,
        help="Número da legislatura (57 = 2023..2026, 56 = 2019..2022)",
    )
    parser.add_argument(
        "--apenas-votadas",
        action="store_true",
        help="Vetorizar apenas proposições que possuem votações",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite máximo de itens para esta execução",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Tamanho do chunk de leitura do banco",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size para inferência no PyTorch",
    )
    parser.add_argument(
        "--model", type=str, default="BAAI/bge-m3", help="Nome do modelo Hugging Face"
    )

    args = parser.parse_args()

    ano_inicio = args.ano_inicio
    ano_fim = args.ano_fim

    if args.legislatura == 57:
        ano_inicio = ano_inicio or 2023
        ano_fim = ano_fim or 2026
    elif args.legislatura == 56:
        ano_inicio = ano_inicio or 2019
        ano_fim = ano_fim or 2022

    executar_geracao_embeddings(
        ano_inicio=ano_inicio,
        ano_fim=ano_fim,
        apenas_votadas=args.apenas_votadas,
        chunk_size=args.chunk_size,
        batch_encode_size=args.batch_size,
        limite_total=args.limit,
        model_name=args.model,
    )


if __name__ == "__main__":
    main()
