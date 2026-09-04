"""
models_vetorial.py — Camada de persistência para embeddings e features de IA.

Suporta specs 001–005 (temas, marcos, similaridade, resumo, impacto).
Compatível com pgvector e futura projeção no Apache AGE.
"""

import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.config import settings
from shared.database import Base
import shared.models  # noqa: F401 (Registra classes relacionais como Deputado)

EMBEDDING_DIM = settings.EMBEDDING_DIMENSION


class TipoEntidadeDocumento(str, enum.Enum):
    proposicao = "proposicao"
    discurso = "discurso"
    evento = "evento"
    tramitacao = "tramitacao"
    relatoria = "relatoria"


class TipoParticipacao(str, enum.Enum):
    autoria = "autoria"
    coautoria = "coautoria"
    relatoria = "relatoria"
    discurso = "discurso"
    evento = "evento"


class TipoMarco(str, enum.Enum):
    proposicao = "proposicao"
    relatoria = "relatoria"
    cpi = "cpi"
    presidencia_comissao = "presidencia_comissao"
    requerimento = "requerimento"
    evento = "evento"


# ===========================================================================
# TEMAS DE ATUAÇÃO — taxonomia semântica (spec 001)
# Distinta de `temas` (codTema da API da Câmara)
# ===========================================================================
class TemaAtuacao(Base):
    __tablename__ = "temasAtuacao"

    id = Column(Integer, primary_key=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    nome = Column(String(150), nullable=False, unique=True)
    descricao = Column(Text)
    embedding = Column(Vector(EMBEDDING_DIM))
    ordem = Column(SmallInteger)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    itens = relationship("ItemTemaAtuacao", back_populates="temaAtuacao")
    deputados = relationship("DeputadoTemaAtuacao", back_populates="temaAtuacao")

    __table_args__ = (
        Index(
            "ix_temas_atuacao_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


# ===========================================================================
# DOCUMENT EMBEDDINGS — armazenamento central (specs 001, 003)
# ===========================================================================
class DocumentEmbedding(Base):
    """
    Mapeamento texto-fonte (jobs futuros):
      proposicao  → ementa + keywords + justificativa
      discurso    → sumario ou transcricao
      evento      → descricao
      tramitacao  → despacho + contexto de relatoria
    """

    __tablename__ = "documentEmbeddings"

    id = Column(Integer, primary_key=True)
    tipoEntidade = Column(
        Enum(TipoEntidadeDocumento, name="tipo_entidade_documento"),
        nullable=False,
        index=True,
    )
    idEntidade = Column(Integer, nullable=False)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    textoFonte = Column(Text)
    textoHash = Column(String(64), nullable=False, index=True)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    modelo = Column(String(100), nullable=False)
    dimensao = Column(SmallInteger, nullable=False)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])

    __table_args__ = (
        UniqueConstraint(
            "tipoEntidade", "idEntidade", "modelo", name="uq_doc_emb_entidade_modelo"
        ),
        Index("ix_doc_emb_tipo_entidade", "tipoEntidade", "idEntidade"),
        Index(
            "ix_document_embeddings_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 24, "ef_construction": 128},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


# ===========================================================================
# ITENS ↔ TEMAS DE ATUAÇÃO — classificação (spec 001, etapa 2)
# ===========================================================================
class ItemTemaAtuacao(Base):
    __tablename__ = "itensTemasAtuacao"

    id = Column(Integer, primary_key=True)
    tipoEntidade = Column(
        Enum(TipoEntidadeDocumento, name="tipo_entidade_documento", create_type=False),
        nullable=False,
        index=True,
    )
    idEntidade = Column(Integer, nullable=False)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idTemaAtuacao = Column(
        Integer,
        ForeignKey("temasAtuacao.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipoParticipacao = Column(
        Enum(TipoParticipacao, name="tipo_participacao"),
        nullable=False,
    )
    peso = Column(Numeric(4, 1), nullable=False)
    scoreClassificacao = Column(Numeric(5, 4))
    rankNoItem = Column(SmallInteger)
    modelo = Column(String(100), nullable=False)
    createdAt = Column(DateTime, server_default=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])
    temaAtuacao = relationship("TemaAtuacao", back_populates="itens")

    __table_args__ = (
        UniqueConstraint(
            "tipoEntidade",
            "idEntidade",
            "idTemaAtuacao",
            "modelo",
            name="uq_item_tema_entidade_modelo",
        ),
    )


# ===========================================================================
# DEPUTADO ↔ TEMAS DE ATUAÇÃO — agregação (spec 001, etapa 3)
# ===========================================================================
class DeputadoTemaAtuacao(Base):
    __tablename__ = "deputadoTemasAtuacao"

    id = Column(Integer, primary_key=True)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idTemaAtuacao = Column(
        Integer,
        ForeignKey("temasAtuacao.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idLegislatura = Column(
        Integer,
        ForeignKey("legislaturas.idLegislatura", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    score = Column(Numeric(5, 4), nullable=False)
    pesoTotal = Column(Numeric(12, 2))
    rank = Column(SmallInteger)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])
    temaAtuacao = relationship("TemaAtuacao", back_populates="deputados")

    __table_args__ = (
        UniqueConstraint(
            "idDeputado",
            "idTemaAtuacao",
            "idLegislatura",
            name="uq_dep_tema_legislatura",
        ),
    )


# ===========================================================================
# PERFIL VETORIAL DO DEPUTADO — vetor composto (spec 003)
# ===========================================================================
class DeputadoPerfilVetorial(Base):
    __tablename__ = "deputadoPerfilVetorial"

    id = Column(Integer, primary_key=True)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idLegislatura = Column(
        Integer,
        ForeignKey("legislaturas.idLegislatura", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vetorTematico = Column(Vector(EMBEDDING_DIM))
    vetorProposicoes = Column(Vector(EMBEDDING_DIM))
    vetorDiscursos = Column(Vector(EMBEDDING_DIM))
    vetorComposto = Column(Vector(EMBEDDING_DIM))
    modelo = Column(String(100), nullable=False)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])

    __table_args__ = (
        UniqueConstraint(
            "idDeputado",
            "idLegislatura",
            "modelo",
            name="uq_dep_perfil_legislatura_modelo",
        ),
        Index(
            "ix_deputado_perfil_vetor_composto_hnsw",
            "vetorComposto",
            postgresql_using="hnsw",
            postgresql_with={"m": 24, "ef_construction": 128},
            postgresql_ops={"vetorComposto": "vector_cosine_ops"},
        ),
        Index(
            "ix_deputado_perfil_vetor_tematico_hnsw",
            "vetorTematico",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"vetorTematico": "vector_cosine_ops"},
        ),
        Index(
            "ix_deputado_perfil_vetor_proposicoes_hnsw",
            "vetorProposicoes",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"vetorProposicoes": "vector_cosine_ops"},
        ),
        Index(
            "ix_deputado_perfil_vetor_discursos_hnsw",
            "vetorDiscursos",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"vetorDiscursos": "vector_cosine_ops"},
        ),
    )


# ===========================================================================
# DEPUTADOS SEMELHANTES — cache de similaridade (spec 003)
# ===========================================================================
class DeputadoSemelhante(Base):
    __tablename__ = "deputadosSemelhantes"

    id = Column(Integer, primary_key=True)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idDeputadoSimilar = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similaridade = Column(Numeric(5, 4), nullable=False)
    explicacao = Column(Text)
    rank = Column(SmallInteger)
    modelo = Column(String(100), nullable=False)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])
    deputadoSimilar = relationship("Deputado", foreign_keys=[idDeputadoSimilar])

    __table_args__ = (
        UniqueConstraint(
            "idDeputado",
            "idDeputadoSimilar",
            "modelo",
            name="uq_dep_semelhante_modelo",
        ),
        CheckConstraint(
            '"idDeputado" <> "idDeputadoSimilar"',
            name="ck_dep_semelhante_distinto",
        ),
    )


# ===========================================================================
# MARCOS DO MANDATO — ranqueados por impacto (spec 002)
# ===========================================================================
class MarcoMandato(Base):
    __tablename__ = "marcosMandato"

    id = Column(Integer, primary_key=True)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipoMarco = Column(
        Enum(TipoMarco, name="tipo_marco"),
        nullable=False,
        index=True,
    )
    tipoEntidade = Column(
        Enum(TipoEntidadeDocumento, name="tipo_entidade_documento", create_type=False),
        nullable=True,
    )
    idEntidade = Column(Integer, nullable=True)
    titulo = Column(Text, nullable=False)
    descricao = Column(Text)
    scoreImpacto = Column(Numeric(5, 2), nullable=False)
    fatores = Column(JSONB)
    idLegislatura = Column(
        Integer,
        ForeignKey("legislaturas.idLegislatura", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dataReferencia = Column(Date)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    rank = Column(SmallInteger)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])

    __table_args__ = (
        Index(
            "ix_marcos_mandato_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


# ===========================================================================
# ÍNDICE DE IMPACTO PARLAMENTAR — scores multidimensionais (spec 005)
# ===========================================================================
class DeputadoImpacto(Base):
    __tablename__ = "deputadoImpacto"

    id = Column(Integer, primary_key=True)
    idDeputado = Column(
        Integer,
        ForeignKey("deputados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idLegislatura = Column(
        Integer,
        ForeignKey("legislaturas.idLegislatura", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scoreTotal = Column(Numeric(5, 2), nullable=False)
    scoreProducao = Column(Numeric(5, 2))
    scoreTramitacao = Column(Numeric(5, 2))
    scoreLideranca = Column(Numeric(5, 2))
    scoreParticipacao = Column(Numeric(5, 2))
    scoreFiscalizacao = Column(Numeric(5, 2))
    detalhes = Column(JSONB)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deputado = relationship("Deputado", foreign_keys=[idDeputado])

    __table_args__ = (
        UniqueConstraint(
            "idDeputado",
            "idLegislatura",
            name="uq_dep_impacto_legislatura",
        ),
    )


# ===========================================================================
# ÍNDICES HNSW — definidos via SQLAlchemy models e migrations Alembic
# Configuração otimizada para alta revocabilidade (Recall):
#   - m = 24 (número de conexões por elemento por camada)
#   - ef_construction = 128 (tamanho da lista de candidatos durante construção)
#   - metric = vector_cosine_ops (distância por cosseno para embeddings normalizados)
# ===========================================================================
