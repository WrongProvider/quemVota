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


def test_cypher_sample_alinhamento_votos_sync():
    """Valida a consulta openCypher de alinhamento de votos no Apache AGE."""
    from shared.database import SessionLocal
    from shared.graph import cypher_sample_alinhamento_votos

    session = SessionLocal()
    try:
        results = cypher_sample_alinhamento_votos(session, 26, 73)
        assert isinstance(results, list)
        if results:
            item = results[0]
            assert "id_votacao" in item
            assert "descricao" in item
            assert "voto_politico1" in item
            assert "voto_politico2" in item
            assert "alinhados" in item
            assert isinstance(item["alinhados"], bool)
    finally:
        session.close()


async def test_cypher_sample_alinhamento_votos_async():
    """Valida a versão assíncrona de alinhamento de votos via AsyncSession."""
    from shared.database import AsyncSessionLocal
    from shared.graph import cypher_sample_alinhamento_votos_async

    async with AsyncSessionLocal() as session:
        results = await cypher_sample_alinhamento_votos_async(session, 26, 73)
        assert isinstance(results, list)
        if results:
            item = results[0]
            assert "id_votacao" in item
            assert "voto_politico1" in item
            assert "voto_politico2" in item
            assert "alinhados" in item


async def test_api_comparador_politicos(client):
    """Valida o endpoint GET /politicos/comparar/{id1}/{id2} via API."""
    response = await client.get("/politicos/comparar/26/73")
    assert response.status_code == 200
    data = response.json()

    assert data["politico1"]["id"] == 26
    assert data["politico2"]["id"] == 73
    assert data["total_votacoes_comuns"] > 0
    assert (
        data["votos_alinhados"] + data["votos_divergentes"]
        == data["total_votacoes_comuns"]
    )
    assert 0.0 <= data["taxa_alinhamento"] <= 100.0
    assert data["fonte_dados"] in ("apache_age_graph", "relacional")
    assert isinstance(data["divergencias"], list)
    assert isinstance(data["alinhamentos"], list)


async def test_api_comparador_politicos_slugs(client):
    """Valida o endpoint GET /politicos/comparar/{slug1}/{slug2} com slugs."""
    response = await client.get("/politicos/comparar/alfredinho/bibo-nunes")
    assert response.status_code == 200
    data = response.json()
    assert data["politico1"]["slug"] == "alfredinho"
    assert data["politico2"]["slug"] == "bibo-nunes"
    assert data["total_votacoes_comuns"] > 0


async def test_api_comparador_politicos_mesmo_politico(client):
    """Garante que comparar o mesmo parlamentar resulta em status 400."""
    response = await client.get("/politicos/comparar/26/26")
    assert response.status_code == 400
    assert "Não é possível comparar" in response.json()["detail"]


async def test_api_comparador_politicos_temas_disponiveis(client):
    """Valida se o endpoint retorna a lista estruturada de temas disponíveis para filtro."""
    response = await client.get("/politicos/comparar/26/73")
    assert response.status_code == 200
    data = response.json()
    assert "temas_disponiveis" in data
    assert isinstance(data["temas_disponiveis"], list)
    if data["temas_disponiveis"]:
        t0 = data["temas_disponiveis"][0]
        assert "tema" in t0
        assert "total_votacoes" in t0
        assert "votos_alinhados" in t0
        assert "votos_divergentes" in t0
        assert "taxa_alinhamento" in t0
        assert t0["total_votacoes"] == t0["votos_alinhados"] + t0["votos_divergentes"]


async def test_api_comparador_politicos_filtro_tema(client):
    """Valida a filtragem de votações por tema legislativo no comparador."""
    # 1. Pega os temas disponíveis
    resp_base = await client.get("/politicos/comparar/26/73")
    assert resp_base.status_code == 200
    data_base = resp_base.json()

    if data_base.get("temas_disponiveis"):
        tema_alvo = data_base["temas_disponiveis"][0]["tema"]
        response = await client.get(f"/politicos/comparar/26/73?tema={tema_alvo}")
        assert response.status_code == 200
        data_filtrada = response.json()
        assert data_filtrada["tema_filtrado"] == tema_alvo
        assert data_filtrada["total_votacoes_comuns"] > 0
        assert (
            data_filtrada["votos_alinhados"] + data_filtrada["votos_divergentes"]
            == data_filtrada["total_votacoes_comuns"]
        )


async def test_api_rede_coautoria(client):
    """Valida o endpoint GET /politicos/{id}/grafo/coautoria."""
    response = await client.get("/politicos/26/grafo/coautoria")
    assert response.status_code == 200
    data = response.json()
    assert "politico_base" in data
    assert data["politico_base"]["id"] == 26
    assert "total_parceiros_distintos" in data
    assert "taxa_coautoria_multipartidaria" in data
    assert isinstance(data["top_parceiros"], list)
    if data["top_parceiros"]:
        p0 = data["top_parceiros"][0]
        assert "politico" in p0
        assert "total_proposicoes_juntos" in p0
        assert "mesmo_partido" in p0
        if p0["politico"].get("url_foto"):
            assert p0["politico"]["url_foto"].startswith("http")


async def test_api_afinidades_voto(client):
    """Valida o endpoint GET /politicos/{id}/grafo/afinidades."""
    response = await client.get("/politicos/26/grafo/afinidades?min_votacoes_comuns=3")
    assert response.status_code == 200
    data = response.json()
    assert "politico_base" in data
    assert "mais_alinhados" in data
    assert "mais_divergentes" in data
    assert "alinhamento_por_bancada" in data
    assert isinstance(data["mais_alinhados"], list)
    assert isinstance(data["mais_divergentes"], list)
    if data["mais_alinhados"]:
        al0 = data["mais_alinhados"][0]
        if al0["politico"].get("url_foto"):
            assert al0["politico"]["url_foto"].startswith("http")


async def test_api_fidelidade_partidaria(client):
    """Valida o endpoint GET /politicos/{id}/grafo/fidelidade-partidaria."""
    response = await client.get("/politicos/26/grafo/fidelidade-partidaria")
    assert response.status_code == 200
    data = response.json()
    assert "politico" in data
    assert "sigla_partido" in data
    assert "total_votacoes_orientadas" in data
    assert "taxa_fidelidade" in data
    assert 0.0 <= data["taxa_fidelidade"] <= 100.0


async def test_api_grafo_proposicao(client):
    """Valida o endpoint GET /proposicoes/{id}/grafo."""
    res_list = await client.get("/proposicoes/?limit=1")
    props = res_list.json()
    prop_id = props[0]["id"] if props else 1

    response = await client.get(f"/proposicoes/{prop_id}/grafo")
    assert response.status_code == 200
    data = response.json()
    assert "id_proposicao" in data
    assert "proposicao" in data
    assert "temas" in data
    assert "votacoes" in data
    assert "fonte_dados" in data
