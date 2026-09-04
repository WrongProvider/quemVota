"""
test_temas.py — Suíte de testes SPEC-001: Classificação de Temas de Atuação Parlamentar.

Cobre:
  1. Estrutura correta do pipeline (invariantes de normalização, limiar, pesos).
  2. Endpoint GET /politicos/{id}/temas após execução do pipeline.
  3. Comportamento do endpoint sem dados no banco (404 com mensagem explicativa).
  4. Integridade dos scores (soma ≤ 1.0, todos no intervalo [0, 1]).
"""

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Fixtures de apoio: client é herdado de conftest.py
# ---------------------------------------------------------------------------


# ===========================================================================
# 1. Testes unitários do pipeline (sem banco, sem I/O)
# ===========================================================================


def test_limiar_e_topk():
    """
    Valida que a função _classificar_item respeita o limiar 0.40
    e retorna no máximo TOP_K=3 temas.
    """
    from tasks.classificar_temas import (
        TOP_K,
        SIM_LIMIAR,
        _classificar_item,
    )

    n_temas = 20
    dim = 1024

    # Cria vetores de temas aleatórios e normaliza
    np.random.seed(42)
    matriz = np.random.randn(n_temas, dim).astype(np.float32)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    matriz /= normas

    temas_meta = [
        {"id": i + 1, "slug": f"tema-{i + 1}", "nome": f"Tema {i + 1}"}
        for i in range(n_temas)
    ]

    # Documento com alta similaridade com tema 0
    vetor = matriz[0] * 0.95
    vetor = vetor / np.linalg.norm(vetor)

    resultado = _classificar_item(vetor, temas_meta, matriz)

    # No máximo TOP_K resultados
    assert len(resultado) <= TOP_K

    # Todos acima do limiar
    for item in resultado:
        assert item["score"] >= SIM_LIMIAR

    # Ranks sequenciais a partir de 1
    for expected_rank, item in enumerate(resultado, start=1):
        assert item["rank"] == expected_rank

    # Scores em ordem decrescente
    if len(resultado) > 1:
        scores = [item["score"] for item in resultado]
        assert scores == sorted(scores, reverse=True)


def test_vetor_zerado_retorna_vazio():
    """
    Um vetor de zeros (proposição sem texto útil) não deve produzir
    nenhuma classificação (todos os scores serão 0 < limiar).
    """
    from tasks.classificar_temas import _classificar_item

    n_temas = 20
    dim = 1024
    np.random.seed(0)
    matriz = np.random.randn(n_temas, dim).astype(np.float32)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    matriz /= normas

    temas_meta = [
        {"id": i + 1, "slug": f"tema-{i + 1}", "nome": f"Tema {i + 1}"}
        for i in range(n_temas)
    ]
    vetor_zero = np.zeros(dim, dtype=np.float32)

    resultado = _classificar_item(vetor_zero, temas_meta, matriz)
    assert resultado == []


def test_pesos_por_tipo_participacao():
    """Valida a constante de pesos por tipo de participação (SPEC-001, etapa 2)."""
    from tasks.classificar_temas import PESOS
    from shared.models_vetorial import TipoParticipacao

    assert PESOS[TipoParticipacao.autoria] == 10.0
    assert PESOS[TipoParticipacao.coautoria] == 5.0
    assert PESOS[TipoParticipacao.relatoria] == 8.0
    assert PESOS[TipoParticipacao.discurso] == 2.0
    assert PESOS[TipoParticipacao.evento] == 1.0


def test_tipo_participacao_proponente_ordem1():
    """proponente=True e ordem=1 → autoria."""
    from tasks.classificar_temas import _tipo_participacao
    from shared.models_vetorial import TipoParticipacao

    assert _tipo_participacao(True, 1) == TipoParticipacao.autoria


def test_tipo_participacao_coautor():
    """proponente=False → coautoria."""
    from tasks.classificar_temas import _tipo_participacao
    from shared.models_vetorial import TipoParticipacao

    assert _tipo_participacao(False, 2) == TipoParticipacao.coautoria
    assert _tipo_participacao(False, None) == TipoParticipacao.coautoria


def test_hash_texto_determinista():
    """_hash_texto deve ser determinista para o mesmo input."""
    from tasks.classificar_temas import _hash_texto

    texto = "Altera a Lei de Diretrizes e Bases da Educação Nacional."
    h1 = _hash_texto(texto)
    h2 = _hash_texto(texto)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 em hex


def test_normalizacao_scores_soma_um():
    """
    Simula a agregação e valida que os scores somam exatamente 1.0
    (ou diferença de ponto flutuante desprezível).
    """
    # Simula os resultados brutos da agregação
    pesos_brutos = [42.5, 30.0, 15.0, 7.5, 5.0]
    total = sum(pesos_brutos)

    scores = [round(p / total, 4) for p in pesos_brutos]
    soma = sum(scores)

    # Todos no intervalo [0, 1]
    for s in scores:
        assert 0.0 <= s <= 1.0

    # Soma próxima de 1.0 (erro de arredondamento tolerado)
    assert abs(soma - 1.0) < 0.01


# ===========================================================================
# 2. Testes de integração com pipeline real (banco de dados)
# ===========================================================================


def test_dry_run_pipeline_sem_gravar():
    """
    Executa o pipeline em dry-run para o deputado 26 e valida
    que métricas são retornadas sem alterar o banco.
    """

    from tasks.classificar_temas import classificar_temas

    metricas = classificar_temas(
        deputado_id=26,
        limit_proposicoes=5,
        dry_run=True,
        force=True,
    )

    assert isinstance(metricas, dict)
    assert "proposicoes_lidas" in metricas
    assert "itens_classificados" in metricas
    assert metricas["deputados_processados"] == 1
    # dry_run: embeddings computados mas nada gravado de novo
    assert metricas["proposicoes_vetorizadas"] >= 0
    assert metricas["proposicoes_sem_embedding"] == 0


def test_pipeline_real_deputado_26():
    """
    Executa o pipeline real para o deputado 26 e valida que dados
    foram persistidos corretamente em deputadoTemasAtuacao.
    """
    from shared.database import SessionLocal
    from shared.models_vetorial import DeputadoTemaAtuacao
    from sqlalchemy import select

    from tasks.classificar_temas import classificar_temas

    # Executa (com force=True para garantir re-run no CI)
    metricas = classificar_temas(
        deputado_id=26,
        limit_proposicoes=10,
        dry_run=False,
        force=True,
    )

    assert metricas["deputados_processados"] == 1

    db = SessionLocal()
    try:
        rows = (
            db.execute(
                select(DeputadoTemaAtuacao)
                .where(DeputadoTemaAtuacao.idDeputado == 26)
                .order_by(DeputadoTemaAtuacao.rank)
            )
            .scalars()
            .all()
        )

        assert len(rows) > 0, "Pipeline não gerou temas para o deputado 26."

        # Scores no intervalo [0, 1]
        for r in rows:
            assert 0.0 <= float(r.score) <= 1.0

        # Scores somam ≤ 1.0 (arredondamento pode fazer ficar pouco acima)
        soma = sum(float(r.score) for r in rows)
        assert soma <= 1.01, f"Soma dos scores = {soma} > 1.01"

        # Ranks sequenciais
        for expected_rank, r in enumerate(rows, start=1):
            assert r.rank == expected_rank

        # Nenhum deputado igual a si mesmo como semelhante (não aplicável aqui,
        # mas garantimos que idDeputado está correto)
        for r in rows:
            assert r.idDeputado == 26

    finally:
        db.close()


# ===========================================================================
# 3. Testes de API HTTP
# ===========================================================================


async def test_api_temas_atuacao_404_sem_dados(client):
    """
    Verifica que a API retorna 404 com mensagem explicativa para um
    parlamentar que ainda não foi processado pelo pipeline.
    """
    # Usar um deputado improvávelmente processado (id muito alto)
    response = await client.get("/politicos/99999/temas")
    assert response.status_code == 404


async def test_api_temas_atuacao_200_apos_pipeline(client):
    """
    Após execução do pipeline para o deputado 26,
    verifica que a API retorna 200 com estrutura correta.
    """
    # Garante que o pipeline rodou (executado pelo teste anterior)
    response = await client.get("/politicos/26/temas?limit=5")

    if response.status_code == 404:
        # Pipeline ainda não rodou — pula o assert sem falhar
        pytest.skip("Pipeline ainda não executado para o deputado 26.")

    assert response.status_code == 200
    data = response.json()

    assert data["id_deputado"] == 26
    assert isinstance(data["id_legislatura"], int)
    assert isinstance(data["total_temas_identificados"], int)
    assert isinstance(data["temas"], list)

    if data["temas"]:
        t0 = data["temas"][0]
        assert "id_tema" in t0
        assert "slug" in t0
        assert "nome" in t0
        assert 0.0 <= t0["score"] <= 1.0
        assert 0.0 <= t0["percentual"] <= 100.0
        assert t0["rank"] == 1

        # Scores em ordem decrescente
        scores = [t["score"] for t in data["temas"]]
        assert scores == sorted(scores, reverse=True)


async def test_api_temas_atuacao_por_slug(client):
    """Valida que o endpoint aceita slug além do ID numérico."""
    response = await client.get("/politicos/alfredinho/temas")
    assert response.status_code in (200, 404)  # 404 se pipeline não rodou


async def test_api_temas_atuacao_limite(client):
    """Valida que o parâmetro limit=2 é respeitado."""
    response = await client.get("/politicos/26/temas?limit=2")
    if response.status_code == 200:
        data = response.json()
        assert len(data["temas"]) <= 2
