"""
vector_search.py — Utilitários de Busca Vetorial e Híbrida com pgvector

Fornece funções otimizadas para:
- Busca por k-vizinhos mais próximos (KNN) usando distância por cosseno (<=>).
- Configuração dinâmica de `hnsw.ef_search` em tempo de execução.
- Busca híbrida (combinação de busca textual full-text/keyword com distância vetorial pgvector).
- Recuperação de deputados semanticamente semelhantes via perfis vetoriais.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Deputado, Proposicao
from shared.models_vetorial import DeputadoPerfilVetorial, DocumentEmbedding


def set_hnsw_ef_search_sync(session: Session, ef_search: int = 100) -> None:
    """
    Ajusta dinamicamente a variável de sessão `hnsw.ef_search` para controlar o trade-off
    entre revocabilidade (recall) e latência em consultas HNSW síncronas.
    """
    session.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))


async def set_hnsw_ef_search_async(session: AsyncSession, ef_search: int = 100) -> None:
    """
    Ajusta dinamicamente a variável de sessão `hnsw.ef_search` em sessões assíncronas.
    """
    await session.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))


def vector_knn_search(
    session: Session,
    query_vector: List[float],
    limit: int = 10,
    ef_search: int = 100,
    tipo_entidade: Optional[str] = None,
    modelo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Realiza busca por k-vizinhos mais próximos (KNN) sobre `documentEmbeddings` usando pgvector.

    Métrica de distância: Cosseno (`DocumentEmbedding.embedding.cosine_distance(query_vector)`).
    Retorna lista de dicionários com ID da entidade, tipo, texto fonte e score de similaridade (1 - distância).
    """
    set_hnsw_ef_search_sync(session, ef_search)

    # Distância cosseno via operador <=> do pgvector
    cosine_dist = DocumentEmbedding.embedding.cosine_distance(query_vector).label(
        "distance"
    )

    query = select(
        DocumentEmbedding.id,
        DocumentEmbedding.tipoEntidade,
        DocumentEmbedding.idEntidade,
        DocumentEmbedding.idDeputado,
        DocumentEmbedding.textoFonte,
        DocumentEmbedding.modelo,
        cosine_dist,
    )

    if tipo_entidade:
        query = query.where(DocumentEmbedding.tipoEntidade == tipo_entidade)
    if modelo:
        query = query.where(DocumentEmbedding.modelo == modelo)

    query = query.order_by(cosine_dist).limit(limit)

    results = session.execute(query).all()

    output = []
    for row in results:
        dist = float(row.distance) if row.distance is not None else 1.0
        similarity = max(0.0, 1.0 - dist)
        output.append(
            {
                "id": row.id,
                "tipoEntidade": row.tipoEntidade.value
                if hasattr(row.tipoEntidade, "value")
                else str(row.tipoEntidade),
                "idEntidade": row.idEntidade,
                "idDeputado": row.idDeputado,
                "textoFonte": row.textoFonte,
                "modelo": row.modelo,
                "distance": dist,
                "similarity": similarity,
            }
        )
    return output


def hybrid_search_proposicoes(
    session: Session,
    text_query: str,
    query_vector: List[float],
    limit: int = 10,
    alpha: float = 0.5,
    ef_search: int = 100,
) -> List[Dict[str, Any]]:
    """
    Busca Híbrida em Proposições combinando pontuação textual com similaridade vetorial pgvector.

    Score Híbrido = alpha * score_textual + (1 - alpha) * score_vetorial
    - score_vetorial = 1 - distância_cosseno
    - score_textual = relevância relativa no filtro ILIKE/full-text
    """
    set_hnsw_ef_search_sync(session, ef_search)

    cosine_dist = DocumentEmbedding.embedding.cosine_distance(query_vector).label(
        "distance"
    )

    # CTE para documentos vetoriais
    vector_stmt = (
        select(
            DocumentEmbedding.idEntidade.label("id_proposicao"),
            cosine_dist,
            DocumentEmbedding.textoFonte,
        )
        .where(DocumentEmbedding.tipoEntidade == "proposicao")
        .order_by(cosine_dist)
        .limit(limit * 3)
    ).cte("vector_matches")

    # Query principal combinando Proposicao e vector_matches
    query = select(
        Proposicao.id,
        Proposicao.idCamara,
        Proposicao.siglaTipo,
        Proposicao.numero,
        Proposicao.ano,
        Proposicao.ementa,
        vector_stmt.c.distance,
    ).join(vector_stmt, vector_stmt.c.id_proposicao == Proposicao.id)

    if text_query:
        search_pattern = f"%{text_query}%"
        query = query.where(
            (Proposicao.ementa.ilike(search_pattern))
            | (Proposicao.keywords.ilike(search_pattern))
        )

    results = session.execute(query.limit(limit)).all()

    output = []
    for row in results:
        dist = float(row.distance) if row.distance is not None else 1.0
        vec_score = max(0.0, 1.0 - dist)
        text_score = 1.0 if text_query else 0.5
        hybrid_score = (alpha * text_score) + ((1.0 - alpha) * vec_score)

        output.append(
            {
                "id": row.id,
                "idCamara": row.idCamara,
                "siglaTipo": row.siglaTipo,
                "numero": row.numero,
                "ano": row.ano,
                "ementa": row.ementa,
                "distance": dist,
                "vectorScore": vec_score,
                "hybridScore": hybrid_score,
            }
        )

    output.sort(key=lambda x: x["hybridScore"], reverse=True)
    return output[:limit]


def find_similar_politicos(
    session: Session,
    id_deputado: int,
    limit: int = 5,
    ef_search: int = 100,
) -> List[Dict[str, Any]]:
    """
    Localiza parlamentares semanticamente semelhantes utilizando o `vetorComposto` de `DeputadoPerfilVetorial`.
    """
    set_hnsw_ef_search_sync(session, ef_search)

    target_perfil = (
        session.query(DeputadoPerfilVetorial)
        .filter(DeputadoPerfilVetorial.idDeputado == id_deputado)
        .first()
    )

    if not target_perfil or target_perfil.vetorComposto is None:
        return []

    target_vec = target_perfil.vetorComposto
    cosine_dist = DeputadoPerfilVetorial.vetorComposto.cosine_distance(
        target_vec
    ).label("distance")

    query = (
        select(
            DeputadoPerfilVetorial.idDeputado,
            Deputado.nome,
            Deputado.siglaPartido,
            Deputado.siglaUF,
            Deputado.urlFoto,
            cosine_dist,
        )
        .join(Deputado, Deputado.id == DeputadoPerfilVetorial.idDeputado)
        .where(DeputadoPerfilVetorial.idDeputado != id_deputado)
        .order_by(cosine_dist)
        .limit(limit)
    )

    results = session.execute(query).all()

    output = []
    for row in results:
        dist = float(row.distance) if row.distance is not None else 1.0
        similarity = max(0.0, 1.0 - dist)
        output.append(
            {
                "idDeputado": row.idDeputado,
                "nome": row.nome,
                "siglaPartido": row.siglaPartido,
                "siglaUF": row.siglaUF,
                "urlFoto": row.urlFoto,
                "distance": dist,
                "similarity": similarity,
            }
        )
    return output
