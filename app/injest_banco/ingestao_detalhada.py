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

def buscar_detalhe_deputado(id_camara: int, tentativas=3):
    for tentativa in range(tentativas):
        try:
            response = requests.get(
                f"{API_BASE}/deputados/{id_camara}",
                headers=HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            return response.json()["dados"]
        except requests.RequestException:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)

def enriquecer_politico(politico: Politico, dados: dict):
    ultimo_status = dados.get("ultimoStatus", {})

    politico.nome_civil = dados.get("nomeCivil")
    politico.sexo = dados.get("sexo")
    politico.data_nascimento = dados.get("dataNascimento")
    politico.escolaridade = dados.get("escolaridade")
    politico.uf_nascimento = dados.get("ufNascimento")
    politico.municipio_nascimento = dados.get("municipioNascimento")

    politico.partido = ultimo_status.get("siglaPartido")
    politico.situacao = ultimo_status.get("situacao")
    politico.condicao_eleitoral = ultimo_status.get("condicaoEleitoral")
    politico.email = ultimo_status.get("email")

    gabinete = ultimo_status.get("gabinete") or {}
    politico.telefone_gabinete = gabinete.get("telefone")
    politico.email_gabinete = gabinete.get("email")


def ingestao_detalhada_politicos(limite: int = 50):
    db = SessionLocal()

    try:
        politicos = (
            db.query(Politico)
            .filter(Politico.nome_civil.is_(None))
            .limit(limite)
            .all()
        )

        logger.info("Enriquecendo %s políticos", len(politicos))

        for politico in politicos:
            logger.info("Buscando detalhe do deputado %s", politico.id_camara)
            dados = buscar_detalhe_deputado(politico.id_camara)
            enriquecer_politico(politico, dados)
            db.commit()
            time.sleep(0.3)  # respeita API

        logger.info("✅ Enriquecimento finalizado")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingestao_detalhada_politicos()