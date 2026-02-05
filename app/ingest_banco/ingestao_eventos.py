import requests
import time
import logging
import argparse
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from backend.database import SessionLocal
from backend.models import Politico, Evento, Orgao

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def buscar_eventos_deputado(
    id_camara: int,
    data_inicio: str,
    data_fim: str,
    pagina: int = 1,
    itens: int = 100,
):
    response = requests.get(
        f"{API_BASE}/deputados/{id_camara}/eventos",
        headers=HEADERS,
        params={
            "dataInicio": data_inicio,
            "dataFim": data_fim,
            "pagina": pagina,
            "itens": itens,
            "ordem": "ASC",
            "ordenarPor": "dataHoraInicio",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

def get_or_create_orgao(db: Session, dados: dict) -> Orgao:
    orgao = (
        db.query(Orgao)
        .filter(Orgao.id_camara == dados["id"])
        .first()
    )

    if orgao:
        return orgao

    orgao = Orgao(
        id_camara=dados["id"],
        sigla=dados.get("sigla"),
        nome=dados.get("nome"),
        tipo_orgao=dados.get("tipoOrgao"),
    )

    db.add(orgao)
    db.flush()  # garante ID sem commit
    return orgao

def criar_evento(
    db: Session,
    politico: Politico,
    dados: dict,
):
    evento = (
        db.query(Evento)
        .filter(Evento.id_camara == dados["id"])
        .first()
    )

    if evento:
        return evento  # evita duplicação

    evento = Evento(
        id_camara=dados["id"],
        politico_id=politico.id,
        data_hora_inicio=datetime.fromisoformat(dados["dataHoraInicio"]),
        data_hora_fim=(
            datetime.fromisoformat(dados["dataHoraFim"])
            if dados.get("dataHoraFim")
            else None
        ),
        situacao=dados.get("situacao"),
        descricao_tipo=dados.get("descricaoTipo"),
        descricao=dados.get("descricao"),
        url_registro=dados.get("urlRegistro"),
    )

    # N:N com órgãos
    for orgao_dados in dados.get("orgaos", []):
        orgao = get_or_create_orgao(db, orgao_dados)
        evento.orgaos.append(orgao)

    db.add(evento)
    return evento

def ingestao_eventos_politicos(
    data_inicio="2021-01-01",
    data_fim="2023-12-31",
    limite_politicos=50,
):
    db = SessionLocal()

    try:
        politicos = (
            db.query(Politico)
            .filter(Politico.id_camara.isnot(None))
            .limit(limite_politicos)
            .all()
        )

        for politico in politicos:
            logger.info(
                "📅 Ingerindo eventos do deputado %s (%s)",
                politico.nome,
                politico.id_camara,
            )

            pagina = 1

            while True:
                payload = buscar_eventos_deputado(
                    politico.id_camara,
                    data_inicio,
                    data_fim,
                    pagina=pagina,
                )

                eventos = payload.get("dados", [])
                if not eventos:
                    break

                for evento_dados in eventos:
                    criar_evento(db, politico, evento_dados)

                db.commit()

                if len(eventos) < 100:
                    break

                pagina += 1
                time.sleep(0.3)

        logger.info("✅ Ingestão de eventos finalizada")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestão de discursos parlamentares"
    )

    parser.add_argument(
        "--data-inicio",
        required=True,
        help="Data inicial (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--data-fim",
        required=True,
        help="Data final (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--limite",
        type=int,
        help="Limite de políticos (debug/teste)",
    )

    args = parser.parse_args()

    ingestao_eventos_politicos(
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        limite_politicos=args.limite,
    )
