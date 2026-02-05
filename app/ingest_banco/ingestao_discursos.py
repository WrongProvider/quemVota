import requests
import time
import logging
import argparse
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from backend.database import SessionLocal
from backend.models import Politico, Discurso

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def buscar_discursos_deputado(
    id_camara: int,
    data_inicio: str,
    data_fim: str,
    pagina: int = 1,
    itens: int = 100,
    tentativas: int = 3,
):
    for tentativa in range(tentativas):
        try:
            response = requests.get(
                f"{API_BASE}/deputados/{id_camara}/discursos",
                params={
                    "dataInicio": data_inicio,
                    "dataFim": data_fim,
                    "pagina": pagina,
                    "itens": itens,
                    "ordenarPor": "dataHoraInicio",
                    "ordem": "ASC",
                },
                headers=HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if tentativa == tentativas - 1:
                raise e
            time.sleep(2 ** tentativa)

def ingestao_discursos_politico(
    dep: Politico,
    data_inicio: str,
    data_fim: str,
):
    db: Session = SessionLocal()

    try:
        pagina = 1

        while True:
            logger.info(
                "Deputado %s | Página %s",
                dep.id_camara,
                pagina,
            )

            payload = buscar_discursos_deputado(
                dep.id_camara,
                data_inicio,
                data_fim,
                pagina,
            )

            dados = payload.get("dados", [])
            if not dados:
                break

            lista_discursos: list[dict] = []

            for d in dados:
                fase = d.get("faseEvento") or {}

                lista_discursos.append(
                    {
                        "politico_id": dep.id,
                        "data_hora_inicio": datetime.fromisoformat(
                            d["dataHoraInicio"]
                        ),
                        "data_hora_fim": (
                            datetime.fromisoformat(d["dataHoraFim"])
                            if d.get("dataHoraFim")
                            else None
                        ),
                        "tipo_discurso": d.get("tipoDiscurso"),
                        "fase_evento_titulo": fase.get("titulo"),
                        "url_texto": d.get("urlTexto"),
                        "url_audio": d.get("urlAudio"),
                        "url_video": d.get("urlVideo"),
                        "keywords": d.get("keywords"),
                        "sumario": d.get("sumario"),
                        "transcricao": d.get("transcricao"),
                    }
                )

            if lista_discursos:
                stmt = insert(Discurso).values(lista_discursos)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=[
                        "politico_id",
                        "data_hora_inicio",
                    ]
                )
                db.execute(stmt)
                db.commit()

            links = payload.get("links", [])
            if not any(l["rel"] == "next" for l in links):
                break

            pagina += 1
            time.sleep(0.2)

        logger.info("✅ Discursos ingeridos para %s", dep.nome)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def runner_ingestao_discursos(
    data_inicio: str,
    data_fim: str,
    limite: int | None = None,
):
    db: Session = SessionLocal()

    try:
        query = db.query(Politico)

        if limite:
            query = query.limit(limite)

        politicos = query.all()

        logger.info(
            "🚀 Iniciando ingestão de discursos para %s políticos",
            len(politicos),
        )

        for politico in politicos:
            ingestao_discursos_politico(
                politico,
                data_inicio,
                data_fim,
            )
            time.sleep(0.5)

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

    runner_ingestao_discursos(
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        limite=args.limite,
    )
