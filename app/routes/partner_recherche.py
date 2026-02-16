"""Partner Recherche API routes.

Partners can request cost estimations and create recherche orders
to acquire business data from external sources.

Endpoint prefix: /partner/recherche
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_partner_with_billing
from app.models.partner import ApiPartner
from app.services.recherche import RecherchService
from app.schemas.recherche import (
    RecherchSchaetzungRequest,
    RecherchSchaetzungResponse,
    RecherchAuftragRequest,
    RecherchAuftragResponse,
    RecherchAuftragDetailResponse,
    RecherchAuftragList,
)

router = APIRouter(prefix="/partner/recherche", tags=["Partner Recherche"])


@router.post(
    "/schaetzung",
    response_model=RecherchSchaetzungResponse,
    summary="Kostenvoranschlag",
    description=(
        "Schätzt die Kosten für eine Recherche basierend auf Region, "
        "Branche und Qualitätsstufe. Erstellt keinen Auftrag."
    ),
)
async def schaetzung(
    body: RecherchSchaetzungRequest,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Get cost estimation without creating an order."""
    service = RecherchService(db)
    result = await service.schaetzung_erstellen(
        partner_id=partner.id,
        geo_ort_id=body.geo_ort_id,
        geo_kreis_id=body.geo_kreis_id,
        plz=body.plz,
        wz_code=body.wz_code,
        google_kategorie_gcid=body.google_kategorie_gcid,
        branche_freitext=body.branche_freitext,
        qualitaets_stufe=body.qualitaets_stufe.value,
    )
    return result


@router.post(
    "",
    response_model=RecherchAuftragResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Recherche-Auftrag erstellen",
    description=(
        "Erstellt einen Recherche-Auftrag und reserviert Credits. "
        "Der Auftrag wird asynchron von einem Worker verarbeitet."
    ),
)
async def auftrag_erstellen(
    body: RecherchAuftragRequest,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Create a recherche order and reserve credits."""
    service = RecherchService(db)
    auftrag = await service.auftrag_erstellen(
        partner_id=partner.id,
        geo_ort_id=body.geo_ort_id,
        geo_kreis_id=body.geo_kreis_id,
        plz=body.plz,
        wz_code=body.wz_code,
        google_kategorie_gcid=body.google_kategorie_gcid,
        branche_freitext=body.branche_freitext,
        qualitaets_stufe=body.qualitaets_stufe.value,
    )
    await db.commit()
    return auftrag


@router.get(
    "",
    response_model=RecherchAuftragList,
    summary="Eigene Aufträge auflisten",
    description="Zeigt alle Recherche-Aufträge des Partners paginiert.",
)
async def auftraege_auflisten(
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Statusfilter (bestaetigt, in_bearbeitung, abgeschlossen, fehlgeschlagen, storniert)",
    ),
    skip: int = Query(0, ge=0, description="Pagination Offset"),
    limit: int = Query(20, ge=1, le=100, description="Max. Anzahl (1-100)"),
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """List own recherche orders."""
    service = RecherchService(db)
    return await service.get_auftraege(
        partner_id=partner.id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{auftrag_id}",
    response_model=RecherchAuftragDetailResponse,
    summary="Auftragsstatus & Ergebnisse",
    description="Zeigt den detaillierten Status und die Ergebnisse eines Auftrags.",
)
async def auftrag_detail(
    auftrag_id: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed order status and results."""
    service = RecherchService(db)
    auftrag = await service.get_auftrag(
        auftrag_id=auftrag_id,
        partner_id=partner.id,
    )
    if not auftrag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auftrag nicht gefunden.",
        )
    return auftrag


@router.delete(
    "/{auftrag_id}",
    response_model=RecherchAuftragResponse,
    summary="Auftrag stornieren",
    description=(
        "Storniert einen Auftrag und gibt reservierte Credits zurück. "
        "Nur möglich, solange der Auftrag noch nicht in Bearbeitung ist."
    ),
)
async def auftrag_stornieren(
    auftrag_id: str,
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an order (only before processing starts)."""
    service = RecherchService(db)
    auftrag = await service.auftrag_stornieren(
        auftrag_id=auftrag_id,
        partner_id=partner.id,
    )
    if not auftrag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auftrag nicht gefunden oder kann nicht mehr storniert werden.",
        )
    await db.commit()
    return auftrag
