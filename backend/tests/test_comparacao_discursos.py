import pytest
from httpx import ASGITransport, AsyncClient

try:
    from backend.main import app
except ImportError:
    from main import app


@pytest.mark.asyncio
async def test_comparar_discursos_mesmo_politico_retorna_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/politicos/comparar/tabata-amaral/tabata-amaral/discursos"
        )
        assert res.status_code == 400
        assert "Não é possível comparar" in res.json()["detail"]


@pytest.mark.asyncio
async def test_comparar_discursos_politico_inexistente_retorna_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/politicos/comparar/slug-inexistente-123/tabata-amaral/discursos"
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_comparar_discursos_sucesso():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/politicos/comparar/tabata-amaral/nikolas-ferreira/discursos"
        )
        assert res.status_code == 200
        data = res.json()
        assert "politico1" in data
        assert "politico2" in data
        assert data["politico1"]["slug"] == "tabata-amaral"
        assert data["politico2"]["slug"] == "nikolas-ferreira"
        assert "total_pares" in data
        assert "total_convergentes" in data
        assert "total_divergentes" in data
        assert "discursos_convergentes" in data
        assert "discursos_divergentes" in data
        assert isinstance(data["discursos_convergentes"], list)
        assert isinstance(data["discursos_divergentes"], list)
        assert (
            data["total_pares"]
            == data["total_convergentes"] + data["total_divergentes"]
        )
