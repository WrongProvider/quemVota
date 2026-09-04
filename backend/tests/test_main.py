async def test_read_main(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api": "Quem Vota", "docs": "/docs"}


async def test_cors_unauthorized_origin(client):
    # Simulate a request from a random site
    response = await client.get("/", headers={"Origin": "https://evil-hacker-site.com"})
    # If CORS is working, the Access-Control-Allow-Origin header should be missing
    # or not match the evil site.
    assert "access-control-allow-origin" not in response.headers


async def test_politicos_schema(client):
    response = await client.get("/politicos/")
    # print(f"STATUS: {response.status_code}")
    # print(f"BODY: {response.text}")
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        politico = data[0]
        expected_keys = {"id", "nome", "sigla_uf", "slug"}
        assert expected_keys.issubset(politico.keys())


async def test_politico_schema(client):
    response = await client.get("/politicos/1")
    data = response.json()
    # assert isinstance(data, list)
    expected_keys = {"id", "nome", "sigla_uf", "slug"}
    assert expected_keys.issubset(data.keys())


async def test_politico_slug(client):
    res_list = await client.get("/politicos/?limit=1")
    list_data = res_list.json()
    slug = list_data[0]["slug"] if list_data else "alfredinho"
    response = await client.get(f"/politicos/{slug}")
    data = response.json()
    expected_keys = {"id", "nome", "sigla_uf", "slug"}
    assert expected_keys.issubset(data.keys())


async def test_politico_votacoes(client):
    response = await client.get("/politicos/1/votacoes")
    data = response.json()
    expected_keys = {
        "id_votacao",
        "data",
        "proposicao_sigla",
        "ementa",
        "voto",
        "resultado_da_votacao",
    }
    assert expected_keys.issubset(data[0].keys())


async def test_politico_atividade_legislativa(client):
    # Testa deputado 213 (Erika Hilton), garantindo que votos nulos ou matérias sem voto não quebrem
    response = await client.get(
        "/politicos/213/atividade-legislativa?limit_votacoes=15&limit_proposicoes=20&offset_votacoes=0"
    )
    assert response.status_code == 200
    data = response.json()
    assert "votacoes" in data
    assert "proposicoes" in data
    assert "total_votacoes" in data
    assert "total_proposicoes" in data
    assert isinstance(data["votacoes"], list)


async def test_proposicoes_schema_com_ultimo_status(client):
    response = await client.get("/proposicoes/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        p = data[0]
        expected_keys = {
            "id",
            "id_camara",
            "sigla_tipo",
            "numero",
            "ano",
            "ementa",
            "data_apresentacao",
            "ultimo_status_data",
            "ultimo_status_situacao",
            "ultimo_status_orgao",
        }
        assert expected_keys.issubset(p.keys())


async def test_proposicoes_filtro_ano_votacao(client):
    response = await client.get("/proposicoes/?ano_votacao=2026&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


