"""add recherche auftrag and roh ergebnis tables plus partner cost fields

Revision ID: 75914bb61196
Revises: 896f2c2e0235
Create Date: 2026-02-15 20:35:30.960675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75914bb61196'
down_revision: Union[str, Sequence[str], None] = '896f2c2e0235'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Note: rch_auftrag and rch_roh_ergebnis tables were already created
    directly from the SQLAlchemy models. This migration only adds the
    new partner cost fields for recherche quality tiers.
    """
    op.add_column('api_partner', sa.Column(
        'kosten_recherche_grundgebuehr', sa.Float(), nullable=False,
        server_default='0.5',
    ))
    op.add_column('api_partner', sa.Column(
        'kosten_recherche_standard', sa.Float(), nullable=False,
        server_default='0.05',
    ))
    op.add_column('api_partner', sa.Column(
        'kosten_recherche_premium', sa.Float(), nullable=False,
        server_default='0.12',
    ))
    op.add_column('api_partner', sa.Column(
        'kosten_recherche_komplett', sa.Float(), nullable=False,
        server_default='0.18',
    ))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('api_partner', 'kosten_recherche_komplett')
    op.drop_column('api_partner', 'kosten_recherche_premium')
    op.drop_column('api_partner', 'kosten_recherche_standard')
    op.drop_column('api_partner', 'kosten_recherche_grundgebuehr')
