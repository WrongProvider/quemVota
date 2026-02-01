from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    Text,
    CHAR,
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
        backref="politico",
        cascade="all, delete-orphan"
    )

class Despesa(Base):
    __tablename__ = "despesas"

    id = Column(Integer, primary_key=True)

    # Relacionamento
    politico_id = Column(Integer, ForeignKey("politicos.id"), nullable=False, index=True)

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

