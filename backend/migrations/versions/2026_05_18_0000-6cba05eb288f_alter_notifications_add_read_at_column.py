"""alter notifications add read_at column

Revision ID: 6cba05eb288f
Revises: 65b0d23dc68e
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6cba05eb288f"
down_revision: Union[str, Sequence[str], None] = "65b0d23dc68e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "notifications",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("notifications", "read_at")
