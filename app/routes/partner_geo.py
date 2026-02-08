"""
Partner Geodata API routes.

Limited geodata access for authenticated partners.
Endpoint prefix: /partner/geodaten
"""
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.auth import get_current_partner_with_billing
from app.models.partner import ApiPartner
from app.models.geo import GeoLand, GeoBundesland, GeoKreis, GeoOrt
from app.services.usage import UsageService
from app.services.billing import BillingService
from app.schemas.geo import (
    GeoLandPartner,
    GeoBundeslandPartner,
    GeoKreisPartner,
    GeoOrtPartner,
)

router = APIRouter(prefix="/partner/geodaten", tags=["Partner Geodaten"])


def round_to_thousand(value: int | None) -> int | None:
    """Round to nearest 1000."""
    if value is None:
        return None
    return round(value / 1000) * 1000


@router.get(
    "/laender",
    response_model=list[GeoLandPartner],
    summary="Alle Länder abrufen",
    description="Gibt eine Liste aller verfügbaren Länder zurück (eingeschränkte Felder).",
)
async def list_laender(
    ist_eu: bool | None = Query(None, description="Filter: nur EU-Länder (true) oder Nicht-EU (false)"),
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Get all countries (limited fields for partners)."""
    t_start = time.monotonic()

    query = select(GeoLand).order_by(GeoLand.name)
    if ist_eu is not None:
        query = query.where(GeoLand.ist_eu == ist_eu)
    result = await db.execute(query)
    items = result.scalars().all()

    # Log usage (Länder are free)
    usage_service = UsageService(db)
    await usage_service.log_usage(
        partner_id=partner.id,
        endpoint="/partner/geodaten/laender",
        methode="GET",
        status_code=200,
        anzahl_ergebnisse=len(items),
        kosten=0.0,
        antwortzeit_ms=int((time.monotonic() - t_start) * 1000),
        parameter={"ist_eu": ist_eu},
    )

    return items


@router.get(
    "/bundeslaender",
    response_model=list[GeoBundeslandPartner],
    summary="Bundesländer eines Landes abrufen",
    description="Gibt Bundesländer für ein bestimmtes Land zurück.",
)
async def list_bundeslaender(
    land_code: str = Query(..., description="Land-Code, z.B. 'DE' für Deutschland"),
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Get federal states for a country (limited fields for partners)."""
    t_start = time.monotonic()

    # Find the land by code
    land_query = select(GeoLand).where(GeoLand.code == land_code.upper())
    land_result = await db.execute(land_query)
    land = land_result.scalar_one_or_none()

    if not land:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Land mit Code '{land_code}' nicht gefunden.",
        )

    # Get bundeslaender for this land
    query = (
        select(GeoBundesland)
        .where(GeoBundesland.land_id == land.id)
        .order_by(GeoBundesland.name)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    # Log usage (Bundesländer are free)
    usage_service = UsageService(db)
    await usage_service.log_usage(
        partner_id=partner.id,
        endpoint="/partner/geodaten/bundeslaender",
        methode="GET",
        status_code=200,
        anzahl_ergebnisse=len(items),
        kosten=0.0,
        antwortzeit_ms=int((time.monotonic() - t_start) * 1000),
        parameter={"land_code": land_code},
    )

    return items


@router.get(
    "/kreise",
    response_model=list[GeoKreisPartner],
    summary="Kreise eines Bundeslandes abrufen",
    description="Gibt Kreise für ein bestimmtes Bundesland zurück inkl. berechneter Abrufkosten.",
)
async def list_kreise(
    bundesland_code: str = Query(..., description="Bundesland-Code, z.B. 'DE-BY' für Bayern"),
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """
    Get counties for a federal state (limited fields for partners).

    Einwohner is rounded to 1000.
    Abrufkosten = Einwohner x Partner.kosten_geoapi_pro_einwohner
    """
    t_start = time.monotonic()

    # Find the bundesland by code
    bl_query = select(GeoBundesland).where(GeoBundesland.code == bundesland_code.upper())
    bl_result = await db.execute(bl_query)
    bundesland = bl_result.scalar_one_or_none()

    if not bundesland:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bundesland mit Code '{bundesland_code}' nicht gefunden.",
        )

    # Get kreise for this bundesland
    query = (
        select(GeoKreis)
        .where(GeoKreis.bundesland_id == bundesland.id)
        .order_by(GeoKreis.name)
    )
    result = await db.execute(query)
    kreise = result.scalars().all()

    # Transform to public schema with calculated fields
    items = []
    gesamt_kosten = 0.0
    for kreis in kreise:
        einwohner_rounded = round_to_thousand(kreis.einwohner)
        abrufkosten = (einwohner_rounded or 0) * partner.kosten_geoapi_pro_einwohner
        gesamt_kosten += abrufkosten

        items.append(GeoKreisPartner(
            id=kreis.id,
            code=kreis.code,
            kuerzel=kreis.autokennzeichen,  # Map autokennzeichen to kuerzel
            name=kreis.name,
            ist_landkreis=kreis.ist_landkreis,
            ist_kreisfreie_stadt=kreis.ist_kreisfreie_stadt,
            einwohner=einwohner_rounded,
            abrufkosten=abrufkosten,
        ))

    # Log usage with calculated costs
    usage_service = UsageService(db)
    usage = await usage_service.log_usage(
        partner_id=partner.id,
        endpoint="/partner/geodaten/kreise",
        methode="GET",
        status_code=200,
        anzahl_ergebnisse=len(items),
        kosten=gesamt_kosten,
        antwortzeit_ms=int((time.monotonic() - t_start) * 1000),
        parameter={"bundesland_code": bundesland_code},
    )

    # Deduct credits for Kreise (only geo endpoint with costs)
    billing_service = BillingService(db)
    await billing_service.deduct_credits(
        partner_id=partner.id,
        kosten=gesamt_kosten,
        usage_id=str(usage.id),
        beschreibung=f"{len(items)} Kreise abgerufen ({bundesland_code})",
    )

    return items


@router.get(
    "/orte",
    response_model=list[GeoOrtPartner],
    summary="Orte eines Kreises abrufen",
    description="Gibt Orte für einen bestimmten Kreis zurück.",
)
async def list_orte(
    kreis_code: str = Query(..., description="Kreis-Code, z.B. 'DE-BY-09162-1234'"),
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """Get cities/municipalities for a county (limited fields for partners)."""
    t_start = time.monotonic()

    # Find the kreis by code
    kreis_query = select(GeoKreis).where(GeoKreis.code == kreis_code)
    kreis_result = await db.execute(kreis_query)
    kreis = kreis_result.scalar_one_or_none()

    if not kreis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kreis mit Code '{kreis_code}' nicht gefunden.",
        )

    # Get orte for this kreis
    query = (
        select(GeoOrt)
        .where(GeoOrt.kreis_id == kreis.id)
        .order_by(GeoOrt.name)
    )
    result = await db.execute(query)
    orte = result.scalars().all()

    # Transform to partner schema
    items = [
        GeoOrtPartner(
            id=ort.id,
            code=ort.code,
            name=ort.name,
            plz=ort.plz,
            lat=ort.lat,
            lng=ort.lng,
            kreis_id=ort.kreis_id,
            ist_hauptort=ort.ist_hauptort or False,
        )
        for ort in orte
    ]

    # Log usage (Orte are free)
    usage_service = UsageService(db)
    await usage_service.log_usage(
        partner_id=partner.id,
        endpoint="/partner/geodaten/orte",
        methode="GET",
        status_code=200,
        anzahl_ergebnisse=len(items),
        kosten=0.0,
        antwortzeit_ms=int((time.monotonic() - t_start) * 1000),
        parameter={"kreis_code": kreis_code},
    )

    return items
