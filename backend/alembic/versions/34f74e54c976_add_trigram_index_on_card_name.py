"""add trigram index on card name

Revision ID: 34f74e54c976
Revises: 97dfa370d0ca
Create Date: 2026-08-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '34f74e54c976'
down_revision: Union[str, Sequence[str], None] = '97dfa370d0ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Backs the deck-builder search box's local-DB card-name lookup
    # (GET /cards/local-search): a plain ILIKE '%text%' over ~116k rows with
    # no index took 2.5s+ (seq scan) -- a trigram GIN index brings the same
    # query down to ~10ms, which is the whole point of searching the local
    # bulk-ingested table instead of proxying live to Scryfall.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_card_name_trgm ON card USING gin (name gin_trgm_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_card_name_trgm")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
