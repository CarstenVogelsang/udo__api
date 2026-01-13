#!/usr/bin/env python3
"""
Script to create standard color palettes.

Usage:
    uv run python scripts/setup_color_palettes.py

This creates a set of predefined color palettes that can be assigned
to geo entities (countries, states, etc.) for theming purposes.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import init_db, async_session_maker
from app.models.base import BasColorPalette
from app.models.geo import generate_uuid


# Standard palettes based on national/regional colors
STANDARD_PALETTES = [
    {
        "name": "Deutschland Schwarz-Rot-Gold",
        "slug": "deutschland-schwarz-rot-gold",
        "primary": "#000000",    # Schwarz
        "secondary": "#DD0000",  # Rot
        "accent": "#FFCC00",     # Gold
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "warm",
    },
    {
        "name": "Bayern Blau-Weiß",
        "slug": "bayern-blau-weiss",
        "primary": "#0066B3",    # Bayerisch Blau
        "secondary": "#FFFFFF",  # Weiß
        "accent": "#FFD700",     # Gold
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "cool",
    },
    {
        "name": "Baden-Württemberg Schwarz-Gold",
        "slug": "baden-wuerttemberg-schwarz-gold",
        "primary": "#000000",    # Schwarz
        "secondary": "#FFCC00",  # Gold
        "accent": "#D4AF37",
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "warm",
    },
    {
        "name": "Nordrhein-Westfalen Grün-Weiß-Rot",
        "slug": "nrw-gruen-weiss-rot",
        "primary": "#009640",    # Grün
        "secondary": "#FFFFFF",  # Weiß
        "accent": "#E30613",     # Rot
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "cool",
    },
    {
        "name": "Hessen Rot-Weiß",
        "slug": "hessen-rot-weiss",
        "primary": "#CE1126",    # Rot
        "secondary": "#FFFFFF",  # Weiß
        "accent": "#FFD700",
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "warm",
    },
    {
        "name": "Sachsen Grün-Weiß",
        "slug": "sachsen-gruen-weiss",
        "primary": "#009639",    # Grün
        "secondary": "#FFFFFF",  # Weiß
        "accent": "#000000",
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "cool",
    },
    {
        "name": "Berlin Rot-Weiß",
        "slug": "berlin-rot-weiss",
        "primary": "#E2001A",    # Rot
        "secondary": "#FFFFFF",  # Weiß
        "accent": "#000000",
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "warm",
    },
    {
        "name": "Hamburg Rot-Weiß",
        "slug": "hamburg-rot-weiss",
        "primary": "#E2001A",    # Rot
        "secondary": "#FFFFFF",  # Weiß
        "accent": "#FFD700",
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "warm",
    },
    {
        "name": "Neutral Grau",
        "slug": "neutral-grau",
        "primary": "#6B7280",    # Grau
        "secondary": "#9CA3AF",  # Hellgrau
        "accent": "#374151",
        "neutral": "#374151",
        "info": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "category": "neutral",
        "is_default": True,
    },
]


async def main():
    """Create standard color palettes."""
    print("=" * 60)
    print("UDO API - Color Palette Setup")
    print("=" * 60)

    # Initialize database
    print("\n[1/2] Initialisiere Datenbank...")
    await init_db()
    print("      ✓ Datenbank initialisiert")

    # Create palettes
    print("\n[2/2] Erstelle Farbpaletten...")

    async with async_session_maker() as db:
        created = 0
        skipped = 0

        for palette_data in STANDARD_PALETTES:
            # Check if already exists
            result = await db.execute(
                select(BasColorPalette).where(
                    BasColorPalette.slug == palette_data["slug"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"      ⊘ {palette_data['name']} (existiert bereits)")
                skipped += 1
                continue

            # Create new palette
            palette = BasColorPalette(
                id=generate_uuid(),
                name=palette_data["name"],
                slug=palette_data["slug"],
                primary=palette_data["primary"],
                secondary=palette_data["secondary"],
                accent=palette_data["accent"],
                neutral=palette_data["neutral"],
                info=palette_data["info"],
                success=palette_data["success"],
                warning=palette_data["warning"],
                error=palette_data["error"],
                category=palette_data.get("category"),
                is_default=palette_data.get("is_default", False),
            )
            db.add(palette)
            print(f"      ✓ {palette_data['name']}")
            created += 1

        await db.commit()

    # Summary
    print("\n" + "=" * 60)
    print(f"Ergebnis: {created} erstellt, {skipped} übersprungen")
    print("=" * 60)

    print("\nVerwendung:")
    print("  Die Paletten können über das Admin-API oder direkt")
    print("  per SQL einer Geo-Entität zugewiesen werden:")
    print()
    print("  UPDATE geo_bundesland")
    print("  SET color_palette_id = (SELECT id FROM bas_color_palette WHERE slug = 'bayern-blau-weiss')")
    print("  WHERE code = 'DE-BY';")
    print()


if __name__ == "__main__":
    asyncio.run(main())
