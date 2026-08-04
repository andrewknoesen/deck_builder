"""Add goldfish session and node tables

Revision ID: 957916eed363
Revises: b73e9561f393
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '957916eed363'
down_revision: Union[str, Sequence[str], None] = 'b73e9561f393'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('goldfishsession',
    sa.Column('deck_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['deck_id'], ['deck.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goldfishsession_deck_id'), 'goldfishsession', ['deck_id'], unique=False)
    op.create_index(op.f('ix_goldfishsession_user_id'), 'goldfishsession', ['user_id'], unique=False)

    op.create_table('goldfishnode',
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('label', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('turn_number', sa.Integer(), nullable=True),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['goldfishsession.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['goldfishnode.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goldfishnode_session_id'), 'goldfishnode', ['session_id'], unique=False)
    op.create_index(op.f('ix_goldfishnode_parent_id'), 'goldfishnode', ['parent_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_goldfishnode_parent_id'), table_name='goldfishnode')
    op.drop_index(op.f('ix_goldfishnode_session_id'), table_name='goldfishnode')
    op.drop_table('goldfishnode')
    op.drop_index(op.f('ix_goldfishsession_user_id'), table_name='goldfishsession')
    op.drop_index(op.f('ix_goldfishsession_deck_id'), table_name='goldfishsession')
    op.drop_table('goldfishsession')
    # ### end Alembic commands ###
