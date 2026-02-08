"""Add api_usage and api_usage_daily tables

Revision ID: 601eff32f69d
Revises: 567197f4e309
Create Date: 2026-02-08 11:32:37.773779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '601eff32f69d'
down_revision: Union[str, Sequence[str], None] = '567197f4e309'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create usage tracking tables."""
    op.create_table(
        'api_usage',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('api_partner.id'), nullable=False),
        sa.Column('endpoint', sa.String(100), nullable=False),
        sa.Column('methode', sa.String(10), nullable=False, server_default='GET'),
        sa.Column('parameter', sa.JSON(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('anzahl_ergebnisse', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('kosten', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('antwortzeit_ms', sa.Integer(), nullable=True),
        sa.Column('erstellt_am', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_usage_partner_date', 'api_usage', ['partner_id', 'erstellt_am'])
    op.create_index('idx_usage_endpoint', 'api_usage', ['endpoint'])
    op.create_index('idx_usage_erstellt_am', 'api_usage', ['erstellt_am'])

    op.create_table(
        'api_usage_daily',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('api_partner.id'), nullable=False),
        sa.Column('datum', sa.Date(), nullable=False),
        sa.Column('endpoint', sa.String(100), nullable=False),
        sa.Column('anzahl_abrufe', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('anzahl_ergebnisse_gesamt', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('kosten_gesamt', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('erstellt_am', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('partner_id', 'datum', 'endpoint', name='uq_daily_partner_datum_endpoint'),
    )
    op.create_index('idx_daily_datum', 'api_usage_daily', ['datum'])


def downgrade() -> None:
    """Drop usage tracking tables."""
    op.drop_table('api_usage_daily')
    op.drop_table('api_usage')
