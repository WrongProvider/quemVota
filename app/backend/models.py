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
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    partido_sigla = Column(String(30))
    situacao = Column(String(50))
    condicao_eleitoral = Column(String(50))

    # Contatos
    email = Column(String(150))
    telefone_gabinete = Column(String(30))
    email_gabinete = Column(String(150))

    # Outros
    url_foto = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Novo vínculo: FK para o partido atual
    partido_id = Column(Integer, ForeignKey("partidos.id", ondelete="SET NULL"), nullable=True)
    partido_sigla = Column(String(10)) # Mantemos a sigla para consultas rápidas/cache

    # Relationships
    partido = relationship("Partido", back_populates="politicos")
    
    # Histórico (já existente no seu código)
    historico_partidos = relationship("PartidoMembro", back_populates="politico")

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
    politico_id = Column(Integer, ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Identificadores oficiais
    # Mudamos para String(100) para garantir e adicionamos unique direto aqui
    cod_documento = Column(String(100), nullable=False, index=True, unique=True)
    cod_lote = Column(Integer)

    # Tempo
    ano = Column(Integer, nullable=False, index=True)
    mes = Column(Integer, nullable=False, index=True)
    data_documento = Column(Date)

    # Classificação - Usando Text para evitar erros de String too long
    tipo_despesa = Column(Text)
    tipo_documento = Column(String(150))
    cod_tipo_documento = Column(Integer)

    # Documento
    num_documento = Column(String(150))
    url_documento = Column(Text)

    # Fornecedor
    nome_fornecedor = Column(Text) # Fornecedores podem ter nomes gigantes
    cnpj_cpf_fornecedor = Column(String(20), index=True)

    # Valores
    valor_documento = Column(Numeric(12, 2))
    valor_liquido = Column(Numeric(12, 2))
    valor_glosa = Column(Numeric(12, 2))

    # Outros
    parcela = Column(Integer, nullable=True, default=0)
    num_ressarcimento = Column(String(100), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Se usar back_populates, lembre de adicionar no model Politico!
    politico = relationship("Politico", back_populates="despesas")

    # Removi a __table_args__ porque coloquei unique=True no cod_documento
    # Se cod_documento for 0 na API, seu código de ingestão deve dar 'continue'
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

    created_at = Column(DateTime, server_default=func.now())

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
    created_at = Column(DateTime, server_default=func.now())

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
    id_camara = Column(Integer, unique=True, nullable=False, index=True)
    uri = Column(Text, unique=True)

    sigla = Column(String(20))
    nome = Column(Text)
    apelido = Column(Text)
    nome_publicacao = Column(Text)
    nome_resumido = Column(Text)

    cod_tipo_orgao = Column(Integer)
    tipo_orgao = Column(String(100))
    casa = Column(String(50))

    data_inicio = Column(Date)
    data_fim = Column(Date)
    data_instalacao = Column(Date)

    sala = Column(String(50))
    url_website = Column(Text)

    eventos = relationship(
        "Evento",
        secondary="eventos_orgaos",
        back_populates="orgaos"
    )

    membros = relationship("OrgaoMembro", back_populates="orgao")


eventos_orgaos = Table(
    "eventos_orgaos",
    Base.metadata,
    Column("evento_id", Integer, ForeignKey("eventos.id"), primary_key=True),
    Column("orgao_id", Integer, ForeignKey("orgaos.id"), primary_key=True),
)

class OrgaoMembro(Base):
    __tablename__ = "orgaos_membros"

    id = Column(Integer, primary_key=True)

    orgao_id = Column(Integer, ForeignKey("orgaos.id", ondelete="CASCADE"), nullable=False, index=True)
    politico_id = Column(Integer, ForeignKey("politicos.id", ondelete="CASCADE"))

    cod_titulo = Column(Integer)
    titulo = Column(String(100))

    data_inicio = Column(Date)
    data_fim = Column(Date)

    orgao = relationship("Orgao", back_populates="membros")
    politico = relationship("Politico")
    
    __table_args__ = (
        UniqueConstraint(
            "orgao_id",
            "politico_id",
            name="uq_orgao_orgao_politico"
    ),
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

    created_at = Column(DateTime, server_default=func.now())

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
    politico_id = Column(
        Integer,
        ForeignKey("politicos.id", ondelete="SET NULL"),
        nullable=True
    )

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

class Votacao(Base):
    __tablename__ = "votacoes"

    id = Column(Integer, primary_key=True)
  # id vem como string da API
    id_camara = Column(String(50), unique=True, index=True)

    proposicao_id = Column(Integer, ForeignKey("proposicoes.id", ondelete="SET NULL"), nullable=True)
    
    data = Column(Date)
    data_hora_registro = Column(DateTime)

    tipo_votacao = Column(String(50)) # Ex: "Nominal" ou "Simbólica"
    descricao = Column(Text)
    aprovacao = Column(Integer)  # 1 aprovado, 0 rejeitado, -1 indefinido
    votos_importados = Column(Boolean, default=False)
    indexada = Column(Boolean, default=False)
    sigla_orgao = Column(String(20))

    evento_id = Column(Integer, ForeignKey("eventos.id", ondelete="SET NULL"), nullable=True)
    # Relacionamento com Órgão (Quem realizou a votação)
    orgao_id = Column(Integer, ForeignKey("orgaos.id"), nullable=True)

    uri = Column(Text)
    uri_evento = Column(Text)
    uri_orgao = Column(Text)

    # Relacionamentos
    votos = relationship("Voto", back_populates="votacao")
    orientacoes = relationship("OrientacaoVotacao", back_populates="votacao")

    created_at = Column(DateTime, server_default=func.now())

class OrientacaoVotacao(Base):
    __tablename__ = "orientacoes_votacao"

    id = Column(Integer, primary_key=True)
    votacao_id = Column(
        Integer,
        ForeignKey("votacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )


    cod_partido_bloco = Column(Integer)
    sigla_partido_bloco = Column(String(20))
    cod_tipo_lideranca = Column(String(50))

    orientacao_voto = Column(String(20))  # Sim, Não, Libera, Obstrução

    uri_partido_bloco = Column(Text)

    votacao = relationship("Votacao", back_populates="orientacoes")

class Voto(Base):
    __tablename__ = "votos"

    id = Column(Integer, primary_key=True)

    votacao_id = Column(
        Integer,
        ForeignKey("votacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    politico_id = Column(
        Integer, 
        ForeignKey("politicos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    tipo_voto = Column(String(20))  
    # Sim, Não, Abstenção, Obstrução, Art. 17, etc.

    data_registro_voto = Column(DateTime)

    sigla_partido = Column(String(30))
    sigla_uf = Column(String(2))

    votacao = relationship("Votacao", back_populates="votos")

    __table_args__ = (
    UniqueConstraint(
        "votacao_id",
        "politico_id",
        name="uq_voto_votacao_politico"
    ),
)


class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True)
    id_camara = Column(Integer, nullable=False, unique=True, index=True)
    uri = Column(Text, unique=True)

    nome = Column(String(200), nullable=False)
    sigla = Column(String(20), nullable=False)
    numero_eleitoral = Column(Integer)

    situacao = Column(String(100))
    total_membros = Column(Integer)
    total_posse = Column(Integer)

    url_facebook = Column(Text)
    url_logo = Column(Text)
    url_website = Column(Text)

    membros = relationship("PartidoMembro", back_populates="partido")
    lideres = relationship("PartidoLider", back_populates="partido")
    politicos = relationship("Politico", back_populates="partido")


class PartidoMembro(Base):
    __tablename__ = "partidos_membros"

    id = Column(Integer, primary_key=True)

    partido_id = Column(
        Integer,
        ForeignKey("partidos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    politico_id = Column(Integer, ForeignKey("politicos.id", ondelete="CASCADE"))

    data_inicio = Column(Date)
    data_fim = Column(Date)

    partido = relationship("Partido", back_populates="membros")
    politico = relationship("Politico")

    __table_args__ = (
    UniqueConstraint(
        "partido_id",
        "politico_id",
        name="uq_partido_partido_politico"
    ),
)


class PartidoLider(Base):
    __tablename__ = "partidos_lideres"

    id = Column(Integer, primary_key=True)

    partido_id = Column(Integer, ForeignKey("partidos.id", ondelete="CASCADE"), nullable=False, index=True)
    politico_id = Column(Integer, ForeignKey("politicos.id", ondelete="CASCADE"))

    cod_titulo = Column(Integer)
    titulo = Column(String(100))

    data_inicio = Column(Date)
    data_fim = Column(Date)

    partido = relationship("Partido", back_populates="lideres")
    politico = relationship("Politico")
