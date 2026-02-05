import requests
import time
import logging
import argparse
from datetime import datetime

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    Partido,
    PartidoMembro,
    PartidoLider,
    Politico,
)

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------
# Utils
# -------------------------

def parse_date(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


def get(url, params=None):
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# -------------------------
# API calls
# -------------------------

def listar_partidos(pagina=1, itens=100):
    return get(
        f"{API_BASE}/partidos",
        params={
            "pagina": pagina,
            "itens": itens,
            "ordem": "ASC",
            "ordenarPor": "sigla",
        },
    )


def detalhe_partido(id_partido):
    return get(f"{API_BASE}/partidos/{id_partido}")


def membros_partido(id_partido, pagina=1, itens=100):
    return get(
        f"{API_BASE}/partidos/{id_partido}/membros",
        params={"pagina": pagina, "itens": itens},
    )


def lideres_partido(id_partido, pagina=1, itens=100):
    return get(
        f"{API_BASE}/partidos/{id_partido}/lideres",
        params={"pagina": pagina, "itens": itens},
    )


# -------------------------
# Upserts
# -------------------------

def upsert_partido(dados: dict, db: Session) -> Partido:
    partido = (
        db.query(Partido)
        .filter(Partido.id_camara == dados["id"])
        .first()
    )

    status = dados.get("status", {})

    if not partido:
        partido = Partido(id_camara=dados["id"])
        db.add(partido)

    partido.nome = dados.get("nome")
    partido.sigla = dados.get("sigla")
    partido.numero_eleitoral = dados.get("numeroEleitoral")
    partido.uri = dados.get("uri")

    partido.situacao = status.get("situacao")
    partido.total_membros = status.get("totalMembros")
    partido.total_posse = status.get("totalPosse")

    partido.url_facebook = dados.get("urlFacebook")
    partido.url_logo = dados.get("urlLogo")
    partido.url_website = dados.get("urlWebSite")

    return partido


def upsert_partido_membro(partido: Partido, d: dict, db: Session):
    politico = (
        db.query(Politico)
        .filter(Politico.id_camara == d["id"])
        .first()
    )

    # ❗ sem político, sem vínculo
    if not politico:
        return

    existe = (
        db.query(PartidoMembro)
        .filter(
            PartidoMembro.partido_id == partido.id,
            PartidoMembro.politico_id == politico.id,
        )
        .first()
    )

    if existe:
        return

    membro = PartidoMembro(
        partido_id=partido.id,
        politico_id=politico.id,
    )

    db.add(membro)
    # flush aqui é opcional
    # db.flush()



def upsert_partido_lider(partido: Partido, d: dict, db: Session):
    politico = (
        db.query(Politico)
        .filter(Politico.id_camara == d["id"])
        .first()
    )

    existe = (
        db.query(PartidoLider)
        .filter(
            PartidoLider.partido_id == partido.id,
            PartidoLider.politico_id == (politico.id if politico else None),
            PartidoLider.cod_titulo == d.get("codTitulo"),
        )
        .first()
    )

    if existe:
        return

    lider = PartidoLider(
        partido_id=partido.id,
        politico_id=politico.id if politico else None,
        cod_titulo=d.get("codTitulo"),
        titulo=d.get("titulo"),
        data_inicio=parse_date(d.get("dataInicio")),
        data_fim=parse_date(d.get("dataFim")),
    )

    db.add(lider)


# -------------------------
# Ingestão principal
# -------------------------

def ingestao_partidos(limite: int | None = None):
    db = SessionLocal()

    try:
        pagina = 1
        total = 0

        while True:
            payload = listar_partidos(pagina=pagina)
            dados = payload.get("dados", [])

            if not dados:
                break

            for p in dados:
                logger.info("🏛️ Partido %s (%s)", p["sigla"], p["id"])

                detalhe = detalhe_partido(p["id"])["dados"]
                partido = upsert_partido(detalhe, db)
                db.flush()  # garante partido.id

                # membros
                mp = 1
                while True:
                    membros = membros_partido(p["id"], mp)["dados"]
                    if not membros:
                        break

                    for m in membros:
                        upsert_partido_membro(partido, m, db)

                    mp += 1

                # líderes
                lp = 1
                while True:
                    lideres = lideres_partido(p["id"], lp)["dados"]
                    if not lideres:
                        break

                    for l in lideres:
                        upsert_partido_lider(partido, l, db)

                    lp += 1

                db.commit()
                total += 1

                if limite and total >= limite:
                    logger.info("🛑 Limite atingido (%s)", limite)
                    return

                time.sleep(0.3)

            if not any(l["rel"] == "next" for l in payload.get("links", [])):
                break

            pagina += 1

        logger.info("✅ Ingestão de partidos finalizada")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# -------------------------
# CLI
# -------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão de partidos da Câmara")
    parser.add_argument(
        "--limite",
        type=int,
        help="Limite de partidos (debug)",
    )

    args = parser.parse_args()

    ingestao_partidos(limite=args.limite)
