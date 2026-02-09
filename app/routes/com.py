"""
API Routes for Company (Unternehmen) data.

All endpoints return the full GeoOrt hierarchy (Ort → Kreis → Bundesland → Land).
These endpoints are only accessible by superadmin users.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.com import ComService
from app.services.kontakt import KontaktService
from app.services.smart_filter import SmartFilterService
from app.services.smart_filter_parser import parse_unternehmen_filter, SmartFilterError
from app.schemas.com import (
    ComUnternehmenWithGeo,
    ComUnternehmenDetail,
    ComUnternehmenList,
    ComUnternehmenCreate,
    ComUnternehmenUpdate,
    ComKontaktBase,
    ComKontaktDetail,
    ComKontaktList,
    ComKontaktCreate,
    ComKontaktUpdate,
)

router = APIRouter(prefix="/unternehmen", tags=["Unternehmen"])


@router.get("", response_model=ComUnternehmenList)
async def list_unternehmen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    geo_ort_id: str | None = Query(None, description="Filter nach Ort-UUID"),
    suche: str | None = Query(
        None,
        min_length=2,
        description="Suche nach Kurzname oder Firmierung"
    ),
    smart_filter_id: str | None = Query(None, description="Gespeicherten Smart Filter anwenden"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller Unternehmen mit vollständiger Geo-Hierarchie (nur Superadmin).

    **Filter:**
    - `geo_ort_id`: Nur Unternehmen aus diesem Ort
    - `suche`: Textsuche in Kurzname und Firmierung
    - `smart_filter_id`: Gespeicherten Smart Filter anwenden (kombinierbar mit suche/geo_ort_id)

    **Response:**
    Jedes Unternehmen enthält die vollständige Geo-Hierarchie:
    Ort → Kreis → Bundesland → Land
    """
    filter_conditions = None

    if smart_filter_id:
        filter_service = SmartFilterService(db)
        smart_filter = await filter_service.get_filter_by_id(smart_filter_id)
        if not smart_filter:
            raise HTTPException(status_code=404, detail="Smart Filter nicht gefunden")
        try:
            condition = parse_unternehmen_filter(smart_filter.dsl_expression)
            filter_conditions = [condition]
        except SmartFilterError as e:
            raise HTTPException(status_code=400, detail=f"Smart Filter DSL error: {e}")

    service = ComService(db)
    return await service.get_unternehmen_list(
        geo_ort_id=geo_ort_id,
        suche=suche,
        skip=skip,
        limit=limit,
        filter_conditions=filter_conditions,
    )


@router.get("/{unternehmen_id}", response_model=ComUnternehmenDetail)
async def get_unternehmen(
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnes Unternehmen mit vollständiger Geo-Hierarchie (nur Superadmin).

    - **unternehmen_id**: UUID des Unternehmens
    """
    service = ComService(db)
    unternehmen = await service.get_unternehmen_by_id(unternehmen_id)
    if not unternehmen:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
    return unternehmen


@router.get("/legacy/{legacy_id}", response_model=ComUnternehmenDetail)
async def get_unternehmen_by_legacy_id(
    legacy_id: int,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unternehmen nach Legacy-ID (kStore) abrufen (nur Superadmin).

    Die Legacy-ID entspricht dem Primary Key `kStore` aus der
    ursprünglichen spi_tStore Tabelle.

    - **legacy_id**: kStore aus der Legacy-Datenbank
    """
    service = ComService(db)
    unternehmen = await service.get_unternehmen_by_legacy_id(legacy_id)
    if not unternehmen:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
    return unternehmen


@router.get("/stats/count")
async def get_unternehmen_count(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Gesamtanzahl der Unternehmen (nur Superadmin).
    """
    service = ComService(db)
    count = await service.get_unternehmen_count()
    return {"total": count}


# ============ Unternehmen CRUD Endpoints ============


@router.post("", response_model=ComUnternehmenDetail, status_code=status.HTTP_201_CREATED)
async def create_unternehmen(
    data: ComUnternehmenCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neues Unternehmen erstellen (nur Superadmin).

    **Pflichtfelder:**
    - `kurzname`: Kurzname des Unternehmens

    **Optionale Felder:**
    - `firmierung`: Vollständiger Firmenname
    - `strasse`: Straßenname
    - `strasse_hausnr`: Hausnummer
    - `geo_ort_id`: UUID des Ortes (aus /geo/orte)
    - `legacy_id`: Optionale Legacy-ID für Migration
    """
    service = ComService(db)
    return await service.create_unternehmen(**data.model_dump())


@router.patch("/{unternehmen_id}", response_model=ComUnternehmenDetail)
async def update_unternehmen(
    unternehmen_id: str,
    data: ComUnternehmenUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unternehmen aktualisieren (nur Superadmin).

    Es werden nur die übermittelten Felder aktualisiert (partial update).

    - **unternehmen_id**: UUID des Unternehmens
    """
    service = ComService(db)

    # Filter out None values for partial update
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    unternehmen = await service.update_unternehmen(unternehmen_id, **update_data)
    if not unternehmen:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
    return unternehmen


@router.delete("/{unternehmen_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unternehmen(
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unternehmen löschen (nur Superadmin).

    **Achtung:** Löscht auch alle zugehörigen Kontakte und
    Organisations-Zuordnungen.

    - **unternehmen_id**: UUID des Unternehmens
    """
    service = ComService(db)
    deleted = await service.delete_unternehmen(unternehmen_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")


# ============ Kontakt Endpoints ============


@router.get("/{unternehmen_id}/kontakte", response_model=ComKontaktList)
async def list_kontakte(
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller Kontakte eines Unternehmens (nur Superadmin).

    Kontakte werden sortiert nach:
    1. Hauptkontakt zuerst
    2. Nachname alphabetisch
    3. Vorname alphabetisch
    """
    service = KontaktService(db)

    # Check if Unternehmen exists
    if not await service.unternehmen_exists(unternehmen_id):
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")

    return await service.get_kontakte_for_unternehmen(
        unternehmen_id=unternehmen_id,
        skip=skip,
        limit=limit
    )


@router.post(
    "/{unternehmen_id}/kontakte",
    response_model=ComKontaktDetail,
    status_code=status.HTTP_201_CREATED
)
async def create_kontakt(
    unternehmen_id: str,
    data: ComKontaktCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neuen Kontakt für ein Unternehmen erstellen (nur Superadmin).

    **Pflichtfelder:**
    - `vorname`: Vorname des Kontakts
    - `nachname`: Nachname des Kontakts

    **Optionale Felder:**
    - `typ`: Kontakttyp (z.B. "Geschäftsführer", "Einkauf")
    - `titel`: Akademischer Titel (z.B. "Dr.", "Prof.")
    - `position`: Berufsbezeichnung
    - `abteilung`: Abteilung im Unternehmen
    - `telefon`: Festnetz
    - `mobil`: Mobilnummer
    - `fax`: Faxnummer
    - `email`: E-Mail-Adresse
    - `notizen`: Freitext-Notizen
    - `ist_hauptkontakt`: Als Hauptkontakt markieren
    """
    service = KontaktService(db)

    # Check if Unternehmen exists
    if not await service.unternehmen_exists(unternehmen_id):
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")

    return await service.create_kontakt(
        unternehmen_id=unternehmen_id,
        **data.model_dump()
    )


@router.get("/{unternehmen_id}/kontakte/{kontakt_id}", response_model=ComKontaktDetail)
async def get_kontakt(
    unternehmen_id: str,
    kontakt_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnen Kontakt abrufen (nur Superadmin).
    """
    service = KontaktService(db)

    kontakt = await service.get_kontakt_by_id(kontakt_id, unternehmen_id)
    if not kontakt:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")

    return kontakt


@router.patch("/{unternehmen_id}/kontakte/{kontakt_id}", response_model=ComKontaktDetail)
async def update_kontakt(
    unternehmen_id: str,
    kontakt_id: str,
    data: ComKontaktUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Kontakt aktualisieren (nur Superadmin).

    Es werden nur die übermittelten Felder aktualisiert (partial update).
    """
    service = KontaktService(db)

    # Filter out None values for partial update
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    kontakt = await service.update_kontakt(
        kontakt_id=kontakt_id,
        unternehmen_id=unternehmen_id,
        **update_data
    )

    if not kontakt:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")

    return kontakt


@router.delete(
    "/{unternehmen_id}/kontakte/{kontakt_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_kontakt(
    unternehmen_id: str,
    kontakt_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Kontakt löschen (nur Superadmin).
    """
    service = KontaktService(db)

    deleted = await service.delete_kontakt(
        kontakt_id=kontakt_id,
        unternehmen_id=unternehmen_id
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
