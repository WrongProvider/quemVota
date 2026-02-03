from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    Text,
    CHAR,
    DateTime,
    UniqueConstraint,
    Table,
    ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base

class Politico(Base):
    __tablename__ = "politicos"

    id = Column(Integer, primary_key=True)
    # Identificação
    id_camara = Column(Integer, nullable=False, unique=True, index=True)
    nome = Column(String(150), nullable=False, index=True)
    nome_civil = Column(String(150))

    # Dados pessoais
    sexo = Column(CHAR(1))
    data_nascimento = Column(Date)
    escolaridade = Column(String(100))
    uf = Column(CHAR(2))
    uf_nascimento = Column(CHAR(2))
    municipio_nascimento = Column(String(100))

    # Dados políticos / institucionais
    partido_sigla = Column(String(10))
    situacao = Column(String(50))
    condicao_eleitoral = Column(String(50))

    # Contatos
    email = Column(String(150))
    telefone_gabinete = Column(String(30))
    email_gabinete = Column(String(150))

    # Outros
    url_foto = Column(Text)

    despesas = relationship(
        "Despesa",
        back_populates="politico",
        cascade="all, delete-orphan"
    )
    discursos = relationship(
        "Discurso",
        back_populates="politico",
        cascade="all, delete-orphan"
    )

class Despesa(Base):
    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True)

    # Relacionamento
    politico_id = Column(Integer, ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identificadores oficiais
    cod_documento = Column(Integer, nullable=False)
    cod_lote = Column(Integer)


    # Tempo
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    data_documento = Column(Date)

    # Classificação
    tipo_despesa = Column(String(200))
    tipo_documento = Column(String(50))
    cod_tipo_documento = Column(Integer)

    # Documento
    num_documento = Column(String(50))
    url_documento = Column(Text)

    # Fornecedor
    nome_fornecedor = Column(String(200))
    cnpj_cpf_fornecedor = Column(String(20))

    # Valores
    valor_documento = Column(Numeric(12, 2))
    valor_liquido = Column(Numeric(12, 2))
    valor_glosa = Column(Numeric(12, 2))

    # Outros
    num_ressarcimento = Column(String(50))
    parcela = Column(Integer)

    created_at = Column(Date)

    __table_args__ = (
    UniqueConstraint(
        "politico_id",
        "cod_documento",
        name="uq_despesa_politico_documento"
    ),
    )

class Discurso(Base):
    __tablename__ = "discursos"

    id = Column(Integer, primary_key=True)

    # Relacionamento
    politico_id = Column(Integer, 
        ForeignKey("politicos.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True)
    evento_id = Column(
        Integer,
        ForeignKey("eventos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    # Tempo
    data_hora_inicio = Column(DateTime, nullable=False)
    data_hora_fim = Column(DateTime)

    # Evento / contexto
    tipo_discurso = Column(String(100))
    fase_evento_titulo = Column(String(255))

    # Conteúdo
    sumario = Column(Text)
    transcricao = Column(Text)
    keywords = Column(Text)

    # Links
    url_texto = Column(Text)
    url_audio = Column(Text)
    url_video = Column(Text)
    # Back evento
    politico = relationship("Politico", back_populates="discursos")
    evento = relationship("Evento", back_populates="discursos")

    created_at = Column(DateTime)

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True)
    id_camara = Column(Integer, unique=True, index=True, nullable=False)
    uri = Column(Text, unique=True, index=True)

    data_hora_inicio = Column(DateTime)
    data_hora_fim = Column(DateTime)
    situacao = Column(String)
    descricao_tipo = Column(String)
    descricao = Column(Text)

    local_externo = Column(Text)
    local_camara_nome = Column(String)
    local_camara_predio = Column(String)
    local_camara_sala = Column(String)
    local_camara_andar = Column(String)

    url_evento = Column(Text)
    created_at = Column(DateTime)

    orgaos = relationship(
        "Orgao",
        secondary="eventos_orgaos",
        back_populates="eventos"
    )

    discursos = relationship(
        "Discurso",
        back_populates="evento"
    )

class Orgao(Base):
    __tablename__ = "orgaos"

    id = Column(Integer, primary_key=True)

    # Identificação oficial
    id_camara = Column(Integer, nullable=False, unique=True, index=True)
    uri = Column(Text)

    sigla = Column(String(20))
    nome = Column(String(150))
    apelido = Column(String(150))

    cod_tipo_orgao = Column(Integer)
    tipo_orgao = Column(String(100))

    nome_publicacao = Column(String(150))
    nome_resumido = Column(String(150))

    eventos = relationship(
        "Evento",
        secondary="eventos_orgaos",
        back_populates="orgaos"
    )

eventos_orgaos = Table(
    "eventos_orgaos",
    Base.metadata,
    Column("evento_id", Integer, ForeignKey("eventos.id"), primary_key=True),
    Column("orgao_id", Integer, ForeignKey("orgaos.id"), primary_key=True),
)


class Proposicao(Base):
    __tablename__ = "proposicoes"

    id = Column(Integer, primary_key=True)
    id_camara = Column(Integer, unique=True, index=True, nullable=False)
    uri = Column(Text, unique=True, index=True)

    # Identificação
    sigla_tipo = Column(String(10), index=True)
    cod_tipo = Column(Integer)
    numero = Column(Integer, index=True)
    ano = Column(Integer, index=True)
    descricao_tipo = Column(String(100))

    # Conteúdo
    ementa = Column(Text)
    ementa_detalhada = Column(Text)
    keywords = Column(Text)
    justificativa = Column(Text)

    # Datas
    data_apresentacao = Column(DateTime)

    # Links
    url_inteiro_teor = Column(Text)
    urn_final = Column(String(100))

    # Relacionamentos
    autores = relationship(
        "ProposicaoAutor",
        back_populates="proposicao",
        cascade="all, delete-orphan"
    )

    temas = relationship(
        "Tema",
        secondary="proposicoes_temas",
        back_populates="proposicoes"
    )

    tramitacoes = relationship(
        "Tramitacao",
        back_populates="proposicao",
        cascade="all, delete-orphan",
        order_by="Tramitacao.data_hora"
    )

    created_at = Column(DateTime)

class ProposicaoAutor(Base):
    __tablename__ = "proposicoes_autores"

    id = Column(Integer, primary_key=True)

    proposicao_id = Column(
        Integer,
        ForeignKey("proposicoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Autor (pode ser deputado, comissão, etc.)
    nome = Column(String(150), nullable=False)
    uri_autor = Column(Text)
    cod_tipo = Column(Integer)
    tipo = Column(String(50))

    ordem_assinatura = Column(Integer)
    proponente = Column(Boolean)

    proposicao = relationship("Proposicao", back_populates="autores")

class Tema(Base):
    __tablename__ = "temas"

    id = Column(Integer, primary_key=True)
    cod_tema = Column(Integer, unique=True, index=True)
    tema = Column(String(150), index=True)

    proposicoes = relationship(
        "Proposicao",
        secondary="proposicoes_temas",
        back_populates="temas"
    )

proposicoes_temas = Table(
    "proposicoes_temas",
    Base.metadata,
    Column("proposicao_id", Integer, ForeignKey("proposicoes.id"), primary_key=True),
    Column("tema_id", Integer, ForeignKey("temas.id"), primary_key=True),
)

class Tramitacao(Base):
    __tablename__ = "tramitacoes"

    id = Column(Integer, primary_key=True)

    proposicao_id = Column(
        Integer,
        ForeignKey("proposicoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    data_hora = Column(DateTime, index=True)
    sequencia = Column(Integer)

    sigla_orgao = Column(String(20))
    uri_orgao = Column(Text)
    uri_ultimo_relator = Column(Text)

    regime = Column(String(150))
    descricao_tramitacao = Column(String(200))
    cod_tipo_tramitacao = Column(Integer)

    descricao_situacao = Column(String(150))
    cod_situacao = Column(Integer)

    despacho = Column(Text)
    url = Column(Text)
    ambito = Column(String(50))
    apreciacao = Column(String(150))

    proposicao = relationship("Proposicao", back_populates="tramitacoes")
