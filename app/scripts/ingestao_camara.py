import requests
import time
import logging
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Politico

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def buscar_deputados_api(pagina: int = 1, itens: int = 100, tentativas=3):
    for tentativa in range(tentativas):
        try:
            response = requests.get(
                f"{API_BASE}/deputados",
                params={
                    "pagina": pagina,
                    "itens": itens,
                    "ordem": "ASC",
                    "ordenarPor": "nome",
                },
                headers=HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)


def carregar_ids_existentes(db: Session) -> dict[int, Politico]:
    politicos = db.query(Politico).all()
    return {p.id_camara: p for p in politicos}


def ingestao_politicos():
    db = SessionLocal()
    pagina = 1

    try:
        cache = carregar_ids_existentes(db)
        logger.info("Cache carregado com %s políticos", len(cache))

        while True:
            logger.info("Buscando página %s", pagina)
            payload = buscar_deputados_api(pagina=pagina)

            dados = payload.get("dados", [])
            if not dados:
                break

            for dep in dados:
                politico = cache.get(dep["id"])

                if politico:
                    politico.nome = dep["nome"]
                    politico.uf = dep["siglaUf"]
                    politico.url_foto = dep.get("urlFoto")
                else:
                    politico = Politico(
                        id_camara=dep["id"],
                        nome=dep["nome"],
                        uf=dep["siglaUf"],
                        url_foto=dep.get("urlFoto"),
                    )
                    db.add(politico)
                    cache[dep["id"]] = politico

            db.commit()

            links = payload.get("links", [])
            tem_proxima = any(link["rel"] == "next" for link in links)

            if not tem_proxima:
                break

            pagina += 1

        logger.info("✅ Ingestão de políticos finalizada")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingestao_politicos()
