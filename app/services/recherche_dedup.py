"""Deduplication service for recherche raw results.

Compares raw results from external providers against existing
companies in com_unternehmen to avoid duplicates.

Deduplication strategy (ordered by confidence):
1. Exact phone number match
2. Normalized website domain match
3. Fuzzy name match (>85%) + same PLZ
"""
import logging
import re
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import urlparse

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.com import ComUnternehmen
from app.models.geo import GeoOrt
from app.models.recherche import RecherchRohErgebnis

logger = logging.getLogger(__name__)


class RecherchDeduplizierungService:
    """Deduplicates raw recherche results against existing companies."""

    # Minimum similarity for name-based dedup
    NAME_SIMILARITY_THRESHOLD = 0.85

    def __init__(self, db: AsyncSession):
        self.db = db

    async def deduplizieren(
        self,
        auftrag_id: str,
    ) -> dict:
        """Run deduplication for all unprocessed raw results of an order.

        Returns:
            Stats dict: {'duplikate': int, 'neue': int, 'aktualisiert': int}
        """
        # Load all unprocessed raw results
        result = await self.db.execute(
            select(RecherchRohErgebnis).where(
                RecherchRohErgebnis.auftrag_id == auftrag_id,
                RecherchRohErgebnis.verarbeitet_am.is_(None),
            )
        )
        rohergebnisse = list(result.scalars().all())

        stats = {"duplikate": 0, "neue": 0, "aktualisiert": 0}

        for roh in rohergebnisse:
            duplikat = await self._finde_duplikat(roh)

            if duplikat:
                roh.ist_duplikat = True
                roh.duplikat_von_id = duplikat.id
                roh.verarbeitet_am = datetime.utcnow()
                stats["duplikate"] += 1
                logger.debug(
                    f"Duplicate: '{roh.name}' matches existing '{duplikat.kurzname}'"
                )
            else:
                # Create new ComUnternehmen
                unternehmen = await self._erstelle_unternehmen(roh)
                roh.ist_duplikat = False
                roh.unternehmen_id = unternehmen.id
                roh.verarbeitet_am = datetime.utcnow()
                stats["neue"] += 1

        await self.db.flush()
        logger.info(
            f"Dedup completed for order {auftrag_id[:8]}...: "
            f"{stats['duplikate']} duplicates, {stats['neue']} new"
        )
        return stats

    async def _finde_duplikat(
        self,
        roh: RecherchRohErgebnis,
    ) -> ComUnternehmen | None:
        """Try to find an existing company that matches this raw result.

        Checks in order of confidence:
        1. Phone number (exact match, normalized)
        2. Website domain (normalized)
        3. Name similarity + PLZ
        """
        # 1. Phone match
        if roh.telefon:
            match = await self._match_telefon(roh.telefon)
            if match:
                return match

        # 2. Website domain match
        if roh.website:
            match = await self._match_website(roh.website)
            if match:
                return match

        # 3. Fuzzy name + PLZ match
        if roh.name and roh.plz:
            match = await self._match_name_plz(roh.name, roh.plz)
            if match:
                return match

        return None

    async def _match_telefon(self, telefon: str) -> ComUnternehmen | None:
        """Find company by normalized phone number."""
        normalized = self._normalize_telefon(telefon)
        if not normalized or len(normalized) < 6:
            return None

        result = await self.db.execute(
            select(ComUnternehmen).where(
                ComUnternehmen.geloescht_am.is_(None),
                ComUnternehmen.telefon.isnot(None),
            ).limit(500)  # Scan limit for safety
        )
        companies = result.scalars().all()

        for company in companies:
            if company.telefon:
                if self._normalize_telefon(company.telefon) == normalized:
                    return company

        return None

    async def _match_website(self, website: str) -> ComUnternehmen | None:
        """Find company by normalized website domain."""
        domain = self._normalize_domain(website)
        if not domain:
            return None

        result = await self.db.execute(
            select(ComUnternehmen).where(
                ComUnternehmen.geloescht_am.is_(None),
                ComUnternehmen.website.isnot(None),
            ).limit(500)
        )
        companies = result.scalars().all()

        for company in companies:
            if company.website:
                if self._normalize_domain(company.website) == domain:
                    return company

        return None

    async def _match_name_plz(
        self,
        name: str,
        plz: str,
    ) -> ComUnternehmen | None:
        """Find company by fuzzy name match within same PLZ area."""
        # Get all Orte with this PLZ
        ort_result = await self.db.execute(
            select(GeoOrt.id).where(GeoOrt.plz == plz)
        )
        ort_ids = [row[0] for row in ort_result.all()]

        if not ort_ids:
            return None

        # Get companies in these Orte
        result = await self.db.execute(
            select(ComUnternehmen).where(
                ComUnternehmen.geloescht_am.is_(None),
                ComUnternehmen.geo_ort_id.in_(ort_ids),
            ).limit(500)
        )
        companies = result.scalars().all()

        normalized_name = self._normalize_name(name)

        for company in companies:
            if company.kurzname:
                similarity = SequenceMatcher(
                    None,
                    normalized_name,
                    self._normalize_name(company.kurzname),
                ).ratio()
                if similarity >= self.NAME_SIMILARITY_THRESHOLD:
                    return company

        return None

    async def _erstelle_unternehmen(
        self,
        roh: RecherchRohErgebnis,
    ) -> ComUnternehmen:
        """Create a new ComUnternehmen from a raw result."""
        # Try to find the GeoOrt for this result
        geo_ort_id = None
        if roh.plz:
            result = await self.db.execute(
                select(GeoOrt.id).where(GeoOrt.plz == roh.plz).limit(1)
            )
            row = result.first()
            if row:
                geo_ort_id = row[0]

        unternehmen = ComUnternehmen(
            kurzname=roh.name[:200] if roh.name else None,
            firmierung=roh.name[:255] if roh.name else None,
            adresszeile=roh.adresse[:500] if roh.adresse else None,
            website=roh.website[:255] if roh.website else None,
            email=roh.email[:255] if roh.email else None,
            telefon=roh.telefon[:50] if roh.telefon else None,
            geo_ort_id=geo_ort_id,
        )
        self.db.add(unternehmen)
        await self.db.flush()

        # Create external ID reference
        if roh.externe_id:
            from app.models.com import ComExternalId
            ext_id = ComExternalId(
                entity_type="unternehmen",
                entity_id=unternehmen.id,
                source_name=roh.quelle,
                id_type="place_id",
                external_value=roh.externe_id[:255],
            )
            self.db.add(ext_id)
            await self.db.flush()

        return unternehmen

    # ---- Normalization helpers ----

    @staticmethod
    def _normalize_telefon(telefon: str) -> str:
        """Normalize phone number: remove all non-digit chars."""
        digits = re.sub(r'\D', '', telefon)
        # Remove country prefix (0049, +49 → starts with 49)
        if digits.startswith('0049'):
            digits = digits[4:]
        elif digits.startswith('49') and len(digits) > 10:
            digits = digits[2:]
        # Remove leading zero
        if digits.startswith('0'):
            digits = digits[1:]
        return digits

    @staticmethod
    def _normalize_domain(url: str) -> str:
        """Extract and normalize domain from URL."""
        if not url:
            return ""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize company name for comparison."""
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in (' gmbh', ' gbr', ' ohg', ' kg', ' e.k.', ' ag', ' ug'):
            name = name.replace(suffix, '')
        # Remove special chars
        name = re.sub(r'[^\w\s]', '', name)
        # Collapse whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        return name
