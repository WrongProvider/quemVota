# backend/repositories/politicos.py
from datetime import date, datetime
import re
import logging
from sqlalchemy.orm import Session
from injest_banco.db.models import (
    Orgao,
    Partido,
    Evento,
    ProposicaoAutor,
    Proposicao,
    VerbaGabinete,
    Votacao,
    Voto,
    Despesa,
    Deputado
)

from sqlalchemy.dialects.postgresql import insert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_datetime(valor: str | None) -> datetime | None:
    if not valor:
        return None

    try:
        return datetime.fromisoformat(valor.replace("Z", ""))
    except ValueError:
        return None

    
def carregar_por_id_camara(db: Session) -> dict[int, Deputado]:
    deputados = db.query(Deputado).all()
    return {d.idCamara: d for d in deputados}


def upsert_politico(db: Session, cache: dict, dep: dict, partido_obj: Partido = None):
    politico = cache.get(dep["id"])

    if politico:
        politico.nome = dep["nome"]
        politico.uf = dep["siglaUf"]
        politico.url_foto = dep.get("urlFoto")
        # Atualiza o vínculo com o partido atual
        if partido_obj:
            politico.partido_id = partido_obj.id
            politico.partido_sigla = partido_obj.sigla
    else:
        politico = Deputado(
            idCamara=dep["id"],
            nome=dep["nome"],
            uf=dep["siglaUf"],
            url_foto=dep.get("urlFoto"),
            partido_id=partido_obj.id if partido_obj else None,
            partido_sigla=partido_obj.sigla if partido_obj else dep.get("siglaPartido")
        )
        db.add(politico)
        db.flush()  # Garante que politico.id seja gerado para o cache
        cache[dep["id"]] = politico
    
    return politico
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
        db.query(Deputado)
        .filter(Deputado.idCamara == d["id"])
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
            db.query(Deputado)
            .filter(Deputado.idCamara == d["id"])
            .first()
        )

        if not politico:
            continue

        if politico not in evento.deputados:
            evento.deputados.append(politico)

    evento.participantes_importados = True

# # def upsert_evento_pauta(db, evento: Evento, pauta: dict):
#     itens = pauta.get("dados", [])

#     for item in itens:
#         pauta_evento = EventoPauta(
#             evento_id=evento.id,
#             descricao=item.get("descricao"),
#             ordem=item.get("ordem"),
#         )
#         db.add(pauta_evento)

#     evento.pauta_importada = True

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



def upsert_votacao_index(db: Session, evento: Evento | None, d: dict, proposicao_id: int = None):
    votacao = (
        db.query(Votacao)
        .filter(Votacao.id_camara == d["id"])
        .first()
    )

    if votacao:
        # Se a votação já existe mas está sem o vínculo, atualizamos agora
        if proposicao_id and not votacao.proposicao_id:
            votacao.proposicao_id = proposicao_id
        return votacao

    votacao = Votacao(
        id_camara=d["id"],
        evento_id=evento.id if evento else None,
        proposicao_id=proposicao_id,
        descricao=d.get("descricao"),
        data=parse_datetime(d.get("data")),
        data_hora_registro=parse_datetime(d.get("dataHoraRegistro")),
        aprovacao=d.get("aprovacao"),
        uri=d.get("uri"),
        indexada=True,
        tipo_votacao=d.get("tipoVotacao")
    )

    db.add(votacao)
    return votacao

def upsert_votacao_detalhada(db: Session, votacao: Votacao, payload: dict):
    d = payload.get("dados", {})

    votacao.descricao = d.get("descricao")
    votacao.data = parse_datetime(d.get("data"))
    votacao.data_hora_registro = parse_datetime(d.get("dataHoraRegistro"))
    votacao.aprovacao = d.get("aprovacao")
    votacao.uri = d.get("uri")

    votacao.votos_importados = True

def upsert_votacao_orientacoes(db: Session, votacao: Votacao, payload: dict):
    dados = payload.get("dados", [])

    for d in dados:
        existe = (
            db.query(OrientacaoVotacao)
            .filter_by(
                votacao_id=votacao.id,
                cod_partido_bloco=d["codPartidoBloco"],
            )
            .first()
        )

        if existe:
            continue

        orientacao = OrientacaoVotacao(
            votacao_id=votacao.id,
            cod_partido_bloco=d["codPartidoBloco"],
            sigla_partido_bloco=d.get("siglaPartidoBloco"),
            orientacao_voto=d.get("orientacaoVoto"),
            cod_tipo_lideranca=d.get("codTipoLideranca"),
        )
        db.add(orientacao)

    votacao.orientacoes_importadas = True

    
def upsert_votacao_votos(db: Session, votacao: Votacao, payload: dict, cache_politicos: dict):
    dados = payload.get("dados", [])
    if not dados: 
        return

    # Otimização: Cache de IDs já inseridos no banco para esta votação
    votos_existentes = {
        v[0] for v in db.query(Voto.politico_id)
        .filter(Voto.votacao_id == votacao.id)
        .all()
    }

    votos_inseridos = 0

    for d in dados:
        # Tenta pegar "deputado_" (conforme seu JSON) ou "deputado" (padrão da API)
        dep_data = d.get("deputado_") or d.get("deputado")
        
        if not dep_data:
            # Se não achar a chave, pula e avisa no log para debug
            # logger.debug(f"Estrutura de voto inesperada: {d.keys()}")
            continue
            
        id_api_deputado = dep_data.get("id")
        if id_api_deputado is None:
            continue

        # Garante que o ID é int para bater com o cache_politicos
        politico = cache_politicos.get(int(id_api_deputado))
        
        if not politico:
            # Se o político não estiver no banco, não conseguimos criar a FK do Voto
            continue

        if politico.id in votos_existentes:
            continue

        novo_voto = Voto(
            votacao_id=votacao.id,
            politico_id=politico.id,
            tipo_voto=d.get("tipoVoto"),
            data_registro_voto=parse_datetime(d.get("dataRegistroVoto")),
            sigla_partido=dep_data.get("siglaPartido"),
            sigla_uf=dep_data.get("siglaUf")
        )
        db.add(novo_voto)
        votos_existentes.add(politico.id) # Evita duplicar no mesmo loop
        votos_inseridos += 1
    
    # Fazemos um flush para garantir que os erros de constraint apareçam aqui se houverem
    db.flush()
    logger.info(f"📊 {votos_inseridos} votos inseridos para a votação {votacao.id_camara}")
    votacao.votos_importados = True

def carregar_partidos_por_sigla(db: Session) -> dict[str, Partido]:
    """
    Retorna um dicionário onde a chave é a sigla e o valor é o objeto Partido.
    Útil para vincular Políticos a Partidos durante a ingestão.
    """
    partidos = db.query(Partido).all()
    # Criamos o mapeamento { 'PT': <Objeto Partido>, 'PL': <Objeto Partido>, ... }
    return {p.sigla: p for p in partidos}


def upsert_despesa(db: Session, politico_id: int, d: dict, cod_doc: str):

    despesa = db.query(Despesa).filter_by(cod_documento=cod_doc).first()

    if not despesa:
        despesa = Despesa(cod_documento=cod_doc, politico_id=politico_id)
        db.add(despesa)
        # Opcional: db.flush() aqui se você processa muitos duplicados no mesmo bloco
    
    # Tratamento de campos
    despesa.parcela = int(d.get("parcela") or 0) if str(d.get("parcela")).isdigit() else 0
    despesa.num_ressarcimento = str(d.get("numRessarcimento") or "")

    # Tratamento para Num Ressarcimento
    # Se for nulo ou string vazia, guardamos como None (NULL no banco)
    raw_ressarc = d.get("numRessarcimento")
    despesa.num_ressarcimento = str(raw_ressarc) if raw_ressarc else None
    # Atualiza os campos (isso garante que se o valor mudar na API, seu banco atualiza)
    despesa.ano = d.get("ano")
    despesa.mes = d.get("mes")
    despesa.tipo_despesa = d.get("tipoDespesa")
    despesa.tipo_documento = d.get("tipoDocumento")
    despesa.cod_tipo_documento = d.get("codTipoDocumento")
    despesa.data_documento = parse_datetime(d.get("dataDocumento"))
    despesa.num_documento = d.get("numDocumento")
    despesa.valor_documento = d.get("valorDocumento")
    despesa.valor_liquido = d.get("valorLiquido")
    despesa.valor_glosa = d.get("valorGlosa")
    despesa.url_documento = d.get("urlDocumento")
    despesa.nome_fornecedor = d.get("nomeFornecedor")
    despesa.cnpj_cpf_fornecedor = d.get("cnpjCpfFornecedor")
    despesa.cod_lote = d.get("codLote")

    return True



def upsert_proposicao(db: Session, d: dict) -> Proposicao:
    """Realiza o upsert da proposição básica."""
    id_camara = d.get("id")
    prop = db.query(Proposicao).filter_by(id_camara=id_camara).first()

    if not prop:
        prop = Proposicao(id_camara=id_camara)
        db.add(prop)
    
    prop.uri = d.get("uri")
    prop.sigla_tipo = d.get("siglaTipo")
    prop.cod_tipo = d.get("codTipo")
    prop.numero = d.get("numero")
    prop.ano = d.get("ano")
    prop.descricao_tipo = d.get("descricaoTipo")
    prop.ementa = d.get("ementa")
    prop.data_apresentacao = parse_datetime(d.get("dataApresentacao"))
    prop.url_inteiro_teor = d.get("urlInteiroTeor")

    # Campos que geralmente vêm do /proposicoes/{id} (detalhes)
    if "ementaDetalhada" in d:
        prop.ementa_detalhada = d.get("ementaDetalhada")
    if "keywords" in d:
        prop.keywords = d.get("keywords")
    if "justificativa" in d:
        prop.justificativa = d.get("justificativa")

    return prop

def extract_id_from_uri(uri: str | None) -> int | None:
    """Extrai o número final de uma URL (ex: .../deputados/73492 -> 73492)"""
    if not uri:
        return None
    match = re.search(r'/(\d+)$', uri)
    return int(match.group(1)) if match else None

from sqlalchemy.dialects.postgresql import insert

# faz o upsert dos autores de proposição
def upsert_proposicao_autor(db: Session, prop_id: int, auth_data: dict, cache_politicos: dict):
    id_autor_camara = extract_id_from_uri(auth_data.get("uri"))
    politico = cache_politicos.get(id_autor_camara)
    
    stmt = insert(ProposicaoAutor).values(
        proposicao_id=prop_id,
        politico_id=politico.id if politico else None,
        nome=auth_data.get("nome"),
        uri_autor=auth_data.get("uri"),
        cod_tipo=auth_data.get("codTipo"),
        tipo=auth_data.get("tipo"),
        ordem_assinatura=auth_data.get("ordemAssinatura"),
        proponente=bool(auth_data.get("proponente"))
    )

    # Em vez de index_elements, usamos o nome da CONSTRAINT que criamos no Passo 1
    stmt = stmt.on_conflict_do_update(
        constraint="uq_autores_final",
        set_={
            "uri_autor": stmt.excluded.uri_autor,
            "ordem_assinatura": stmt.excluded.ordem_assinatura,
            "proponente": stmt.excluded.proponente
        }
    )
    
    db.execute(stmt)

def vincular_votacao_a_proposicao(db: Session, votacao: Votacao, id_proposicao_camara: int):
    """
    Busca a proposição pelo ID da Câmara e vincula à votação local.
    """
    if not id_proposicao_camara:
        return

    prop = db.query(Proposicao).filter_by(id_camara=id_proposicao_camara).first()
    if prop:
        votacao.proposicao_id = prop.id
        # logger.info(f"🔗 Votação {votacao.id_camara} vinculada à Proposição {prop.sigla_tipo} {prop.numero}/{prop.ano}")

