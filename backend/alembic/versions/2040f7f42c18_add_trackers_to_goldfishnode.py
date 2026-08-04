"""Add trackers column to goldfishnode

Revision ID: 2040f7f42c18
Revises: 957916eed363
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2040f7f42c18'
down_revision: Union[str, Sequence[str], None] = '957916eed363'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('goldfishnode', sa.Column('trackers', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('goldfishnode', 'trackers')
