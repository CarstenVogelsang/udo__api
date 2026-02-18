"""add bewertungsplattform and unternehmen_bewertung

Revision ID: e4db50debd03
Revises: b92cd3a09b4d
Create Date: 2026-02-18 10:03:50.325741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4db50debd03'
down_revision: Union[str, Sequence[str], None] = 'b92cd3a09b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Seed data for bas_bewertungsplattform
PLATTFORMEN = [
    ("google", "Google Maps", "https://maps.google.com", "brand-google"),
    ("yelp", "Yelp", "https://www.yelp.com", "brand-yelp"),
    ("tripadvisor", "TripAdvisor", "https://www.tripadvisor.com", "plane"),
    ("trustpilot", "Trustpilot", "https://www.trustpilot.com", "star"),
    ("kununu", "kununu", "https://www.kununu.com", "building"),
]


def upgrade() -> None:
    """Seed platforms and backfill Google ratings from metadaten JSON."""
    # Tables already exist (created in prior migration).
    # This migration seeds lookup data and backfills ratings.

    # 1. Seed platforms (idempotent: skip if code already exists)
    for code, name, website, icon in PLATTFORMEN:
        op.execute(sa.text(
            "INSERT INTO bas_bewertungsplattform (id, code, name, website, icon, erstellt_am) "
            "SELECT gen_random_uuid()::text, :code, :name, :website, :icon, NOW() "
            "WHERE NOT EXISTS (SELECT 1 FROM bas_bewertungsplattform WHERE code = :code)"
        ).bindparams(code=code, name=name, website=website, icon=icon))

    # 2. Backfill: Copy existing Google ratings from metadaten JSON
    op.execute(sa.text("""
        INSERT INTO com_unternehmen_bewertung
            (id, unternehmen_id, plattform_id, bewertung, anzahl_bewertungen,
             verteilung, erstellt_am, aktualisiert_am)
        SELECT
            gen_random_uuid()::text,
            u.id,
            p.id,
            (u.metadaten->'google'->>'rating')::float,
            (u.metadaten->'google'->>'rating_count')::int,
            u.metadaten->'google'->'rating_distribution',
            NOW(),
            NOW()
        FROM com_unternehmen u
        CROSS JOIN bas_bewertungsplattform p
        WHERE p.code = 'google'
          AND u.metadaten->'google'->>'rating' IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM com_unternehmen_bewertung b
              WHERE b.unternehmen_id = u.id AND b.plattform_id = p.id
          )
    """))


def downgrade() -> None:
    """Remove seeded data (tables remain)."""
    op.execute(sa.text("DELETE FROM com_unternehmen_bewertung"))
    op.execute(sa.text("DELETE FROM bas_bewertungsplattform"))
