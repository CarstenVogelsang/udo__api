"""
API Routes for Plugin administration.

Provides CRUD operations for:
- Plugins
- Kategorien (Categories)
- Projekttypen (Project types)
- Preise (Prices)

All endpoints require superadmin authentication.

IMPORTANT: Route order matters in FastAPI!
Static paths (e.g., /kategorien, /projekttypen) must come BEFORE
dynamic paths (e.g., /{plugin_id}) to avoid matching issues.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.plugin import (
    KategorieService,
    PluginService,
    ProjekttypService,
    PreisService,
)
from app.schemas.plugin import (
    # Kategorie
    PlgKategorieBase,
    PlgKategorieDetail,
    PlgKategorieList,
    PlgKategorieCreate,
    PlgKategorieUpdate,
    # Plugin
    PlgPluginBase,
    PlgPluginDetail,
    PlgPluginList,
    PlgPluginCreate,
    PlgPluginUpdate,
    PlgPluginVersionDetail,
    PlgPluginVersionCreate,
    # Projekttyp
    PlgProjekttypBase,
    PlgProjekttypDetail,
    PlgProjekttypList,
    PlgProjekttypCreate,
    PlgProjekttypUpdate,
    # Preis
    PlgPreisBase,
    PlgPreisDetail,
    PlgPreisList,
    PlgPreisCreate,
    PlgPreisUpdate,
)

router = APIRouter(prefix="/plugins", tags=["Plugins (Admin)"])


# =============================================================================
# Kategorie Routes (static paths first)
# =============================================================================

@router.get("/kategorien", response_model=PlgKategorieList)
async def list_kategorien(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    nur_aktiv: bool = Query(True, description="Nur aktive Kategorien"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Plugin-Kategorien (nur Superadmin)."""
    service = KategorieService(db)
    return await service.get_list(nur_aktiv=nur_aktiv, skip=skip, limit=limit)


@router.get("/kategorien/{kategorie_id}", response_model=PlgKategorieDetail)
async def get_kategorie(
    kategorie_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelne Kategorie abrufen (nur Superadmin)."""
    service = KategorieService(db)
    kategorie = await service.get_by_id(kategorie_id)
    if not kategorie:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    return kategorie


@router.post("/kategorien", response_model=PlgKategorieDetail, status_code=status.HTTP_201_CREATED)
async def create_kategorie(
    data: PlgKategorieCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neue Kategorie erstellen (nur Superadmin)."""
    service = KategorieService(db)

    # Check if slug already exists
    existing = await service.get_by_slug(data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug bereits vergeben")

    return await service.create(**data.model_dump())


@router.put("/kategorien/{kategorie_id}", response_model=PlgKategorieDetail)
async def update_kategorie(
    kategorie_id: str,
    data: PlgKategorieUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Kategorie aktualisieren (nur Superadmin)."""
    service = KategorieService(db)
    kategorie = await service.update(kategorie_id, **data.model_dump(exclude_unset=True))
    if not kategorie:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")
    return kategorie


@router.delete("/kategorien/{kategorie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kategorie(
    kategorie_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Kategorie deaktivieren (nur Superadmin)."""
    service = KategorieService(db)
    if not await service.delete(kategorie_id):
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden")


# =============================================================================
# Projekttyp Routes (static paths - must come before /{plugin_id})
# =============================================================================

@router.get("/projekttypen", response_model=PlgProjekttypList)
async def list_projekttypen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Projekttypen (nur Superadmin)."""
    service = ProjekttypService(db)
    return await service.get_list(skip=skip, limit=limit)


@router.get("/projekttypen/{projekttyp_id}", response_model=PlgProjekttypDetail)
async def get_projekttyp(
    projekttyp_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelnen Projekttyp abrufen (nur Superadmin)."""
    service = ProjekttypService(db)
    projekttyp = await service.get_by_id(projekttyp_id)
    if not projekttyp:
        raise HTTPException(status_code=404, detail="Projekttyp nicht gefunden")
    return projekttyp


@router.post("/projekttypen", response_model=PlgProjekttypDetail, status_code=status.HTTP_201_CREATED)
async def create_projekttyp(
    data: PlgProjekttypCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neuen Projekttyp erstellen (nur Superadmin)."""
    service = ProjekttypService(db)

    # Check if slug already exists
    existing = await service.get_by_slug(data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug bereits vergeben")

    return await service.create(**data.model_dump())


@router.put("/projekttypen/{projekttyp_id}", response_model=PlgProjekttypDetail)
async def update_projekttyp(
    projekttyp_id: str,
    data: PlgProjekttypUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Projekttyp aktualisieren (nur Superadmin)."""
    service = ProjekttypService(db)
    projekttyp = await service.update(projekttyp_id, **data.model_dump(exclude_unset=True))
    if not projekttyp:
        raise HTTPException(status_code=404, detail="Projekttyp nicht gefunden")
    return projekttyp


@router.post("/projekttypen/seed", response_model=list[PlgProjekttypBase])
async def seed_projekttypen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Standard-Projekttypen anlegen (nur Superadmin)."""
    service = ProjekttypService(db)
    return await service.seed_default_types()


# =============================================================================
# Preis Routes (static paths - must come before /{plugin_id})
# =============================================================================

@router.get("/preise", response_model=PlgPreisList)
async def list_preise(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    plugin_id: str | None = Query(None, description="Filter nach Plugin"),
    projekttyp_id: str | None = Query(None, description="Filter nach Projekttyp"),
    nur_aktiv: bool = Query(True, description="Nur aktive Preise"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Preise (nur Superadmin)."""
    service = PreisService(db)
    return await service.get_list(
        plugin_id=plugin_id,
        projekttyp_id=projekttyp_id,
        nur_aktiv=nur_aktiv,
        skip=skip,
        limit=limit,
    )


@router.get("/preise/{preis_id}", response_model=PlgPreisDetail)
async def get_preis(
    preis_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelnen Preis abrufen (nur Superadmin)."""
    service = PreisService(db)
    preis = await service.get_by_id(preis_id)
    if not preis:
        raise HTTPException(status_code=404, detail="Preis nicht gefunden")
    return preis


@router.post("/preise", response_model=PlgPreisDetail, status_code=status.HTTP_201_CREATED)
async def create_preis(
    data: PlgPreisCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neuen Preis erstellen (nur Superadmin)."""
    service = PreisService(db)

    # Check if price already exists for this combination
    existing = await service.get_for_plugin_and_typ(data.plugin_id, data.projekttyp_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Preis für diese Plugin/Projekttyp-Kombination existiert bereits"
        )

    return await service.create(**data.model_dump())


@router.put("/preise/{preis_id}", response_model=PlgPreisDetail)
async def update_preis(
    preis_id: str,
    data: PlgPreisUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Preis aktualisieren (nur Superadmin)."""
    service = PreisService(db)
    preis = await service.update(preis_id, **data.model_dump(exclude_unset=True))
    if not preis:
        raise HTTPException(status_code=404, detail="Preis nicht gefunden")
    return preis


@router.delete("/preise/{preis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preis(
    preis_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Preis deaktivieren (nur Superadmin)."""
    service = PreisService(db)
    if not await service.deactivate(preis_id):
        raise HTTPException(status_code=404, detail="Preis nicht gefunden")


# =============================================================================
# Plugin Routes (dynamic /{plugin_id} paths - MUST come LAST)
# =============================================================================

@router.get("", response_model=PlgPluginList)
async def list_plugins(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    plugin_status: str | None = Query(None, alias="status", description="Filter nach Status"),
    kategorie_id: str | None = Query(None, description="Filter nach Kategorie"),
    suche: str | None = Query(None, min_length=2, description="Textsuche"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Plugins (nur Superadmin)."""
    service = PluginService(db)
    return await service.get_list(
        status=plugin_status,
        kategorie_id=kategorie_id,
        suche=suche,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=PlgPluginDetail, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    data: PlgPluginCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neues Plugin erstellen (nur Superadmin)."""
    service = PluginService(db)

    # Check if slug already exists
    existing = await service.get_by_slug(data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug bereits vergeben")

    return await service.create(**data.model_dump())


@router.get("/{plugin_id}", response_model=PlgPluginDetail)
async def get_plugin(
    plugin_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelnes Plugin abrufen (nur Superadmin)."""
    service = PluginService(db)
    plugin = await service.get_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin nicht gefunden")
    return plugin


@router.put("/{plugin_id}", response_model=PlgPluginDetail)
async def update_plugin(
    plugin_id: str,
    data: PlgPluginUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Plugin aktualisieren (nur Superadmin)."""
    service = PluginService(db)
    plugin = await service.update(plugin_id, **data.model_dump(exclude_unset=True))
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin nicht gefunden")
    return plugin


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin(
    plugin_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Plugin als deprecated markieren (nur Superadmin)."""
    service = PluginService(db)
    if not await service.delete(plugin_id):
        raise HTTPException(status_code=404, detail="Plugin nicht gefunden")


# =============================================================================
# Plugin Version Routes (nested under /{plugin_id})
# =============================================================================

@router.get("/{plugin_id}/versionen", response_model=list[PlgPluginVersionDetail])
async def list_plugin_versions(
    plugin_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Versionen eines Plugins abrufen (nur Superadmin)."""
    service = PluginService(db)

    # Verify plugin exists
    plugin = await service.get_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin nicht gefunden")

    return await service.get_versions(plugin_id)


@router.post("/{plugin_id}/versionen", response_model=PlgPluginVersionDetail, status_code=status.HTTP_201_CREATED)
async def create_plugin_version(
    plugin_id: str,
    data: PlgPluginVersionCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neue Plugin-Version erstellen (nur Superadmin)."""
    service = PluginService(db)
    version = await service.add_version(
        plugin_id=plugin_id,
        version=data.version,
        changelog=data.changelog,
        ist_breaking_change=data.ist_breaking_change,
        min_api_version=data.min_api_version,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Plugin nicht gefunden")
    return version
