#!/usr/bin/env python3
"""Background worker for processing recherche orders.

Polls the database for confirmed orders (status=BESTAETIGT),
picks them up with FOR UPDATE SKIP LOCKED, runs external provider
searches, deduplicates results, and creates new companies.

Usage:
    uv run python scripts/recherche_worker.py
    uv run python scripts/recherche_worker.py --poll-interval 10
    uv run python scripts/recherche_worker.py --once  (process one order and exit)

Deployment:
    Run as a separate Coolify service with the same Docker image.
    Entrypoint: uv run python scripts/recherche_worker.py
"""
import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.database import async_session_maker
from app.models.geo import GeoOrt, GeoKreis
from app.models.recherche import RecherchRohErgebnis
from app.services.recherche import RecherchService
from app.services.recherche_dedup import RecherchDeduplizierungService
from app.services.recherche_provider import ProviderRegistry, RohErgebnisData
from app.services.provider_google_places import GooglePlacesProvider
from app.services.provider_dataforseo import DataForSeoProvider
from app.services.setting import SettingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("recherche_worker")

# Graceful shutdown
shutdown_event = asyncio.Event()


def handle_signal(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_event.set()


async def setup_registry(db_session) -> ProviderRegistry:
    """Create and configure the provider registry with DB credentials."""
    settings_service = SettingService(db_session)

    registry = ProviderRegistry()

    # Google Places
    google_key = await settings_service.get_value(
        "recherche.google_places_api_key", "",
    )
    if google_key:
        registry.register(GooglePlacesProvider(api_key=google_key))
        logger.info("Google Places provider registered")
    else:
        logger.warning("Google Places API key not configured")

    # DataForSEO
    dfs_login = await settings_service.get_value("recherche.dataforseo_login", "")
    dfs_password = await settings_service.get_value("recherche.dataforseo_password", "")
    if dfs_login and dfs_password:
        registry.register(DataForSeoProvider(login=dfs_login, password=dfs_password))
        logger.info("DataForSEO provider registered")
    else:
        logger.warning("DataForSEO credentials not configured")

    return registry


async def resolve_search_params(db_session, auftrag) -> dict:
    """Resolve geographic and search parameters from the order.

    Returns dict with: lat, lng, radius_m, suchbegriff
    """
    from sqlalchemy import select

    lat, lng, radius_m = None, None, 5000  # Default 5km

    if auftrag.geo_ort_id:
        result = await db_session.execute(
            select(GeoOrt).where(GeoOrt.id == auftrag.geo_ort_id)
        )
        ort = result.scalar_one_or_none()
        if ort:
            lat, lng = ort.lat, ort.lng
            radius_m = 3000  # Smaller radius for single Ort

    elif auftrag.geo_kreis_id:
        # Use first Ort in Kreis as center, larger radius
        result = await db_session.execute(
            select(GeoOrt).where(
                GeoOrt.kreis_id == auftrag.geo_kreis_id,
                GeoOrt.ist_hauptort == True,
            ).limit(1)
        )
        ort = result.scalar_one_or_none()
        if ort:
            lat, lng = ort.lat, ort.lng
        # Get Kreis info for radius
        kreis_result = await db_session.execute(
            select(GeoKreis).where(GeoKreis.id == auftrag.geo_kreis_id)
        )
        kreis = kreis_result.scalar_one_or_none()
        if kreis and kreis.einwohner:
            # Rough radius based on population density
            radius_m = min(50000, max(5000, kreis.einwohner // 10))
        else:
            radius_m = 15000  # Default for Kreis

    elif auftrag.plz:
        result = await db_session.execute(
            select(GeoOrt).where(GeoOrt.plz == auftrag.plz).limit(1)
        )
        ort = result.scalar_one_or_none()
        if ort:
            lat, lng = ort.lat, ort.lng
            radius_m = 5000

    # Build search term
    suchbegriff = auftrag.branche_freitext or "Restaurant"

    # If we have a Google category, try to use it
    if auftrag.google_kategorie_gcid:
        from app.models.branche import BrnGoogleKategorie
        result = await db_session.execute(
            select(BrnGoogleKategorie).where(
                BrnGoogleKategorie.gcid == auftrag.google_kategorie_gcid,
            )
        )
        gkat = result.scalar_one_or_none()
        if gkat:
            suchbegriff = gkat.name_de or gkat.name or suchbegriff

    return {
        "lat": lat or 51.4,     # Fallback: center of Germany
        "lng": lng or 7.0,
        "radius_m": radius_m,
        "suchbegriff": suchbegriff,
    }


async def verarbeite_auftrag(db_session, auftrag, registry: ProviderRegistry):
    """Process a single recherche order end-to-end.

    Steps:
    1. Resolve geo coordinates and search parameters
    2. Get providers for the chosen quality tier
    3. Run searches across all providers
    4. Store raw results
    5. Deduplicate against existing companies
    6. Calculate actual costs
    7. Settle credits
    """
    service = RecherchService(db_session)

    try:
        # 1. Resolve search parameters
        params = await resolve_search_params(db_session, auftrag)
        logger.info(
            f"Search params: lat={params['lat']}, lng={params['lng']}, "
            f"radius={params['radius_m']}m, term='{params['suchbegriff']}'"
        )

        # 2. Get providers for quality tier
        providers = registry.get_providers(auftrag.qualitaets_stufe)
        logger.info(
            f"Using {len(providers)} providers for tier '{auftrag.qualitaets_stufe}': "
            f"{[p.name for p in providers]}"
        )

        # 3. Run searches
        all_results: list[RohErgebnisData] = []
        for provider in providers:
            try:
                results = await provider.suchen(
                    lat=params["lat"],
                    lng=params["lng"],
                    radius_m=params["radius_m"],
                    suchbegriff=params["suchbegriff"],
                )
                all_results.extend(results)
                logger.info(f"Provider '{provider.name}': {len(results)} results")
            except Exception as e:
                logger.error(f"Provider '{provider.name}' failed: {e}")

        if not all_results:
            logger.warning(f"No results found for order {auftrag.id[:8]}...")

        # 4. Store raw results
        for roh_data in all_results:
            roh = RecherchRohErgebnis(
                auftrag_id=auftrag.id,
                quelle=roh_data.quelle,
                externe_id=roh_data.externe_id,
                name=roh_data.name,
                adresse=roh_data.adresse,
                plz=roh_data.plz,
                ort=roh_data.ort,
                telefon=roh_data.telefon,
                website=roh_data.website,
                email=roh_data.email,
                kategorie=roh_data.kategorie,
                lat=roh_data.lat,
                lng=roh_data.lng,
                rohdaten=roh_data.rohdaten,
            )
            db_session.add(roh)
        await db_session.flush()

        # 5. Deduplicate
        dedup_service = RecherchDeduplizierungService(db_session)
        dedup_stats = await dedup_service.deduplizieren(auftrag.id)

        # 6. Calculate actual costs
        from app.services.recherche_kosten import RecherchKostenService
        kosten_service = RecherchKostenService(db_session)
        pro_treffer = kosten_service._pro_treffer_kosten(None, auftrag.qualitaets_stufe)
        # Load partner for actual rates
        from sqlalchemy import select as sel
        from app.models.partner import ApiPartner
        partner_result = await db_session.execute(
            sel(ApiPartner).where(ApiPartner.id == auftrag.partner_id)
        )
        partner = partner_result.scalar_one_or_none()
        if partner:
            pro_treffer = kosten_service._pro_treffer_kosten(
                partner, auftrag.qualitaets_stufe,
            )

        grundgebuehr_cents = round(
            (partner.kosten_recherche_grundgebuehr if partner else 0.50) * 100,
        )
        kosten_cents = grundgebuehr_cents + round(dedup_stats["neue"] * pro_treffer * 100)

        # 7. Mark as completed and settle credits
        await service.auftrag_abschliessen(
            auftrag_id=auftrag.id,
            ergebnis_roh=len(all_results),
            ergebnis_neu=dedup_stats["neue"],
            ergebnis_duplikat=dedup_stats["duplikate"],
            ergebnis_aktualisiert=dedup_stats.get("aktualisiert", 0),
            kosten_tatsaechlich_cents=kosten_cents,
        )

        await db_session.commit()
        logger.info(
            f"Order {auftrag.id[:8]}... completed: "
            f"{len(all_results)} raw, {dedup_stats['neue']} new, "
            f"{dedup_stats['duplikate']} duplicates, cost={kosten_cents}ct"
        )

    except Exception as e:
        await db_session.rollback()
        logger.error(f"Error processing order {auftrag.id[:8]}...: {e}", exc_info=True)

        # Mark as failed (with retry logic)
        try:
            async with async_session_maker() as error_session:
                error_service = RecherchService(error_session)
                await error_service.auftrag_fehlgeschlagen(
                    auftrag_id=auftrag.id,
                    fehler=str(e)[:1000],
                )
                await error_session.commit()
        except Exception as inner_e:
            logger.error(f"Failed to mark order as failed: {inner_e}")


async def worker_loop(poll_interval: int = 5, once: bool = False):
    """Main worker loop: poll DB for orders and process them."""
    logger.info(
        f"Recherche Worker started (poll_interval={poll_interval}s, "
        f"once={once})"
    )

    # Setup signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    while not shutdown_event.is_set():
        try:
            async with async_session_maker() as session:
                # Setup provider registry (re-reads credentials each iteration)
                registry = await setup_registry(session)

                if not registry.available_providers:
                    logger.warning(
                        "No providers configured. "
                        "Set API keys via PATCH /admin/settings/recherche.*"
                    )
                    if once:
                        return
                    await asyncio.sleep(poll_interval * 6)  # Wait longer
                    continue

                # Try to pick up an order
                service = RecherchService(session)
                auftrag = await service.naechsten_auftrag_holen()

                if auftrag:
                    await session.commit()  # Commit the status change

                    logger.info(
                        f"Processing order: {auftrag.id[:8]}... "
                        f"(attempt {auftrag.versuche}/{auftrag.max_versuche})"
                    )

                    # Process in a fresh session
                    async with async_session_maker() as work_session:
                        await verarbeite_auftrag(work_session, auftrag, registry)

                    if once:
                        return
                else:
                    if once:
                        logger.info("No orders to process.")
                        return

        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)

        # Wait before next poll
        if not once and not shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    shutdown_event.wait(),
                    timeout=poll_interval,
                )
            except asyncio.TimeoutError:
                pass  # Normal timeout, continue polling

    logger.info("Recherche Worker stopped.")


def main():
    parser = argparse.ArgumentParser(description="Recherche Background Worker")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between DB polls (default: 5)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one order and exit",
    )
    args = parser.parse_args()

    asyncio.run(worker_loop(
        poll_interval=args.poll_interval,
        once=args.once,
    ))


if __name__ == "__main__":
    main()
