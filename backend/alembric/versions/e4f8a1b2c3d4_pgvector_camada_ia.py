"""pgvector camada ia

Revision ID: e4f8a1b2c3d4
Revises: d9a27be33e0a
Create Date: 2026-06-16 12:00:00.000000

"""

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e4f8a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d9a27be33e0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))

tipo_entidade_documento = postgresql.ENUM(
    "proposicao",
    "discurso",
    "evento",
    "tramitacao",
    "relatoria",
    name="tipo_entidade_documento",
    create_type=False,
)

tipo_participacao = postgresql.ENUM(
    "autoria",
    "coautoria",
    "relatoria",
    "discurso",
    "evento",
    name="tipo_participacao",
    create_type=False,
)

tipo_marco = postgresql.ENUM(
    "proposicao",
    "relatoria",
    "cpi",
    "presidencia_comissao",
    "requerimento",
    "evento",
    name="tipo_marco",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    bind = op.get_bind()
    tipo_entidade_documento.create(bind, checkfirst=True)
    tipo_participacao.create(bind, checkfirst=True)
    tipo_marco.create(bind, checkfirst=True)

    op.create_table(
        "temasAtuacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("ordem", sa.SmallInteger(), nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_temasAtuacao_slug"), "temasAtuacao", ["slug"], unique=True)

    op.create_table(
        "documentEmbeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipoEntidade", tipo_entidade_documento, nullable=False),
        sa.Column("idEntidade", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=True),
        sa.Column("textoFonte", sa.Text(), nullable=True),
        sa.Column("textoHash", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("modelo", sa.String(length=100), nullable=False),
        sa.Column("dimensao", sa.SmallInteger(), nullable=False),
        sa.Column(
            "createdAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updatedAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tipoEntidade",
            "idEntidade",
            "modelo",
            name="uq_doc_emb_entidade_modelo",
        ),
    )
    op.create_index(
        op.f("ix_documentEmbeddings_idDeputado"),
        "documentEmbeddings",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documentEmbeddings_textoHash"),
        "documentEmbeddings",
        ["textoHash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documentEmbeddings_tipoEntidade"),
        "documentEmbeddings",
        ["tipoEntidade"],
        unique=False,
    )
    op.create_index(
        "ix_doc_emb_tipo_entidade",
        "documentEmbeddings",
        ["tipoEntidade", "idEntidade"],
        unique=False,
    )

    op.create_table(
        "itensTemasAtuacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipoEntidade", tipo_entidade_documento, nullable=False),
        sa.Column("idEntidade", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=False),
        sa.Column("idTemaAtuacao", sa.Integer(), nullable=False),
        sa.Column("tipoParticipacao", tipo_participacao, nullable=False),
        sa.Column("peso", sa.Numeric(precision=4, scale=1), nullable=False),
        sa.Column(
            "scoreClassificacao", sa.Numeric(precision=5, scale=4), nullable=True
        ),
        sa.Column("rankNoItem", sa.SmallInteger(), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=False),
        sa.Column(
            "createdAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idTemaAtuacao"], ["temasAtuacao.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tipoEntidade",
            "idEntidade",
            "idTemaAtuacao",
            "modelo",
            name="uq_item_tema_entidade_modelo",
        ),
    )
    op.create_index(
        op.f("ix_itensTemasAtuacao_idDeputado"),
        "itensTemasAtuacao",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itensTemasAtuacao_idTemaAtuacao"),
        "itensTemasAtuacao",
        ["idTemaAtuacao"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itensTemasAtuacao_tipoEntidade"),
        "itensTemasAtuacao",
        ["tipoEntidade"],
        unique=False,
    )

    op.create_table(
        "deputadoTemasAtuacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=False),
        sa.Column("idTemaAtuacao", sa.Integer(), nullable=False),
        sa.Column("idLegislatura", sa.Integer(), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("pesoTotal", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("rank", sa.SmallInteger(), nullable=True),
        sa.Column(
            "updatedAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idLegislatura"], ["legislaturas.idLegislatura"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["idTemaAtuacao"], ["temasAtuacao.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idDeputado",
            "idTemaAtuacao",
            "idLegislatura",
            name="uq_dep_tema_legislatura",
        ),
    )
    op.create_index(
        op.f("ix_deputadoTemasAtuacao_idDeputado"),
        "deputadoTemasAtuacao",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deputadoTemasAtuacao_idLegislatura"),
        "deputadoTemasAtuacao",
        ["idLegislatura"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deputadoTemasAtuacao_idTemaAtuacao"),
        "deputadoTemasAtuacao",
        ["idTemaAtuacao"],
        unique=False,
    )

    op.create_table(
        "deputadoPerfilVetorial",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=False),
        sa.Column("idLegislatura", sa.Integer(), nullable=True),
        sa.Column("vetorTematico", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("vetorProposicoes", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("vetorDiscursos", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("vetorComposto", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=False),
        sa.Column(
            "updatedAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idLegislatura"], ["legislaturas.idLegislatura"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idDeputado",
            "idLegislatura",
            "modelo",
            name="uq_dep_perfil_legislatura_modelo",
        ),
    )
    op.create_index(
        op.f("ix_deputadoPerfilVetorial_idDeputado"),
        "deputadoPerfilVetorial",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deputadoPerfilVetorial_idLegislatura"),
        "deputadoPerfilVetorial",
        ["idLegislatura"],
        unique=False,
    )

    op.create_table(
        "deputadosSemelhantes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=False),
        sa.Column("idDeputadoSimilar", sa.Integer(), nullable=False),
        sa.Column("similaridade", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("explicacao", sa.Text(), nullable=True),
        sa.Column("rank", sa.SmallInteger(), nullable=True),
        sa.Column("modelo", sa.String(length=100), nullable=False),
        sa.Column(
            "updatedAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.CheckConstraint(
            '"idDeputado" <> "idDeputadoSimilar"',
            name="ck_dep_semelhante_distinto",
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idDeputadoSimilar"], ["deputados.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idDeputado",
            "idDeputadoSimilar",
            "modelo",
            name="uq_dep_semelhante_modelo",
        ),
    )
    op.create_index(
        op.f("ix_deputadosSemelhantes_idDeputado"),
        "deputadosSemelhantes",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deputadosSemelhantes_idDeputadoSimilar"),
        "deputadosSemelhantes",
        ["idDeputadoSimilar"],
        unique=False,
    )

    op.create_table(
        "marcosMandato",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=False),
        sa.Column("tipoMarco", tipo_marco, nullable=False),
        sa.Column("tipoEntidade", tipo_entidade_documento, nullable=True),
        sa.Column("idEntidade", sa.Integer(), nullable=True),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("scoreImpacto", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("fatores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("idLegislatura", sa.Integer(), nullable=True),
        sa.Column("dataReferencia", sa.Date(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("rank", sa.SmallInteger(), nullable=True),
        sa.Column(
            "updatedAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idLegislatura"], ["legislaturas.idLegislatura"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_marcosMandato_idDeputado"),
        "marcosMandato",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marcosMandato_idLegislatura"),
        "marcosMandato",
        ["idLegislatura"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marcosMandato_tipoMarco"),
        "marcosMandato",
        ["tipoMarco"],
        unique=False,
    )

    op.create_table(
        "deputadoImpacto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idDeputado", sa.Integer(), nullable=False),
        sa.Column("idLegislatura", sa.Integer(), nullable=True),
        sa.Column("scoreTotal", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("scoreProducao", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("scoreTramitacao", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("scoreLideranca", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("scoreParticipacao", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("scoreFiscalizacao", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("detalhes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updatedAt", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["idDeputado"], ["deputados.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idLegislatura"], ["legislaturas.idLegislatura"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "idDeputado",
            "idLegislatura",
            name="uq_dep_impacto_legislatura",
        ),
    )
    op.create_index(
        op.f("ix_deputadoImpacto_idDeputado"),
        "deputadoImpacto",
        ["idDeputado"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deputadoImpacto_idLegislatura"),
        "deputadoImpacto",
        ["idLegislatura"],
        unique=False,
    )

    op.execute(
        """
        CREATE INDEX ix_document_embeddings_embedding_hnsw
        ON "documentEmbeddings"
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_deputado_perfil_vetor_composto_hnsw
        ON "deputadoPerfilVetorial"
        USING hnsw ("vetorComposto" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_deputado_perfil_vetor_composto_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_document_embeddings_embedding_hnsw")

    op.drop_index(
        op.f("ix_deputadoImpacto_idLegislatura"), table_name="deputadoImpacto"
    )
    op.drop_index(op.f("ix_deputadoImpacto_idDeputado"), table_name="deputadoImpacto")
    op.drop_table("deputadoImpacto")

    op.drop_index(op.f("ix_marcosMandato_tipoMarco"), table_name="marcosMandato")
    op.drop_index(op.f("ix_marcosMandato_idLegislatura"), table_name="marcosMandato")
    op.drop_index(op.f("ix_marcosMandato_idDeputado"), table_name="marcosMandato")
    op.drop_table("marcosMandato")

    op.drop_index(
        op.f("ix_deputadosSemelhantes_idDeputadoSimilar"),
        table_name="deputadosSemelhantes",
    )
    op.drop_index(
        op.f("ix_deputadosSemelhantes_idDeputado"),
        table_name="deputadosSemelhantes",
    )
    op.drop_table("deputadosSemelhantes")

    op.drop_index(
        op.f("ix_deputadoPerfilVetorial_idLegislatura"),
        table_name="deputadoPerfilVetorial",
    )
    op.drop_index(
        op.f("ix_deputadoPerfilVetorial_idDeputado"),
        table_name="deputadoPerfilVetorial",
    )
    op.drop_table("deputadoPerfilVetorial")

    op.drop_index(
        op.f("ix_deputadoTemasAtuacao_idTemaAtuacao"),
        table_name="deputadoTemasAtuacao",
    )
    op.drop_index(
        op.f("ix_deputadoTemasAtuacao_idLegislatura"),
        table_name="deputadoTemasAtuacao",
    )
    op.drop_index(
        op.f("ix_deputadoTemasAtuacao_idDeputado"),
        table_name="deputadoTemasAtuacao",
    )
    op.drop_table("deputadoTemasAtuacao")

    op.drop_index(
        op.f("ix_itensTemasAtuacao_tipoEntidade"),
        table_name="itensTemasAtuacao",
    )
    op.drop_index(
        op.f("ix_itensTemasAtuacao_idTemaAtuacao"),
        table_name="itensTemasAtuacao",
    )
    op.drop_index(
        op.f("ix_itensTemasAtuacao_idDeputado"),
        table_name="itensTemasAtuacao",
    )
    op.drop_table("itensTemasAtuacao")

    op.drop_index("ix_doc_emb_tipo_entidade", table_name="documentEmbeddings")
    op.drop_index(
        op.f("ix_documentEmbeddings_tipoEntidade"),
        table_name="documentEmbeddings",
    )
    op.drop_index(
        op.f("ix_documentEmbeddings_textoHash"),
        table_name="documentEmbeddings",
    )
    op.drop_index(
        op.f("ix_documentEmbeddings_idDeputado"),
        table_name="documentEmbeddings",
    )
    op.drop_table("documentEmbeddings")

    op.drop_index(op.f("ix_temasAtuacao_slug"), table_name="temasAtuacao")
    op.drop_table("temasAtuacao")

    bind = op.get_bind()
    tipo_marco.drop(bind, checkfirst=True)
    tipo_participacao.drop(bind, checkfirst=True)
    tipo_entidade_documento.drop(bind, checkfirst=True)

    op.execute("DROP EXTENSION IF EXISTS vector")
