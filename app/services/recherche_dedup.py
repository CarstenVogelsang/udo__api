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

from app.models.com import (
    ComUnternehmen,
    ComUnternehmenQuelldaten,
    ComExternalId,
    ComUnternehmenGoogleType,
)
from app.models.branche import BrnGoogleKategorie, BrnGoogleMapping
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

                # Update metadaten even for duplicates (newer data is better)
                neue_meta = self._extrahiere_metadaten(roh)
                if neue_meta:
                    bestehende = duplikat.metadaten or {}
                    bestehende.update(neue_meta)
                    duplikat.metadaten = bestehende

                # Fill missing strasse/email from raw data
                if roh.rohdaten and isinstance(roh.rohdaten, dict):
                    if not duplikat.strasse:
                        addr_info = roh.rohdaten.get('address_info') or {}
                        strasse = (addr_info.get('address') or '').strip()
                        if strasse:
                            duplikat.strasse = strasse[:255]
                    if not duplikat.email:
                        for ci in (roh.rohdaten.get('contact_info') or []):
                            if ci.get('type') == 'mail' and ci.get('value'):
                                duplikat.email = ci['value'].strip()[:255]
                                break

                # Upsert quelldaten (raw source data for re-processing)
                await self._upsert_quelldaten(duplikat.id, roh)

                # Upsert platform rating (Google, Yelp, etc.)
                await self._upsert_bewertung(duplikat.id, roh)

                # Update Google Types and WZ code (adds new types, keeps existing)
                await self._setze_google_types_und_wz_code(duplikat, roh)

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

        # Extract street and email from raw provider data
        strasse = None
        email_from_contact = None
        if roh.rohdaten and isinstance(roh.rohdaten, dict):
            addr_info = roh.rohdaten.get('address_info') or {}
            strasse = (addr_info.get('address') or '').strip() or None

            # Email from contact_info (DataForSEO finds emails via backlinks)
            if not roh.email:
                for ci in (roh.rohdaten.get('contact_info') or []):
                    if ci.get('type') == 'mail' and ci.get('value'):
                        email_from_contact = ci['value'].strip()
                        break

        email = roh.email or email_from_contact

        unternehmen = ComUnternehmen(
            kurzname=roh.name[:200] if roh.name else None,
            firmierung=roh.name[:255] if roh.name else None,
            adresszeile=roh.adresse[:500] if roh.adresse else None,
            strasse=strasse[:255] if strasse else None,
            website=roh.website[:255] if roh.website else None,
            email=email[:255] if email else None,
            telefon=roh.telefon[:50] if roh.telefon else None,
            geo_ort_id=geo_ort_id,
            metadaten=self._extrahiere_metadaten(roh),
        )
        self.db.add(unternehmen)
        await self.db.flush()

        # Create external ID reference
        if roh.externe_id:
            ext_id = ComExternalId(
                entity_type="unternehmen",
                entity_id=unternehmen.id,
                source_name=roh.quelle,
                id_type="place_id",
                external_value=roh.externe_id[:255],
            )
            self.db.add(ext_id)

        # Store raw source data for re-processing
        await self._upsert_quelldaten(unternehmen.id, roh)

        # Upsert platform rating (Google, Yelp, etc.)
        await self._upsert_bewertung(unternehmen.id, roh)

        # Set Google Types and derive WZ code
        await self._setze_google_types_und_wz_code(unternehmen, roh)

        await self.db.flush()
        return unternehmen

    # ---- Google Types and WZ-Code derivation ----

    async def _setze_google_types_und_wz_code(
        self,
        unternehmen: ComUnternehmen,
        roh: RecherchRohErgebnis,
    ) -> None:
        """Extract Google Place Types and derive WZ code.

        1. Extract category_ids from raw data (gcid:xxx format)
        2. Validate each gcid exists in brn_google_kategorie
        3. Create entries in com_unternehmen_google_type
        4. Derive WZ code from primary Google type via brn_google_mapping
        """
        if not roh.rohdaten or not isinstance(roh.rohdaten, dict):
            return

        # Extract Google category IDs (format: "gcid:chinese_restaurant")
        category_ids = roh.rohdaten.get('category_ids') or []
        if not category_ids:
            return

        wz_code_gefunden = None

        for i, gcid in enumerate(category_ids):
            # Validate gcid exists in brn_google_kategorie
            result = await self.db.execute(
                select(BrnGoogleKategorie).where(BrnGoogleKategorie.gcid == gcid)
            )
            google_kat = result.scalar_one_or_none()

            if not google_kat:
                logger.debug(f"Google category '{gcid}' not found in database, skipping")
                continue

            # Check if entry already exists (avoid duplicates)
            existing = await self.db.execute(
                select(ComUnternehmenGoogleType).where(
                    ComUnternehmenGoogleType.unternehmen_id == unternehmen.id,
                    ComUnternehmenGoogleType.gcid == gcid,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Create junction entry
            google_type = ComUnternehmenGoogleType(
                unternehmen_id=unternehmen.id,
                gcid=gcid,
                ist_primaer=(i == 0),  # First is primary
                ist_abgeleitet=False,  # Direct from provider
                quelle=roh.quelle,
            )
            self.db.add(google_type)

            # Try to derive WZ code from the first (primary) Google type
            if i == 0 and not wz_code_gefunden:
                mapping_result = await self.db.execute(
                    select(BrnGoogleMapping).where(
                        BrnGoogleMapping.gcid == gcid,
                        BrnGoogleMapping.ist_primaer == True,
                    )
                )
                mapping = mapping_result.scalar_one_or_none()
                if mapping:
                    wz_code_gefunden = mapping.wz_code
                    logger.debug(
                        f"Derived WZ code '{wz_code_gefunden}' from gcid '{gcid}'"
                    )

        # Set WZ code on company if found
        if wz_code_gefunden:
            unternehmen.wz_code = wz_code_gefunden

    # ---- Rich data extraction ----

    def _extrahiere_metadaten(self, roh: RecherchRohErgebnis) -> dict:
        """Extract structured metadata from raw provider data."""
        if not roh.rohdaten or not isinstance(roh.rohdaten, dict):
            return {}

        raw = roh.rohdaten
        meta = {}

        if roh.quelle == 'dataforseo':
            google = {}

            # External IDs
            if raw.get('place_id'):
                google['place_id'] = raw['place_id']
            if raw.get('cid'):
                google['cid'] = raw['cid']

            # Rating
            rating_data = raw.get('rating') or {}
            if rating_data.get('value'):
                google['rating'] = rating_data['value']
                google['rating_count'] = rating_data.get('votes_count')
            if raw.get('rating_distribution'):
                google['rating_distribution'] = raw['rating_distribution']

            # Business metadata
            if raw.get('price_level'):
                google['price_level'] = raw['price_level']
            if raw.get('is_claimed') is not None:
                google['is_claimed'] = raw['is_claimed']

            # Images
            if raw.get('main_image'):
                google['main_image'] = raw['main_image']
            if raw.get('logo'):
                google['logo'] = raw['logo']
            if raw.get('total_photos'):
                google['total_photos'] = raw['total_photos']

            # Categories
            if raw.get('category'):
                google['categories'] = [raw['category']]
                if raw.get('additional_categories'):
                    google['categories'].extend(raw['additional_categories'])
            if raw.get('category_ids'):
                google['category_ids'] = raw['category_ids']

            # Place topics
            if raw.get('place_topics'):
                google['place_topics'] = raw['place_topics']

            # Attributes (only available_attributes, skip unavailable)
            attrs_raw = raw.get('attributes') or {}
            available = attrs_raw.get('available_attributes') or {}
            if available:
                google['attributes'] = available

            # Opening hours (simplified format)
            work_time = raw.get('work_time') or {}
            work_hours = work_time.get('work_hours') or {}
            timetable = work_hours.get('timetable')
            if timetable:
                oeffnungszeiten = {}
                for day, slots in timetable.items():
                    if slots is None:
                        oeffnungszeiten[day] = None
                    else:
                        oeffnungszeiten[day] = [
                            {
                                'open': f"{s['open']['hour']:02d}:{s['open']['minute']:02d}",
                                'close': f"{s['close']['hour']:02d}:{s['close']['minute']:02d}",
                            }
                            for s in slots
                        ]
                google['oeffnungszeiten'] = oeffnungszeiten

            # Coordinates
            if raw.get('latitude'):
                google['lat'] = raw['latitude']
                google['lng'] = raw['longitude']

            # People also search (compact, max 10)
            if raw.get('people_also_search'):
                google['people_also_search'] = [
                    {
                        'title': p.get('title'),
                        'cid': p.get('cid'),
                        'rating': (p.get('rating') or {}).get('value'),
                    }
                    for p in raw['people_also_search'][:10]
                ]

            if google:
                google['_provider'] = 'dataforseo'
                google['_fetched_at'] = datetime.utcnow().isoformat()
                meta['google'] = google

        return meta

    async def _upsert_quelldaten(
        self,
        unternehmen_id: str,
        roh: RecherchRohErgebnis,
    ) -> None:
        """Store or update raw source data for a company."""
        if not roh.rohdaten:
            return

        existing = await self.db.execute(
            select(ComUnternehmenQuelldaten).where(
                ComUnternehmenQuelldaten.unternehmen_id == unternehmen_id,
                ComUnternehmenQuelldaten.provider == roh.quelle,
                ComUnternehmenQuelldaten.provider_id == roh.externe_id,
            )
        )
        qd = existing.scalar_one_or_none()
        if qd:
            qd.rohdaten = roh.rohdaten
            qd.aktualisiert_am = datetime.utcnow()
        else:
            self.db.add(ComUnternehmenQuelldaten(
                unternehmen_id=unternehmen_id,
                provider=roh.quelle,
                provider_id=roh.externe_id,
                rohdaten=roh.rohdaten,
            ))

    async def _upsert_bewertung(
        self,
        unternehmen_id: str,
        roh: RecherchRohErgebnis,
    ) -> None:
        """Create or update platform rating from raw result data."""
        if not roh.rohdaten or not isinstance(roh.rohdaten, dict):
            return

        raw = roh.rohdaten

        if roh.quelle == 'dataforseo':
            rating_data = raw.get('rating') or {}
            if not rating_data.get('value'):
                return

            # Resolve Google platform
            from app.models.base import BasBewertungsplattform
            from app.models.com import ComUnternehmenBewertung

            result = await self.db.execute(
                select(BasBewertungsplattform).where(
                    BasBewertungsplattform.code == 'google'
                )
            )
            plattform = result.scalar_one_or_none()
            if not plattform:
                logger.warning("Platform 'google' not found in bas_bewertungsplattform")
                return

            # Upsert: check if rating already exists
            existing = await self.db.execute(
                select(ComUnternehmenBewertung).where(
                    ComUnternehmenBewertung.unternehmen_id == unternehmen_id,
                    ComUnternehmenBewertung.plattform_id == plattform.id,
                )
            )
            bewertung = existing.scalar_one_or_none()

            if bewertung:
                bewertung.bewertung = rating_data['value']
                bewertung.anzahl_bewertungen = rating_data.get('votes_count')
                bewertung.verteilung = raw.get('rating_distribution')
                bewertung.aktualisiert_am = datetime.utcnow()
            else:
                self.db.add(ComUnternehmenBewertung(
                    unternehmen_id=unternehmen_id,
                    plattform_id=plattform.id,
                    bewertung=rating_data['value'],
                    anzahl_bewertungen=rating_data.get('votes_count'),
                    verteilung=raw.get('rating_distribution'),
                ))

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
