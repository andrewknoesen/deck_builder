"""Add state column to goldfishnode

Revision ID: 97dfa370d0ca
Revises: 2040f7f42c18
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97dfa370d0ca'
down_revision: Union[str, Sequence[str], None] = '2040f7f42c18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('goldfishnode', sa.Column('state', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('goldfishnode', 'state')
