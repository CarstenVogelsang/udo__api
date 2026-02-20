"""
API Routes for UDO Klassifikation management.

Endpoints for managing company classification taxonomy and assignments.
These endpoints are only accessible by superadmin users.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.klassifikation import KlassifikationService
from app.schemas.com import (
    ComKlassifikationList,
    ComKlassifikationDetail,
    ComKlassifikationCreate,
    ComKlassifikationUpdate,
    ComUnternehmenKlassifikationDetail,
    ComUnternehmenKlassifikationAssign,
    ComUnternehmenList,
)

router = APIRouter(prefix="/klassifikationen", tags=["Klassifikationen"])


# ============ Klassifikation CRUD ============


@router.get("", response_model=ComKlassifikationList)
async def list_klassifikationen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    dimension: str | None = Query(
        None, description="Filter nach Dimension (kueche, betriebsart, angebot)"
    ),
    suche: str | None = Query(None, min_length=1, description="Suche in Name und Slug"),
    nur_aktiv: bool = Query(True, description="Nur aktive Klassifikationen"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller UDO-Klassifikationen (nur Superadmin).

    UDO-Klassifikationen sind deutsche Ergänzungen zu Google Place Types,
    z.B. "Döner-Imbiss", "Pommesbude", "Currywurstbude".

    **Filter:**
    - `dimension`: Filter nach Dimension (kueche, betriebsart, angebot)
    - `suche`: Textsuche in Name und Slug
    - `nur_aktiv`: Nur aktive Klassifikationen (Standard: true)
    """
    service = KlassifikationService(db)
    return await service.get_klassifikation_list(
        dimension=dimension,
        suche=suche,
        nur_aktiv=nur_aktiv,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ComKlassifikationDetail, status_code=status.HTTP_201_CREATED)
async def create_klassifikation(
    data: ComKlassifikationCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neue Klassifikation erstellen (nur Superadmin).

    **Request Body:**
    - `slug`: Eindeutiger Identifier (lowercase, underscore, z.B. "doener_imbiss")
    - `name_de`: Deutscher Anzeigename (z.B. "Döner-Imbiss")
    - `dimension`: Kategorie-Dimension (kueche, betriebsart, angebot)
    - `beschreibung`: Optionale Beschreibung
    - `google_mapping_gcid`: Optionales Mapping zu Google-Kategorie
    - `parent_id`: Optionale Eltern-Klassifikation (UUID)
    """
    service = KlassifikationService(db)

    # Check if slug already exists
    existing = await service.get_klassifikation_by_slug(data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Klassifikation mit Slug '{data.slug}' existiert bereits"
        )

    return await service.create_klassifikation(
        slug=data.slug,
        name_de=data.name_de,
        dimension=data.dimension,
        beschreibung=data.beschreibung,
        google_mapping_gcid=data.google_mapping_gcid,
        parent_id=data.parent_id,
    )


@router.get("/stats/count")
async def get_klassifikation_count(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    nur_aktiv: bool = Query(True, description="Nur aktive Klassifikationen zählen"),
):
    """
    Gesamtanzahl der Klassifikationen (nur Superadmin).
    """
    service = KlassifikationService(db)
    count = await service.get_klassifikation_count(nur_aktiv=nur_aktiv)
    return {"total": count}


@router.get("/dimensionen")
async def get_dimensionen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Liste aller Dimensionen (nur Superadmin).

    Gibt alle eindeutigen Dimensions-Werte zurück (z.B. "kueche", "betriebsart").
    """
    service = KlassifikationService(db)
    dimensions = await service.get_dimensions()
    return {"dimensionen": dimensions}


@router.get("/slug/{slug}", response_model=ComKlassifikationDetail)
async def get_klassifikation_by_slug(
    slug: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Klassifikation nach Slug abrufen (nur Superadmin).

    - **slug**: Eindeutiger Slug (z.B. "doener_imbiss")
    """
    service = KlassifikationService(db)
    klass = await service.get_klassifikation_by_slug(slug)
    if not klass:
        raise HTTPException(status_code=404, detail="Klassifikation nicht gefunden")
    return klass


@router.get("/{klassifikation_id}", response_model=ComKlassifikationDetail)
async def get_klassifikation(
    klassifikation_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelne Klassifikation abrufen (nur Superadmin).

    - **klassifikation_id**: UUID der Klassifikation
    """
    service = KlassifikationService(db)
    klass = await service.get_klassifikation_by_id(klassifikation_id)
    if not klass:
        raise HTTPException(status_code=404, detail="Klassifikation nicht gefunden")
    return klass


@router.patch("/{klassifikation_id}", response_model=ComKlassifikationDetail)
async def update_klassifikation(
    klassifikation_id: str,
    data: ComKlassifikationUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Klassifikation aktualisieren (nur Superadmin).

    - **klassifikation_id**: UUID der Klassifikation

    **Request Body (alle optional):**
    - `slug`: Neuer Slug
    - `name_de`: Neuer Name
    - `dimension`: Neue Dimension
    - `beschreibung`: Neue Beschreibung
    - `google_mapping_gcid`: Neues Google-Mapping
    - `parent_id`: Neue Eltern-Klassifikation
    - `ist_aktiv`: Aktiv-Status
    """
    service = KlassifikationService(db)

    # Check slug uniqueness if changing
    if data.slug:
        existing = await service.get_klassifikation_by_slug(data.slug)
        if existing and str(existing.id) != klassifikation_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Klassifikation mit Slug '{data.slug}' existiert bereits"
            )

    klass = await service.update_klassifikation(
        klassifikation_id,
        slug=data.slug,
        name_de=data.name_de,
        dimension=data.dimension,
        beschreibung=data.beschreibung,
        google_mapping_gcid=data.google_mapping_gcid,
        parent_id=data.parent_id,
        ist_aktiv=data.ist_aktiv,
    )
    if not klass:
        raise HTTPException(status_code=404, detail="Klassifikation nicht gefunden")
    return klass


@router.delete("/{klassifikation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_klassifikation(
    klassifikation_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Klassifikation löschen (nur Superadmin).

    Löscht auch alle Zuordnungen zu Unternehmen (via CASCADE).

    - **klassifikation_id**: UUID der Klassifikation
    """
    service = KlassifikationService(db)
    deleted = await service.delete_klassifikation(klassifikation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Klassifikation nicht gefunden")


@router.get("/{klassifikation_id}/unternehmen", response_model=ComUnternehmenList)
async def get_klassifikation_unternehmen(
    klassifikation_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Unternehmen mit dieser Klassifikation auflisten (nur Superadmin).

    Gibt alle Unternehmen zurück, denen diese Klassifikation zugeordnet ist.

    - **klassifikation_id**: UUID der Klassifikation
    """
    service = KlassifikationService(db)

    # Verify klassifikation exists
    klass = await service.get_klassifikation_by_id(klassifikation_id)
    if not klass:
        raise HTTPException(status_code=404, detail="Klassifikation nicht gefunden")

    return await service.get_unternehmen_for_klassifikation(
        klassifikation_id, skip=skip, limit=limit
    )


# ============ Unternehmen Assignments ============
# Note: These are also in com.py router as /unternehmen/{id}/klassifikationen
# This provides the reverse lookup from klassifikation perspective


@router.post(
    "/{klassifikation_id}/unternehmen/{unternehmen_id}",
    response_model=ComUnternehmenKlassifikationDetail,
    status_code=status.HTTP_201_CREATED,
)
async def assign_klassifikation_to_unternehmen(
    klassifikation_id: str,
    unternehmen_id: str,
    data: ComUnternehmenKlassifikationAssign | None = None,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Klassifikation zu Unternehmen zuordnen (nur Superadmin).

    - **klassifikation_id**: UUID der Klassifikation
    - **unternehmen_id**: UUID des Unternehmens

    **Request Body (optional):**
    - `ist_primaer`: Als primäre Klassifikation markieren
    - `quelle`: Quelle der Zuordnung (manuell, regel, ki)
    """
    service = KlassifikationService(db)

    ist_primaer = data.ist_primaer if data else False
    quelle = data.quelle if data else "manuell"

    result = await service.assign_klassifikation(
        unternehmen_id=unternehmen_id,
        klassifikation_id=klassifikation_id,
        ist_primaer=ist_primaer,
        quelle=quelle,
    )
    if not result:
        raise HTTPException(status_code=409, detail="Zuordnung existiert bereits")

    # Reload with full data
    klassifikationen = await service.get_klassifikationen_for_unternehmen(unternehmen_id)
    for k in klassifikationen:
        if str(k.klassifikation_id) == klassifikation_id:
            return k

    return result


@router.delete(
    "/{klassifikation_id}/unternehmen/{unternehmen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_klassifikation_from_unternehmen(
    klassifikation_id: str,
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Klassifikation von Unternehmen entfernen (nur Superadmin).

    - **klassifikation_id**: UUID der Klassifikation
    - **unternehmen_id**: UUID des Unternehmens
    """
    service = KlassifikationService(db)
    removed = await service.remove_klassifikation(unternehmen_id, klassifikation_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Zuordnung nicht gefunden")
