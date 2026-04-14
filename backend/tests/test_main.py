def test_read_main(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"status":"ok","api":"Quem Vota","docs":"/docs"}

def test_cors_unauthorized_origin(client):
    # Simulate a request from a random site
    response = client.get("/", headers={"Origin": "https://evil-hacker-site.com"})
    # If CORS is working, the Access-Control-Allow-Origin header should be missing 
    # or not match the evil site.
    assert "access-control-allow-origin" not in response.headers

def test_politicos_schema(client):
    response = client.get('/politicos')
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        politico = data[0]
        expected_keys = {"id", "nome", "sigla_uf", "slug"}
        assert expected_keys.issubset(politico.keys())

def test_politico_schema(client):
    response = client.get('/politicos/1')
    data = response.json()
    # assert isinstance(data, list)
    expected_keys = {"id", "nome", "sigla_uf", "slug"}
    assert expected_keys.issubset(data.keys())       
