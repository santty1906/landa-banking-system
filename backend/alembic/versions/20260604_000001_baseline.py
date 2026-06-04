"""baseline migration scaffold

Revision ID: 20260604_000001
Revises:
Create Date: 2026-06-04 00:00:01
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260604_000001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Intentionally empty: foundation migration to validate migration plumbing.
    pass


def downgrade() -> None:
    pass
