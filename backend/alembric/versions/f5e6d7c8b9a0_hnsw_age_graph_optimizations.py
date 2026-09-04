"""hnsw_age_graph_optimizations

Revision ID: f5e6d7c8b9a0
Revises: e4f8a1b2c3d4
Create Date: 2026-07-30 12:00:00.000000

"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5e6d7c8b9a0"
down_revision: Union[str, Sequence[str], None] = "e4f8a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Optmize pgvector HNSW indexes & setup Apache AGE graph."""
    
    # 1. Drop existing sub-optimal HNSW indexes
    op.execute("DROP INDEX IF EXISTS ix_document_embeddings_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_deputado_perfil_vetor_composto_hnsw")

    # 2. Re-create HNSW indexes with optimal parameters (m=24, ef_construction=128)
    op.execute(
        """
        CREATE INDEX ix_document_embeddings_embedding_hnsw
        ON "documentEmbeddings"
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 24, ef_construction = 128);
        """
    )
    op.execute(
        """
        CREATE INDEX ix_deputado_perfil_vetor_composto_hnsw
        ON "deputadoPerfilVetorial"
        USING hnsw ("vetorComposto" vector_cosine_ops)
        WITH (m = 24, ef_construction = 128);
        """
    )

    # 3. Create HNSW indexes on additional vector columns
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_temas_atuacao_embedding_hnsw
        ON "temasAtuacao"
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_marcos_mandato_embedding_hnsw
        ON "marcosMandato"
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_deputado_perfil_vetor_tematico_hnsw
        ON "deputadoPerfilVetorial"
        USING hnsw ("vetorTematico" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_deputado_perfil_vetor_proposicoes_hnsw
        ON "deputadoPerfilVetorial"
        USING hnsw ("vetorProposicoes" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )

    # 4. Setup Apache AGE Graph (if extension is available)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'age') THEN
                CREATE EXTENSION IF NOT EXISTS age;
                LOAD 'age';
                SET search_path = ag_catalog, "$user", public;
                IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'quemvota_graph') THEN
                    PERFORM ag_catalog.create_graph('quemvota_graph');
                END IF;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Apache AGE setup skipped or failed: %', SQLERRM;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema: Restore previous HNSW index parameters & drop graph."""
    # Drop new indexes
    op.execute("DROP INDEX IF EXISTS ix_deputado_perfil_vetor_proposicoes_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_deputado_perfil_vetor_tematico_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_marcos_mandato_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_temas_atuacao_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_deputado_perfil_vetor_composto_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_document_embeddings_embedding_hnsw")

    # Re-create original default indexes
    op.execute(
        """
        CREATE INDEX ix_document_embeddings_embedding_hnsw
        ON "documentEmbeddings"
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )
    op.execute(
        """
        CREATE INDEX ix_deputado_perfil_vetor_composto_hnsw
        ON "deputadoPerfilVetorial"
        USING hnsw ("vetorComposto" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )

    # Drop AGE graph if exists
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'age') THEN
                LOAD 'age';
                SET search_path = ag_catalog, "$user", public;
                IF EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'quemvota_graph') THEN
                    PERFORM ag_catalog.drop_graph('quemvota_graph', true);
                END IF;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Apache AGE teardown skipped: %', SQLERRM;
        END $$;
        """
    )
