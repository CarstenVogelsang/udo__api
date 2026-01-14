"""
API Routes for Organisation management.

Endpoints for managing organisation groupings of companies.
These endpoints are only accessible by superadmin users.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.organisation import OrganisationService
from app.schemas.com import (
    ComOrganisationList,
    ComOrganisationDetail,
    ComOrganisationCreate,
    ComOrganisationUpdate,
    ComUnternehmenList,
)

router = APIRouter(prefix="/organisationen", tags=["Organisationen"])


@router.get("", response_model=ComOrganisationList)
async def list_organisationen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    suche: str | None = Query(None, min_length=2, description="Suche nach Kurzname"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller Organisationen (nur Superadmin).

    Organisationen sind Gruppen wie Verbände, Einkaufsgemeinschaften oder Konzerne,
    denen mehrere Unternehmen angehören können.

    **Filter:**
    - `suche`: Textsuche im Kurznamen
    """
    service = OrganisationService(db)
    return await service.get_organisation_list(suche=suche, skip=skip, limit=limit)


@router.post("", response_model=ComOrganisationDetail, status_code=status.HTTP_201_CREATED)
async def create_organisation(
    data: ComOrganisationCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neue Organisation erstellen (nur Superadmin).

    **Request Body:**
    - `kurzname`: Name der Organisation (erforderlich)
    - `legacy_id`: Optionale Legacy-ID (kStoreGruppe)
    """
    service = OrganisationService(db)
    return await service.create_organisation(
        kurzname=data.kurzname,
        legacy_id=data.legacy_id
    )


@router.get("/stats/count")
async def get_organisation_count(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Gesamtanzahl der Organisationen (nur Superadmin).
    """
    service = OrganisationService(db)
    count = await service.get_organisation_count()
    return {"total": count}


@router.get("/{organisation_id}", response_model=ComOrganisationDetail)
async def get_organisation(
    organisation_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelne Organisation abrufen (nur Superadmin).

    - **organisation_id**: UUID der Organisation
    """
    service = OrganisationService(db)
    org = await service.get_organisation_by_id(organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return org


@router.patch("/{organisation_id}", response_model=ComOrganisationDetail)
async def update_organisation(
    organisation_id: str,
    data: ComOrganisationUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Organisation aktualisieren (nur Superadmin).

    - **organisation_id**: UUID der Organisation

    **Request Body:**
    - `kurzname`: Neuer Name (optional)
    """
    service = OrganisationService(db)
    org = await service.update_organisation(organisation_id, kurzname=data.kurzname)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return org


@router.delete("/{organisation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organisation(
    organisation_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Organisation löschen (nur Superadmin).

    Löscht auch alle Zuordnungen zu Unternehmen.

    - **organisation_id**: UUID der Organisation
    """
    service = OrganisationService(db)
    deleted = await service.delete_organisation(organisation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")


@router.get("/{organisation_id}/unternehmen", response_model=ComUnternehmenList)
async def get_organisation_unternehmen(
    organisation_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Unternehmen einer Organisation auflisten (nur Superadmin).

    Gibt alle Unternehmen zurück, die dieser Organisation zugeordnet sind.

    - **organisation_id**: UUID der Organisation
    """
    service = OrganisationService(db)

    # Verify organisation exists
    org = await service.get_organisation_by_id(organisation_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")

    return await service.get_unternehmen_for_organisation(
        organisation_id, skip=skip, limit=limit
    )


@router.post(
    "/{organisation_id}/unternehmen/{unternehmen_id}",
    status_code=status.HTTP_201_CREATED
)
async def assign_unternehmen(
    organisation_id: str,
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unternehmen zu Organisation zuordnen (nur Superadmin).

    - **organisation_id**: UUID der Organisation
    - **unternehmen_id**: UUID des Unternehmens
    """
    service = OrganisationService(db)
    result = await service.assign_unternehmen(organisation_id, unternehmen_id)
    if not result:
        raise HTTPException(status_code=409, detail="Zuordnung existiert bereits")
    return {"message": "Zuordnung erstellt"}


@router.delete(
    "/{organisation_id}/unternehmen/{unternehmen_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_unternehmen(
    organisation_id: str,
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unternehmen aus Organisation entfernen (nur Superadmin).

    - **organisation_id**: UUID der Organisation
    - **unternehmen_id**: UUID des Unternehmens
    """
    service = OrganisationService(db)
    removed = await service.remove_unternehmen(organisation_id, unternehmen_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Zuordnung nicht gefunden")


@router.get("/legacy/{legacy_id}", response_model=ComOrganisationDetail)
async def get_organisation_by_legacy_id(
    legacy_id: int,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Organisation nach Legacy-ID (kStoreGruppe) abrufen (nur Superadmin).

    Die Legacy-ID entspricht dem Primary Key `kStoreGruppe` aus der
    ursprünglichen spi_tStoreGruppe Tabelle.

    - **legacy_id**: kStoreGruppe aus der Legacy-Datenbank
    """
    service = OrganisationService(db)
    org = await service.get_organisation_by_legacy_id(legacy_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")
    return org
