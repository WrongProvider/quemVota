# backend/repositories/politicos.py
from datetime import date, datetime
from sqlalchemy.orm import Session
from backend.models import (
    Orgao,
    OrgaoMembro,
    Politico,
    Evento,
)

def parse_datetime(valor: str | None) -> datetime | None:
    if not valor:
        return None

    try:
        return datetime.fromisoformat(valor.replace("Z", ""))
    except ValueError:
        return None

    
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

def carregar_eventos_indexados(db):
    eventos = db.query(Evento).all()
    return {e.id_camara: e for e in eventos}

def upsert_evento_index(db, cache: dict, d: dict):
    id_camara = d["id"]

    evento = cache.get(id_camara)

    # ⚠️ eventos da listagem SEM data não entram
    data_inicio = parse_datetime(d.get("dataHoraInicio"))
    if not data_inicio:
        return

    if evento:
        return

    evento = Evento(
        id_camara=id_camara,
        uri=d.get("uri"),
        data_hora_inicio=data_inicio,
        data_hora_fim=parse_datetime(d.get("dataHoraFim")),
        situacao=d.get("situacao"),
        descricao_tipo=d.get("descricaoTipo"),
        local_externo=d.get("localExterno"),
    )

    db.add(evento)
    cache[id_camara] = evento

def upsert_evento_detalhado(db, evento: Evento, d: dict):
    evento.uri = d.get("uri")
    evento.situacao = d.get("situacao")
    evento.descricao_tipo = d.get("descricaoTipo")
    evento.descricao = d.get("descricao")
    evento.url_evento = d.get("url")

    local = d.get("localCamara") or {}

    evento.local_camara_nome = local.get("nome")
    evento.local_camara_predio = local.get("predio")
    evento.local_camara_sala = local.get("sala")
    evento.local_camara_andar = local.get("andar")

    evento.data_hora_inicio = (
        parse_datetime(d.get("dataHoraInicio"))
        or evento.data_hora_inicio
    )

    evento.data_hora_fim = parse_datetime(d.get("dataHoraFim"))

    evento.detalhado = True

def upsert_evento_deputados(db, evento: Evento, deputados: dict):
    dados = deputados.get("dados", [])

    for d in dados:
        politico = (
            db.query(Politico)
            .filter(Politico.id_camara == d["id"])
            .first()
        )

        if not politico:
            continue

        if politico not in evento.deputados:
            evento.deputados.append(politico)

    evento.participantes_importados = True

def upsert_evento_pauta(db, evento: Evento, pauta: dict):
    itens = pauta.get("dados", [])

    for item in itens:
        pauta_evento = EventoPauta(
            evento_id=evento.id,
            descricao=item.get("descricao"),
            ordem=item.get("ordem"),
        )
        db.add(pauta_evento)

    evento.pauta_importada = True

def upsert_evento_votacoes(db, evento: Evento, payload: dict):
    votacoes = payload.get("dados", [])

    for v in votacoes:
        votacao = Votacao(
            evento_id=evento.id,
            id_camara=v["id"],
            descricao=v.get("descricao"),
            data=parse_datetime(v.get("dataHoraRegistro")),
        )
        db.add(votacao)

    evento.votacoes_importadas = True
