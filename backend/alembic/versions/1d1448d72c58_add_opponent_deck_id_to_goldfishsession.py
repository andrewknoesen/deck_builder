"""add opponent_deck_id to goldfishsession

Revision ID: 1d1448d72c58
Revises: fe61afe24235
Create Date: 2026-08-11 09:16:22.259540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d1448d72c58'
down_revision: Union[str, Sequence[str], None] = 'fe61afe24235'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nullable FK added via ALTER TABLE to an already-existing table — unlike
    # 957916eed363's inline FKs on op.create_table(...), this needs its own
    # op.create_foreign_key(...) alongside op.add_column(...).
    op.add_column(
        'goldfishsession', sa.Column('opponent_deck_id', sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f('ix_goldfishsession_opponent_deck_id'),
        'goldfishsession',
        ['opponent_deck_id'],
        unique=False,
    )
    op.create_foreign_key(
        'fk_goldfishsession_opponent_deck_id_deck',
        'goldfishsession',
        'deck',
        ['opponent_deck_id'],
        ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_goldfishsession_opponent_deck_id_deck', 'goldfishsession', type_='foreignkey'
    )
    op.drop_index(
        op.f('ix_goldfishsession_opponent_deck_id'), table_name='goldfishsession'
    )
    op.drop_column('goldfishsession', 'opponent_deck_id')
