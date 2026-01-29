import requests
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Politico

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

def buscar_deputados_api(pagina: int = 1, itens: int = 100):
    response = requests.get(
        f"{API_BASE}/deputados",
        params={
            "pagina": pagina,
            "itens": itens,
            "ordem": "ASC",
            "ordenarPor": "nome"
        },
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()
    return response.json()

def upsert_politico(dep: dict, db: Session):
    politico = (
        db.query(Politico)
        .filter(Politico.id_camara == dep["id"])
        .first()
    )

    if politico:
        politico.nome = dep["nome"]
        politico.uf = dep["siglaUf"]
        politico.url_foto = dep.get("urlFoto")
        return politico

    politico = Politico(
        id_camara=dep["id"],
        nome=dep["nome"],
        uf=dep["siglaUf"],
        url_foto=dep.get("urlFoto"),
    )

    db.add(politico)
    return politico

def ingestao_politicos():
    db = SessionLocal()
    pagina = 1

    try:
        while True:
            print(f"📥 Buscando página {pagina}...")
            payload = buscar_deputados_api(pagina=pagina)

            dados = payload.get("dados", [])
            if not dados:
                break

            for dep in dados:
                upsert_politico(dep, db)

            db.commit()

            links = payload.get("links", [])
            tem_proxima = any(link["rel"] == "next" for link in links)

            if not tem_proxima:
                break

            pagina += 1

        print("✅ Ingestão de políticos finalizada")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    ingestao_politicos()
