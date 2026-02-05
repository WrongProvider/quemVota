import requests
import logging
from datetime import date
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    Orgao,
    OrgaoMembro,
    Politico,
    Evento,
    Votacao
)


BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------
# Utils
# -------------------------
def parse_date(v):
    return date.fromisoformat(v) if v else None


def camara_get(path, params=None):
    r = requests.get(f"{BASE_URL}{path}", params=params)
    r.raise_for_status()
    return r.json()

def upsert_evento(d: dict, db: Session) -> Evento:
    evento = (
        db.query(Evento)
        .filter(Evento.id_camara == d["id"])
        .first()
    )

    if not evento:
        evento = Evento(id_camara=d["id"])
        db.add(evento)

    evento.descricao = d.get("descricao")
    evento.data_hora_inicio = d.get("dataHoraInicio")
    evento.data_hora_fim = d.get("dataHoraFim")
    evento.situacao = d.get("situacao")
    evento.local_camara = d.get("localCamara")
    evento.uri = d.get("uri")

    return evento

def upsert_orgao(d: dict, db: Session) -> Orgao:
    orgao = (
        db.query(Orgao)
        .filter(Orgao.id_camara == d["id"])
        .first()
    )

    if not orgao:
        orgao = Orgao(id_camara=d["id"])
        db.add(orgao)

    orgao.nome = d.get("nome")
    orgao.sigla = d.get("sigla")
    orgao.tipo_orgao = d.get("tipoOrgao")
    orgao.cod_tipo_orgao = d.get("codTipoOrgao")
    orgao.apelido = d.get("apelido")
    orgao.nome_publicacao = d.get("nomePublicacao")
    orgao.nome_resumido = d.get("nomeResumido")
    orgao.uri = d.get("uri")

    return orgao

def enrich_orgao(orgao: Orgao, detalhe: dict):
    orgao.casa = detalhe.get("casa")
    orgao.sala = detalhe.get("sala")
    orgao.url_website = detalhe.get("urlWebsite")

    for campo, attr in [
        ("dataInicio", "data_inicio"),
        ("dataFim", "data_fim"),
        ("dataInstalacao", "data_instalacao"),
    ]:
        if detalhe.get(campo):
            setattr(orgao, attr, date.fromisoformat(detalhe[campo]))

def ingest_eventos_orgao(orgao: Orgao, db: Session):
    dados = camara_get(f"/orgaos/{orgao.id_camara}/eventos")["dados"]

    for d in dados:
        evento = upsert_evento(d, db)

        if orgao not in evento.orgaos:
            evento.orgaos.append(orgao)


def ingest_membros_orgao(orgao: Orgao, db: Session):
    dados = camara_get(f"/orgaos/{orgao.id_camara}/membros")["dados"]

    for d in dados:
        politico = (
            db.query(Politico)
            .filter(Politico.id_camara == d["id"])
            .first()
        )

        if not politico:
            continue  # não cria político fantasma

        existe = (
            db.query(OrgaoMembro)
            .filter_by(orgao_id=orgao.id, politico_id=politico.id)
            .first()
        )

        if existe:
            continue

        membro = OrgaoMembro(
            orgao_id=orgao.id,
            politico_id=politico.id,
            data_inicio=parse_date(d.get("dataInicio")),
            data_fim=parse_date(d.get("dataFim")),
            titulo=d.get("titulo"),
        )
        db.add(membro)

def ingest_votacoes_orgao(orgao: Orgao, db: Session):
    dados = camara_get(f"/orgaos/{orgao.id_camara}/votacoes")["dados"]

    for d in dados:
        existe = (
            db.query(Votacao)
            .filter(Votacao.id_camara == d["id"])
            .first()
        )

        if existe:
            continue

        votacao = Votacao(
            id_camara=d["id"],
            orgao_id=orgao.id,
            descricao=d.get("descricao"),
            data=parse_date(d.get("data")),
            uri=d.get("uri"),
            uri_evento=d.get("uriEvento"),
        )
        db.add(votacao)

def ingestao_orgaos():
    db = SessionLocal()

    lista = camara_get("/orgaos")["dados"]

    for d in lista:
        try:
            logger.info(f"🏛️ Órgão {d['sigla']} ({d['id']})")

            orgao = upsert_orgao(d, db)
            db.flush()

            detalhe = camara_get(f"/orgaos/{orgao.id_camara}")["dados"]
            enrich_orgao(orgao, detalhe)

            ingest_eventos_orgao(orgao, db)
            ingest_membros_orgao(orgao, db)
            ingest_votacoes_orgao(orgao, db)

            db.commit()

        except Exception:
            db.rollback()
            logger.exception(f"❌ Erro no órgão {d['id']}")
    
        finally:
            db.close()