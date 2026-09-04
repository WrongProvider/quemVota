"""
test_vector_and_graph.py — Suíte de Testes para pgvector (HNSW) e Apache AGE Graph-RAG
"""

from shared.models_vetorial import (
    DeputadoPerfilVetorial,
    DocumentEmbedding,
    TemaAtuacao,
)
from shared.vector_search import (
    find_similar_politicos,
    hybrid_search_proposicoes,
    vector_knn_search,
)
from shared.graph import (
    GRAPH_NAME,
    LABEL_POLITICO,
    LABEL_PROPOSICAO,
    LABEL_TEMA,
    LABEL_VOTACAO,
    EDGE_BELONGS_TO_THEME,
    EDGE_PROPOSED,
    EDGE_VOTED_IN,
    graph_rag_retrieval,
    init_age_extension,
)


def test_hnsw_indexes_metadata():
    """Valida se os índices HNSW e suas configurações (m=24, ef_construction=128) estão declarados nos modelos SQLAlchemy."""
    # DocumentEmbedding
    doc_table = DocumentEmbedding.__table__
    index_names = [idx.name for idx in doc_table.indexes]
    assert "ix_document_embeddings_embedding_hnsw" in index_names

    hnsw_idx = next(
        idx
        for idx in doc_table.indexes
        if idx.name == "ix_document_embeddings_embedding_hnsw"
    )
    assert hnsw_idx.dialect_kwargs.get("postgresql_using") == "hnsw"
    assert hnsw_idx.dialect_kwargs.get("postgresql_with") == {
        "m": 24,
        "ef_construction": 128,
    }

    # DeputadoPerfilVetorial
    perfil_table = DeputadoPerfilVetorial.__table__
    perfil_indexes = [idx.name for idx in perfil_table.indexes]
    assert "ix_deputado_perfil_vetor_composto_hnsw" in perfil_indexes

    composto_idx = next(
        idx
        for idx in perfil_table.indexes
        if idx.name == "ix_deputado_perfil_vetor_composto_hnsw"
    )
    assert composto_idx.dialect_kwargs.get("postgresql_with") == {
        "m": 24,
        "ef_construction": 128,
    }


def test_vector_search_functions_exist():
    """Verifica a integridade da API do módulo vector_search."""
    assert callable(vector_knn_search)
    assert callable(hybrid_search_proposicoes)
    assert callable(find_similar_politicos)


def test_graph_schema_constants():
    """Valida as constantes de rótulos e arestas do grafo Apache AGE."""
    assert GRAPH_NAME == "quemvota_graph"
    assert LABEL_POLITICO == "Politico"
    assert LABEL_VOTACAO == "Votacao"
    assert LABEL_PROPOSICAO == "Proposicao"
    assert LABEL_TEMA == "Tema"
    assert EDGE_VOTED_IN == "VOTED_IN"
    assert EDGE_PROPOSED == "PROPOSED"
    assert EDGE_BELONGS_TO_THEME == "BELONGS_TO_THEME"
    assert callable(graph_rag_retrieval)
    assert callable(init_age_extension)


def test_temas_atuacao_seeded():
    """Valida se os 20 temas canônicos de atuação foram persistidos com embeddings."""
    from shared.database import SessionLocal

    session = SessionLocal()
    try:
        count = session.query(TemaAtuacao).count()
        assert count == 20
        primeiro = (
            session.query(TemaAtuacao).filter(TemaAtuacao.slug == "economia").first()
        )
        assert primeiro is not None
        assert primeiro.embedding is not None
        assert len(primeiro.embedding) == 1024
    finally:
        session.close()


def test_knn_vector_search_execution():
    """Valida se a busca por k-vizinhos mais próximos (KNN) no pgvector executa sem erros."""
    from shared.database import SessionLocal

    session = SessionLocal()
    try:
        # Usa o embedding do primeiro tema como vetor de consulta
        tema = session.query(TemaAtuacao).first()
        assert tema is not None
        vector = list(tema.embedding)
        results = vector_knn_search(session, query_vector=vector, limit=3)
        assert isinstance(results, list)
        if results:
            assert "similarity" in results[0]
            assert "distance" in results[0]
            assert results[0]["similarity"] >= 0.0
    finally:
        session.close()


def test_apache_age_cypher_queries():
    """Valida execução de queries openCypher no Apache AGE."""
    from shared.database import SessionLocal
    from shared.graph import execute_cypher, get_graph_stats

    session = SessionLocal()
    try:
        stats = get_graph_stats(session)
        assert isinstance(stats, dict)
        assert "nodes" in stats
        assert "edges" in stats
        assert stats["total_nodes"] > 0

        # Executa uma query Cypher direta
        res = execute_cypher(session, "MATCH (n) RETURN count(n)", "cnt agtype")
        assert len(res) > 0
    finally:
        session.close()
