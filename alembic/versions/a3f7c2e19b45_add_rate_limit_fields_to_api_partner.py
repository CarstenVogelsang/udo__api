"""Add rate limit fields to api_partner

Revision ID: a3f7c2e19b45
Revises: 8b4d514c8309
Create Date: 2026-02-08 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7c2e19b45'
down_revision: Union[str, None] = '8b4d514c8309'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('api_partner', sa.Column('rate_limit_pro_minute', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('api_partner', sa.Column('rate_limit_pro_stunde', sa.Integer(), nullable=False, server_default='1000'))
    op.add_column('api_partner', sa.Column('rate_limit_pro_tag', sa.Integer(), nullable=False, server_default='10000'))


def downgrade() -> None:
    op.drop_column('api_partner', 'rate_limit_pro_tag')
    op.drop_column('api_partner', 'rate_limit_pro_stunde')
    op.drop_column('api_partner', 'rate_limit_pro_minute')
