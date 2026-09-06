"""add_trgm_index_proposicoes_ementa

Revision ID: c1a2b3d4e5f6
Revises: 8052abf4e149
Create Date: 2026-09-06 08:00:00.000000

"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8052abf4e149"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_proposicoes_ementa_trgm ON proposicoes "
        "USING gin (ementa gin_trgm_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_proposicoes_ementa_trgm;")
