# backend/ingest/ingestao_camara.py
import logging

from backend.database import SessionLocal
from ingest_banco.api_camara import buscar_deputados
from ingest_banco.db_upsert import (
    carregar_por_id_camara,
    upsert_politico,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingestao_politicos():
    db = SessionLocal()
    pagina = 1

    try:
        cache = carregar_por_id_camara(db)
        logger.info("Cache carregado com %s políticos", len(cache))

        while True:
            logger.info("Buscando página %s", pagina)
            payload = buscar_deputados(pagina=pagina)
            

            dados = payload.get("dados", [])
            if not dados:
                break

            for dep in dados:
                upsert_politico(db, cache, dep)
                logger.info(
                "Página %s: %s deputados processados",
                pagina,
                len(dados)
            )

            db.commit()

            if not any(link["rel"] == "next" for link in payload.get("links", [])):
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
