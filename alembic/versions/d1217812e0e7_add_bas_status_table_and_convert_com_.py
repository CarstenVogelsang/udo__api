"""add bas_status table and convert com_unternehmen status to FK

Revision ID: d1217812e0e7
Revises: b93537e1486f
Create Date: 2026-02-13 10:05:08.727455

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd1217812e0e7'
down_revision: Union[str, Sequence[str], None] = 'b93537e1486f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs for seed data (stable across migrations)
STATUS_AKTIV_ID = 'a1b2c3d4-0001-4000-8000-000000000001'
STATUS_GESCHLOSSEN_ID = 'a1b2c3d4-0002-4000-8000-000000000002'
STATUS_UNBEKANNT_ID = 'a1b2c3d4-0003-4000-8000-000000000003'


def upgrade() -> None:
    """Create bas_status table and convert com_unternehmen.status to FK."""

    # 0. Drop table if it was pre-created by Base.metadata.create_all()
    op.execute(text("DROP TABLE IF EXISTS bas_status CASCADE"))

    # 1. Create bas_status table
    op.create_table(
        'bas_status',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('code', sa.String(30), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('kontext', sa.String(50), nullable=False, index=True),
        sa.Column('icon', sa.String(50)),
        sa.Column('farbe', sa.String(20)),
        sa.Column('sortierung', sa.Integer(), default=0),
        sa.Column('erstellt_am', sa.DateTime()),
        sa.UniqueConstraint('code', 'kontext', name='uq_status_code_kontext'),
    )

    # 2. Seed initial status values for 'unternehmen' context
    op.execute(
        f"INSERT INTO bas_status (id, code, name, kontext, icon, farbe, sortierung) VALUES "
        f"('{STATUS_AKTIV_ID}', 'aktiv', 'Aktiv', 'unternehmen', 'circle-check', 'success', 1), "
        f"('{STATUS_GESCHLOSSEN_ID}', 'geschlossen', 'Geschlossen', 'unternehmen', 'circle-x', 'error', 2), "
        f"('{STATUS_UNBEKANNT_ID}', 'unbekannt', 'Unbekannt', 'unternehmen', 'help', 'warning', 3)"
    )

    # 3. Add status_id column (nullable initially)
    op.add_column('com_unternehmen',
        sa.Column('status_id', sa.String(36), nullable=True)
    )

    # 4. Migrate existing status string values to FK references
    op.execute(
        f"UPDATE com_unternehmen SET status_id = '{STATUS_AKTIV_ID}' "
        f"WHERE status = 'aktiv'"
    )
    op.execute(
        f"UPDATE com_unternehmen SET status_id = '{STATUS_GESCHLOSSEN_ID}' "
        f"WHERE status = 'geschlossen'"
    )
    op.execute(
        f"UPDATE com_unternehmen SET status_id = '{STATUS_UNBEKANNT_ID}' "
        f"WHERE status = 'unbekannt' OR status IS NULL"
    )

    # 5. Drop old status column
    op.drop_column('com_unternehmen', 'status')

    # 6. Add FK constraint and index
    op.create_foreign_key(
        'fk_unternehmen_status', 'com_unternehmen',
        'bas_status', ['status_id'], ['id']
    )
    op.create_index('idx_unternehmen_status', 'com_unternehmen', ['status_id'])


def downgrade() -> None:
    """Revert: restore status as VARCHAR, drop bas_status table."""

    # 1. Add back the old status column
    op.add_column('com_unternehmen',
        sa.Column('status', sa.String(20), server_default='unbekannt')
    )

    # 2. Migrate FK values back to strings
    op.execute(
        "UPDATE com_unternehmen u SET status = s.code "
        "FROM bas_status s WHERE u.status_id = s.id"
    )

    # 3. Drop FK, index, and status_id column
    op.drop_constraint('fk_unternehmen_status', 'com_unternehmen', type_='foreignkey')
    op.drop_index('idx_unternehmen_status', table_name='com_unternehmen')
    op.drop_column('com_unternehmen', 'status_id')

    # 4. Drop bas_status table
    op.drop_table('bas_status')
