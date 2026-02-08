"""Add billing account, credit transaction and invoice tables

Revision ID: 8b4d514c8309
Revises: 601eff32f69d
Create Date: 2026-02-08 13:58:46.346098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b4d514c8309'
down_revision: Union[str, Sequence[str], None] = '601eff32f69d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create billing tables."""
    # 1. Billing Account (1:1 with api_partner)
    op.create_table(
        'api_billing_account',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('api_partner.id'), nullable=False, unique=True),
        sa.Column('billing_typ', sa.String(20), nullable=False, server_default='internal'),
        sa.Column('guthaben_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rechnungs_limit_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('warnung_bei_cents', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('warnung_gesendet_am', sa.DateTime(), nullable=True),
        sa.Column('ist_gesperrt', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('gesperrt_grund', sa.String(255), nullable=True),
        sa.Column('gesperrt_am', sa.DateTime(), nullable=True),
        sa.Column('erstellt_am', sa.DateTime(), nullable=True),
        sa.Column('aktualisiert_am', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_billing_typ', 'api_billing_account', ['billing_typ'])

    # 2. Credit Transaction
    op.create_table(
        'api_credit_transaction',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('billing_account_id', sa.String(36), sa.ForeignKey('api_billing_account.id'), nullable=False),
        sa.Column('typ', sa.String(20), nullable=False),
        sa.Column('betrag_cents', sa.Integer(), nullable=False),
        sa.Column('saldo_danach_cents', sa.Integer(), nullable=False),
        sa.Column('beschreibung', sa.String(255), nullable=True),
        sa.Column('referenz_typ', sa.String(50), nullable=True),
        sa.Column('referenz_id', sa.String(100), nullable=True),
        sa.Column('erstellt_von', sa.String(100), nullable=False, server_default='system'),
        sa.Column('erstellt_am', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_credit_billing_id', 'api_credit_transaction', ['billing_account_id'])
    op.create_index('idx_credit_erstellt_am', 'api_credit_transaction', ['erstellt_am'])
    op.create_index('idx_credit_typ', 'api_credit_transaction', ['typ'])

    # 3. Invoice
    op.create_table(
        'api_invoice',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('api_partner.id'), nullable=False),
        sa.Column('rechnungsnummer', sa.String(50), nullable=False, unique=True),
        sa.Column('zeitraum_von', sa.Date(), nullable=False),
        sa.Column('zeitraum_bis', sa.Date(), nullable=False),
        sa.Column('summe_netto_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summe_brutto_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mwst_satz', sa.Float(), nullable=False, server_default='19.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='entwurf'),
        sa.Column('positionen', sa.JSON(), nullable=True),
        sa.Column('erstellt_am', sa.DateTime(), nullable=True),
        sa.Column('aktualisiert_am', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_invoice_partner_zeitraum', 'api_invoice', ['partner_id', 'zeitraum_von'])


def downgrade() -> None:
    """Drop billing tables."""
    op.drop_table('api_invoice')
    op.drop_table('api_credit_transaction')
    op.drop_table('api_billing_account')
