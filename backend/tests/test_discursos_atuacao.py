"""
test_discursos_atuacao.py — Testes unitários e de integração para SPEC-007.

Testa:
  - Sanitização e validação com Pydantic V2 (DiscursoCamaraSchema).
  - Serialização dos schemas de resposta da API.
  - Endpoint GET /politicos/{politico_id}/discursos-atuacao (200, 404, paginação, busca).
"""

from datetime import datetime
import pytest

from backend.schemas import (
    DiscursoAtuacaoItemResponse,
    PoliticoDiscursosAtuacaoResponse,
    ProposicaoCorrelataDiscurso,
    VotacaoCorrelataDiscurso,
)
from injest_banco.schemas_camara import DiscursoCamaraSchema


def test_discurso_camara_schema_sanitization():
    """Valida que DiscursoCamaraSchema sanitiza strings, null-bytes e extrai faseEvento."""
    raw = {
        "dataHoraInicio": "2026-07-07T20:44",
        "dataHoraFim": None,
        "faseEvento": {"titulo": "Ordem do Dia"},
        "tipoDiscurso": " COMO LÍDER\x00 ",
        "sumario": "  Defendeu o Projeto de Lei nº 896, de 2023.  ",
        "keywords": "Mulheres, Misoginia",
        "urlTexto": None,
    }
    schema = DiscursoCamaraSchema(idDeputadoCamara=204534, **raw)
    assert schema.idDeputadoCamara == 204534
    assert schema.tipoDiscurso == "COMO LÍDER"
    assert schema.faseEventoTitulo == "Ordem do Dia"
    assert "896" in (schema.sumario or "")
    assert "\x00" not in (schema.tipoDiscurso or "")


def test_discurso_schemas_serialization():
    """Valida a serialização dos modelos de resposta Pydantic V2."""
    prop = ProposicaoCorrelataDiscurso(
        id=672890,
        sigla_tipo="PLP",
        numero=41,
        ano=2026,
        ementa="Dispõe sobre violência contra a mulher",
        tipo_participacao="Coautoria",
        url_camara="https://camara.leg.br",
    )
    vot = VotacaoCorrelataDiscurso(
        id=138651,
        id_votacao_camara="2606313-100",
        data="2026-07-07",
        sigla_orgao="PLEN",
        descricao="Aprovado o Substitutivo",
        voto_registrado="Artigo 17",
        aprovacao=1,
    )
    item = DiscursoAtuacaoItemResponse(
        id=1,
        data_hora_inicio=datetime(2026, 7, 7, 20, 44),
        tipo_discurso="COMO LÍDER",
        sumario="Pronunciamento na tribuna",
        proposicoes_correlatas=[prop],
        votacoes_correlatas=[vot],
    )
    resp = PoliticoDiscursosAtuacaoResponse(
        id_deputado=592,
        nome_deputado="Tabata Amaral",
        total_discursos=1,
        itens=[item],
    )

    data = resp.model_dump()
    assert data["id_deputado"] == 592
    assert len(data["itens"]) == 1
    assert data["itens"][0]["proposicoes_correlatas"][0]["numero"] == 41
    assert data["itens"][0]["votacoes_correlatas"][0]["voto_registrado"] == "Artigo 17"


@pytest.mark.asyncio
async def test_discursos_atuacao_endpoint_parlamentar_existente(client):
    """
    Testa o endpoint para um parlamentar cadastrado no banco.
    Deve responder 200 com a estrutura correta.
    """
    # Consulta pelo slug canônico de Tabata Amaral ou ID 592
    response = await client.get("/politicos/592/discursos-atuacao?limit=5")
    if response.status_code == 404:
        # Se 592 não estiver com o ID interno 592 no fixture, busca lista de políticos
        list_resp = await client.get("/politicos?limit=1")
        if list_resp.status_code == 200 and list_resp.json():
            dep_id = list_resp.json()[0]["id"]
            response = await client.get(
                f"/politicos/{dep_id}/discursos-atuacao?limit=5"
            )

    assert response.status_code == 200
    body = response.json()
    assert "id_deputado" in body
    assert "total_discursos" in body
    assert "itens" in body
    assert isinstance(body["itens"], list)


@pytest.mark.asyncio
async def test_discursos_atuacao_endpoint_paginacao_e_busca(client):
    """Valida que parâmetros limit, offset e busca 'q' são aceitos sem erro."""
    response = await client.get(
        "/politicos/592/discursos-atuacao?limit=2&offset=0&q=educacao"
    )
    if response.status_code == 404:
        list_resp = await client.get("/politicos?limit=1")
        dep_id = list_resp.json()[0]["id"]
        response = await client.get(
            f"/politicos/{dep_id}/discursos-atuacao?limit=2&offset=0&q=educacao"
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["itens"]) <= 2


@pytest.mark.asyncio
async def test_discursos_atuacao_endpoint_parlamentar_inexistente(client):
    """Valida que parlamentar inexistente retorna 404 Not Found."""
    response = await client.get("/politicos/999999999/discursos-atuacao")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
