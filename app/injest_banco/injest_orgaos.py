import logging

from injest_banco.db.database import SessionLocal
from api_camara import (
    buscar_orgaos,
    buscar_orgao_detalhe,
    buscar_orgao_membros,
    buscar_orgao_eventos,
)
from db_upsert import (
    carregar_orgaos_por_id_camara,
    upsert_orgao,
    enrich_orgao,
    upsert_orgao_membro,
    upsert_evento_minimo,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingestao_orgaos():
    db = SessionLocal()

    try:
        cache = carregar_orgaos_por_id_camara(db)
        payload = buscar_orgaos()

        for d in payload.get("dados", []):
            logger.info("🏛️ Órgão %s (%s)", d.get("sigla"), d["id"])

            orgao = upsert_orgao(db, cache, d)
            db.flush()

            detalhe = buscar_orgao_detalhe(orgao.id_camara)["dados"]
            enrich_orgao(orgao, detalhe)

            # membros
            membros = buscar_orgao_membros(orgao.id_camara).get("dados", [])
            for m in membros:
                upsert_orgao_membro(db, orgao, m)

            # eventos (N:N)
            eventos = buscar_orgao_eventos(orgao.id_camara).get("dados", [])
            for e in eventos:
                evento = upsert_evento_minimo(db, e)

                if orgao not in evento.orgaos:
                    evento.orgaos.append(orgao)

            db.commit()

        logger.info("✅ Ingestão de órgãos finalizada")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingestao_orgaos()
