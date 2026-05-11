"""add books search vector

Revision ID: 411cc493b898
Revises: 7f897e68c817
Create Date: 2026-05-10 22:58:55.513744

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '411cc493b898'
down_revision: Union[str, Sequence[str], None] = '7f897e68c817'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE books
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english',
                coalesce(title, '') || ' ' || coalesce(description, ''))
        ) STORED
        """
    )
    op.execute(
        "CREATE INDEX idx_books_search_vector ON books USING GIN(search_vector)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_books_search_vector")
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS search_vector")
