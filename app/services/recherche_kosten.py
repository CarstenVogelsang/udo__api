"""Cost estimation service for Recherche-Aufträge.

Estimates how many new businesses can be found for a given region/industry,
and calculates the expected cost based on the chosen quality tier.
"""
import logging
import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geo import GeoOrt, GeoKreis
from app.models.com import ComUnternehmen
from app.models.partner import ApiPartner
from app.models.recherche import RecherchQualitaetsStufe

logger = logging.getLogger(__name__)

# Heuristic: estimated businesses per inhabitant by broad category.
# These are rough multipliers — can be refined with real data later.
BETRIEBE_PRO_EINWOHNER = {
    "gastronomie": 1 / 300,      # ~1 restaurant per 300 inhabitants
    "einzelhandel": 1 / 200,     # ~1 retail shop per 200
    "dienstleistung": 1 / 150,   # ~1 service provider per 150
    "default": 1 / 250,          # fallback
}


class RecherchKostenService:
    """Estimates costs for recherche orders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def schaetzen(
        self,
        partner_id: str,
        geo_ort_id: str | None = None,
        geo_kreis_id: str | None = None,
        plz: str | None = None,
        wz_code: str | None = None,
        google_kategorie_gcid: str | None = None,
        branche_freitext: str | None = None,
        qualitaets_stufe: str = RecherchQualitaetsStufe.STANDARD.value,
    ) -> dict:
        """Create a cost estimation without creating an order.

        Args:
            partner_id: Partner UUID (for partner-specific cost rates).
            geo_ort_id: Filter by specific Ort.
            geo_kreis_id: Filter by Kreis (all Orte within).
            plz: Filter by postal code.
            wz_code: Industry filter (WZ-2008 code).
            google_kategorie_gcid: Google category filter.
            branche_freitext: Free-text industry description.
            qualitaets_stufe: Quality tier (standard/premium/komplett).

        Returns:
            Dict with estimation details:
            - einwohner: Total inhabitants in scope
            - geschaetzt_gesamt: Estimated total businesses
            - bestehend: Already in UDO database
            - geschaetzt_neu: Expected new finds
            - grundgebuehr_cents: Base fee
            - pro_treffer_cents: Per-hit cost
            - geschaetzt_kosten_cents: Total estimated cost
            - qualitaets_stufe: Chosen tier
        """
        # 1. Determine population in scope
        einwohner = await self._einwohner_ermitteln(geo_ort_id, geo_kreis_id, plz)

        # 2. Estimate total businesses using heuristic
        branche_key = self._branche_key(wz_code, google_kategorie_gcid, branche_freitext)
        multiplikator = BETRIEBE_PRO_EINWOHNER.get(
            branche_key, BETRIEBE_PRO_EINWOHNER["default"],
        )
        geschaetzt_gesamt = max(1, round(einwohner * multiplikator))

        # 3. Count existing businesses in scope
        bestehend = await self._bestehende_zaehlen(geo_ort_id, geo_kreis_id, plz)

        # 4. Estimate new finds
        geschaetzt_neu = max(0, geschaetzt_gesamt - bestehend)

        # 5. Calculate costs based on partner rates + tier
        partner = (await self.db.execute(
            select(ApiPartner).where(ApiPartner.id == partner_id)
        )).scalar_one_or_none()

        grundgebuehr_cents = round((partner.kosten_recherche_grundgebuehr if partner else 0.50) * 100)
        pro_treffer = self._pro_treffer_kosten(partner, qualitaets_stufe)
        pro_treffer_cents = round(pro_treffer * 100)
        geschaetzt_kosten_cents = grundgebuehr_cents + (geschaetzt_neu * pro_treffer_cents)

        return {
            "einwohner": einwohner,
            "geschaetzt_gesamt": geschaetzt_gesamt,
            "bestehend": bestehend,
            "geschaetzt_neu": geschaetzt_neu,
            "grundgebuehr_cents": grundgebuehr_cents,
            "pro_treffer_cents": pro_treffer_cents,
            "geschaetzt_kosten_cents": geschaetzt_kosten_cents,
            "qualitaets_stufe": qualitaets_stufe,
        }

    def reservierung_betrag(self, schaetzung_kosten_cents: int) -> int:
        """Calculate reservation amount with 20% buffer.

        Args:
            schaetzung_kosten_cents: Estimated cost in cents.

        Returns:
            Reservation amount (estimation × 1.2).
        """
        return math.ceil(schaetzung_kosten_cents * 1.2)

    # ---- Internal helpers ----

    async def _einwohner_ermitteln(
        self,
        geo_ort_id: str | None,
        geo_kreis_id: str | None,
        plz: str | None,
    ) -> int:
        """Determine total inhabitants for the given geographic scope."""
        if geo_ort_id:
            result = await self.db.execute(
                select(GeoOrt.einwohner).where(GeoOrt.id == geo_ort_id)
            )
            einwohner = result.scalar_one_or_none()
            return einwohner or 10_000  # Fallback

        if geo_kreis_id:
            result = await self.db.execute(
                select(GeoKreis.einwohner).where(GeoKreis.id == geo_kreis_id)
            )
            einwohner = result.scalar_one_or_none()
            return einwohner or 100_000  # Fallback

        if plz:
            # Sum inhabitants of all Orte with this PLZ
            result = await self.db.execute(
                select(func.coalesce(func.sum(GeoOrt.einwohner), 0)).where(
                    GeoOrt.plz == plz,
                )
            )
            einwohner = result.scalar() or 0
            return einwohner or 20_000  # Fallback

        return 50_000  # Default fallback

    async def _bestehende_zaehlen(
        self,
        geo_ort_id: str | None,
        geo_kreis_id: str | None,
        plz: str | None,
    ) -> int:
        """Count existing companies in the given scope."""
        query = select(func.count(ComUnternehmen.id)).where(
            ComUnternehmen.geloescht_am.is_(None),
        )

        if geo_ort_id:
            query = query.where(ComUnternehmen.geo_ort_id == geo_ort_id)
        elif geo_kreis_id:
            # All Orte in this Kreis
            ort_ids = select(GeoOrt.id).where(GeoOrt.kreis_id == geo_kreis_id)
            query = query.where(ComUnternehmen.geo_ort_id.in_(ort_ids))
        elif plz:
            ort_ids = select(GeoOrt.id).where(GeoOrt.plz == plz)
            query = query.where(ComUnternehmen.geo_ort_id.in_(ort_ids))

        result = await self.db.execute(query)
        return result.scalar() or 0

    def _branche_key(
        self,
        wz_code: str | None,
        google_kategorie_gcid: str | None,
        branche_freitext: str | None,
    ) -> str:
        """Map industry filter to a heuristic category."""
        text = (branche_freitext or "").lower()

        # Simple keyword matching for the heuristic
        if any(kw in text for kw in ("restaurant", "gastro", "essen", "café", "bar", "imbiss")):
            return "gastronomie"
        if any(kw in text for kw in ("laden", "shop", "handel", "geschäft", "markt")):
            return "einzelhandel"
        if any(kw in text for kw in ("dienst", "beratung", "service", "agentur")):
            return "dienstleistung"

        # WZ code prefix mapping (rough)
        if wz_code:
            if wz_code.startswith("56"):  # WZ 56 = Gastronomie
                return "gastronomie"
            if wz_code.startswith(("45", "47")):  # Handel
                return "einzelhandel"

        return "default"

    def _pro_treffer_kosten(
        self,
        partner: ApiPartner | None,
        qualitaets_stufe: str,
    ) -> float:
        """Get per-hit cost based on partner rates and quality tier."""
        if not partner:
            defaults = {
                RecherchQualitaetsStufe.STANDARD.value: 0.05,
                RecherchQualitaetsStufe.PREMIUM.value: 0.12,
                RecherchQualitaetsStufe.KOMPLETT.value: 0.18,
            }
            return defaults.get(qualitaets_stufe, 0.05)

        mapping = {
            RecherchQualitaetsStufe.STANDARD.value: partner.kosten_recherche_standard,
            RecherchQualitaetsStufe.PREMIUM.value: partner.kosten_recherche_premium,
            RecherchQualitaetsStufe.KOMPLETT.value: partner.kosten_recherche_komplett,
        }
        return mapping.get(qualitaets_stufe, partner.kosten_recherche_standard)
