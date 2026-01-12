#!/usr/bin/env python3
"""
Script to create the initial superadmin account.

Usage:
    uv run python scripts/create_superadmin.py

IMPORTANT: The API key is displayed only once! Store it securely.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, async_session_maker
from app.services.partner import PartnerService
from app.schemas.partner import ApiPartnerCreate


async def main():
    """Create the initial superadmin account."""
    print("=" * 60)
    print("UDO API - Superadmin Setup")
    print("=" * 60)

    # Initialize database (creates tables if not exist)
    print("\n[1/3] Initialisiere Datenbank...")
    await init_db()
    print("      ✓ Datenbank initialisiert")

    # Create superadmin
    print("\n[2/3] Erstelle Superadmin-Account...")

    async with async_session_maker() as db:
        service = PartnerService(db)

        # Create the superadmin
        data = ApiPartnerCreate(
            name="Superadmin",
            email=None,  # Optional - can be set later via Admin API
            role="superadmin",
            kosten_geoapi_pro_einwohner=0.0,  # Superadmin hat keine Kosten
        )

        try:
            partner, api_key = await service.create_partner(data)
            await db.commit()

            print("      ✓ Superadmin erstellt")

            # Display the API key
            print("\n[3/3] API-Key generiert")
            print("\n" + "=" * 60)
            print("WICHTIG: Speichern Sie diesen API-Key sicher!")
            print("Er wird nur EINMAL angezeigt und kann nicht wiederhergestellt werden.")
            print("=" * 60)
            print(f"\n  API-Key: {api_key}\n")
            print("=" * 60)

            print("\nVerwendung:")
            print("  curl -H 'X-API-Key: <API-KEY>' http://localhost:8001/api/v1/admin/partners")
            print("\nOder in Swagger UI:")
            print("  1. Öffnen Sie http://localhost:8001/docs")
            print("  2. Klicken Sie auf 'Authorize'")
            print("  3. Geben Sie den API-Key ein")
            print()

        except Exception as e:
            print(f"      ✗ Fehler: {e}")
            print("\nHinweis: Wenn bereits ein Superadmin existiert,")
            print("können Sie einen neuen über die Admin-API erstellen.")
            raise


if __name__ == "__main__":
    asyncio.run(main())
