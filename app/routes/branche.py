"""
API Routes for Branchenklassifikation.

Provides endpoints for WZ-2008 industry codes, business directories,
regional social media groups, and Google Business category mappings.

All endpoints require partner authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_partner_with_billing
from app.models.partner import ApiPartner
from app.services.branche import BranchenService
from app.schemas.branche import (
    BrnBrancheBase,
    BrnBrancheDetail,
    BrnBrancheList,
    BrnVerzeichnisBase,
    BrnVerzeichnisList,
    BrnVerzeichnisListForBranche,
    BrnRegionaleGruppeBase,
    BrnRegionaleGruppeList,
    BrnRegionaleGruppeListForBranche,
    BrnGoogleKategorieBase,
    BrnGoogleKategorieDetail,
    BrnGoogleKategorieList,
    BrnGoogleMappingListForBranche,
)

router = APIRouter(prefix="/branchen", tags=["Branchenklassifikation"])

# Separate routers for top-level resources
verzeichnis_router = APIRouter(prefix="/verzeichnisse", tags=["Branchenverzeichnisse"])
gruppen_router = APIRouter(prefix="/gruppen", tags=["Regionale Gruppen"])
google_router = APIRouter(prefix="/google-kategorien", tags=["Google Kategorien"])


# ============ Branchen (WZ-Codes) ============


@router.get("", response_model=BrnBrancheList)
async def list_branchen(
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    ebene: int | None = Query(None, ge=1, le=5, description="Filter nach Hierarchie-Ebene (1-5)"),
    suche: str | None = Query(None, min_length=1, description="Volltextsuche in WZ-Code und Bezeichnung"),
    nur_aktiv: bool = Query(True, description="Nur aktive Branchen anzeigen"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller WZ-2008 Branchencodes.

    Unterstützt Filter nach Hierarchie-Ebene und Textsuche.
    """
    service = BranchenService(db)
    return await service.get_branchen(
        ebene=ebene, suche=suche, nur_aktiv=nur_aktiv, skip=skip, limit=limit
    )


@router.get("/{wz_code}", response_model=BrnBrancheDetail)
async def get_branche(
    wz_code: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelne Branche nach WZ-Code abrufen.

    - **wz_code**: WZ-2008 Code (z.B. "69.20.1")
    """
    service = BranchenService(db)
    branche = await service.get_branche_by_wz_code(wz_code)
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")
    return branche


@router.get("/{wz_code}/kinder", response_model=list[BrnBrancheBase])
async def list_kinder(
    wz_code: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """
    Unterkategorien eines WZ-Codes abrufen.

    Gibt alle direkten Kinder (parent_wz_code == wz_code) zurück.
    """
    service = BranchenService(db)
    # Verify parent exists
    branche = await service.get_branche_by_wz_code(wz_code)
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")
    return await service.get_kinder(wz_code)


@router.get("/{wz_code}/verzeichnisse", response_model=BrnVerzeichnisListForBranche)
async def list_verzeichnisse_fuer_branche(
    wz_code: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    region: str | None = Query(None, description="Filter nach Region (z.B. 'DE', 'AT')"),
    kosten: str | None = Query(None, description="Filter nach Kostenmodell (kostenlos, freemium, kostenpflichtig)"),
):
    """
    Branchenverzeichnisse für einen WZ-Code.

    Liefert sowohl branchenspezifische als auch branchenübergreifende
    Verzeichnisse (z.B. Gelbe Seiten), sortiert nach Relevanz.
    """
    service = BranchenService(db)
    branche = await service.get_branche_by_wz_code(wz_code)
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")

    verzeichnisse = await service.get_verzeichnisse_fuer_branche(
        wz_code=wz_code, region=region, kosten=kosten
    )
    return {
        "branche": branche,
        "verzeichnisse": verzeichnisse,
        "gesamt": len(verzeichnisse),
    }


@router.get("/{wz_code}/gruppen", response_model=BrnRegionaleGruppeListForBranche)
async def list_gruppen_fuer_branche(
    wz_code: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    plz_prefix: str | None = Query(None, description="Filter nach PLZ-Prefix (z.B. '10' für Berlin)"),
    plattform: str | None = Query(None, description="Filter nach Plattform (facebook, linkedin, xing, nextdoor, sonstige)"),
    werbung_erlaubt: bool | None = Query(None, description="Filter: nur Gruppen wo Werbung erlaubt"),
):
    """
    Regionale Gruppen für einen WZ-Code.

    Gruppen auf Facebook, LinkedIn etc. für lokale Werbung.
    """
    service = BranchenService(db)
    branche = await service.get_branche_by_wz_code(wz_code)
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")

    gruppen = await service.get_gruppen_fuer_branche(
        wz_code=wz_code,
        plz_prefix=plz_prefix,
        plattform=plattform,
        werbung_erlaubt=werbung_erlaubt,
    )
    return {
        "branche": branche,
        "gruppen": gruppen,
        "gesamt": len(gruppen),
    }


@router.get("/{wz_code}/google-kategorien", response_model=BrnGoogleMappingListForBranche)
async def list_google_kategorien_fuer_branche(
    wz_code: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    nur_primaer: bool = Query(False, description="Nur primäre Google-Kategorie"),
):
    """
    Google Business Kategorien für einen WZ-Code.

    Zeigt das Mapping zwischen WZ-Code und Google Business Profile Kategorien.
    """
    service = BranchenService(db)
    branche = await service.get_branche_by_wz_code(wz_code)
    if not branche:
        raise HTTPException(status_code=404, detail="Branche nicht gefunden")

    mappings = await service.get_google_kategorien_fuer_branche(
        wz_code=wz_code, nur_primaer=nur_primaer
    )
    return {
        "branche": branche,
        "mappings": mappings,
        "gesamt": len(mappings),
    }


# ============ Verzeichnisse (alle) ============


@verzeichnis_router.get("", response_model=BrnVerzeichnisList)
async def list_alle_verzeichnisse(
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    branchenuebergreifend: bool | None = Query(None, description="Filter: nur branchenübergreifende"),
    kosten: str | None = Query(None, description="Filter nach Kostenmodell"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Alle Branchenverzeichnisse.

    Kann nach branchenübergreifend und Kostenmodell gefiltert werden.
    """
    service = BranchenService(db)
    return await service.get_alle_verzeichnisse(
        branchenuebergreifend=branchenuebergreifend, kosten=kosten, skip=skip, limit=limit
    )


# ============ Gruppen (alle) ============


@gruppen_router.get("", response_model=BrnRegionaleGruppeList)
async def list_alle_gruppen(
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    bundesland: str | None = Query(None, description="Filter nach Bundesland (z.B. 'Bayern')"),
    plattform: str | None = Query(None, description="Filter nach Plattform"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Alle regionalen Gruppen.

    Kann nach Bundesland und Plattform gefiltert werden.
    """
    service = BranchenService(db)
    return await service.get_alle_gruppen(
        bundesland=bundesland, plattform=plattform, skip=skip, limit=limit
    )


# ============ Google-Kategorien (alle) ============


@google_router.get("", response_model=BrnGoogleKategorieList)
async def list_google_kategorien(
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
    suche: str | None = Query(None, min_length=1, description="Textsuche in GCID und Bezeichnung"),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Alle Google Business Kategorien.

    Unterstützt Textsuche über GCID, deutschen und englischen Namen.
    """
    service = BranchenService(db)
    return await service.get_google_kategorien(suche=suche, skip=skip, limit=limit)


@google_router.get("/{gcid:path}", response_model=BrnGoogleKategorieDetail)
async def get_google_kategorie(
    gcid: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelne Google Kategorie nach GCID abrufen.

    - **gcid**: Google Category ID (z.B. "gcid:tax_consultant")
    """
    service = BranchenService(db)
    kategorie = await service.get_google_kategorie_by_gcid(gcid)
    if not kategorie:
        raise HTTPException(status_code=404, detail="Google-Kategorie nicht gefunden")
    return kategorie
