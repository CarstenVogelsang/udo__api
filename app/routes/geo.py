"""
API Routes for Geodata (Superadmin only).

All endpoints return the full parent hierarchy for each entity.
These endpoints are only accessible by superadmin users.
For partner access, use /partner/geodaten/ endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.geo import GeoService
from app.schemas.geo import (
    GeoLandBase,
    GeoLandDetail,
    GeoLandList,
    GeoBundeslandWithParent,
    GeoBundeslandDetail,
    GeoBundeslandList,
    GeoRegierungsbezirkWithParents,
    GeoRegierungsbezirkList,
    GeoKreisWithParents,
    GeoKreisDetail,
    GeoKreisList,
    GeoOrtWithParents,
    GeoOrtDetail,
    GeoOrtList,
    GeoOrtsteilWithParents,
    GeoOrtsteilDetail,
    GeoOrtsteilList,
)

router = APIRouter(prefix="/geo", tags=["Geodaten"])


# ============ Länder ============

@router.get("/laender", response_model=GeoLandList)
async def list_laender(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller Länder (nur Superadmin).

    Gibt eine paginierte Liste aller Länder zurück.
    """
    service = GeoService(db)
    return await service.get_laender(skip=skip, limit=limit)


@router.get("/laender/{land_id}", response_model=GeoLandDetail)
async def get_land(
    land_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnes Land abrufen (nur Superadmin).

    - **land_id**: UUID des Landes
    """
    service = GeoService(db)
    land = await service.get_land_by_id(land_id)
    if not land:
        raise HTTPException(status_code=404, detail="Land nicht gefunden")
    return land


@router.get("/laender/code/{code}", response_model=GeoLandDetail)
async def get_land_by_code(
    code: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Land nach ISO-Code abrufen (nur Superadmin).

    - **code**: ISO 3166-1 alpha-2 Code (z.B. "DE")
    """
    service = GeoService(db)
    land = await service.get_land_by_code(code)
    if not land:
        raise HTTPException(status_code=404, detail="Land nicht gefunden")
    return land


# ============ Bundesländer ============

@router.get("/bundeslaender", response_model=GeoBundeslandList)
async def list_bundeslaender(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    land_id: str | None = Query(None, description="Filter nach Land-UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Bundesländer (nur Superadmin).

    Optional filterbar nach Land.
    Jedes Bundesland enthält sein übergeordnetes Land.
    """
    service = GeoService(db)
    return await service.get_bundeslaender(land_id=land_id, skip=skip, limit=limit)


@router.get("/bundeslaender/{bundesland_id}", response_model=GeoBundeslandDetail)
async def get_bundesland(
    bundesland_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnes Bundesland mit Land abrufen (nur Superadmin).

    - **bundesland_id**: UUID des Bundeslandes
    """
    service = GeoService(db)
    bl = await service.get_bundesland_by_id(bundesland_id)
    if not bl:
        raise HTTPException(status_code=404, detail="Bundesland nicht gefunden")
    return bl


@router.get("/bundeslaender/code/{code}", response_model=GeoBundeslandDetail)
async def get_bundesland_by_code(
    code: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Bundesland nach Code abrufen (nur Superadmin).

    - **code**: Hierarchischer Code (z.B. "DE-BY")
    """
    service = GeoService(db)
    bl = await service.get_bundesland_by_code(code)
    if not bl:
        raise HTTPException(status_code=404, detail="Bundesland nicht gefunden")
    return bl


# ============ Regierungsbezirke ============

@router.get("/regierungsbezirke", response_model=GeoRegierungsbezirkList)
async def list_regierungsbezirke(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    bundesland_id: str | None = Query(None, description="Filter nach Bundesland-UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Regierungsbezirke (nur Superadmin).

    Optional filterbar nach Bundesland.
    Enthält die vollständige übergeordnete Hierarchie.
    """
    service = GeoService(db)
    return await service.get_regierungsbezirke(bundesland_id=bundesland_id, skip=skip, limit=limit)


@router.get("/regierungsbezirke/{regbez_id}", response_model=GeoRegierungsbezirkWithParents)
async def get_regierungsbezirk(
    regbez_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelner Regierungsbezirk mit vollständiger Hierarchie (nur Superadmin).
    """
    service = GeoService(db)
    regbez = await service.get_regierungsbezirk_by_id(regbez_id)
    if not regbez:
        raise HTTPException(status_code=404, detail="Regierungsbezirk nicht gefunden")
    return regbez


# ============ Kreise ============

@router.get("/kreise", response_model=GeoKreisList)
async def list_kreise(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    bundesland_id: str | None = Query(None, description="Filter nach Bundesland-UUID"),
    regierungsbezirk_id: str | None = Query(None, description="Filter nach Regierungsbezirk-UUID"),
    autokennzeichen: str | None = Query(None, description="Filter nach Autokennzeichen (z.B. 'M')"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Kreise mit vollständiger Hierarchie (nur Superadmin).

    Filterbar nach Bundesland, Regierungsbezirk oder Autokennzeichen.
    Jeder Kreis enthält: Regierungsbezirk → Bundesland → Land
    """
    service = GeoService(db)
    return await service.get_kreise(
        bundesland_id=bundesland_id,
        regierungsbezirk_id=regierungsbezirk_id,
        autokennzeichen=autokennzeichen,
        skip=skip,
        limit=limit
    )


@router.get("/kreise/{kreis_id}", response_model=GeoKreisDetail)
async def get_kreis(
    kreis_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelner Kreis mit vollständiger Hierarchie (nur Superadmin).

    Enthält: Regierungsbezirk → Bundesland → Land
    """
    service = GeoService(db)
    kreis = await service.get_kreis_by_id(kreis_id)
    if not kreis:
        raise HTTPException(status_code=404, detail="Kreis nicht gefunden")
    return kreis


@router.get("/kreise/ags/{ags}", response_model=GeoKreisDetail)
async def get_kreis_by_ags(
    ags: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Kreis nach AGS-Code (nur Superadmin).

    - **ags**: 5-stelliger Kreisschlüssel (z.B. "09162")
    """
    service = GeoService(db)
    kreis = await service.get_kreis_by_ags(ags)
    if not kreis:
        raise HTTPException(status_code=404, detail="Kreis nicht gefunden")
    return kreis


# ============ Orte ============

@router.get("/orte", response_model=GeoOrtList)
async def list_orte(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    kreis_id: str | None = Query(None, description="Filter nach Kreis-UUID"),
    plz: str | None = Query(None, min_length=4, max_length=10, description="Filter nach PLZ"),
    suche: str | None = Query(None, min_length=2, description="Suche nach Ortsname"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Orte mit vollständiger Hierarchie (nur Superadmin).

    Filterbar nach Kreis, PLZ oder Ortsname.
    Jeder Ort enthält: Kreis → Regierungsbezirk → Bundesland → Land
    """
    service = GeoService(db)
    return await service.get_orte(
        kreis_id=kreis_id,
        plz=plz,
        suche=suche,
        skip=skip,
        limit=limit
    )


@router.get("/orte/{ort_id}", response_model=GeoOrtDetail)
async def get_ort(
    ort_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelner Ort mit vollständiger Hierarchie (nur Superadmin).
    """
    service = GeoService(db)
    ort = await service.get_ort_by_id(ort_id)
    if not ort:
        raise HTTPException(status_code=404, detail="Ort nicht gefunden")
    return ort


# ============ Ortsteile ============

@router.get("/ortsteile", response_model=GeoOrtsteilList)
async def list_ortsteile(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    ort_id: str | None = Query(None, description="Filter nach Ort-UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Ortsteile mit vollständiger Hierarchie (nur Superadmin).

    Filterbar nach Ort.
    Jeder Ortsteil enthält: Ort → Kreis → Regierungsbezirk → Bundesland → Land
    """
    service = GeoService(db)
    return await service.get_ortsteile(ort_id=ort_id, skip=skip, limit=limit)


@router.get("/ortsteile/{ortsteil_id}", response_model=GeoOrtsteilDetail)
async def get_ortsteil(
    ortsteil_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelner Ortsteil mit vollständiger Hierarchie (nur Superadmin).
    """
    service = GeoService(db)
    ortsteil = await service.get_ortsteil_by_id(ortsteil_id)
    if not ortsteil:
        raise HTTPException(status_code=404, detail="Ortsteil nicht gefunden")
    return ortsteil
