"""add ist_geheim to system_setting

Adds ist_geheim boolean column, marks sensitive settings, and
encrypts existing plaintext values for secret settings.

Revision ID: 09150ae3af07
Revises: 4ab994ff485f
Create Date: 2026-02-16 18:24:06.158399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09150ae3af07'
down_revision: Union[str, Sequence[str], None] = '4ab994ff485f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Keys that should be marked as secret and have their values encrypted
SECRET_KEYS = [
    "recherche.google_places_api_key",
    "recherche.dataforseo_password",
]


def upgrade() -> None:
    """Add ist_geheim column, mark secrets, encrypt existing values."""
    # 1. Add column with server_default so existing rows get FALSE
    op.add_column(
        'system_setting',
        sa.Column('ist_geheim', sa.Boolean(), nullable=False, server_default='false'),
    )

    # 2. Mark known secret keys
    system_setting = sa.table(
        'system_setting',
        sa.column('key', sa.String),
        sa.column('value', sa.Text),
        sa.column('ist_geheim', sa.Boolean),
    )
    op.execute(
        system_setting.update()
        .where(system_setting.c.key.in_(SECRET_KEYS))
        .values(ist_geheim=True)
    )

    # 3. Encrypt existing plaintext values for secret keys
    conn = op.get_bind()
    rows = conn.execute(
        sa.select(system_setting.c.key, system_setting.c.value)
        .where(
            system_setting.c.key.in_(SECRET_KEYS),
            system_setting.c.value != '',
            system_setting.c.value.isnot(None),
        )
    ).fetchall()

    if rows:
        # Import crypto module for encryption
        from app.services.crypto import encrypt_value

        for row in rows:
            encrypted = encrypt_value(row.value)
            conn.execute(
                system_setting.update()
                .where(system_setting.c.key == row.key)
                .values(value=encrypted)
            )

    # Remove server_default after data migration
    op.alter_column('system_setting', 'ist_geheim', server_default=None)


def downgrade() -> None:
    """Remove ist_geheim column. WARNING: encrypted values are NOT decrypted."""
    op.drop_column('system_setting', 'ist_geheim')
