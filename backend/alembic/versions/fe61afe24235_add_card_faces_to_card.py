"""add card_faces to card

Revision ID: fe61afe24235
Revises: 34f74e54c976
Create Date: 2026-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe61afe24235'
down_revision: Union[str, Sequence[str], None] = '34f74e54c976'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('card', sa.Column('card_faces', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('card', 'card_faces')
