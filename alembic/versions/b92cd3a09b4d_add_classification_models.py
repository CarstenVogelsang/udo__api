"""add_classification_models

Revision ID: b92cd3a09b4d
Revises: 5812571c7269
Create Date: 2026-02-17 19:39:15.907188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b92cd3a09b4d'
down_revision: Union[str, Sequence[str], None] = '5812571c7269'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy import inspect
    from alembic import op

    # Get database connection to check existing tables/columns
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Check existing columns in com_unternehmen
    existing_columns = []
    if 'com_unternehmen' in existing_tables:
        existing_columns = [c['name'] for c in inspector.get_columns('com_unternehmen')]

    # 1. Add wz_code to com_unternehmen (if not exists)
    if 'wz_code' not in existing_columns:
        op.add_column('com_unternehmen', sa.Column('wz_code', sa.String(length=10), nullable=True))
        op.create_index('idx_unternehmen_wz_code', 'com_unternehmen', ['wz_code'], unique=False)
        op.create_foreign_key('fk_com_unternehmen_wz_code', 'com_unternehmen', 'brn_branche', ['wz_code'], ['wz_code'])

    # 2. Create com_unternehmen_google_type junction table (if not exists)
    if 'com_unternehmen_google_type' not in existing_tables:
        op.create_table(
            'com_unternehmen_google_type',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('unternehmen_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('com_unternehmen.id'), nullable=False),
            sa.Column('gcid', sa.String(100), sa.ForeignKey('brn_google_kategorie.gcid'), nullable=False),
            sa.Column('ist_primaer', sa.Boolean(), default=False),
            sa.Column('ist_abgeleitet', sa.Boolean(), default=False),
            sa.Column('quelle', sa.String(50)),
            sa.Column('erstellt_am', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('uq_unt_gtype', 'com_unternehmen_google_type', ['unternehmen_id', 'gcid'], unique=True)
        op.create_index('idx_unt_gtype_unternehmen', 'com_unternehmen_google_type', ['unternehmen_id'])
        op.create_index('idx_unt_gtype_gcid', 'com_unternehmen_google_type', ['gcid'])

    # 3. Create com_klassifikation taxonomy table (if not exists)
    if 'com_klassifikation' not in existing_tables:
        op.create_table(
            'com_klassifikation',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('slug', sa.String(100), unique=True, nullable=False),
            sa.Column('name_de', sa.String(200), nullable=False),
            sa.Column('beschreibung', sa.Text()),
            sa.Column('dimension', sa.String(50)),
            sa.Column('google_mapping_gcid', sa.String(100), sa.ForeignKey('brn_google_kategorie.gcid'), nullable=True),
            sa.Column('parent_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('ist_aktiv', sa.Boolean(), default=True),
            sa.Column('erstellt_am', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('aktualisiert_am', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        # Add self-referential FK after table creation
        op.create_foreign_key('fk_klassifikation_parent', 'com_klassifikation', 'com_klassifikation', ['parent_id'], ['id'])
        op.create_index('idx_klassifikation_slug', 'com_klassifikation', ['slug'])
        op.create_index('idx_klassifikation_dimension', 'com_klassifikation', ['dimension'])
        op.create_index('idx_klassifikation_parent', 'com_klassifikation', ['parent_id'])

    # 4. Create com_unternehmen_klassifikation junction table (if not exists)
    if 'com_unternehmen_klassifikation' not in existing_tables:
        op.create_table(
            'com_unternehmen_klassifikation',
            sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('unternehmen_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('com_unternehmen.id'), nullable=False),
            sa.Column('klassifikation_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('com_klassifikation.id'), nullable=False),
            sa.Column('ist_primaer', sa.Boolean(), default=False),
            sa.Column('quelle', sa.String(50)),
            sa.Column('erstellt_am', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('uq_unt_klass', 'com_unternehmen_klassifikation', ['unternehmen_id', 'klassifikation_id'], unique=True)
        op.create_index('idx_unt_klass_unternehmen', 'com_unternehmen_klassifikation', ['unternehmen_id'])
        op.create_index('idx_unt_klass_klassifikation', 'com_unternehmen_klassifikation', ['klassifikation_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 4. Drop com_unternehmen_klassifikation
    op.drop_index('idx_unt_klass_klassifikation', table_name='com_unternehmen_klassifikation')
    op.drop_index('idx_unt_klass_unternehmen', table_name='com_unternehmen_klassifikation')
    op.drop_index('uq_unt_klass', table_name='com_unternehmen_klassifikation')
    op.drop_table('com_unternehmen_klassifikation')

    # 3. Drop com_klassifikation
    op.drop_index('idx_klassifikation_parent', table_name='com_klassifikation')
    op.drop_index('idx_klassifikation_dimension', table_name='com_klassifikation')
    op.drop_index('idx_klassifikation_slug', table_name='com_klassifikation')
    op.drop_constraint('fk_klassifikation_parent', 'com_klassifikation', type_='foreignkey')
    op.drop_table('com_klassifikation')

    # 2. Drop com_unternehmen_google_type
    op.drop_index('idx_unt_gtype_gcid', table_name='com_unternehmen_google_type')
    op.drop_index('idx_unt_gtype_unternehmen', table_name='com_unternehmen_google_type')
    op.drop_index('uq_unt_gtype', table_name='com_unternehmen_google_type')
    op.drop_table('com_unternehmen_google_type')

    # 1. Remove wz_code from com_unternehmen
    op.drop_constraint('fk_com_unternehmen_wz_code', 'com_unternehmen', type_='foreignkey')
    op.drop_index('idx_unternehmen_wz_code', table_name='com_unternehmen')
    op.drop_column('com_unternehmen', 'wz_code')
