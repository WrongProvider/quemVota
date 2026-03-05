"""
models.py — SQLAlchemy ORM fiel à API de Dados Abertos da Câmara dos Deputados
Nomenclatura: camelCase nos campos, espelhando exatamente os campos da API.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    SmallInteger,
    Date,
    DateTime,
    Numeric,
    Text,
    Boolean,
    CHAR,
    UniqueConstraint,
    Table,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from injest_banco.db.database import Base


# ---------------------------------------------------------------------------
# Tabela associativa: eventos ↔ órgãos
# ---------------------------------------------------------------------------
eventosOrgaos = Table(
    "eventosOrgaos",
    Base.metadata,
    Column("idEvento", Integer, ForeignKey("eventos.id", ondelete="CASCADE"), primary_key=True),
    Column("idOrgao",  Integer, ForeignKey("orgaos.id",  ondelete="CASCADE"), primary_key=True),
)

# ---------------------------------------------------------------------------
# Tabela associativa: proposições ↔ temas
# ---------------------------------------------------------------------------
proposicoesTemas = Table(
    "proposicoesTemas",
    Base.metadata,
    Column("idProposicao", Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"), primary_key=True),
    Column("idTema",       Integer, ForeignKey("temas.id",        ondelete="CASCADE"), primary_key=True),
)


# ===========================================================================
# LEGISLATURAS
# ===========================================================================
class Legislatura(Base):
    """
    /legislaturas
    Campos: idLegislatura, uri, dataInicio, dataFim, anoEleicao
    """
    __tablename__ = "legislaturas"

    id            = Column(Integer, primary_key=True)                          # PK interna
    idLegislatura = Column(Integer, nullable=False, unique=True, index=True)   # id da API
    uri           = Column(Text)
    dataInicio    = Column(Date)
    dataFim       = Column(Date)
    anoEleicao    = Column(Integer)

    # Relationships
    mesas    = relationship("LegislaturaMesa", back_populates="legislatura")
    deputados = relationship("Deputado", back_populates="legislatura",
                             foreign_keys="Deputado.idLegislaturaFinal")


# ===========================================================================
# LEGISLATURAS — MESAS
# ===========================================================================
class LegislaturaMesa(Base):
    """
    /legislaturas/{id}/mesa
    Campos: idOrgao, uriOrgao, siglaOrgao, nomeOrgao,
            idDeputado, uriDeputado, nomeDeputado, siglaPartido,
            siglaUF, cargo, dataInicio, dataFim, idLegislatura
    """
    __tablename__ = "legislaturasMesas"

    id           = Column(Integer, primary_key=True)
    idLegislatura = Column(Integer, ForeignKey("legislaturas.idLegislatura", ondelete="CASCADE"),
                           nullable=False, index=True)
    idOrgao      = Column(Integer, ForeignKey("orgaos.idCamara"), nullable=True, index=True)
    uriOrgao     = Column(Text)
    siglaOrgao   = Column(String(50))
    nomeOrgao    = Column(String(200))

    idDeputado   = Column(Integer, ForeignKey("deputados.idCamara", ondelete="SET NULL"),
                          nullable=True, index=True)
    uriDeputado  = Column(Text)
    nomeDeputado = Column(String(200))
    siglaPartido = Column(String(50))
    siglaUF      = Column(CHAR(2))
    cargo        = Column(String(100))

    dataInicio   = Column(DateTime)
    dataFim      = Column(DateTime)

    legislatura  = relationship("Legislatura", back_populates="mesas")
    deputado     = relationship("Deputado", foreign_keys=[idDeputado])

    __table_args__ = (
        UniqueConstraint("idLegislatura", "idDeputado", "cargo", "dataInicio", name="uq_mesa_leg_dep_cargo_data"),
    )


# ===========================================================================
# ÓRGÃOS
# ===========================================================================
class Orgao(Base):
    """
    /orgaos
    Campos: uri, sigla, apelido, nome, nomePublicacao,
            codTipoOrgao, tipoOrgao, dataInicio, dataInstalacao,
            dataFim, dataFimOriginal, codSituacao, descricaoSituacao,
            casa, sala, urlWebsite
    """
    __tablename__ = "orgaos"

    id               = Column(Integer, primary_key=True)
    idCamara         = Column(Integer, nullable=False, unique=True, index=True)
    uri              = Column(Text, unique=True)

    sigla            = Column(String(50), index=True)
    apelido          = Column(Text)
    nome             = Column(Text)
    nomePublicacao   = Column(Text)

    codTipoOrgao     = Column(Integer)
    tipoOrgao        = Column(String(100))
    casa             = Column(String(50))
    sala             = Column(String(50))

    dataInicio       = Column(Date)
    dataInstalacao   = Column(Date)
    dataFim          = Column(Date)
    dataFimOriginal  = Column(Date)

    codSituacao      = Column(Integer)
    descricaoSituacao = Column(String(100))

    urlWebsite       = Column(Text)

    createdAt        = Column(DateTime, server_default=func.now())

    # Relationships
    eventos = relationship("Evento", secondary="eventosOrgaos", back_populates="orgaos")
    membros = relationship("OrgaoDeputado", back_populates="orgao")


# ===========================================================================
# ÓRGÃOS — MEMBROS (deputados por órgão)
# ===========================================================================
class OrgaoDeputado(Base):
    """
    /orgaos/{id}/membros  e  orgaosDeputados-L51.csv
    Campos: uriOrgao, siglaOrgao, nomeOrgao, nomePublicacaoOrgao,
            uriDeputado, nomeDeputado, siglaPartido, siglaUF,
            cargo, dataInicio, dataFim
    """
    __tablename__ = "orgaosDeputados"

    id                 = Column(Integer, primary_key=True)
    idOrgao            = Column(Integer, ForeignKey("orgaos.id",     ondelete="CASCADE"),  nullable=False, index=True)
    idDeputado         = Column(Integer, ForeignKey("deputados.id",  ondelete="CASCADE"),  nullable=True,  index=True)

    nomePublicacaoOrgao = Column(Text)
    uriDeputado        = Column(Text)
    nomeDeputado       = Column(String(200))
    siglaPartido       = Column(String(50))
    siglaUF            = Column(CHAR(2))
    cargo              = Column(String(100))
    codTitulo          = Column(Integer)

    dataInicio         = Column(Date)
    dataFim            = Column(Date)

    orgao    = relationship("Orgao",    back_populates="membros")
    deputado = relationship("Deputado", back_populates="orgaos")

    __table_args__ = (
        UniqueConstraint("idOrgao", "idDeputado", name="uq_orgaodeputado"),
    )


# ===========================================================================
# DEPUTADOS
# ===========================================================================
class Deputado(Base):
    """
    /deputados  e  deputados.csv
    Campos: uri, nome, idLegislaturaInicial, idLegislaturaFinal, nomeCivil,
            cpf, siglaSexo, urlRedeSocial, urlWebsite, dataNascimento,
            dataFalecimento, ufNascimento, municipioNascimento
    Campos adicionais (perfil completo): escolaridade, situacao,
            condicaoEleitoral, email, telefoneGabinete, emailGabinete, urlFoto
    """
    __tablename__ = "deputados"

    id                  = Column(Integer, primary_key=True)
    idCamara            = Column(Integer, nullable=False, unique=True, index=True)
    uri                 = Column(Text, unique=True)

    # Identificação
    nome                = Column(String(200), nullable=False, index=True)
    nomeCivil           = Column(String(200))
    cpf                 = Column(String(14))
    siglaSexo           = Column(CHAR(1))

    # Legislaturas
    idLegislaturaInicial = Column(Integer, ForeignKey("legislaturas.idLegislatura"), nullable=True)
    idLegislaturaFinal   = Column(Integer, ForeignKey("legislaturas.idLegislatura"), nullable=True, index=True)

    # Dados pessoais
    dataNascimento      = Column(Date)
    dataFalecimento     = Column(Date)
    ufNascimento        = Column(CHAR(2))
    municipioNascimento = Column(String(100))

    # Dados políticos
    siglaUF             = Column(CHAR(2), index=True)
    siglaPartido        = Column(String(20), index=True)
    idPartido           = Column(Integer, ForeignKey("partidos.id", ondelete="SET NULL"), nullable=True)
    escolaridade        = Column(String(100))
    situacao            = Column(String(50))
    condicaoEleitoral   = Column(String(50))

    # Contatos
    email               = Column(String(200))
    telefoneGabinete    = Column(String(30))
    emailGabinete       = Column(String(200))

    # Mídia
    urlFoto             = Column(Text)
    urlRedeSocial       = Column(Text)
    urlWebsite          = Column(Text)

    createdAt           = Column(DateTime, server_default=func.now())

    # Relationships
    legislatura    = relationship("Legislatura", back_populates="deputados",
                                  foreign_keys=[idLegislaturaFinal])
    partido        = relationship("Partido", back_populates="deputados")
    orgaos         = relationship("OrgaoDeputado", back_populates="deputado")
    ocupacoes      = relationship("DeputadoOcupacao",  back_populates="deputado", cascade="all, delete-orphan")
    profissoes     = relationship("DeputadoProfissao", back_populates="deputado", cascade="all, delete-orphan")
    despesas       = relationship("Despesa",     back_populates="deputado", cascade="all, delete-orphan")
    discursos      = relationship("Discurso",    back_populates="deputado", cascade="all, delete-orphan")
    votos          = relationship("Voto",        back_populates="deputado", cascade="all, delete-orphan")
    presencas      = relationship("PresencaDeputado", back_populates="deputado", cascade="all, delete-orphan")
    frentes        = relationship("FrenteDeputado",   back_populates="deputado")
    gruposMembros  = relationship("GrupoMembro",      back_populates="deputado")
    buscaPopular   = relationship("BuscaPopular",     back_populates="deputado", uselist=False)


# ===========================================================================
# DEPUTADOS — OCUPAÇÕES
# ===========================================================================
class DeputadoOcupacao(Base):
    """
    /deputados/{id}/ocupacoes  e  deputadosOcupacoes.csv
    Campos: id (idCamara deputado), uri, titulo, entidade,
            entidadeUF, entidadePais, anoInicio, anoFim
    """
    __tablename__ = "deputadosOcupacoes"

    id          = Column(Integer, primary_key=True)
    idDeputado  = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)

    titulo      = Column(Text)
    entidade    = Column(Text)
    entidadeUF  = Column(CHAR(2))
    entidadePais = Column(Text)
    anoInicio   = Column(Integer)
    anoFim      = Column(Integer)

    deputado = relationship("Deputado", back_populates="ocupacoes")

    # Adicione este bloco no final da classe:
    __table_args__ = (
        UniqueConstraint("idDeputado", "titulo", "entidade", "entidadeUF", "entidadePais", "anoInicio", "anoFim", name="uq_deputado_ocupacao"),
    )
# ===========================================================================
# DEPUTADOS — PROFISSÕES
# ===========================================================================
class DeputadoProfissao(Base):
    """
    /deputados/{id}/profissoes  e  deputadosProfissoes.csv
    Campos: uri (idCamara), id, dataHora, codTipoProfissao, titulo
    """
    __tablename__ = "deputadosProfissoes"

    id               = Column(Integer, primary_key=True)
    idDeputado       = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)
    dataHora         = Column(DateTime)
    codTipoProfissao = Column(Integer)
    titulo           = Column(String(200))

    deputado = relationship("Deputado", back_populates="profissoes")


# ===========================================================================
# PARTIDOS
# ===========================================================================
class Partido(Base):
    __tablename__ = "partidos"

    id               = Column(Integer, primary_key=True)
    idCamara         = Column(Integer, nullable=False, unique=True, index=True)
    uri              = Column(Text, unique=True)

    nome             = Column(String(200), nullable=False)
    sigla            = Column(String(50),  nullable=False, index=True)
    numeroEleitoral  = Column(Integer)

    situacao         = Column(String(100))
    totalMembros     = Column(Integer)
    totalPosse       = Column(Integer)

    urlFacebook      = Column(Text)
    urlLogo          = Column(Text)
    urlWebsite       = Column(Text)

    deputados = relationship("Deputado",       back_populates="partido")
    membros   = relationship("PartidoMembro",  back_populates="partido")
    lideres   = relationship("PartidoLider",   back_populates="partido")


class PartidoMembro(Base):
    __tablename__ = "partidosMembros"

    id         = Column(Integer, primary_key=True)
    idPartido  = Column(Integer, ForeignKey("partidos.id", ondelete="CASCADE"), nullable=False, index=True)
    idDeputado = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=True,  index=True)

    dataInicio = Column(Date)
    dataFim    = Column(Date)

    partido  = relationship("Partido",  back_populates="membros")
    deputado = relationship("Deputado")

    __table_args__ = (
        UniqueConstraint("idPartido", "idDeputado", name="uq_partido_membro"),
    )


class PartidoLider(Base):
    __tablename__ = "partidosLideres"

    id         = Column(Integer, primary_key=True)
    idPartido  = Column(Integer, ForeignKey("partidos.id",   ondelete="CASCADE"), nullable=False, index=True)
    idDeputado = Column(Integer, ForeignKey("deputados.id",  ondelete="CASCADE"), nullable=True,  index=True)

    codTitulo  = Column(Integer)
    titulo     = Column(String(100))
    dataInicio = Column(Date)
    dataFim    = Column(Date)

    partido  = relationship("Partido",  back_populates="lideres")
    deputado = relationship("Deputado")


# ===========================================================================
# EVENTOS
# ===========================================================================
class Evento(Base):
    """
    /eventos  e  eventos-2026.csv
    Campos: id, uri, urlDocumentoPauta, dataHoraInicio, dataHoraFim,
            situacao, descricao, descricaoTipo, localExterno,
            localCamara.nome, localCamara.predio, localCamara.sala, localCamara.andar
    """
    __tablename__ = "eventos"

    id                 = Column(Integer, primary_key=True)
    idCamara           = Column(Integer, unique=True, index=True, nullable=False)
    uri                = Column(Text, unique=True)
    urlDocumentoPauta  = Column(Text)

    dataHoraInicio     = Column(DateTime, index=True)
    dataHoraFim        = Column(DateTime)
    situacao           = Column(String(50))
    descricao          = Column(Text)
    descricaoTipo      = Column(String(100))

    localExterno       = Column(Text)
    localCamaraNome    = Column(String(200))        # localCamara.nome
    localCamaraPredio  = Column(String(100))        # localCamara.predio
    localCamaraSala    = Column(String(50))         # localCamara.sala
    localCamaraAndar   = Column(String(50))         # localCamara.andar

    urlEvento          = Column(Text)
    createdAt          = Column(DateTime, server_default=func.now())

    orgaos    = relationship("Orgao",    secondary="eventosOrgaos", back_populates="eventos")
    discursos = relationship("Discurso", back_populates="evento")
    requerimentos = relationship("EventoRequerimento", back_populates="evento",
                                 cascade="all, delete-orphan")
    presencas = relationship("PresencaDeputado", back_populates="evento",
                             cascade="all, delete-orphan")


# ===========================================================================
# EVENTOS — REQUERIMENTOS
# ===========================================================================
class EventoRequerimento(Base):
    """
    /eventos/{id}/requerimentos  e  eventosRequerimentos-2026.csv
    Campos: idEvento, uriEvento, tituloRequerimento, uriRequerimento
    """
    __tablename__ = "eventosRequerimentos"

    id                 = Column(Integer, primary_key=True)
    idEvento           = Column(Integer, ForeignKey("eventos.id", ondelete="CASCADE"),
                                nullable=False, index=True)
    tituloRequerimento = Column(String(200))
    uriRequerimento    = Column(Text)

    evento = relationship("Evento", back_populates="requerimentos")


# ===========================================================================
# EVENTOS — PRESENÇA DE DEPUTADOS
# ===========================================================================
class PresencaDeputado(Base):
    """
    /eventos/{id}/deputados  e  eventosPresencaDeputados-2026.csv
    Campos: idEvento, uriEvento, dataHoraInicio, idDeputado, uriDeputado
    """
    __tablename__ = "eventosPresencaDeputados"

    id             = Column(Integer, primary_key=True)
    idEvento       = Column(Integer, ForeignKey("eventos.id",   ondelete="CASCADE"), nullable=False, index=True)
    idDeputado     = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=False, index=True)
    dataHoraInicio = Column(DateTime)

    evento   = relationship("Evento",   back_populates="presencas")
    deputado = relationship("Deputado", back_populates="presencas")

    __table_args__ = (
        UniqueConstraint("idEvento", "idDeputado", name="uq_presenca_evento_deputado"),
    )


# ===========================================================================
# PROPOSIÇÕES
# ===========================================================================
class Proposicao(Base):
    """
    /proposicoes  e  proposicoes-2026.csv
    Campos: id, uri, siglaTipo, numero, ano, codTipo, descricaoTipo,
            ementa, ementaDetalhada, keywords, dataApresentacao,
            uriOrgaoNumerador, uriPropAnterior, uriPropPrincipal, uriPropPosterior,
            urlInteiroTeor, urnFinal
            ultimoStatus_* → desnormalizado para acesso rápido
    """
    __tablename__ = "proposicoes"

    id                = Column(Integer, primary_key=True)
    idCamara          = Column(Integer, nullable=False, unique=True, index=True)
    uri               = Column(Text, unique=True, index=True)

    # Identificação
    siglaTipo         = Column(String(50), index=True)
    codTipo           = Column(Integer)
    numero            = Column(Integer, index=True)
    ano               = Column(Integer, index=True)
    descricaoTipo     = Column(Text)

    # Conteúdo
    ementa            = Column(Text)
    ementaDetalhada   = Column(Text)
    keywords          = Column(Text)
    justificativa     = Column(Text)

    # Datas
    dataApresentacao  = Column(DateTime)

    # Relações entre proposições (URIs da API)
    uriOrgaoNumerador = Column(Text)
    uriPropAnterior   = Column(Text)
    uriPropPrincipal  = Column(Text)
    uriPropPosterior  = Column(Text)

    # Links
    urlInteiroTeor    = Column(Text)
    urnFinal          = Column(String(200))

    # Último status — desnormalizado (espelho do último registro de tramitação)
    ultimoStatus_dataHora            = Column(DateTime)
    ultimoStatus_sequencia           = Column(Integer)
    ultimoStatus_uriRelator          = Column(Text)
    ultimoStatus_idOrgao             = Column(Integer)
    ultimoStatus_siglaOrgao          = Column(String(50))
    ultimoStatus_uriOrgao            = Column(Text)
    ultimoStatus_regime              = Column(String(200))
    ultimoStatus_descricaoTramitacao = Column(String(200))
    ultimoStatus_idTipoTramitacao    = Column(Integer)
    ultimoStatus_descricaoSituacao   = Column(String(150))
    ultimoStatus_idSituacao          = Column(Integer)
    ultimoStatus_despacho            = Column(Text)
    ultimoStatus_apreciacao          = Column(String(200))
    ultimoStatus_url                 = Column(Text)

    createdAt = Column(DateTime, server_default=func.now())

    # Relationships
    autores      = relationship("ProposicaoAutor", back_populates="proposicao",
                                cascade="all, delete-orphan")
    temas        = relationship("Tema", secondary="proposicoesTemas", back_populates="proposicoes")
    tramitacoes  = relationship("Tramitacao",  back_populates="proposicao",
                                cascade="all, delete-orphan", order_by="Tramitacao.dataHora")
    votacoes     = relationship("Votacao",     back_populates="proposicao")


# ===========================================================================
# PROPOSIÇÕES — AUTORES
# ===========================================================================
class ProposicaoAutor(Base):
    """
    /proposicoes/{id}/autores  e  proposicoesAutores-2026.csv
    Campos: idProposicao, uriProposicao, idDeputadoAutor, uriAutor,
            codTipoAutor, tipoAutor, nomeAutor, siglaPartidoAutor,
            uriPartidoAutor, siglaUFAutor, ordemAssinatura, proponente
    """
    __tablename__ = "proposicoesAutores"

    id              = Column(Integer, primary_key=True)
    idProposicao    = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    idDeputadoAutor = Column(Integer, ForeignKey("deputados.id",   ondelete="SET NULL"),
                             nullable=True, index=True)

    uriAutor          = Column(Text)
    codTipoAutor      = Column(Integer)
    tipoAutor         = Column(String(50))
    nomeAutor         = Column(Text, nullable=False)
    siglaPartidoAutor = Column(String(50))
    uriPartidoAutor   = Column(Text)
    siglaUFAutor      = Column(CHAR(2))
    ordemAssinatura   = Column(Integer)
    proponente        = Column(Boolean)

    proposicao = relationship("Proposicao", back_populates="autores")
    deputado   = relationship("Deputado")

    __table_args__ = (
        UniqueConstraint("idProposicao", "idDeputadoAutor", "nomeAutor",
                         name="uq_autor_proposicao",
                         postgresql_nulls_not_distinct=True),
    )


# ===========================================================================
# TEMAS
# ===========================================================================
class Tema(Base):
    """
    /referencias/proposicoes/codTema  e  proposicoesTemas-2026.csv
    Campos: codTema, tema, relevancia (na tabela associativa)
    """
    __tablename__ = "temas"

    id      = Column(Integer, primary_key=True)
    codTema = Column(Integer, unique=True, index=True)
    tema    = Column(String(150), index=True)

    proposicoes = relationship("Proposicao", secondary="proposicoesTemas",
                               back_populates="temas")


# ===========================================================================
# TRAMITAÇÕES
# ===========================================================================
class Tramitacao(Base):
    """
    /proposicoes/{id}/tramitacoes
    Campos: sequencia, dataHora, siglaOrgao, uriOrgao, uriUltimoRelator,
            regime, descricaoTramitacao, codTipoTramitacao,
            descricaoSituacao, codSituacao, despacho, url, ambito, apreciacao
    """
    __tablename__ = "tramitacoes"

    id           = Column(Integer, primary_key=True)
    idProposicao = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"),
                          nullable=False, index=True)

    dataHora              = Column(DateTime, index=True)
    sequencia             = Column(Integer)

    siglaOrgao            = Column(String(50))
    uriOrgao              = Column(Text)
    uriUltimoRelator      = Column(Text)

    regime                = Column(String(200))
    descricaoTramitacao   = Column(String(200))
    codTipoTramitacao     = Column(Integer)

    descricaoSituacao     = Column(String(150))
    codSituacao           = Column(Integer)

    despacho              = Column(Text)
    url                   = Column(Text)
    ambito                = Column(String(50))
    apreciacao            = Column(String(200))

    proposicao = relationship("Proposicao", back_populates="tramitacoes")


# ===========================================================================
# VOTAÇÕES
# ===========================================================================
class Votacao(Base):
    """
    /votacoes  e  votacoes-2026.csv
    Campos: id, uri, data, dataHoraRegistro, idOrgao, uriOrgao, siglaOrgao,
            idEvento, uriEvento, aprovacao, votosSim, votosNao, votosOutros,
            descricao,
            ultimaAberturaVotacao_dataHoraRegistro, ultimaAberturaVotacao_descricao,
            ultimaApresentacaoProposicao_dataHoraRegistro, _descricao,
            _idProposicao, _uriProposicao
    """
    __tablename__ = "votacoes"

    id                  = Column(Integer, primary_key=True)
    idCamara            = Column(String(50), unique=True, index=True)   # e.g. "2578879-38"
    uri                 = Column(Text)

    idProposicao        = Column(Integer, ForeignKey("proposicoes.id", ondelete="CASCADE"),
                                 nullable=True, index=True)
    idOrgao             = Column(Integer, ForeignKey("orgaos.id"), nullable=True, index=True)
    idEvento            = Column(Integer, ForeignKey("eventos.id",  ondelete="SET NULL"), nullable=True)

    data                = Column(Date)
    dataHoraRegistro    = Column(DateTime)

    siglaOrgao          = Column(String(50))
    uriOrgao            = Column(Text)
    uriEvento           = Column(Text)

    aprovacao           = Column(SmallInteger)   # 1 aprovado, 0 rejeitado, -1 indefinido
    votosSim            = Column(Integer)
    votosNao            = Column(Integer)
    votosOutros         = Column(Integer)
    descricao           = Column(Text)

    tipoVotacao         = Column(String(50))
    votosImportados     = Column(Boolean, default=False)
    indexada            = Column(Boolean, default=False)

    # Última abertura da votação
    ultimaAberturaVotacao_dataHoraRegistro = Column(DateTime)
    ultimaAberturaVotacao_descricao        = Column(Text)

    # Última apresentação de proposição associada
    ultimaApresentacaoProposicao_dataHoraRegistro = Column(DateTime)
    ultimaApresentacaoProposicao_descricao        = Column(Text)
    ultimaApresentacaoProposicao_idProposicao     = Column(Integer)
    ultimaApresentacaoProposicao_uriProposicao    = Column(Text)

    createdAt = Column(DateTime, server_default=func.now())

    proposicao  = relationship("Proposicao",  back_populates="votacoes")
    votos       = relationship("Voto",               back_populates="votacao", cascade="all, delete-orphan")
    orientacoes = relationship("VotacaoOrientacao",  back_populates="votacao", cascade="all, delete-orphan")
    objetos     = relationship("VotacaoObjeto",      back_populates="votacao", cascade="all, delete-orphan")


# ===========================================================================
# VOTAÇÕES — VOTOS
# ===========================================================================
class Voto(Base):
    """
    /votacoes/{id}/votos  e  votacoesVotos-2026.csv
    Campos: idVotacao, uriVotacao, dataHoraVoto, voto,
            deputado_id, deputado_uri, deputado_nome, deputado_siglaPartido,
            deputado_uriPartido, deputado_siglaUf, deputado_idLegislatura, deputado_urlFoto
    """
    __tablename__ = "votacoesVotos"

    id           = Column(Integer, primary_key=True)
    idVotacao    = Column(Integer, ForeignKey("votacoes.id",   ondelete="CASCADE"), nullable=False, index=True)
    idDeputado   = Column(Integer, ForeignKey("deputados.id",  ondelete="CASCADE"), nullable=False, index=True)

    dataHoraVoto      = Column(DateTime)
    voto              = Column(String(30))        # Sim, Não, Abstenção, Obstrução, etc.
    siglaPartido      = Column(String(50))
    uriPartido        = Column(Text)
    siglaUF           = Column(CHAR(2))
    idLegislatura     = Column(Integer)

    votacao  = relationship("Votacao",  back_populates="votos")
    deputado = relationship("Deputado", back_populates="votos")

    __table_args__ = (
        UniqueConstraint("idVotacao", "idDeputado", name="uq_voto_votacao_deputado"),
    )


# ===========================================================================
# VOTAÇÕES — ORIENTAÇÕES
# ===========================================================================
class VotacaoOrientacao(Base):
    """
    /votacoes/{id}/orientacoes  e  votacoesOrientacoes-2026.csv
    Campos: idVotacao, uriVotacao, siglaOrgao, descricao,
            siglaBancada, uriBancada, orientacao
    """
    __tablename__ = "votacoesOrientacoes"

    id            = Column(Integer, primary_key=True)
    idVotacao     = Column(Integer, ForeignKey("votacoes.id", ondelete="CASCADE"),
                           nullable=False, index=True)

    siglaOrgao    = Column(String(50))
    siglaBancada  = Column(String(50))
    uriBancada    = Column(Text)
    orientacao    = Column(String(30))    # Sim, Não, Libera, Obstrução

    votacao = relationship("Votacao", back_populates="orientacoes")


# ===========================================================================
# VOTAÇÕES — OBJETOS (proposições votadas)
# ===========================================================================
class VotacaoObjeto(Base):
    """
    /votacoes/{id}/objetos  e  votacoesObjetos-2026.csv
    Campos: idVotacao, uriVotacao, data, descricao,
            proposicao_id, proposicao_uri, proposicao_ementa,
            proposicao_codTipo, proposicao_siglaTipo,
            proposicao_numero, proposicao_ano, proposicao_titulo
    """
    __tablename__ = "votacoesObjetos"

    id                  = Column(Integer, primary_key=True)
    idVotacao           = Column(Integer, ForeignKey("votacoes.id", ondelete="CASCADE"),
                                 nullable=False, index=True)

    data                    = Column(Date)
    descricao               = Column(Text)
    proposicao_id           = Column(Integer, index=True)
    proposicao_uri          = Column(Text)
    proposicao_ementa       = Column(Text)
    proposicao_codTipo      = Column(Integer)
    proposicao_siglaTipo    = Column(String(50))
    proposicao_numero       = Column(Integer)
    proposicao_ano          = Column(Integer)
    proposicao_titulo       = Column(String(200))

    votacao = relationship("Votacao", back_populates="objetos")


# ===========================================================================
# DISCURSOS
# ===========================================================================
class Discurso(Base):
    """
    /deputados/{id}/discursos
    """
    __tablename__ = "discursos"

    id           = Column(Integer, primary_key=True)
    idDeputado   = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    idEvento     = Column(Integer, ForeignKey("eventos.id",   ondelete="SET NULL"),
                          nullable=True, index=True)

    dataHoraInicio   = Column(DateTime, nullable=False)
    dataHoraFim      = Column(DateTime)

    tipoDiscurso      = Column(String(100))
    faseEventoTitulo  = Column(String(255))

    sumario      = Column(Text)
    transcricao  = Column(Text)
    keywords     = Column(Text)

    urlTexto     = Column(Text)
    urlAudio     = Column(Text)
    urlVideo     = Column(Text)

    createdAt    = Column(DateTime, server_default=func.now())

    deputado = relationship("Deputado", back_populates="discursos")
    evento   = relationship("Evento",   back_populates="discursos")


# ===========================================================================
# DESPESAS (CEAP)
# ===========================================================================
# ===========================================================================
# DESPESAS (CEAP — Cota para Exercício da Atividade Parlamentar)
# ===========================================================================
class Despesa(Base):
    """
    Fonte: http://www.camara.leg.br/cotas/Ano-{ano}.csv.zip
    Chave de upsert: codDocumento (ideDocumento no CSV)

    Campos do CSV → modelo:
        nuDeputadoId            → idDeputado   (FK resolvida via idCamara)
        ideDocumento            → codDocumento
        numAno / numMes         → ano / mes
        txtDescricao            → tipoDespesa
        numSubCota              → numSubCota
        numEspecificacaoSubCota → numEspecificacaoSubCota
        indTipoDocumento        → codTipoDocumento
        txtNumero               → numDocumento
        datEmissao              → dataDocumento
        vlrDocumento            → valorDocumento
        vlrGlosa                → valorGlosa
        vlrLiquido              → valorLiquido
        txtFornecedor           → nomeFornecedor
        txtCNPJCPF              → cnpjCpfFornecedor
        urlDocumento            → urlDocumento
        numParcela              → parcela
        numLote                 → codLote
        numRessarcimento        → numRessarcimento
        txtPassageiro           → txPassageiro
        txtTrecho               → txTrecho
    """
    __tablename__ = "despesas"

    id         = Column(Integer, primary_key=True)
    idDeputado = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    # Chave de deduplicação — ideDocumento no CSV
    codDocumento      = Column(String(100), nullable=False, unique=True, index=True)

    # Período
    ano               = Column(Integer,     nullable=False, index=True)
    mes               = Column(Integer,     nullable=False, index=True)
    dataDocumento     = Column(DateTime)

    # Classificação da despesa
    tipoDespesa            = Column(Text)
    numSubCota             = Column(Integer)        # código da subcota (ex: 1 = escritório)
    numEspecificacaoSubCota = Column(Integer)       # especificação dentro da subcota

    # Documento fiscal
    codTipoDocumento  = Column(Integer)             # indTipoDocumento no CSV
    numDocumento      = Column(String(150))
    urlDocumento      = Column(Text)

    # Fornecedor
    nomeFornecedor    = Column(Text)
    cnpjCpfFornecedor = Column(String(20), index=True)

    # Valores
    valorDocumento    = Column(Numeric(12, 2))
    valorGlosa        = Column(Numeric(12, 2))
    valorLiquido      = Column(Numeric(12, 2))

    # Controle de lote / ressarcimento
    parcela           = Column(Integer,     default=0)
    codLote           = Column(Integer)
    numRessarcimento  = Column(String(100))

    # Passagens aéreas (preenchido apenas quando tipoDespesa = passagem)
    txPassageiro      = Column(Text)
    txTrecho          = Column(Text)

    createdAt         = Column(DateTime, server_default=func.now())

    deputado = relationship("Deputado", back_populates="despesas")


# Índice composto para consultas por deputado + período (já declarado no final do arquivo)
# Index("ix_despesas_dep_ano_mes", Despesa.idDeputado, Despesa.ano, Despesa.mes)

# ===========================================================================
# FRENTES PARLAMENTARES
# ===========================================================================
class Frente(Base):
    """
    /frentes  e  frentes.csv
    Campos: id, uri, titulo, dataCriacao, idLegislatura, telefone, email,
            keywords, idSituacao, situacao, urlWebsite, urlDocumento,
            coordenador_id, coordenador_uri, coordenador_nome,
            coordenador_siglaPartido, coordenador_uriPartido,
            coordenador_siglaUf, coordenador_idLegislatura, coordenador_urlFoto
    """
    __tablename__ = "frentes"

    id            = Column(Integer, primary_key=True)
    idCamara      = Column(Integer, nullable=False, unique=True, index=True)
    uri           = Column(Text, unique=True)

    titulo        = Column(Text)
    dataCriacao   = Column(Date)
    idLegislatura = Column(Integer, ForeignKey("legislaturas.idLegislatura"), nullable=True)

    telefone      = Column(String(30))
    email         = Column(String(200))
    keywords      = Column(Text)

    idSituacao    = Column(Integer)
    situacao      = Column(Text)
    urlWebsite    = Column(Text)
    urlDocumento  = Column(Text)

    # Coordenador
    coordenador_id            = Column(Integer, ForeignKey("deputados.id", ondelete="SET NULL"), nullable=True)
    coordenador_uri           = Column(Text)
    coordenador_nome          = Column(Text)
    coordenador_siglaPartido  = Column(String(50))
    coordenador_uriPartido    = Column(Text)
    coordenador_siglaUf       = Column(CHAR(2))
    coordenador_idLegislatura = Column(Integer)
    coordenador_urlFoto       = Column(Text)

    membros = relationship("FrenteDeputado", back_populates="frente",
                           cascade="all, delete-orphan")


class FrenteDeputado(Base):
    """
    /frentes/{id}/membros  e  frentesDeputados.csv
    Campos: id (frente), uri, titulo, deputado_.id, deputado_.uri, etc.
            dataInicio, dataFim
    """
    __tablename__ = "frentesDeputados"

    id          = Column(Integer, primary_key=True)
    idFrente    = Column(Integer, ForeignKey("frentes.id",    ondelete="CASCADE"), nullable=False, index=True)
    idDeputado  = Column(Integer, ForeignKey("deputados.id",  ondelete="CASCADE"), nullable=True,  index=True)

    uriDeputado  = Column(Text)
    uriPartido   = Column(Text)
    nomeDeputado = Column(String(200))
    siglaUf      = Column(CHAR(2))
    idLegislatura = Column(Integer)
    urlFoto      = Column(Text)
    codTitulo    = Column(Integer)
    titulo       = Column(String(100))

    dataInicio   = Column(Date)
    dataFim      = Column(Date)

    frente   = relationship("Frente",   back_populates="membros")
    deputado = relationship("Deputado", back_populates="frentes")

    __table_args__ = (
        UniqueConstraint("idFrente", "idDeputado", name="uq_frente_deputado"),
    )


# ===========================================================================
# GRUPOS PARLAMENTARES
# ===========================================================================
class Grupo(Base):
    """
    /grupos  e  grupos.csv
    Campos: idGrupo, uriGrupo, nomeGrupo, anoCriacao, projetoTitulo,
            projetoUri, resolucaoTitulo, resolucaoUri, subvencionado,
            grupoMisto, ativo, observacao + ultimoStatus_*
    """
    __tablename__ = "grupos"

    id          = Column(Integer, primary_key=True)
    idCamara    = Column(Integer, nullable=False, unique=True, index=True)
    uri         = Column(Text, unique=True)

    nomeGrupo       = Column(String(200))
    anoCriacao      = Column(Integer)
    projetoTitulo   = Column(String(100))
    projetoUri      = Column(Text)
    resolucaoTitulo = Column(String(100))
    resolucaoUri    = Column(Text)

    subvencionado   = Column(Boolean)
    grupoMisto      = Column(Boolean)
    ativo           = Column(Boolean, index=True)
    observacao      = Column(Text)

    # Último status
    ultimoStatus_idLegislatura           = Column(Integer)
    ultimoStatus_dataStatus              = Column(DateTime)
    ultimoStatus_presidenteNome          = Column(String(200))
    ultimoStatus_presidenteUri           = Column(Text)
    ultimoStatus_documento               = Column(String(100))
    ultimoStatus_oficioTitulo            = Column(String(200))
    ultimoStatus_oficioUri               = Column(Text)
    ultimoStatus_oficioAutorTipo         = Column(String(50))
    ultimoStatus_oficioAutorNome         = Column(String(200))
    ultimoStatus_oficioAutorUri          = Column(Text)
    ultimoStatus_oficioDataApresentacao  = Column(DateTime)
    ultimoStatus_oficioDataPublicacao    = Column(DateTime)

    membros   = relationship("GrupoMembro",    back_populates="grupo", cascade="all, delete-orphan")
    historico = relationship("GrupoHistorico", back_populates="grupo", cascade="all, delete-orphan")


class GrupoMembro(Base):
    """
    /grupos/{id}/membros  e  gruposMembros.csv
    Campos: idGrupo, uriGrupo, nomeGrupo, membro_idlegislatura,
            membro_ordem_entrada, membro_datainicio, membro_datafim,
            membro_nome, membro_tipo, membro_uri, membro_cargo
    """
    __tablename__ = "gruposMembros"

    id            = Column(Integer, primary_key=True)
    idGrupo       = Column(Integer, ForeignKey("grupos.id",    ondelete="CASCADE"), nullable=False, index=True)
    idDeputado    = Column(Integer, ForeignKey("deputados.id", ondelete="CASCADE"), nullable=True,  index=True)

    idLegislatura = Column(Integer)
    ordemEntrada  = Column(Integer)
    dataInicio    = Column(DateTime)
    dataFim       = Column(DateTime)
    nome          = Column(String(200))
    tipo          = Column(String(50))
    uri           = Column(Text)
    cargo         = Column(String(100))

    grupo    = relationship("Grupo",    back_populates="membros")
    deputado = relationship("Deputado", back_populates="gruposMembros")

    __table_args__ = (
        UniqueConstraint("idGrupo", "idDeputado", name="uq_grupo_membro"),
    )


class GrupoHistorico(Base):
    """
    /grupos/{id}/historico  e  gruposHistorico.csv
    Campos: id, uri, nome, idLegislatura, dataStatus, documentoSgm,
            presidente, presidenteUri, observacao,
            oficioTitulo, oficioAutorTipo, oficioAutor, oficioAutorUri,
            oficioDataApresentacao, oficioDataPublicacao
    """
    __tablename__ = "gruposHistorico"

    id            = Column(Integer, primary_key=True)
    idGrupo       = Column(Integer, ForeignKey("grupos.id", ondelete="CASCADE"), nullable=False, index=True)
    idLegislatura = Column(Integer)

    dataStatus              = Column(DateTime)
    documentoSgm            = Column(String(100))
    presidente              = Column(String(200))
    presidenteUri           = Column(Text)
    observacao              = Column(Text)
    oficioTitulo            = Column(String(200))
    oficioAutorTipo         = Column(Text)
    oficioAutor             = Column(String(200))
    oficioAutorUri          = Column(Text)
    oficioDataApresentacao  = Column(DateTime)
    oficioDataPublicacao    = Column(DateTime)

    grupo = relationship("Grupo", back_populates="historico")


# ===========================================================================
# FUNCIONÁRIOS (servidores da Câmara)
# ===========================================================================
class Funcionario(Base):
    """
    /funcionarios  e  funcionarios.csv
    Campos: ponto, codGrupo, grupo, nome, cargo, lotacao,
            atoNomeacao, dataNomeacao, dataInicioHistorico,
            dataPubNomeacao, funcao, uriLotacao
    """
    __tablename__ = "funcionarios"

    id                 = Column(Integer, primary_key=True)
    ponto              = Column(String(20), nullable=False, unique=True, index=True)
    codGrupo           = Column(Integer)
    grupo              = Column(String(100))
    nome               = Column(String(200), nullable=False, index=True)
    cargo              = Column(String(200))
    lotacao            = Column(String(300))
    atoNomeacao        = Column(String(100))
    dataNomeacao       = Column(Date)
    dataInicioHistorico = Column(Date)
    dataPubNomeacao    = Column(Date)
    funcao             = Column(String(200))
    uriLotacao         = Column(Text)


# ===========================================================================
# LICITAÇÕES
# ===========================================================================
class Licitacao(Base):
    """
    /licitacoes  e  licitacoes-2026.csv
    Campos: idLicitacao, numero, ano, numProcesso, anoProcesso, objeto,
            modalidade, tipo, situacao, vlrEstimado, vlrContratado, vlrPago,
            dataAutorizacao, dataPublicacao, dataAbertura,
            numItens, numUnidades, numPropostas, numContratos
    """
    __tablename__ = "licitacoes"

    id              = Column(Integer, primary_key=True)
    idLicitacao     = Column(Integer, nullable=False, unique=True, index=True)
    numero          = Column(Integer)
    ano             = Column(Integer, index=True)
    numProcesso     = Column(Integer)
    anoProcesso     = Column(Integer)

    objeto          = Column(Text)
    modalidade      = Column(String(100))
    tipo            = Column(String(100))
    situacao        = Column(String(100))

    vlrEstimado     = Column(Numeric(15, 2))
    vlrContratado   = Column(Numeric(15, 2))
    vlrPago         = Column(Numeric(15, 2))

    dataAutorizacao = Column(Date)
    dataPublicacao  = Column(Date)
    dataAbertura    = Column(Date)

    numItens        = Column(Integer)
    numUnidades     = Column(Integer)
    numPropostas    = Column(Integer)
    numContratos    = Column(Integer)

    pedidos    = relationship("LicitacaoPedido",   back_populates="licitacao", cascade="all, delete-orphan")
    propostas  = relationship("LicitacaoProposta", back_populates="licitacao", cascade="all, delete-orphan")
    itens      = relationship("LicitacaoItem",     back_populates="licitacao", cascade="all, delete-orphan")
    contratos  = relationship("LicitacaoContrato", back_populates="licitacao", cascade="all, delete-orphan")


class LicitacaoPedido(Base):
    """
    licitacoesPedidos-2026.csv
    Campos: ano, idLicitacao, tipoRegistro, numPedido, anoPedido,
            dataHoraCadastro, idOrgao, orgao, objeto, observacoes
    """
    __tablename__ = "licitacoesPedidos"

    id              = Column(Integer, primary_key=True)
    idLicitacao     = Column(Integer, ForeignKey("licitacoes.idLicitacao", ondelete="CASCADE"),
                             nullable=False, index=True)
    ano             = Column(Integer, index=True)
    tipoRegistro    = Column(String(50))
    numPedido       = Column(Integer)
    anoPedido       = Column(Integer)
    dataHoraCadastro = Column(DateTime)
    idOrgao         = Column(Integer)
    orgao           = Column(String(300))
    objeto          = Column(Text)
    observacoes     = Column(Text)

    licitacao = relationship("Licitacao", back_populates="pedidos")


class LicitacaoProposta(Base):
    """
    licitacoesPropostas-2026.csv
    Campos: ano, idLicitacao, numItem, descricao, numSubitens,
            unidadesLicitadas, vlrEstimado, unidadesProposta, vlrProposta,
            numProposta, marcaProposta, fornecedorCpfCnpj, fornecedorSituacao,
            dataProposta, diasValidadeProposta, observacoes, urlDocumento
    """
    __tablename__ = "licitacoesPropostas"

    id                   = Column(Integer, primary_key=True)
    idLicitacao          = Column(Integer, ForeignKey("licitacoes.idLicitacao", ondelete="CASCADE"),
                                  nullable=False, index=True)
    ano                  = Column(Integer)
    numItem              = Column(Integer)
    descricao            = Column(Text)
    numSubitens          = Column(Integer)
    unidadesLicitadas    = Column(Numeric(15, 4))
    vlrEstimado          = Column(Numeric(15, 2))
    unidadesProposta     = Column(Numeric(15, 4))
    vlrProposta          = Column(Numeric(15, 2))
    numProposta          = Column(Integer)
    marcaProposta        = Column(String(200))
    fornecedorCpfCnpj    = Column(String(20), index=True)
    fornecedorSituacao   = Column(String(50))
    dataProposta         = Column(Date)
    diasValidadeProposta = Column(Integer)
    observacoes          = Column(Text)
    urlDocumento         = Column(Text)

    licitacao = relationship("Licitacao", back_populates="propostas")


class LicitacaoItem(Base):
    """
    licitacoesItens-2026.csv
    Campos: ano, idLicitacao, numItem, numSubitem, descricao, especificacao,
            unidade, qtdLicitada, vlrUnitarioEstimado, qtdContratada,
            vlrUnitarioContratado, vlrTotalContratado, fornecedorCpfCnpj,
            fornecedorNome, uriContrato, numContrato, anoContrato, tipoContrato,
            situacaoItem, observacoes, naturezaDespesa, programaTrabalho, codPTRES
    """
    __tablename__ = "licitacoesItens"

    id                    = Column(Integer, primary_key=True)
    idLicitacao           = Column(Integer, ForeignKey("licitacoes.idLicitacao", ondelete="CASCADE"),
                                   nullable=False, index=True)
    ano                   = Column(Integer)
    numItem               = Column(Integer)
    numSubitem            = Column(Integer)
    descricao             = Column(Text)
    especificacao         = Column(Text)
    unidade               = Column(String(50))

    qtdLicitada           = Column(Numeric(15, 4))
    vlrUnitarioEstimado   = Column(Numeric(15, 2))
    qtdContratada         = Column(Numeric(15, 4))
    vlrUnitarioContratado = Column(Numeric(15, 2))
    vlrTotalContratado    = Column(Numeric(15, 2))

    fornecedorCpfCnpj     = Column(String(20), index=True)
    fornecedorNome        = Column(Text)
    uriContrato           = Column(Text)
    numContrato           = Column(Integer)
    anoContrato           = Column(Integer)
    tipoContrato          = Column(String(50))
    situacaoItem          = Column(String(50))
    observacoes           = Column(Text)

    naturezaDespesa       = Column(String(100))
    programaTrabalho      = Column(String(100))
    codPTRES              = Column(String(50))

    licitacao = relationship("Licitacao", back_populates="itens")


class LicitacaoContrato(Base):
    """
    licitacoesContratos-2026.csv
    Campos: ano, idLicitacao, numContrato, anoContrato, tipoContrato,
            situacaoContrato, vlrOriginal, vlrTotal, objeto,
            dataAssinatura, dataPublicacao, dataInicioVigenciaOriginal,
            dataFimVigenciaOriginal, dataFimUltimaVigencia,
            fornecedorCpfCnpj, fornecedorNome, fornecedorEndereco,
            fornecedorCidade, fornecedorSiglaUF,
            numSeqArquivoInstrContratual, txtNomeArquivo
    """
    __tablename__ = "licitacoesContratos"

    id                          = Column(Integer, primary_key=True)
    idLicitacao                 = Column(Integer, ForeignKey("licitacoes.idLicitacao", ondelete="CASCADE"),
                                         nullable=False, index=True)
    ano                         = Column(Integer)
    numContrato                 = Column(Integer)
    anoContrato                 = Column(Integer)
    tipoContrato                = Column(String(50))
    situacaoContrato            = Column(String(50))

    vlrOriginal                 = Column(Numeric(15, 2))
    vlrTotal                    = Column(Numeric(15, 2))
    objeto                      = Column(Text)

    dataAssinatura              = Column(Date)
    dataPublicacao              = Column(Date)
    dataInicioVigenciaOriginal  = Column(Date)
    dataFimVigenciaOriginal     = Column(Date)
    dataFimUltimaVigencia       = Column(Date)

    fornecedorCpfCnpj           = Column(String(20), index=True)
    fornecedorNome              = Column(Text)
    fornecedorEndereco          = Column(Text)
    fornecedorCidade            = Column(String(100))
    fornecedorSiglaUF           = Column(CHAR(2))

    numSeqArquivoInstrContratual = Column(Integer)
    txtNomeArquivo               = Column(String(300))

    licitacao = relationship("Licitacao", back_populates="contratos")


# ===========================================================================
# TECAD — CATEGORIAS E TERMOS (Tesauro)
# ===========================================================================
class TecadCategoria(Base):
    """
    tecadCategorias.csv
    Campos: codCategoria, categoria, codSubCategoria, subCategoria
    """
    __tablename__ = "tecadCategorias"

    id             = Column(Integer, primary_key=True)
    codCategoria   = Column(Integer, index=True)
    categoria      = Column(String(200))
    codSubCategoria = Column(Integer, index=True)
    subCategoria   = Column(String(200))

    __table_args__ = (
        UniqueConstraint("codCategoria", "codSubCategoria", name="uq_tecad_cat_subcat"),
    )


class TecadTermo(Base):
    """
    tecadTermos.csv
    Campos: codTermo, termo, categorias, subcategorias,
            notasExplicativas, notasHistoricas, notasAplicativas, fontes,
            use, usadoPara, termosEspecificos, termosGenericos, termosRelacionados
    """
    __tablename__ = "tecadTermos"

    id                 = Column(Integer, primary_key=True)
    codTermo           = Column(Integer, unique=True, index=True)
    termo              = Column(Text, index=True)
    categorias         = Column(Text)
    subcategorias      = Column(Text)
    notasExplicativas  = Column(Text)
    notasHistoricas    = Column(Text)
    notasAplicativas   = Column(Text)
    fontes             = Column(Text)
    use                = Column(Text)
    usadoPara          = Column(Text)
    termosEspecificos  = Column(Text)
    termosGenericos    = Column(Text)
    termosRelacionados = Column(Text)


# ===========================================================================
# VERBA DE GABINETE
# ===========================================================================
class VerbaGabinete(Base):
    __tablename__ = "verbasGabinete"

    id              = Column(Integer, primary_key=True, index=True)
    idDeputado      = Column(Integer, ForeignKey("deputados.id"), index=True)
    idCamara        = Column(Integer, index=True)
    ano             = Column(Integer, index=True)
    mes             = Column(Integer, index=True)
    valorDisponivel = Column(Numeric(12, 2))
    valorGasto      = Column(Numeric(12, 2))


# ===========================================================================
# BUSCA POPULAR (tabela auxiliar de produto)
# ===========================================================================
class BuscaPopular(Base):
    __tablename__ = "buscaPopular"

    id         = Column(Integer, primary_key=True, index=True)
    idDeputado = Column(Integer, ForeignKey("deputados.id"), nullable=False, unique=True)
    count      = Column(Integer, default=1, nullable=False)
    updatedAt  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", back_populates="buscaPopular")


# ===========================================================================
# ÍNDICES COMPOSTOS ADICIONAIS
# ===========================================================================
Index("ix_proposicoes_tipo_ano",  Proposicao.siglaTipo, Proposicao.ano)
Index("ix_votacoes_data_orgao",   Votacao.data, Votacao.siglaOrgao)
Index("ix_despesas_dep_ano_mes",  Despesa.idDeputado, Despesa.ano, Despesa.mes)
Index("ix_tramitacoes_prop_seq",  Tramitacao.idProposicao, Tramitacao.sequencia)
Index("ix_licitacoes_ano_sit",    Licitacao.ano, Licitacao.situacao)