"""
API Route for Hersteller-Recherche bulk import.

Accepts the complete research JSON and imports all data in one transaction.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.schemas.hersteller_recherche import (
    HerstellerRechercheImport,
    ImportResult,
)
from app.services.hersteller_recherche import HerstellerRechercheService

router = APIRouter(prefix="/hersteller-recherche", tags=["Hersteller-Recherche Import"])


@router.post("/import", response_model=ImportResult)
async def import_hersteller_recherche(
    data: HerstellerRechercheImport,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    dry_run: bool = Query(False, description="Nur simulieren, keine DB-Änderungen"),
):
    """
    Vollständiges Recherche-JSON importieren.

    Nimmt das JSON der Recherche-KI entgegen und importiert alle Daten:
    - Hersteller (ComUnternehmen) anlegen/aktualisieren
    - Rechtsform + Herkunftsland mappen
    - EU-Bevollmächtigter (GPSR) anlegen
    - Profiltexte (B2C/B2B) für Hersteller, Marken, Serien
    - Logos/Medien mit Lizenz-Referenz
    - Marken + Serien (Dedup über Name)
    - Quellen (Upsert über URL)
    - Vertriebsstruktur
    - Unternehmenstyp-Klassifikationen

    **Sicherheitsregeln:**
    - Bestehende Daten werden NICHT überschrieben (nur leere Felder befüllt)
    - Bei Unsicherheit: Warnung im Response statt stille Überschreibung

    **Dry-Run:** `?dry_run=true` zeigt was passieren würde, ohne DB-Änderungen.
    """
    service = HerstellerRechercheService(db)
    return await service.importiere(data, dry_run=dry_run)
