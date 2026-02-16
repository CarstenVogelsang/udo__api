"""
API Routes for Product (Produktdaten) data.

Covers: Artikel CRUD, Sortiment-Zuordnung, Eigenschaften (EAV),
Bilder, and Stammdaten lookups (Sortimente, Eigenschaften, Kategorien, Wertelisten).
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.prod import ProdService
from app.schemas.prod import (
    ProdArtikelList,
    ProdArtikelDetail,
    ProdArtikelCreate,
    ProdArtikelUpdate,
    ProdArtikelEigenschaftRead,
    ProdArtikelEigenschaftenBulk,
    ProdArtikelBildRead,
    ProdArtikelBildCreate,
    ProdSortimentDetailRead,
    ProdSortimentEigenschaftRead,
    ProdEigenschaftRead,
    ProdKategorieRead,
    ProdKategorieCreate,
    ProdWertelisteRead,
    ProdWertelisteCreate,
)

router = APIRouter(prefix="/prod", tags=["Produktdaten"])


# ============ Artikel CRUD ============


@router.get("/artikel", response_model=ProdArtikelList)
async def list_artikel(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    hersteller_id: str | None = Query(None, description="Filter nach Hersteller-UUID"),
    marke_id: str | None = Query(None, description="Filter nach Marke-UUID"),
    kategorie_id: str | None = Query(None, description="Filter nach Kategorie-UUID"),
    sortiment_code: str | None = Query(None, description="Filter nach Sortiment-Code (z.B. 'moba')"),
    suche: str | None = Query(None, min_length=2, description="Textsuche in Bezeichnung, Artikelnr, EAN"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(50, ge=1, le=500, description="Maximale Anzahl Einträge"),
):
    """
    Artikelliste mit Filtern und Pagination.

    **Filter:**
    - `hersteller_id`: Nur Artikel dieses Herstellers
    - `marke_id`: Nur Artikel dieser Marke
    - `kategorie_id`: Nur Artikel dieser Kategorie
    - `sortiment_code`: Nur Artikel eines Sortiments (z.B. 'moba', 'sammler')
    - `suche`: Textsuche in Bezeichnung, Artikelnummer und EAN
    """
    service = ProdService(db)
    return await service.get_artikel_list(
        hersteller_id=hersteller_id,
        marke_id=marke_id,
        kategorie_id=kategorie_id,
        sortiment_code=sortiment_code,
        suche=suche,
        skip=skip,
        limit=limit,
    )


@router.post("/artikel", response_model=ProdArtikelDetail, status_code=status.HTTP_201_CREATED)
async def create_artikel(
    data: ProdArtikelCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neuen Artikel anlegen.

    **Pflichtfelder:** hersteller_id, marke_id, artikelnummer_hersteller, bezeichnung
    """
    service = ProdService(db)
    return await service.create_artikel(**data.model_dump())


@router.get("/artikel/{artikel_id}", response_model=ProdArtikelDetail)
async def get_artikel(
    artikel_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Artikel-Detail mit Sortimenten, Eigenschaften und Bildern."""
    service = ProdService(db)
    artikel = await service.get_artikel_by_id(artikel_id)
    if not artikel:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return artikel


@router.patch("/artikel/{artikel_id}", response_model=ProdArtikelDetail)
async def update_artikel(
    artikel_id: str,
    data: ProdArtikelUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Artikel aktualisieren (partial update)."""
    service = ProdService(db)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    artikel = await service.update_artikel(artikel_id, **update_data)
    if not artikel:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return artikel


@router.delete("/artikel/{artikel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artikel(
    artikel_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Artikel soft-löschen (setzt geloescht_am)."""
    service = ProdService(db)
    deleted = await service.soft_delete_artikel(artikel_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")


# ============ Sortiment-Zuordnung ============


@router.post(
    "/artikel/{artikel_id}/sortimente/{sortiment_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def assign_sortiment(
    artikel_id: str,
    sortiment_code: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Sortiment einem Artikel zuweisen."""
    service = ProdService(db)
    success = await service.assign_sortiment(artikel_id, sortiment_code)
    if not success:
        raise HTTPException(status_code=404, detail="Sortiment nicht gefunden")


@router.delete(
    "/artikel/{artikel_id}/sortimente/{sortiment_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_sortiment(
    artikel_id: str,
    sortiment_code: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Sortiment von einem Artikel entfernen."""
    service = ProdService(db)
    success = await service.remove_sortiment(artikel_id, sortiment_code)
    if not success:
        raise HTTPException(status_code=404, detail="Zuordnung nicht gefunden")


# ============ Eigenschaften (EAV) ============


@router.get("/artikel/{artikel_id}/eigenschaften", response_model=list[ProdArtikelEigenschaftRead])
async def get_artikel_eigenschaften(
    artikel_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Eigenschaftswerte eines Artikels."""
    service = ProdService(db)
    return await service.get_artikel_eigenschaften(artikel_id)


@router.put("/artikel/{artikel_id}/eigenschaften", response_model=list[ProdArtikelEigenschaftRead])
async def set_artikel_eigenschaften(
    artikel_id: str,
    data: ProdArtikelEigenschaftenBulk,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Eigenschaftswerte setzen (Bulk-Upsert).

    Pro Eigenschaft wird anhand des `eigenschaft_code` zugeordnet.
    Existierende Werte werden überschrieben.
    """
    service = ProdService(db)
    eigenschaften_data = [e.model_dump() for e in data.eigenschaften]
    return await service.set_artikel_eigenschaften(artikel_id, eigenschaften_data)


# ============ Bilder ============


@router.post(
    "/artikel/{artikel_id}/bilder",
    response_model=ProdArtikelBildRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_bild(
    artikel_id: str,
    data: ProdArtikelBildCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Bild zu einem Artikel hinzufügen."""
    service = ProdService(db)
    return await service.add_bild(artikel_id, **data.model_dump())


@router.delete(
    "/artikel/{artikel_id}/bilder/{bild_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_bild(
    artikel_id: str,
    bild_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Bild von einem Artikel entfernen."""
    service = ProdService(db)
    success = await service.remove_bild(artikel_id, bild_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")


# ============ Stammdaten ============


@router.get("/sortimente", response_model=list[ProdSortimentDetailRead])
async def list_sortimente(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Sortimente mit ihren Eigenschafts-Blueprints."""
    service = ProdService(db)
    return await service.get_sortimente()


@router.get(
    "/sortimente/{sortiment_code}/eigenschaften",
    response_model=list[ProdSortimentEigenschaftRead],
)
async def get_sortiment_eigenschaften(
    sortiment_code: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Blueprint: Welche Eigenschaften gehören zu diesem Sortiment?"""
    service = ProdService(db)
    return await service.get_sortiment_eigenschaften(sortiment_code)


@router.get("/eigenschaften", response_model=list[ProdEigenschaftRead])
async def list_eigenschaften(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Eigenschafts-Definitionen."""
    service = ProdService(db)
    return await service.get_eigenschaften()


@router.get("/kategorien", response_model=list[ProdKategorieRead])
async def list_kategorien(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    parent_id: str | None = Query(None, description="Nur Unterkategorien dieses Knotens"),
):
    """Kategorie-Baum (Top-Level wenn kein parent_id)."""
    service = ProdService(db)
    return await service.get_kategorien(parent_id=parent_id)


@router.post("/kategorien", response_model=ProdKategorieRead, status_code=status.HTTP_201_CREATED)
async def create_kategorie(
    data: ProdKategorieCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neue Kategorie anlegen."""
    service = ProdService(db)
    return await service.create_kategorie(**data.model_dump())


@router.get("/wertelisten/{typ}", response_model=list[ProdWertelisteRead])
async def get_werteliste(
    typ: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Einträge einer Werteliste (z.B. spurweite, epoche, artikelstatus)."""
    service = ProdService(db)
    return await service.get_werteliste(typ)


@router.post(
    "/wertelisten/{typ}",
    response_model=ProdWertelisteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_werteliste_entry(
    typ: str,
    data: ProdWertelisteCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neuen Eintrag in einer Werteliste anlegen."""
    service = ProdService(db)
    return await service.create_werteliste_entry(typ, **data.model_dump())


# ============ Import ============


@router.post("/import/{source_id}")
async def run_import(
    source_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    import_file_id: str = Query(..., description="UUID der hochgeladenen Import-Datei"),
    sortiment_code: str = Query(..., description="Sortiment-Code (z.B. 'moba')"),
    dry_run: bool = Query(False, description="Nur validieren, keine Daten schreiben"),
):
    """
    Excel-Import für Produktdaten.

    Kern-Felder werden über ETL-FieldMappings zugeordnet.
    Eigenschafts-Spalten werden automatisch per Code-Matching erkannt.
    """
    from app.services.prod_import import ProdImportService

    service = ProdImportService(db)
    return await service.run_import(
        source_id=source_id,
        import_file_id=import_file_id,
        sortiment_code=sortiment_code,
        dry_run=dry_run,
    )


@router.post("/import/{source_id}/preview")
async def preview_import(
    source_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    import_file_id: str = Query(..., description="UUID der hochgeladenen Import-Datei"),
    row_index: int = Query(0, ge=0, description="Zeilen-Index für Vorschau"),
):
    """Vorschau einer einzelnen Import-Zeile mit Feld-Zuordnungen."""
    from app.services.prod_import import ProdImportService

    service = ProdImportService(db)
    return await service.preview_row(
        source_id=source_id,
        import_file_id=import_file_id,
        row_index=row_index,
    )
