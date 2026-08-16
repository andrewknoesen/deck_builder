"""Add outcome column to goldfishsession

Revision ID: 9ebb5d15bcf9
Revises: 1d1448d72c58
Create Date: 2026-08-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ebb5d15bcf9'
down_revision: Union[str, Sequence[str], None] = '1d1448d72c58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('goldfishsession', sa.Column('outcome', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('goldfishsession', 'outcome')
