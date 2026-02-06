# backend/repositories/politicos.py
from datetime import date
from sqlalchemy.orm import Session
from backend.models import (
    Orgao,
    OrgaoMembro,
    Politico,
    Evento,
)


def carregar_por_id_camara(db: Session) -> dict[int, Politico]:
    politicos = db.query(Politico).all()
    return {p.id_camara: p for p in politicos}


def upsert_politico(db: Session, cache: dict[int, Politico], dep: dict):
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

# -------------------------
# Cache
# -------------------------

def carregar_orgaos_por_id_camara(db: Session) -> dict[int, Orgao]:
    return {o.id_camara: o for o in db.query(Orgao).all()}


# -------------------------
# Orgao
# -------------------------

def upsert_orgao(db: Session, cache: dict, d: dict) -> Orgao:
    orgao = cache.get(d["id"])

    if not orgao:
        orgao = Orgao(id_camara=d["id"])
        db.add(orgao)
        cache[d["id"]] = orgao

    orgao.nome = d.get("nome")
    orgao.sigla = d.get("sigla")
    orgao.tipo_orgao = d.get("tipoOrgao")
    orgao.cod_tipo_orgao = d.get("codTipoOrgao")
    orgao.apelido = d.get("apelido")
    orgao.nome_publicacao = d.get("nomePublicacao")
    orgao.nome_resumido = d.get("nomeResumido")
    orgao.uri = d.get("uri")

    return orgao


def enrich_orgao(orgao: Orgao, d: dict):
    orgao.casa = d.get("casa")
    orgao.sala = d.get("sala")
    orgao.url_website = d.get("urlWebsite")

    for campo_api, campo_db in [
        ("dataInicio", "data_inicio"),
        ("dataFim", "data_fim"),
        ("dataInstalacao", "data_instalacao"),
    ]:
        valor = d.get(campo_api)
        if d.get(campo_api):
            setattr(
                orgao,
                campo_db,
                date.fromisoformat(valor[:10]),
            )


# -------------------------
# Membros
# -------------------------

def upsert_orgao_membro(db: Session, orgao: Orgao, d: dict):
    politico = (
        db.query(Politico)
        .filter(Politico.id_camara == d["id"])
        .first()
    )

    if not politico:
        return  # não cria político fantasma

    existe = (
        db.query(OrgaoMembro)
        .filter_by(
            orgao_id=orgao.id,
            politico_id=politico.id,
        )
        .first()
    )

    if existe:
        return

    membro = OrgaoMembro(
        orgao_id=orgao.id,
        politico_id=politico.id,
        titulo=d.get("titulo"),
        data_inicio=d.get("dataInicio"),
        data_fim=d.get("dataFim"),
    )
    db.add(membro)


# -------------------------
# Eventos (N:N)
# -------------------------

def upsert_evento_minimo(db: Session, d: dict) -> Evento:
    evento = (
        db.query(Evento)
        .filter(Evento.id_camara == d["id"])
        .first()
    )

    if evento:
        return evento

    evento = Evento(
        id_camara=d["id"],
        descricao=d.get("descricao"),
        descricao_tipo=d.get("descricaoTipo"),
        situacao=d.get("situacao"),
        uri=d.get("uri"),
        url_evento=d.get("urlRegistro"),
        data_hora_inicio=d.get("dataHoraInicio"),
        data_hora_fim=d.get("dataHoraFim"),
    )
    db.add(evento)
    db.flush()  # garante evento.id
    return evento