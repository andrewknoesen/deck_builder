"""cascade goldfish deck FKs so deleting a deck doesn't 500

Deleting a deck with practice sessions (or one used as another session's
opponent) violated these FKs since they had no ON DELETE rule (Postgres
defaults to RESTRICT). deck_id now cascades the delete to its sessions
(and goldfishnode.session_id cascades again so their nodes go too);
opponent_deck_id just gets nulled out since the session itself is still
meaningful without an opponent deck.

Revision ID: f3a1c9d2b7e4
Revises: 9ebb5d15bcf9
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9d2b7e4'
down_revision: Union[str, Sequence[str], None] = '9ebb5d15bcf9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        'goldfishsession_deck_id_fkey', 'goldfishsession', type_='foreignkey'
    )
    op.create_foreign_key(
        'goldfishsession_deck_id_fkey',
        'goldfishsession',
        'deck',
        ['deck_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.drop_constraint(
        'fk_goldfishsession_opponent_deck_id_deck', 'goldfishsession', type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_goldfishsession_opponent_deck_id_deck',
        'goldfishsession',
        'deck',
        ['opponent_deck_id'],
        ['id'],
        ondelete='SET NULL',
    )

    op.drop_constraint(
        'goldfishnode_session_id_fkey', 'goldfishnode', type_='foreignkey'
    )
    op.create_foreign_key(
        'goldfishnode_session_id_fkey',
        'goldfishnode',
        'goldfishsession',
        ['session_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'goldfishnode_session_id_fkey', 'goldfishnode', type_='foreignkey'
    )
    op.create_foreign_key(
        'goldfishnode_session_id_fkey',
        'goldfishnode',
        'goldfishsession',
        ['session_id'],
        ['id'],
    )

    op.drop_constraint(
        'fk_goldfishsession_opponent_deck_id_deck', 'goldfishsession', type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_goldfishsession_opponent_deck_id_deck',
        'goldfishsession',
        'deck',
        ['opponent_deck_id'],
        ['id'],
    )

    op.drop_constraint(
        'goldfishsession_deck_id_fkey', 'goldfishsession', type_='foreignkey'
    )
    op.create_foreign_key(
        'goldfishsession_deck_id_fkey',
        'goldfishsession',
        'deck',
        ['deck_id'],
        ['id'],
    )
